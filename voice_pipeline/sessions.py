"""内存会话历史管理（线程安全）"""
import threading
import time

_lock = threading.Lock()
_history: dict[str, list[dict]] = {}


def get_history(session_id: str) -> list[dict]:
    """返回该 session 的历史副本，避免外部修改内部状态。"""
    with _lock:
        return [dict(m) for m in _history.get(session_id, [])]


def append_message(session_id: str, role: str, content: str) -> None:
    with _lock:
        _history.setdefault(session_id, []).append(
            {"role": role, "content": content, "ts": time.time()}
        )


def reset() -> None:
    """清空所有历史（测试用）。"""
    with _lock:
        _history.clear()
