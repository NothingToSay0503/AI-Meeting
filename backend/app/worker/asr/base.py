from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class AsrSegment:
    speaker: str
    begin: int
    end: int
    text: str


@dataclass(frozen=True)
class AsrResult:
    text: str
    segments: list[AsrSegment]
    raw: dict


class AsrProvider(Protocol):
    def transcribe(self, file_path: Path) -> AsrResult:
        raise NotImplementedError
