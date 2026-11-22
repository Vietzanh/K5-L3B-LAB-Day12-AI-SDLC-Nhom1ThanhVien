"""Ghi JSONL tất định: làm tròn 3 chữ số khi XUẤT (tính toán dùng giá trị chính xác)."""

import json


# v1.2: độ tươi xuất ĐỦ chính xác (không làm tròn) để snapshot/gather_end khớp từng giá trị với file kho
# (Ticket-03: "so chính xác id, kind và độ tươi"); vẫn tất định vì repr float cố định. Xem docs/clarify.md.
EXACT_KEYS = {"fresh"}


def _clean(v, key=None):
    if isinstance(v, float):
        if key in EXACT_KEYS:
            return v
        r = round(v, 3)
        return 0.0 if r == 0 else r  # tránh -0.0
    if isinstance(v, dict):
        return {k: _clean(x, k) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    return v


def dumps(obj) -> str:
    return json.dumps(_clean(obj), ensure_ascii=False, separators=(",", ":"))


class JsonlWriter:
    def __init__(self, path: str):
        self._f = open(path, "w", encoding="utf-8", newline="\n")

    def write(self, obj):
        self._f.write(dumps(obj) + "\n")

    def close(self):
        self._f.close()
