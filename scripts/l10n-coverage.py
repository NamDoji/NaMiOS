#!/usr/bin/env python3
"""NaMiOS — đo ĐỘ PHỦ dịch tiếng Việt THẬT trên catalog .mo đã cài (không đoán).

Đọc trực tiếp các file `.mo` (tự phân tích, không cần polib/msgunfmt) ở:
  - <root>/usr/share/locale/vi/LC_MESSAGES/*.mo      (bản vi upstream trong gói app)
  - <root>/usr/share/locale/vi_NM/LC_MESSAGES/*.mo   (LỚP PHỦ NaMiOS)
Đếm số chuỗi ĐÃ DỊCH (msgstr != "") mỗi domain, hợp nhất theo msgid (overlay thắng),
rồi so với "mẫu số" (tổng chuỗi mỗi domain) lấy từ coverage-baseline.json
(ảnh chụp l10n.kde.org — có URL + ngày) để ra % TRUNG THỰC.

Chạy ở: chroot sau khi cài gói (build-time) hoặc phiên Live (boot-time).
  python3 scripts/l10n-coverage.py [--root /] [--baseline distro/.../coverage-baseline.json] [--json out.json]

TRUNG THỰC (feedback): chỉ báo số ĐO ĐƯỢC; chỗ còn tiếng Anh là giới hạn thật của
hệ sinh thái dịch, KHÔNG tô hồng "đã Việt hoá 100%".
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

_MAGIC_LE = 0x950412DE
_MAGIC_BE = 0xDE120495


def translated_msgids(mo_path: Path) -> set[str]:
    """Trả về tập msgid có bản dịch KHÁC RỖNG trong 1 file .mo (bỏ mục header
    msgid=""). Tự phân tích định dạng .mo chuẩn GNU gettext — không phụ thuộc lib."""
    data = mo_path.read_bytes()
    if len(data) < 20:
        return set()
    magic = struct.unpack("<I", data[:4])[0]
    if magic == _MAGIC_LE:
        endian = "<"
    elif magic == _MAGIC_BE:
        endian = ">"
    else:
        return set()  # không phải .mo hợp lệ -> bỏ qua (không đoán)

    n = struct.unpack(endian + "I", data[8:12])[0]
    off_orig = struct.unpack(endian + "I", data[12:16])[0]
    off_tr = struct.unpack(endian + "I", data[16:20])[0]

    out: set[str] = set()
    for i in range(n):
        o_len, o_off = struct.unpack(endian + "II", data[off_orig + i * 8 : off_orig + i * 8 + 8])
        t_len, t_off = struct.unpack(endian + "II", data[off_tr + i * 8 : off_tr + i * 8 + 8])
        msgid = data[o_off : o_off + o_len]
        msgstr = data[t_off : t_off + t_len]
        if not msgid:
            continue  # mục header
        # msgid dạng số nhiều ngăn bằng \x00 — lấy phần đơn làm khoá; coi là
        # "đã dịch" nếu có BẤT KỲ dạng msgstr nào khác rỗng.
        key = msgid.split(b"\x00", 1)[0].decode("utf-8", "replace")
        if any(part for part in msgstr.split(b"\x00")):
            out.add(key)
    return out


def scan_locale(root: Path, lang: str) -> dict[str, set[str]]:
    """Map domain -> tập msgid đã dịch, cho 1 ngôn ngữ dưới <root>/usr/share/locale."""
    base = root / "usr" / "share" / "locale" / lang / "LC_MESSAGES"
    res: dict[str, set[str]] = {}
    if not base.is_dir():
        return res
    for mo in sorted(base.glob("*.mo")):
        res[mo.stem] = translated_msgids(mo)
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description="Đo độ phủ dịch tiếng Việt NaMiOS")
    ap.add_argument("--root", default="/", help="gốc hệ thống (mặc định /)")
    ap.add_argument("--baseline", default="", help="coverage-baseline.json (mẫu số)")
    ap.add_argument("--json", default="", help="ghi kết quả JSON ra file")
    args = ap.parse_args()

    root = Path(args.root)
    upstream = scan_locale(root, "vi")
    overlay = scan_locale(root, "vi_NM")

    baseline: dict[str, int] = {}
    if args.baseline:
        bp = Path(args.baseline)
        if bp.is_file():
            raw = json.loads(bp.read_text(encoding="utf-8"))
            baseline = {k: int(v["total"]) for k, v in raw.get("domains", {}).items()}

    domains = sorted(set(upstream) | set(overlay) | set(baseline))
    rows = []
    sum_up = sum_eff = sum_total = 0
    for d in domains:
        up = upstream.get(d, set())
        ov = overlay.get(d, set())
        eff = up | ov
        total = baseline.get(d, 0)
        rows.append((d, len(up), len(ov), len(eff), total))
        sum_up += len(up)
        sum_eff += len(eff)
        sum_total += total

    def pct(a: int, b: int) -> str:
        return f"{100 * a / b:.0f}%" if b else "—"

    print(f"{'domain':40s} {'vi':>6} {'+phủ':>6} {'hiệu dụng':>10} {'tổng':>7} {'%vi':>5} {'%hd':>5}")
    print("-" * 86)
    for d, up, ov, eff, total in rows:
        print(f"{d:40.40s} {up:6d} {ov:6d} {eff:10d} {total:7d} {pct(up,total):>5} {pct(eff,total):>5}")
    print("-" * 86)
    print(
        f"{'TỔNG':40s} {sum_up:6d} {'':>6} {sum_eff:10d} {sum_total:7d} "
        f"{pct(sum_up,sum_total):>5} {pct(sum_eff,sum_total):>5}"
    )
    if sum_total:
        print(
            f"\nĐộ phủ hiệu dụng (vi upstream + lớp phủ NaMiOS) = {pct(sum_eff,sum_total)} "
            f"trên {sum_total} chuỗi mẫu. Phần còn lại hiện tiếng Anh — giới hạn thật."
        )

    if args.json:
        payload = {
            "domains": {
                d: {"vi": up, "overlay": ov, "effective": eff, "total": total}
                for d, up, ov, eff, total in rows
            },
            "summary": {"vi": sum_up, "effective": sum_eff, "total": sum_total},
        }
        Path(args.json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nĐã ghi JSON: {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
