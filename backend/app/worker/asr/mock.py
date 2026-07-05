from pathlib import Path

from app.worker.asr.base import AsrResult, AsrSegment


class MockAsrProvider:
    def transcribe(self, file_path: Path) -> AsrResult:
        text = "项目会议开始。张三负责整理接口字段差异清单，周五完成。李四负责跟进测试环境。浼氳"
        return AsrResult(
            text=text,
            segments=[
                AsrSegment(speaker="spk-0", begin=0, end=3200, text="项目会议开始。"),
                AsrSegment(speaker="spk-1", begin=3200, end=9000, text="张三负责整理接口字段差异清单，周五完成。"),
                AsrSegment(speaker="spk-2", begin=9000, end=12500, text="李四负责跟进测试环境。"),
            ],
            raw={"provider": "mock", "file_name": file_path.name},
        )
