import base64
import datetime
import hashlib
import hmac
import json
import math
import time
from pathlib import Path
from time import mktime
from urllib.parse import urlparse
from wsgiref.handlers import format_date_time

import requests
from urllib3 import encode_multipart_formdata

from app.worker.asr.base import AsrResult, AsrSegment


class IflytekSpeedAsrProvider:
    upload_host = "upload-ost-api.xfyun.cn"
    api_host = "ost-api.xfyun.cn"
    upload_api = "/file/upload"
    mpupload_init = "/file/mpupload/init"
    mpupload_upload = "/file/mpupload/upload"
    mpupload_complete = "/file/mpupload/complete"
    task_create_uri = "/v2/ost/pro_create"
    task_query_uri = "/v2/ost/query"
    chunk_size = 5 * 1024 * 1024
    direct_upload_limit = 30 * 1024 * 1024
    max_audio_size = 500 * 1024 * 1024
    sample_rates = {
        3: [44100, 48000, 32000, 0],
        2: [22050, 24000, 16000, 0],
        0: [11025, 12000, 8000, 0],
    }

    def __init__(
        self,
        app_id: str,
        api_key: str,
        api_secret: str,
        *,
        language: str = "zh_cn",
        accent: str = "mandarin",
        domain: str = "pro_ost_ed",
        vspp_on: int = 1,
    ):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.language = language
        self.accent = accent
        self.domain = domain
        self.vspp_on = vspp_on

    def validate_audio_file(self, file_path: Path) -> None:
        if file_path.suffix.lower() != ".mp3":
            raise ValueError("Only MP3 audio is supported by the first iFLYTEK integration")
        if file_path.exists() and file_path.stat().st_size > self.max_audio_size:
            raise ValueError("Audio file exceeds the 500MB iFLYTEK limit")
        if file_path.exists():
            header = file_path.read_bytes()[:16]
            has_id3_tag = header.startswith(b"ID3")
            has_mp3_frame_sync = len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0
            if not has_id3_tag and not has_mp3_frame_sync:
                raise ValueError(
                    "The uploaded file is not a valid MP3 audio stream. "
                    "Please export or convert it to real MP3 with lame encoding.",
                )
            audio_info = self._read_first_mp3_frame_info(header)
            if audio_info is not None and (audio_info["sample_rate"] != 16000 or audio_info["channel_mode"] != 3):
                raise ValueError(
                    "iFLYTEK speed transcription requires 16kHz mono MP3 audio. "
                    f"Detected sample_rate={audio_info['sample_rate']}Hz, "
                    f"channel_mode={audio_info['channel_mode']}.",
                )

    def _read_first_mp3_frame_info(self, header: bytes) -> dict[str, int] | None:
        if len(header) < 4 or not (header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
            return None
        value = int.from_bytes(header[:4], "big")
        version = (value >> 19) & 0b11
        layer = (value >> 17) & 0b11
        sample_rate_index = (value >> 10) & 0b11
        channel_mode = (value >> 6) & 0b11
        if version == 1 or layer != 1 or sample_rate_index == 3:
            return None
        return {
            "sample_rate": self.sample_rates[version][sample_rate_index],
            "channel_mode": channel_mode,
        }

    def _request_id(self) -> str:
        return time.strftime("%Y%m%d%H%M%S")

    def _digest(self, body: bytes = b"") -> str:
        return "SHA-256=" + base64.b64encode(hashlib.sha256(body).digest()).decode("utf-8")

    def build_auth_headers(
        self,
        *,
        url: str,
        content_type: str,
        method: str = "POST",
        body: bytes = b"",
    ) -> dict[str, str]:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        date = format_date_time(mktime(datetime.datetime.now().timetuple()))
        digest = self._digest(body)
        signature_origin = f"host: {host}\ndate: {date}\n{method} {parsed.path} HTTP/1.1\ndigest: {digest}"
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        authorization = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line digest", signature="{base64.b64encode(signature).decode("utf-8")}"'
        )
        return {
            "host": host,
            "date": date,
            "authorization": authorization,
            "digest": digest,
            "content-type": content_type,
        }

    def _post(self, url: str, body: bytes, content_type: str) -> dict:
        headers = self.build_auth_headers(url=url, content_type=content_type, body=body)
        response = requests.post(url, headers=headers, data=body, timeout=60)
        try:
            result = response.json()
        except ValueError as exc:
            if response.status_code >= 400:
                raise RuntimeError(f"iFLYTEK HTTP {response.status_code}: {response.text}") from exc
            raise
        if response.status_code >= 400:
            raise RuntimeError(
                f"iFLYTEK HTTP {response.status_code}: "
                f"code={result.get('code')}, message={result.get('message', response.text)}",
            )
        if result.get("code") != 0:
            raise RuntimeError(result.get("message", "iFLYTEK API request failed"))
        return result

    def upload_audio(self, file_path: Path) -> str:
        self.validate_audio_file(file_path)
        if file_path.stat().st_size < self.direct_upload_limit:
            return self._upload_small_file(file_path)
        return self._upload_large_file(file_path)

    def _upload_small_file(self, file_path: Path) -> str:
        url = f"https://{self.upload_host}{self.upload_api}"
        fields = {
            "data": (str(file_path), file_path.read_bytes()),
            "app_id": self.app_id,
            "request_id": self._request_id(),
        }
        body, content_type = encode_multipart_formdata(fields)
        result = self._post(url, body, content_type)
        return result["data"]["url"]

    def _upload_large_file(self, file_path: Path) -> str:
        upload_id = self._init_multipart_upload()
        file_size = file_path.stat().st_size
        chunk_count = math.ceil(file_size / self.chunk_size)

        with file_path.open("rb") as file:
            for slice_id in range(1, chunk_count + 1):
                chunk = file.read(self.chunk_size)
                self._upload_multipart_chunk(file_path, upload_id, slice_id, chunk)

        return self._complete_multipart_upload(upload_id)

    def _init_multipart_upload(self) -> str:
        url = f"https://{self.upload_host}{self.mpupload_init}"
        body = json.dumps({"app_id": self.app_id, "request_id": self._request_id()}).encode("utf-8")
        result = self._post(url, body, "application/json")
        return result["data"]["upload_id"]

    def _upload_multipart_chunk(self, file_path: Path, upload_id: str, slice_id: int, chunk: bytes) -> None:
        url = f"https://{self.upload_host}{self.mpupload_upload}"
        fields = {
            "data": (str(file_path), chunk),
            "app_id": self.app_id,
            "request_id": self._request_id(),
            "upload_id": upload_id,
            "slice_id": slice_id,
        }
        body, content_type = encode_multipart_formdata(fields)
        self._post(url, body, content_type)

    def _complete_multipart_upload(self, upload_id: str) -> str:
        url = f"https://{self.upload_host}{self.mpupload_complete}"
        body = json.dumps(
            {
                "app_id": self.app_id,
                "request_id": self._request_id(),
                "upload_id": upload_id,
            },
        ).encode("utf-8")
        result = self._post(url, body, "application/json")
        return result["data"]["url"]

    def create_task(
        self,
        audio_url: str,
        *,
        language: str,
        accent: str,
        domain: str,
        vspp_on: int,
    ) -> str:
        url = f"https://{self.api_host}{self.task_create_uri}"
        body = json.dumps(
            {
                "common": {"app_id": self.app_id},
                "business": {
                    "request_id": self._request_id(),
                    "language": language,
                    "accent": accent,
                    "domain": domain,
                    "vspp_on": vspp_on,
                },
                "data": {
                    "audio_url": audio_url,
                    "audio_src": "http",
                    "format": "audio/mp3",
                    "encoding": "lame",
                },
            },
        ).encode("utf-8")
        result = self._post(url, body, "application/json")
        return result["data"]["task_id"]

    def query_task(self, task_id: str) -> dict:
        url = f"https://{self.api_host}{self.task_query_uri}"
        body = json.dumps(
            {
                "common": {"app_id": self.app_id},
                "business": {"task_id": task_id},
            },
        ).encode("utf-8")
        return self._post(url, body, "application/json")

    def transcribe(self, file_path: Path) -> AsrResult:
        audio_url = self.upload_audio(file_path)
        task_id = self.create_task(
            audio_url,
            language=self.language,
            accent=self.accent,
            domain=self.domain,
            vspp_on=self.vspp_on,
        )

        for _ in range(120):
            time.sleep(5)
            response = self.query_task(task_id)
            status = response.get("data", {}).get("task_status")
            if status in {"3", "4"}:
                return self.parse_result(response)
            if status == "-1":
                raise RuntimeError(response.get("data", {}).get("message", "iFLYTEK transcription failed"))

        raise TimeoutError("iFLYTEK transcription did not finish in time")

    def parse_result(self, response: dict) -> AsrResult:
        lattice = response.get("data", {}).get("result", {}).get("lattice", [])
        full_text: list[str] = []
        segments: list[AsrSegment] = []

        for item in lattice:
            text = self._parse_lattice_text(item)
            if not text:
                continue
            full_text.append(text)
            segments.append(
                AsrSegment(
                    speaker=item.get("spk", "speaker-0"),
                    begin=int(item.get("begin", 0)),
                    end=int(item.get("end", 0)),
                    text=text,
                ),
            )

        return AsrResult(text="".join(full_text), segments=segments, raw=response)

    def _parse_lattice_text(self, item: dict) -> str:
        words: list[str] = []
        rt_list = item.get("json_1best", {}).get("st", {}).get("rt", [])
        for rt in rt_list:
            for ws in rt.get("ws", []):
                for cw in ws.get("cw", []):
                    if cw.get("wp", "n") != "g":
                        words.append(cw.get("w", ""))
        return "".join(words)
