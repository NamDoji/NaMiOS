#!/usr/bin/env python3
"""NaMiOS — sinh icon ứng dụng "squircle + glyph trắng" cho các app mặc định
còn đang rơi về icon "stock"/mặc định của breeze trong Start menu/taskbar
(đợt icon-designer Team 1 tiếp theo, 11/11/2026 — mục tiêu: bộ icon NaMiOS
ĐẦY ĐỦ, đồng bộ, KHÔNG còn mảng trộn vài icon NaMiOS + rất nhiều icon
breeze mặc định).

Dùng LẠI NGUYÊN VẸN công thức squircle đã có (build_tile trong
make-common-launcher-icons.py / make-app-icon-light.py / make-namioffice-app-
icons.py): canvas 1024, bo góc RADIUS = 0.2235*S, viền 4px, gradient dọc
nhạt->đậm cùng tông, glyph TRẮNG đơn sắc vẽ ở giữa.

TÊN ICON ĐÃ XÁC MINH THẬT (không đoán) — tải .deb thật từ deb.debian.org
(snapshot trixie, 11/11/2026) rồi `dpkg-deb -x` đọc Icon= trong .desktop bên
trong từng gói:
  - okular                 : Icon=okular              (gói "okular")
  - ark                    : Icon=ark                 (gói "ark",
    org.kde.ark.desktop — KHÔNG phải "org.kde.ark" như tên file .desktop dễ
    nhầm, Icon= bên trong vẫn là tên ngắn "ark")
  - kde-spectacle          : Icon=spectacle            (gói "kde-spectacle",
    org.kde.spectacle.desktop — Icon= bên trong là tên ngắn "spectacle")
  - vlc                    : Icon=vlc                  (gói "vlc")
  - haruna (dự phòng)      : Icon=haruna               (gói "haruna", phòng
    hờ nếu NaMiMedia đổi player sau này — xem hook 0455, KHÔNG cài mặc định)
  - elisa (dự phòng)       : Icon=elisa                (gói "elisa-player",
    cùng lý do dự phòng với haruna, KHÔNG cài mặc định)
  - kinfocenter            : Icon=hwinfo               (gói "kinfocenter",
    org.kde.kinfocenter.desktop — tên generic breeze "hwinfo", KHÔNG phải
    "kinfocenter"/"org.kde.kinfocenter")
  - systemsettings         : Icon=preferences-system   (gói "systemsettings",
    cả systemsettings.desktop và kdesystemsettings.desktop đều dùng tên
    generic breeze này)
  - cập nhật hệ thống      : Icon=system-software-update (dùng bởi CẢ
    org.kde.discover.notifier.desktop lẫn namios-cpl-update.desktop — xem
    distro/.../usr/share/applications/namios-cpl-update.desktop)

CẢNH BÁO ĐÃ GHI RÕ (đọc trước khi tưởng "chỉ app này đổi màu"): "hwinfo",
"preferences-system", "system-software-update" là TÊN ICON GENERIC breeze —
dùng chung bởi NHIỀU chỗ trong desktop (không riêng gì Kinfocenter/System
Settings/Discover notifier), nên ghi đè 3 tên này trong theme sẽ đổi icon ở
MỌI nơi khác cũng tra đúng tên đó, không chỉ 3 launcher nói trên. Đây là
rủi ro đã biết, không phải lỗi — 3 app này THẬT SỰ dùng đúng 3 tên generic
này (đã xác minh qua .deb thật), không có tên riêng nào khác để nhắm chính
xác hơn.

Chỉ rasterize PNG bằng Pillow (không cần SVG) — ship vào MỌI thư mục
<N>x<N>/apps đã tồn tại sẵn của NaMiOS-Lotus + hicolor, dưới các tên icon đã
xác minh ở trên.

Tái lập: python3 branding/icons/make-system-media-icons.py
"""
from __future__ import annotations

import math
import os
import re
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ICONS_ROOT = os.path.join(ROOT, "distro/live-build/config/includes.chroot/usr/share/icons")
OUT_DIR = os.path.join(ROOT, "branding/icons/out/system-media")
THEMES = ["NaMiOS-Lotus", "hicolor"]
SIZE_RE = re.compile(r"^(\d+)x\1$")

