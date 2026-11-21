"""Kiểm tra trước khi gắn tag phase (skill `phase-check`). Chỉ dùng thư viện chuẩn.

    python3 tools/phase_check.py 1            # kiểm tra, KHÔNG gắn tag
    python3 tools/phase_check.py 1 --no-test  # bỏ bước chạy test (khi vừa chạy run_smoke.sh)

Điều kiện (khớp mục "Bắt buộc" trong README):
  - test xanh (smoke hộp đen + unit);
  - docs/verification/phase-<n>.md có ít nhất một dòng AC đã điền;
  - docs/proof/phase-<n>/ có ít nhất một file bằng chứng;
  - docs/ai-usage-log.md có ít nhất một dòng cho phase này; docs/standup.md có dòng cho phase này;
  - phase 2 và 4: docs/retro.md mục tương ứng đã điền; phase 3: có ít nhất một ADR (docs/adr/0001-*.md...);
  - phase 4: docs/members/<handle>.md tồn tại;
  - cây làm việc sạch, tag phase-<n> chưa tồn tại.
In lệnh gắn tag nếu đạt; mã thoát 0 = đạt, 1 = chưa đạt, 2 = sai tham số.
"""

import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    try:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def table_rows(text):
    """Các dòng dữ liệu (bỏ tiêu đề và dòng phân cách) của mọi bảng markdown, đã tách ô."""
    rows, header_seen = [], False
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            header_seen = False
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        if not header_seen:
            header_seen = True
            continue
        if any(cells):
            rows.append(cells)
    return rows


def rows_for_phase(text, n):
    pat = re.compile(rf"^(phase[- ]?)?{n}$|^p{n}$", re.I)
    return [r for r in table_rows(text) if r and pat.match(r[0])]


def retro_filled(text, n):
    m = re.search(rf"^## Phase {n}.*?(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return False
    return any(re.match(r"^- [^:]+:\s*\S", ln.strip()) for ln in m.group(0).splitlines())


def git(*args):
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


def handles():
    out = []
    for r in table_rows(_read("TEAM.md")):
        if len(r) > 1 and r[1]:
            out.append(r[1].lstrip("@").strip("` "))
    return out


def check(n, run_tests=True):
    problems = []
    if run_tests:
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(["tests", "."]))
        p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=ROOT,
                           env=env, capture_output=True, text=True)
        if p.returncode != 0:
            problems.append("test chưa xanh:\n    " + "\n    ".join(p.stderr.strip().splitlines()[-3:]))
    if not table_rows(_read(f"docs/verification/phase-{n}.md")):
        problems.append(f"docs/verification/phase-{n}.md chưa có dòng AC nào")
    if not [f for f in glob.glob(os.path.join(ROOT, "docs", "proof", f"phase-{n}", "*")) if os.path.isfile(f)]:
        problems.append(f"docs/proof/phase-{n}/ chưa có bằng chứng (chạy: bash tools/run_smoke.sh phase-{n})")
    if not rows_for_phase(_read("docs/ai-usage-log.md"), n):
        problems.append(f"docs/ai-usage-log.md chưa có dòng nào cho Phase {n}")
    if not rows_for_phase(_read("docs/standup.md"), n):
        problems.append(f"docs/standup.md chưa có dòng nào cho Phase {n}")
    if n in (2, 4) and not retro_filled(_read("docs/retro.md"), n):
        problems.append(f"docs/retro.md mục Phase {n} chưa điền")
    if n == 3 and not glob.glob(os.path.join(ROOT, "docs", "adr", "0[0-9][0-9][1-9]-*.md")):
        problems.append("Phase 3 (change request) cần ít nhất một ADR trong docs/adr/")
    if n == 4:
        for h in handles():
            if not os.path.exists(os.path.join(ROOT, "docs", "members", f"{h}.md")):
                problems.append(f"thiếu docs/members/{h}.md")
    code, dirty = git("status", "--porcelain")
    if code == 0 and dirty:
        problems.append("cây làm việc chưa sạch (commit hết trước khi gắn tag)")
    code, tags = git("tag", "--list", f"phase-{n}")
    if code == 0 and tags:
        problems.append(f"tag phase-{n} đã tồn tại")
    return problems


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1 or args[0] not in ("1", "2", "3", "4"):
        print("cách dùng: python3 tools/phase_check.py <1..4> [--no-test]", file=sys.stderr)
        return 2
    n = int(args[0])
    problems = check(n, run_tests="--no-test" not in argv)
    if problems:
        print(f"PHASE {n}: CHƯA SẴN SÀNG GẮN TAG")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"PHASE {n}: ĐẠT. Gắn tag bằng:")
    print(f'  git tag -a phase-{n} -m "Phase {n}" && git push origin phase-{n}')
    if n == 4:
        print('  gh release create v1.0.0 --title "v1.0.0" --notes-file CHANGELOG.md')
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
