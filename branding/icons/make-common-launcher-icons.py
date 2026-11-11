#!/usr/bin/env python3
"""NaMiOS — sinh 3 icon ứng dụng "launcher" còn THIẾU trong NaMiOS-Lotus:
Terminal (konsole), Text editor (kate/kwrite), Trung tâm phần mềm (Discover).

3 gói này ĐÃ được kéo vào ISO (xem package-lists/*.list.chroot: konsole, kate,
plasma-discover) nhưng CHƯA có icon squircle thương hiệu riêng trong
NaMiOS-Lotus — launcher của chúng đang rơi về icon "stock" upstream (lạc tông
với phần còn lại của Start menu/taskbar vốn đã đồng bộ hoá "squircle + glyph
trắng đơn sắc" cho mọi app khác: xem firefox/kcalc/mail-client/...).

Dùng LẠI chính xác công thức squircle đã có (build_tile trong
make-app-icon-light.py / make-namioffice-app-icons.py): canvas 1024, bo góc
RADIUS = 0.2235*S, viền 4px, gradient dọc nhạt->đậm cùng tông, rồi vẽ glyph
TRẮNG đơn giản ở giữa — tái dùng NGUYÊN VẸN ngôn ngữ thị giác đã có, chỉ thêm 3
tông màu MỚI (chưa trùng 8 tông đang dùng: tím ảnh/ xanh Writer/ ngọc trình
duyệt/ xanh lá Calc/ navy máy tính/ cam thư mục+Impress/ đỏ mail/ ngà sen) để
vẫn phân biệt được bằng mắt trong lưới icon:
  - Terminal   -> than chì trung tính gần đen (KHÔNG xanh — khác navy kcalc)
  - Text editor-> vàng ấm (dùng ĐÚNG 2 màu khoá thương hiệu vang_tam/vang_nuoc
    trong brand.json, chưa app nào dùng tới)
  - Discover   -> hồng mâm xôi (chưa app nào dùng hồng/đỏ-tía)

Chỉ rasterize PNG bằng Pillow (không cần SVG) — ship vào MỌI thư mục
<N>x<N>/apps đã tồn tại sẵn của NaMiOS-Lotus + hicolor, dưới các tên icon
chuẩn mà .desktop upstream của 3 gói này khai (nhiều alias để chắc ăn khớp
đúng theo Icon= thực tế từng bản KDE):
  - Terminal:   utilities-terminal, org.kde.konsole, konsole
  - Text editor: kate, org.kde.kate, accessories-text-editor, org.kde.kwrite
  - Discover:   plasma-discover, org.kde.discover

Tái lập: python3 branding/icons/make-common-launcher-icons.py
"""
from __future__ import annotations

import os
import re
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ICONS_ROOT = os.path.join(ROOT, "distro/live-build/config/includes.chroot/usr/share/icons")
OUT_DIR = os.path.join(ROOT, "branding/icons/out/common-launchers")
THEMES = ["NaMiOS-Lotus", "hicolor"]
SIZE_RE = re.compile(r"^(\d+)x\1$")

S = 1024
RADIUS = round(0.2235 * S)  # squircle — giống hệt make-app-icon-light.py

WHITE = (255, 255, 255)


def _size_dirs(theme_root: str) -> list[tuple[int, str]]:
    out = []
    if not os.path.isdir(theme_root):
        return out
    for name in sorted(os.listdir(theme_root)):
        m = SIZE_RE.match(name)
        if m and os.path.isdir(os.path.join(theme_root, name, "apps")):
            out.append((int(m.group(1)), os.path.join(theme_root, name, "apps")))
    return out


def build_tile(top: tuple[int, int, int], bottom: tuple[int, int, int], border: tuple[int, int, int]) -> Image.Image:
    grad = Image.new("RGB", (S, S))
    px = grad.load()
    for y in range(S):
        t = y / (S - 1)
        row = (
            int(top[0] + (bottom[0] - top[0]) * t),
            int(top[1] + (bottom[1] - top[1]) * t),
            int(top[2] + (bottom[2] - top[2]) * t),
        )
        for x in range(S):
            px[x, y] = row
    tile = grad.convert("RGBA")

    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=RADIUS, fill=255)
    tile.putalpha(mask)

    bd = ImageDraw.Draw(tile)
    bd.rounded_rectangle([2, 2, S - 3, S - 3], radius=RADIUS - 2, outline=border + (255,), width=4)
    return tile