S = 1024
RADIUS = round(0.2235 * S)  # squircle — giống hệt make-app-icon-light.py

WHITE = (255, 255, 255)


def lighten(rgb: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(c + (255 - c) * amount) for c in rgb)  # type: ignore[return-value]


def darken(rgb: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(c * (1 - amount)) for c in rgb)  # type: ignore[return-value]


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
    """Y hệt build_tile của make-common-launcher-icons.py — gradient dọc +
    squircle mask + viền mảnh."""
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


# --- Glyph bằng mask riêng (cho hình có "lỗ khoét" — bánh răng) ------------

def _punch_mask_to_white_layer(mask: Image.Image) -> Image.Image:
    white = Image.new("RGBA", mask.size, WHITE + (255,))
    white.putalpha(mask)
    return white


# --- 1) VLC / NaMiMedia: màn hình + nút play --------------------------------

def glyph_vlc(tile: Image.Image) -> None:
    d = ImageDraw.Draw(tile)
    bx0, by0, bx1, by1 = 210, 290, 814, 734
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=54, outline=WHITE + (255,), width=34)
    tri = [(432, 398), (432, 626), (654, 512)]
    d.polygon(tri, fill=WHITE + (255,))


# --- 2) Okular / NaMiPDF: trang tài liệu + kính lúp (viewer, khác Kate) -----

def glyph_okular(tile: Image.Image) -> None:
    d = ImageDraw.Draw(tile)
    px0, py0, px1, py1 = 282, 222, 738, 758
    d.rounded_rectangle([px0, py0, px1, py1], radius=46, outline=WHITE + (255,), width=30)
    line_h = 32
    xs = px0 + 64
    widths = [330, 270, 150]
    ys = [320, 418, 516]
    for y, w in zip(ys, widths):
        d.rounded_rectangle([xs, y, xs + w, y + line_h], radius=line_h // 2, fill=WHITE + (255,))
    # Kính lúp đè lên góc dưới-phải trang — dấu hiệu "xem/đọc", khác Kate
    # (chỉ có 3 dòng chữ, không kính lúp).
    mx, my, mr = 706, 706, 92
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], outline=WHITE + (255,), width=32)
    d.line([(mx + mr * 0.66, my + mr * 0.66), (mx + mr * 1.42, my + mr * 1.42)], fill=WHITE + (255,), width=40)


# --- 3) Ark / NaMiArchive: hộp lưu trữ + khoá kéo (zipper) ------------------

def glyph_ark(tile: Image.Image) -> None:
    d = ImageDraw.Draw(tile)
    bx0, by0, bx1, by1 = 270, 258, 754, 766
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=56, outline=WHITE + (255,), width=34)
    cx = (bx0 + bx1) / 2
    zig = [
        (cx, by0 + 30),
        (cx - 42, by0 + 108),
        (cx + 42, by0 + 192),
        (cx - 42, by0 + 276),
        (cx + 42, by0 + 360),
        (cx - 42, by0 + 444),
        (cx, by1 - 30),
    ]
    d.line(zig, fill=WHITE + (255,), width=24, joint="curve")
    # Tay kéo (pull tab) ở đầu khoá kéo.
    d.rounded_rectangle([cx - 36, by0 + 2, cx + 36, by0 + 60], radius=16, fill=WHITE + (255,))


# --- 4) Spectacle / NaMiChụp: khung chụp 4 góc + nút chụp -------------------

def glyph_spectacle(tile: Image.Image) -> None:
    d = ImageDraw.Draw(tile)
    fx0, fy0, fx1, fy1 = 262, 248, 762, 712
    L = 140
    sw = 36
    d.line([(fx0, fy0 + L), (fx0, fy0), (fx0 + L, fy0)], fill=WHITE + (255,), width=sw, joint="curve")
    d.line([(fx1 - L, fy0), (fx1, fy0), (fx1, fy0 + L)], fill=WHITE + (255,), width=sw, joint="curve")
    d.line([(fx0, fy1 - L), (fx0, fy1), (fx0 + L, fy1)], fill=WHITE + (255,), width=sw, joint="curve")
    d.line([(fx1 - L, fy1), (fx1, fy1), (fx1, fy1 - L)], fill=WHITE + (255,), width=sw, joint="curve")
    # Nút chụp (shutter) nằm giữa cạnh dưới khung — gợi "bấm chụp".
    cx = (fx0 + fx1) / 2
    r = 72
    d.ellipse([cx - r, fy1 - r, cx + r, fy1 + r], fill=WHITE + (255,))


