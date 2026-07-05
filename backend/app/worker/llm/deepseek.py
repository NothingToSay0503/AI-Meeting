import json
import re
from datetime import date, timedelta

from langchain_openai import ChatOpenAI

from app.worker.llm.base import MinutesResult


WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _next_weekday(base_date: date, weekday: int) -> date:
    days_until_next_week = 7 - base_date.weekday()
    return base_date + timedelta(days=days_until_next_week + weekday)


def build_minutes_prompt(transcript: str, *, today: date | None = None) -> str:
    current_date = today or date.today()
    weekday_label = WEEKDAY_CN[current_date.weekday()]
    next_tuesday = _next_weekday(current_date, 1)
    return (
        "请从会议转写文本中提取结构化纪要，只返回 JSON，不要返回 Markdown 代码块或解释文字。\n"
        "JSON 字段必须包含 topic, participants, key_points, decisions, todos。\n"
        "todos 每项包含 description, assignee_name, due_date, source_sentence, confidence。\n"
        f"当前日期工具结果：{current_date.isoformat()}（{weekday_label}）。\n"
        "如果会议记录没有明确说明会议日期，默认本次会议就是当前日期召开。\n"
        "请以会议日期为基准推断相对截止时间，例如今天、明天、本周五、下周二、月底、下班前。\n"
        f"日期推断示例：若当前日期是 {current_date.isoformat()}（{weekday_label}），"
        f"会议中提到“下周二下班前完成”，due_date 应输出 {next_tuesday.isoformat()}。\n"
        "due_date 必须只输出 YYYY-MM-DD；无法从文本和会议日期推断时输出 null。\n\n"
        f"会议转写：{transcript}"
    )


def _parse_model_json(content: str) -> MinutesResult:
    cleaned = content.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
    return MinutesResult.model_validate(json.loads(cleaned))


class DeepSeekMinutesProvider:
    def __init__(self, *, api_key: str, base_url: str, model: str):
        self.model = ChatOpenAI(api_key=api_key, base_url=base_url, model=model, temperature=0)

    def summarize(self, transcript: str) -> MinutesResult:
        prompt = build_minutes_prompt(transcript)
        response = self.model.invoke(prompt)
        return _parse_model_json(response.content)