def glyph_terminal(tile: Image.Image) -> None:
    """Màn hình bezel bo góc + dấu nhắc lệnh ">" và gạch dưới "_" màu trắng."""
    d = ImageDraw.Draw(tile)
    bx0, by0, bx1, by1 = 230, 260, 794, 764
    sw = 34
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=54, outline=WHITE + (255,), width=sw)
    # Dấu nhắc lệnh ">" (2 nét gấp khúc).
    cx0, cy0 = 330, 420
    d.line([(cx0, cy0), (cx0 + 110, cy0 + 90), (cx0, cy0 + 180)], fill=WHITE + (255,), width=sw, joint="curve")
    # Gạch dưới con trỏ "_".
    d.line([(480, cy0 + 180), (660, cy0 + 180)], fill=WHITE + (255,), width=sw)


def glyph_text_editor(tile: Image.Image) -> None:
    """Trang giấy bo góc màu trắng + 3 dòng chữ (khác độ dài) — "notepad"."""
    d = ImageDraw.Draw(tile)
    px0, py0, px1, py1 = 270, 232, 754, 792
    d.rounded_rectangle([px0, py0, px1, py1], radius=48, outline=WHITE + (255,), width=30)
    line_h = 34
    xs = px0 + 70
    widths = [360, 300, 180]
    ys = [360, 470, 580]
    for y, w in zip(ys, widths):
        d.rounded_rectangle([xs, y, xs + w, y + line_h], radius=line_h // 2, fill=WHITE + (255,))


def glyph_discover(tile: Image.Image) -> None:
    """Mũi tên hướng xuống "tải về" rơi vào khay mở — glyph "get app"."""
    d = ImageDraw.Draw(tile)
    cx = S / 2
    sw = 40
    # Thân mũi tên.
    d.line([(cx, 250), (cx, 560)], fill=WHITE + (255,), width=sw)
    # Đầu mũi tên (tam giác, nối liền thân).
    d.polygon(
        [(cx - 130, 470), (cx + 130, 470), (cx, 640)],
        fill=WHITE + (255,),
    )
    # Khay hứng (2 cạnh + đáy, hở phía trên — kiểu "inbox/tray").
    d.line(
        [(cx - 220, 660), (cx - 220, 770), (cx + 220, 770), (cx + 220, 660)],
        fill=WHITE + (255,),
        width=sw,
        joint="curve",
    )


APPS = {
    "terminal": {
        "top": (130, 134, 141),
        "bottom": (26, 28, 32),
        "border": (82, 85, 90),
        "glyph": glyph_terminal,
        "names": ["utilities-terminal", "org.kde.konsole", "konsole"],
    },
    "text-editor": {
        "top": (248, 219, 163),
        "bottom": (188, 138, 67),  # vang_nuoc (brand.json)
        "border": (214, 170, 97),
        "glyph": glyph_text_editor,
        "names": ["kate", "org.kde.kate", "accessories-text-editor", "org.kde.kwrite"],
    },
    "discover": {
        "top": (255, 190, 212),
        "bottom": (214, 54, 104),
        "border": (232, 140, 166),
        "glyph": glyph_discover,
        "names": ["plasma-discover", "org.kde.discover"],
    },
}


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    written: list[tuple[str, int, str]] = []

    for app, spec in APPS.items():
        tile = build_tile(spec["top"], spec["bottom"], spec["border"])
        spec["glyph"](tile)
        master_path = os.path.join(OUT_DIR, f"{app}_1024.png")
        tile.save(master_path, "PNG")
        print(f"wrote master {master_path}")

        for theme in THEMES:
            for size, apps_dir in _size_dirs(os.path.join(ICONS_ROOT, theme)):
                icon = tile.resize((size, size), Image.LANCZOS)
                for name in spec["names"]:
                    target = os.path.join(apps_dir, f"{name}.png")
                    icon.save(target, "PNG")
                    written.append((app, size, target))

    print(f"total: {len(written)} icon files written across {len(THEMES)} themes")


if __name__ == "__main__":
    main()
