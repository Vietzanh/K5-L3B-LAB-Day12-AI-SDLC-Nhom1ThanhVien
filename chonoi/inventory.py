"""File kho v1.2 (Ticket-03): {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}.

Cá thể nội bộ: {"id", "kind", "u"} với `u` = đơn vị tươi (240 đơn vị / 1 điểm, ADR-0001) để so ngưỡng 30
và tính giá chính xác; chỉ đổi sang `fresh = u / 240` khi xuất.
Đọc: từ chối kho đếm (object), sai schema, kind lạ, id trùng/rỗng, fresh ngoài [0, 100] (BadInput -> mã 2).
Ghi: sắp theo id, fresh đủ chính xác (repr float) để đọc lại ra đúng `u`; qua file tạm cùng thư mục rồi thay thế.
"""

import json
import math
import os
import tempfile

from .contract import INGREDIENTS
from .errors import BadInput
from .ids import sort_by_id

KINDS_P1 = INGREDIENTS  # giữ tên cũ cho mã đang import
SCALE = 240  # đơn vị tươi / 1 điểm


def to_units(fresh):
    u = fresh * SCALE
    r = round(u)
    return r if abs(u - r) < 1e-6 else u


def fresh_of(u):
    return u / SCALE


def view(it) -> dict:
    return {"id": it["id"], "kind": it["kind"], "fresh": fresh_of(it["u"])}


def views_by_id(items) -> list:
    return [view(it) for it in sort_by_id(items)]


def validate_items(items, kinds=INGREDIENTS, name="items") -> list:
    """Mảng cá thể {id, kind, fresh} -> danh sách cá thể nội bộ (giữ thứ tự)."""
    if not isinstance(items, list):
        raise BadInput(f"{name} phải là mảng cá thể {{id, kind, fresh}} (kho đếm theo loại không còn hợp lệ ở v1.2)")
    out, seen = [], set()
    for i, it in enumerate(items):
        if not isinstance(it, dict) or set(it) != {"id", "kind", "fresh"}:
            raise BadInput(f"{name}[{i}] phải có đúng id, kind, fresh")
        if not isinstance(it["id"], str) or not it["id"] or it["id"] in seen:
            raise BadInput(f"{name}[{i}].id phải là chuỗi khác rỗng, duy nhất")
        seen.add(it["id"])
        if it["kind"] not in kinds:
            raise BadInput(f"nguyên liệu lạ: {it['kind']}")
        f = it["fresh"]
        if isinstance(f, bool) or not isinstance(f, (int, float)) or not math.isfinite(f) or not 0 <= f <= 100:
            raise BadInput(f"{name}[{i}].fresh phải hữu hạn trong [0, 100]")
        out.append({"id": it["id"], "kind": it["kind"], "u": to_units(f)})
    return out


def read_inventory(path: str, kinds=INGREDIENTS) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_items(data["items"], kinds)


def inventory_doc(items) -> dict:
    return {"items": views_by_id(items)}


def write_inventory(path: str, items: list):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(inventory_doc(items), f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