# --- 5) hwinfo (Kinfocenter): chip phần cứng + chân cắm ---------------------

def glyph_chip(tile: Image.Image) -> None:
    d = ImageDraw.Draw(tile)
    cx0, cy0, cx1, cy1 = 300, 300, 724, 724
    d.rounded_rectangle([cx0, cy0, cx1, cy1], radius=40, outline=WHITE + (255,), width=30)
    ix0, iy0, ix1, iy1 = 392, 392, 632, 632
    d.rounded_rectangle([ix0, iy0, ix1, iy1], radius=20, outline=WHITE + (255,), width=18)
    pin_len = 46
    pin_w = 22
    xs = [372, 512, 652]
    for x in xs:
        d.line([(x, cy0 - pin_len), (x, cy0)], fill=WHITE + (255,), width=pin_w)
        d.line([(x, cy1), (x, cy1 + pin_len)], fill=WHITE + (255,), width=pin_w)
    ys = [372, 512, 652]
    for y in ys:
        d.line([(cx0 - pin_len, y), (cx0, y)], fill=WHITE + (255,), width=pin_w)
        d.line([(cx1, y), (cx1 + pin_len, y)], fill=WHITE + (255,), width=pin_w)


# --- 6) preferences-system (System Settings): bánh răng --------------------

def glyph_gear(tile: Image.Image) -> None:
    cx, cy = 512, 512
    r_body = 196
    r_hole = 86
    tooth_inner = r_body - 26
    tooth_outer = r_body + 96
    tooth_w = 92

    mask = Image.new("L", (S, S), 0)
    dm = ImageDraw.Draw(mask)
    dm.ellipse([cx - r_body, cy - r_body, cx + r_body, cy + r_body], fill=255)
    for ang_deg in range(0, 360, 45):
        ang = math.radians(ang_deg)
        x0 = cx + tooth_inner * math.cos(ang)
        y0 = cy + tooth_inner * math.sin(ang)
        x1 = cx + tooth_outer * math.cos(ang)
        y1 = cy + tooth_outer * math.sin(ang)
        dm.line([(x0, y0), (x1, y1)], fill=255, width=tooth_w)
    dm.ellipse([cx - r_hole, cy - r_hole, cx + r_hole, cy + r_hole], fill=0)

    tile.alpha_composite(_punch_mask_to_white_layer(mask))


# --- 7) system-software-update: mũi tên vòng tròn (refresh/update) ---------

def glyph_refresh(tile: Image.Image) -> None:
    d = ImageDraw.Draw(tile)
    cx, cy = 512, 512
    r = 230
    sw = 58
    start_deg, end_deg = 206, 506  # vòng ~300 độ, hở ~60 độ
    d.arc([cx - r, cy - r, cx + r, cy + r], start=start_deg, end=end_deg, fill=WHITE + (255,), width=sw)

    end_rad = math.radians(end_deg % 360)
    px = cx + r * math.cos(end_rad)
    py = cy + r * math.sin(end_rad)
    # Hướng tiếp tuyến (chiều kim đồng hồ) tại điểm cuối cung.
    tx, ty = -math.sin(end_rad), math.cos(end_rad)
    # Hướng pháp tuyến (theo bán kính) để tạo đáy mũi tên.
    nx, ny = math.cos(end_rad), math.sin(end_rad)
    arrow_len = 150
    arrow_half_w = 110
    tip = (px + tx * arrow_len * 0.55, py + ty * arrow_len * 0.55)
    base1 = (px + nx * arrow_half_w - tx * arrow_len * 0.45, py + ny * arrow_half_w - ty * arrow_len * 0.45)
    base2 = (px - nx * arrow_half_w - tx * arrow_len * 0.45, py - ny * arrow_half_w - ty * arrow_len * 0.45)
    d.polygon([tip, base1, base2], fill=WHITE + (255,))


