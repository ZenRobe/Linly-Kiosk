"""LLM token delta 流的分句工具。

把流式到达的 token 切成「完整句」，供 TTS 逐句合成，降低首音延迟。
纯逻辑、无 IO，便于单测。
"""
from typing import Iterable, Iterator

# 句末标点：遇之立即切句
_SENTENCE_END = set("。！？!?…\n")
# 软标点：累积达到 _SOFT_MIN 字时才切，避免短句碎片
_SOFT_CUT = set("，,;；")
_SOFT_MIN = 12


class SentenceSplitter:
    """增量分句器：逐个 feed delta，返回本次产出的完整句列表。"""

    def __init__(self) -> None:
        self._buf: list[str] = []

    def feed(self, delta: str) -> list[str]:
        out: list[str] = []
        for ch in delta:
            self._buf.append(ch)
            if ch in _SENTENCE_END:
                out.append("".join(self._buf))
                self._buf = []
            elif ch in _SOFT_CUT and len(self._buf) >= _SOFT_MIN:
                out.append("".join(self._buf))
                self._buf = []
        return out

    def flush(self) -> list[str]:
        if self._buf:
            sentence = "".join(self._buf)
            self._buf = []
            return [sentence]
        return []


def sentence_chunks(deltas: Iterable[str]) -> Iterator[str]:
    """函数式包装：消费 delta 可迭代对象，产出完整句。"""
    sp = SentenceSplitter()
    for delta in deltas:
        for sentence in sp.feed(delta):
            yield sentence
    for sentence in sp.flush():
        yield sentence
