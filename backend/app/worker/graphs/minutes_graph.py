from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.worker.llm.base import MinutesProvider, MinutesResult


class MinutesState(TypedDict):
    transcript: str
    provider: MinutesProvider
    result: MinutesResult | None


def load_transcript(state: MinutesState) -> MinutesState:
    return state


def clean_and_chunk(state: MinutesState) -> MinutesState:
    return {**state, "transcript": " ".join(state["transcript"].split())}


def summarize_minutes(state: MinutesState) -> MinutesState:
    return {**state, "result": state["provider"].summarize(state["transcript"])}


def build_minutes_graph():
    graph = StateGraph(MinutesState)
    graph.add_node("load_transcript", load_transcript)
    graph.add_node("clean_and_chunk", clean_and_chunk)
    graph.add_node("summarize_minutes", summarize_minutes)
    graph.set_entry_point("load_transcript")
    graph.add_edge("load_transcript", "clean_and_chunk")
    graph.add_edge("clean_and_chunk", "summarize_minutes")
    graph.add_edge("summarize_minutes", END)
    return graph.compile()


def run_minutes_graph(transcript: str, provider: MinutesProvider) -> MinutesResult:
    result = build_minutes_graph().invoke(
        {"transcript": transcript, "provider": provider, "result": None}
    )
    return result["result"]