# --- Bảng màu + ánh xạ app -> (tile, glyph, tên icon thật) ------------------

DO_SON = (0xC9, 0x36, 0x43)       # đỏ son — brand.json "son", dành cho NaMiMedia
MUC_DEM = (0x12, 0x2A, 0x3A)      # mực đêm — brand.json "muc_dem", dành cho nhóm "system"

ARK_BASE = (41, 133, 178)         # lam thép (cerulean) — MỚI, chưa app nào dùng
SPECTACLE_BASE = (173, 58, 173)   # tím mâm-xôi (magenta/orchid) — MỚI
OKULAR_BASE = (0x92, 0x21, 0x2E)  # đỏ đài (dai, brand.json) — thẫm hơn hẳn đỏ mail

APPS = {
    "vlc": {
        "top": lighten(DO_SON, 0.46),
        "bottom": DO_SON,
        "border": lighten(DO_SON, 0.22),
        "glyph": glyph_vlc,
        "names": ["vlc", "haruna", "elisa"],
    },
    "okular": {
        "top": lighten(OKULAR_BASE, 0.44),
        "bottom": OKULAR_BASE,
        "border": lighten(OKULAR_BASE, 0.2),
        "glyph": glyph_okular,
        "names": ["okular"],
    },
    "ark": {
        "top": lighten(ARK_BASE, 0.52),
        "bottom": darken(ARK_BASE, 0.14),
        "border": lighten(ARK_BASE, 0.28),
        "glyph": glyph_ark,
        "names": ["ark"],
    },
    "spectacle": {
        "top": lighten(SPECTACLE_BASE, 0.5),
        "bottom": darken(SPECTACLE_BASE, 0.12),
        "border": lighten(SPECTACLE_BASE, 0.26),
        "glyph": glyph_spectacle,
        "names": ["spectacle"],
    },
    "hwinfo": {
        "top": lighten(MUC_DEM, 0.5),
        "bottom": MUC_DEM,
        "border": lighten(MUC_DEM, 0.25),
        "glyph": glyph_chip,
        "names": ["hwinfo"],
    },
    "preferences-system": {
        "top": lighten(MUC_DEM, 0.5),
        "bottom": MUC_DEM,
        "border": lighten(MUC_DEM, 0.25),
        "glyph": glyph_gear,
        "names": ["preferences-system"],
    },
    "system-software-update": {
        "top": lighten(MUC_DEM, 0.5),
        "bottom": MUC_DEM,
        "border": lighten(MUC_DEM, 0.25),
        "glyph": glyph_refresh,
        "names": ["system-software-update"],
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

    # --- NaMiOS Welcome (Icon=namios-welcome, autostart lần đầu) ------------
    # Dùng LẠI chính master ngà + sen đã có (make-app-icon-light.py) — app
    # "Welcome/Giới thiệu nhanh" dùng logo hệ điều hành là hợp lý (giống
    # macOS/Ubuntu Welcome dùng logo OS), KHÔNG tự vẽ glyph mới.
    light_master_path = os.path.join(ROOT, "branding/icons/NaMiOS_App_Icon_Light_1024.png")
    if os.path.isfile(light_master_path):
        light_master = Image.open(light_master_path).convert("RGBA")
        for theme in THEMES:
            for size, apps_dir in _size_dirs(os.path.join(ICONS_ROOT, theme)):
                icon = light_master.resize((size, size), Image.LANCZOS)
                target = os.path.join(apps_dir, "namios-welcome.png")
                icon.save(target, "PNG")
                written.append(("namios-welcome", size, target))
    else:
        print(f"!! khong thay {light_master_path} — bo qua namios-welcome.png (verified_on_host: NO)")

    print(f"total: {len(written)} icon files written across {len(THEMES)} themes")


if __name__ == "__main__":
    main()
