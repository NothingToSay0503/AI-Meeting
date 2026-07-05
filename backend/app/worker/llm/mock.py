from app.worker.llm.base import ExtractedTodo, MinutesResult


class MockMinutesProvider:
    def summarize(self, transcript: str) -> MinutesResult:
        return MinutesResult(
            topic="项目周会",
            participants=["张三", "李四"],
            key_points=["确认接口字段差异", "推进测试环境准备"],
            decisions=["本周五前完成接口字段差异清单"],
            todos=[
                ExtractedTodo(
                    description="整理接口字段差异清单",
                    assignee_name="张三",
                    due_date=None,
                    source_sentence="张三负责整理接口字段差异清单，周五完成。",
                    confidence=0.86,
                ),
            ],
            raw={"provider": "mock", "transcript_length": len(transcript)},
        )
