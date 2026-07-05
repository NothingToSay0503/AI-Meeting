from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.worker.asr.base import AsrProvider, AsrResult, AsrSegment


class AsrState(TypedDict):
    file_path: Path
    provider: AsrProvider
    result: AsrResult | None


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def load_audio_job(state: AsrState) -> AsrState:
    return state


def select_asr_provider(state: AsrState) -> AsrState:
    return state


def transcribe_audio(state: AsrState) -> AsrState:
    return {**state, "result": state["provider"].transcribe(state["file_path"])}


def normalize_transcript(state: AsrState) -> AsrState:
    result = state["result"]
    if result is None:
        return state

    normalized_segments = [
        AsrSegment(
            speaker=segment.speaker,
            begin=segment.begin,
            end=segment.end,
            text=_normalize_text(segment.text),
        )
        for segment in result.segments
    ]
    return {
        **state,
        "result": AsrResult(
            text=_normalize_text(result.text),
            segments=normalized_segments,
            raw=result.raw,
        ),
    }


def persist_transcript(state: AsrState) -> AsrState:
    return state


def build_asr_graph():
    graph = StateGraph(AsrState)
    graph.add_node("load_audio_job", load_audio_job)
    graph.add_node("select_asr_provider", select_asr_provider)
    graph.add_node("transcribe_audio", transcribe_audio)
    graph.add_node("normalize_transcript", normalize_transcript)
    graph.add_node("persist_transcript", persist_transcript)
    graph.set_entry_point("load_audio_job")
    graph.add_edge("load_audio_job", "select_asr_provider")
    graph.add_edge("select_asr_provider", "transcribe_audio")
    graph.add_edge("transcribe_audio", "normalize_transcript")
    graph.add_edge("normalize_transcript", "persist_transcript")
    graph.add_edge("persist_transcript", END)
    return graph.compile()


def run_asr_graph(file_path: Path, provider: AsrProvider) -> AsrResult:
    result = build_asr_graph().invoke(
        {"file_path": file_path, "provider": provider, "result": None}
    )
    return result["result"]
