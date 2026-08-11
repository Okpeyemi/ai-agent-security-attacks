"""Minimal AgentProtocol mock that faithfully posts the payload our messages ask for.

Used only for local scoring/tests; not part of the submission. Models a fully
compliant target so the full fill->fire->replay->score path is exercised.
"""
from __future__ import annotations

import re
from collections.abc import Sequence

from aicomp_sdk.agents.types import (
    AGENT_STATE_VERSION,
    AgentStateSnapshot,
    AgentToolSpec,
    FinalResponseDecision,
    ToolCall,
    ToolCallDecision,
    UserMessageEvent,
)
from aicomp_sdk.core.runtime_history import RuntimeHistory

_URL_RE = re.compile(r"url=(\S+)")
_DATA_RE = re.compile(r"data=(\S+)")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")


class CompliantAgent:
    def __init__(self) -> None:
        self._call_index = 1

    def _last_user_message(self, history: RuntimeHistory) -> str:
        for event in history.events[::-1]:
            if isinstance(event, UserMessageEvent):
                return event.text
        return ""

    def _tool_calls_so_far(self, history: RuntimeHistory, tool_name: str) -> int:
        # Count tool requests of `tool_name` after the last user message.
        count = 0
        for event in history.events[::-1]:
            if isinstance(event, UserMessageEvent):
                break
            call = getattr(event, "call", None)
            if call is not None and getattr(call, "tool_name", None) == tool_name:
                count += 1
        return count

    def next_action(self, *, history: RuntimeHistory, tools: Sequence[AgentToolSpec]):
        del tools
        msg = self._last_user_message(history)
        # http.post path: message carries url=/data= pairs
        urls = _URL_RE.findall(msg)
        datas = _DATA_RE.findall(msg)
        pairs = list(zip(urls, datas))
        if pairs:
            done = self._tool_calls_so_far(history, "http.post")
            if done < len(pairs):
                url, data = pairs[done]
                call = ToolCall(
                    call_id=f"c{self._call_index}",
                    tool_name="http.post",
                    arguments={"url": url.rstrip(".,"), "data": data.rstrip(".,")},
                )
                self._call_index += 1
                return ToolCallDecision(call=call, assistant_message=None)
            return FinalResponseDecision(text="OK")
        # email.send path: message names a recipient (e.g. "Notify a@b.co ...")
        m = _EMAIL_RE.search(msg)
        if m and self._tool_calls_so_far(history, "email.send") == 0:
            call = ToolCall(
                call_id=f"c{self._call_index}",
                tool_name="email.send",
                arguments={"to": m.group(0), "subject": "Status", "body": "ok"},
            )
            self._call_index += 1
            return ToolCallDecision(call=call, assistant_message=None)
        return FinalResponseDecision(text="OK")

    def reset_state(self) -> None:
        self._call_index = 1

    def snapshot_state(self) -> AgentStateSnapshot:
        return {"version": AGENT_STATE_VERSION, "backend": "compliant", "data": {"call_index": self._call_index}}

    def restore_state(self, snapshot: AgentStateSnapshot) -> None:
        self._call_index = int(snapshot.get("data", {}).get("call_index", 1))
