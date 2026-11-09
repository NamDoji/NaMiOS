#!/usr/bin/env python3
"""Sinh lại icon ứng dụng "namios" + "start-here-namios" ở MỌI kích thước đã
có sẵn trong 2 theme icon của repo, từ ảnh vuông v2 "Sen Việt"
(branding/logo-sen-viet-v2/NaMiOS_App_Icon_1024.png — sen đỏ son trên nền
vuông bo góc mực đêm), THAY cho bản "Sen bừng sáng" navy/jade cũ.

Không rasterize SVG (môi trường build không có cairosvg/rsvg/inkscape) —
chỉ resize PNG 1024px gốc bằng Pillow LANCZOS xuống từng cỡ đích. Giữ
nguyên cấu trúc thư mục/kích thước/index.theme đã có, CHỈ ghi đè 2 tên file
sau tại mọi kích thước tìm thấy:
  - usr/share/icons/NaMiOS-Lotus/<size>x<size>/apps/namios.png
  - usr/share/icons/NaMiOS-Lotus/<size>x<size>/apps/start-here-namios.png
  - usr/share/icons/hicolor/<size>x<size>/apps/namios.png
  - usr/share/icons/hicolor/<size>x<size>/apps/start-here-namios.png

Tái lập: python3 branding/icons/make-icon-theme.py
"""
from __future__ import annotations

import os
import re
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "branding/logo-sen-viet-v2/NaMiOS_App_Icon_1024.png")
ICONS_ROOT = os.path.join(
    ROOT, "distro/live-build/config/includes.chroot/usr/share/icons"
)
THEMES = ["NaMiOS-Lotus", "hicolor"]
FILENAMES = ["namios.png", "start-here-namios.png"]

SIZE_RE = re.compile(r"^(\d+)x\1$")


def find_size_dirs(theme_root: str) -> list[tuple[int, str]]:
    """Trả về [(size, path/to/apps)] cho mọi thư mục <N>x<N>/apps đang tồn tại."""
    out = []
    if not os.path.isdir(theme_root):
        return out
    for name in sorted(os.listdir(theme_root)):
        m = SIZE_RE.match(name)
        if not m:
            continue
        apps_dir = os.path.join(theme_root, name, "apps")
        if os.path.isdir(apps_dir):
            out.append((int(m.group(1)), apps_dir))
    return out


def main() -> None:
    master = Image.open(SRC).convert("RGBA")
    assert master.size == (1024, 1024), f"expected 1024x1024, got {master.size}"

    written = []
    for theme in THEMES:
        theme_root = os.path.join(ICONS_ROOT, theme)
        size_dirs = find_size_dirs(theme_root)
        if not size_dirs:
            print(f"!! no <N>x<N>/apps dirs found under {theme_root}")
            continue
        for size, apps_dir in size_dirs:
            icon = master.resize((size, size), Image.LANCZOS)
            for fname in FILENAMES:
                target_path = os.path.join(apps_dir, fname)
                if not os.path.exists(target_path):
                    # Chỉ ghi đè icon đã tồn tại từ trước (không tạo thêm
                    # tên file mới ngoài namios.png/start-here-namios.png).
                    continue
                icon.save(target_path, "PNG")
                written.append((target_path, size))

    for path, size in written:
        print(f"wrote {path} ({size}x{size})")
    print(f"total: {len(written)} icon files regenerated from {SRC}")


if __name__ == "__main__":
    main()
