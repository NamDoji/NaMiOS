#!/usr/bin/env python3
"""NaMiOS — sinh BỘ ICON ỨNG DỤNG NaMiOffice (Writer/Calc/Impress/Draw/Base/Math)
thay cho icon "stock" LibreOffice trong Start menu / taskbar (yêu cầu Cuong
10/11/2026: "Đổi bộ logo").

NGUYÊN TẮC THƯƠNG HIỆU CỐ ĐỊNH (Cuong): hoa sen / mọi ô icon KHÔNG BAO GIỜ đặt
trên nền đen — luôn nền NGÀ ấm. 6 icon dùng CHUNG một ô tile ngà bo góc squircle
(cùng bán kính/đệm với branding/icons/make-app-icon-light.py) để cả bộ đọc như
MỘT bộ NaMiOffice thống nhất, chỉ khác nhau ở:
  - "thẻ tài liệu" trắng ngà bên trong (dải tiêu đề màu accent riêng từng app)
  - hoạ tiết glyph riêng (dòng chữ / lưới bảng tính / khung trình chiếu /
    hình khối vẽ / trụ CSDL / ký hiệu Σ công thức)
  - một vệt sen rất mờ (tỉ lệ/khoảng alpha CỐ ĐỊNH cho cả 6 icon) ở góc dưới-phải
    ô tile, phía sau thẻ tài liệu — nhánh thương hiệu, KHÔNG cạnh tranh với glyph.

Không rasterize SVG (môi trường build không có cairosvg/rsvg/inkscape) — chỉ vẽ
bằng Pillow ImageDraw ở canvas 1024 rồi resize LANCZOS xuống từng cỡ icon.

Tái lập: python3 branding/icons/make-namioffice-app-icons.py
Sinh ra:
  - master 1024px mỗi app tại branding/icons/out/namioffice/NaMiOffice_<App>_1024.png
  - PNG từng cỡ (48/64/128/256/512) ghi vào
    distro/live-build/config/includes.chroot/usr/share/icons/hicolor/<N>x<N>/apps/
    namioffice-<app>.png (chỉ ghi vào thư mục cỡ đã tồn tại sẵn trong hicolor).
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SYMBOL = os.path.join(ROOT, "branding/logo-sen-viet-v2/NaMiOS_Sen_Viet_Symbol_1024.png")
FONT_BOLD = os.path.join(ROOT, "branding/fonts/DejaVuSans-Bold.ttf")
OUT_DIR = os.path.join(ROOT, "branding/icons/out/namioffice")
ICONS_ROOT = os.path.join(ROOT, "distro/live-build/config/includes.chroot/usr/share/icons/hicolor")

SHIP_SIZES = [48, 64, 128, 256, 512]  # chỉ ghi vào <N>x<N>/apps đã có sẵn trong hicolor

S = 1024  # canvas master

# --- Màu thương hiệu "Sen Việt" (cố định, Cuong chốt) ------------------------
NGA_TOP = (0xFB, 0xF8, 0xF2)   # ngà — bg tile trên
NGA_BOT = (0xEF, 0xE3, 0xD1)   # ngà — bg tile dưới
DO_SON = (0xC9, 0x36, 0x43)    # đỏ son
DO_DAI = (0x92, 0x21, 0x2E)    # đỏ đài
VANG_TAM = (0xF2, 0xC6, 0x6D)  # vàng tâm
MUC = (0x18, 0x2E, 0x3B)       # mực
CALC_GREEN = (0x2E, 0x7D, 0x5B)  # xanh bảng tính (ngoài palette lotus, chọn dễ đọc)

BORDER = (0xE2, 0xD2, 0xB9)    # viền ngà ấm nhạt quanh tile (đồng bộ app-icon gốc)
CARD_FILL = (0xFF, 0xFD, 0xF8)  # "thẻ tài liệu" — trắng ấm, nổi trên nền ngà

RADIUS = round(0.2235 * S)  # squircle — giống hệt make-app-icon-light.py


def lighten(rgb: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    """Pha nhạt màu về phía trắng theo tỉ lệ amount (0..1)."""
    return tuple(round(c + (255 - c) * amount) for c in rgb)  # type: ignore[return-value]


def darken(rgb: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(c * (1 - amount)) for c in rgb)  # type: ignore[return-value]


# --- 1) Ô tile ngà dùng chung (squircle + viền + vệt sen mờ góc dưới-phải) ---

def build_tile() -> Image.Image:
    grad = Image.new("RGB", (S, S))
    px = grad.load()
    for y in range(S):
        t = y / (S - 1)
        row = (
            int(NGA_TOP[0] + (NGA_BOT[0] - NGA_TOP[0]) * t),
            int(NGA_TOP[1] + (NGA_BOT[1] - NGA_TOP[1]) * t),
            int(NGA_TOP[2] + (NGA_BOT[2] - NGA_TOP[2]) * t),
        )
        for x in range(S):
            px[x, y] = row
    tile = grad.convert("RGBA")

    # Vệt sen rất mờ — thương hiệu nhẹ, góc dưới-phải, PHÍA SAU thẻ tài liệu
    # (thẻ vẽ sau sẽ che gần hết, chỉ ló một chút ra ngoài rìa thẻ).
    sym = Image.open(SYMBOL).convert("RGBA")
    bbox = sym.getbbox()
    sym = sym.crop(bbox)
    wm_target = round(0.46 * S)
    scale = wm_target / max(sym.width, sym.height)
    sym_r = sym.resize((round(sym.width * scale), round(sym.height * scale)), Image.LANCZOS)
    # Tô phẳng 1 màu (viền ngà ấm) + hạ alpha rất thấp -> như khắc chìm, không
    # cạnh tranh màu với glyph app.
    solid = Image.new("RGBA", sym_r.size, BORDER + (0,))
    a = sym_r.getchannel("A").point(lambda v: int(v * (46 / 255)))
    solid.putalpha(a)
    wx = S - sym_r.width + round(0.10 * S)
    wy = S - sym_r.height + round(0.12 * S)
    tile.alpha_composite(solid, (wx, wy))

    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=RADIUS, fill=255)
    tile.putalpha(mask)

    bd = ImageDraw.Draw(tile)
    bd.rounded_rectangle([2, 2, S - 3, S - 3], radius=RADIUS - 2, outline=BORDER + (255,), width=4)
    return tile


# --- 2) "Thẻ tài liệu" trắng ngà + dải tiêu đề accent, trả về hộp thân bài ---

CARD_W = round(0.52 * S)
CARD_H = round(0.66 * S)
CARD_X0 = (S - CARD_W) // 2
CARD_Y0 = round((S - CARD_H) / 2) - round(0.012 * S)
CARD_X1 = CARD_X0 + CARD_W
CARD_Y1 = CARD_Y0 + CARD_H
CARD_RADIUS = round(0.10 * CARD_W)
HEADER_H = round(0.24 * CARD_H)
PAD = round(0.075 * CARD_W)


def draw_card(canvas: Image.Image, accent: tuple[int, int, int]) -> tuple[int, int, int, int]:
    # Bóng mềm (blur) dưới thẻ, để thẻ nổi lên trên ô tile ngà.
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    off = round(0.018 * S)
    sd.rounded_rectangle(
        [CARD_X0, CARD_Y0 + off, CARD_X1, CARD_Y1 + off],
        radius=CARD_RADIUS,
        fill=darken(NGA_BOT, 0.35) + (90,),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(round(0.016 * S)))
    canvas.alpha_composite(shadow)

    d = ImageDraw.Draw(canvas)
    # Thân thẻ trắng ấm.
    d.rounded_rectangle(
        [CARD_X0, CARD_Y0, CARD_X1, CARD_Y1],
        radius=CARD_RADIUS,
        fill=CARD_FILL + (255,),
        outline=accent + (90,),
        width=max(2, round(0.0035 * S)),
    )
    # Dải tiêu đề accent — chỉ bo 2 góc trên, khớp góc thẻ.
    d.rounded_rectangle(
        [CARD_X0, CARD_Y0, CARD_X1, CARD_Y0 + HEADER_H],
        radius=CARD_RADIUS,
        fill=accent + (255,),
        corners=(True, True, False, False),
    )
    return (CARD_X0 + PAD, CARD_Y0 + HEADER_H + PAD, CARD_X1 - PAD, CARD_Y1 - PAD)


# --- 3) Glyph riêng từng app, vẽ trong hộp thân bài (body box) ---------------

def glyph_writer(canvas: Image.Image, body: tuple[int, int, int, int], accent: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = body
    bw, bh = x1 - x0, y1 - y0
    d = ImageDraw.Draw(canvas)
    # Dòng tiêu đề đậm.
    title_h = round(0.12 * bh)
    d.rounded_rectangle([x0, y0, x0 + round(0.62 * bw), y0 + title_h], radius=title_h // 2, fill=accent + (255,))
    # Các dòng văn bản (skeleton text) — nhạt hơn, tỉ lệ khác nhau.
    muted = lighten(accent, 0.45)
    line_h = round(0.082 * bh)
    gap = round(0.075 * bh)
    widths = [1.0, 1.0, 0.8, 1.0, 0.55]
    y = y0 + title_h + gap
    for wf in widths:
        if y + line_h > y1:
            break
        d.rounded_rectangle([x0, y, x0 + round(wf * bw), y + line_h], radius=line_h // 2, fill=muted + (255,))
        y += line_h + gap


def glyph_calc(canvas: Image.Image, body: tuple[int, int, int, int], accent: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = body
    bw, bh = x1 - x0, y1 - y0
    d = ImageDraw.Draw(canvas)
    ncols, nrows = 4, 5
    gap = round(0.018 * bw)
    cell_w = (bw - gap * (ncols - 1)) / ncols
    cell_h = (bh - gap * (nrows - 1)) / nrows
    light = lighten(accent, 0.82)
    corner = darken(accent, 0.18)
    for r in range(nrows):
        for c in range(ncols):
            cx0 = x0 + c * (cell_w + gap)
            cy0 = y0 + r * (cell_h + gap)
            cx1 = cx0 + cell_w
            cy1 = cy0 + cell_h
            if r == 0 and c == 0:
                fill = corner
            elif r == 0 or c == 0:
                fill = accent
            else:
                fill = light
            d.rounded_rectangle([cx0, cy0, cx1, cy1], radius=round(0.12 * cell_w), fill=fill + (255,))


def glyph_impress(canvas: Image.Image, body: tuple[int, int, int, int], accent: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = body
    bw, bh = x1 - x0, y1 - y0
    d = ImageDraw.Draw(canvas)
    slide_h = round(0.60 * bh)
    sx0, sy0, sx1, sy1 = x0, y0, x1, y0 + slide_h
    d.rounded_rectangle([sx0, sy0, sx1, sy1], radius=round(0.08 * bw), fill=lighten(accent, 0.84) + (255,),
                         outline=accent + (255,), width=max(2, round(0.012 * bw)))
    scx, scy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
    tri_r = 0.30 * slide_h
    tri = [
        (scx - tri_r * 0.55, scy - tri_r),
        (scx - tri_r * 0.55, scy + tri_r),
        (scx + tri_r * 1.05, scy),
    ]
    d.polygon(tri, fill=accent + (255,))
    # Hai dòng ghi chú ngắn dưới slide.
    muted = lighten(accent, 0.55)
    line_h = round(0.09 * bh)
    gap = round(0.08 * bh)
    y = sy1 + gap
    for wf in (0.55, 0.35):
        if y + line_h > y1:
            break
        d.rounded_rectangle([x0, y, x0 + round(wf * bw), y + line_h], radius=line_h // 2, fill=muted + (255,))
        y += line_h + gap


def glyph_draw(canvas: Image.Image, body: tuple[int, int, int, int], accent: tuple[int, int, int], outline: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = body
    bw, bh = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    size = 0.56 * min(bw, bh)
    stroke = max(3, round(0.022 * bw))

    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    fill_a = accent + (205,)

    # Hình vuông bo góc (lệch dưới-trái).
    sq_cx, sq_cy = cx - 0.12 * bw, cy + 0.10 * bh
    ld.rounded_rectangle(
        [sq_cx - size / 2, sq_cy - size / 2, sq_cx + size / 2, sq_cy + size / 2],
        radius=round(0.18 * size), fill=fill_a, outline=outline + (255,), width=stroke,
    )
    canvas.alpha_composite(layer)

    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    # Hình tròn (lệch trên-phải).
    ci_cx, ci_cy = cx + 0.16 * bw, cy - 0.14 * bh
    r = size * 0.48
    ld.ellipse([ci_cx - r, ci_cy - r, ci_cx + r, ci_cy + r], fill=fill_a, outline=outline + (255,), width=stroke)
    canvas.alpha_composite(layer)

    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    # Tam giác (trên cùng, chồng lên cả hai).
    tr_cx, tr_cy = cx - 0.02 * bw, cy - 0.30 * bh
    tr = size * 0.52
    tri = [
        (tr_cx, tr_cy - tr * 0.62),
        (tr_cx - tr * 0.58, tr_cy + tr * 0.46),
        (tr_cx + tr * 0.58, tr_cy + tr * 0.46),
    ]
    ld.polygon(tri, fill=fill_a, outline=outline + (255,))
    # polygon() không vẽ outline dày theo width -> viền thủ công bằng line nối.
    ld.line(tri + [tri[0]], fill=outline + (255,), width=stroke, joint="curve")
    canvas.alpha_composite(layer)


def glyph_base(canvas: Image.Image, body: tuple[int, int, int, int], accent: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = body
    bw, bh = x1 - x0, y1 - y0
    cx = (x0 + x1) / 2
    d = ImageDraw.Draw(canvas)
    cyl_w = 0.66 * bw
    cx0, cx1 = cx - cyl_w / 2, cx + cyl_w / 2
    ell_h = 0.20 * bh
    top_y = y0 + ell_h / 2
    bot_y = y1 - ell_h / 2
    body_fill = accent
    top_fill = lighten(accent, 0.28)
    bot_fill = darken(accent, 0.10)

    # Thân trụ (hình chữ nhật giữa hai elip).
    d.rectangle([cx0, top_y, cx1, bot_y], fill=body_fill + (255,))
    # Elip đáy trước (vẽ trước để thân đè lên nửa trên của nó).
    d.ellipse([cx0, bot_y - ell_h / 2, cx1, bot_y + ell_h / 2], fill=bot_fill + (255,))
    d.rectangle([cx0, top_y, cx1, bot_y], fill=body_fill + (255,))
    # Elip đỉnh (đè lên trên cùng).
    d.ellipse([cx0, top_y - ell_h / 2, cx1, top_y + ell_h / 2], fill=top_fill + (255,),
              outline=darken(accent, 0.05) + (255,), width=max(2, round(0.01 * bw)))
    # Hai vạch elip ngang biểu thị các đĩa xếp chồng.
    for frac in (0.37, 0.67):
        ry = top_y + (bot_y - top_y) * frac
        rh = ell_h * 0.42
        d.arc([cx0, ry - rh / 2, cx1, ry + rh / 2], start=10, end=170,
              fill=lighten(accent, 0.55) + (255,), width=max(2, round(0.012 * bw)))


def glyph_math(canvas: Image.Image, body: tuple[int, int, int, int], accent: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = body
    bw, bh = x1 - x0, y1 - y0
    d = ImageDraw.Draw(canvas)
    ch = "∑"  # Σ (summation)
    size = round(0.95 * min(bw, bh))
    font = ImageFont.truetype(FONT_BOLD, size)
    bbox = d.textbbox((0, 0), ch, font=font)
    while (bbox[2] - bbox[0] > bw or bbox[3] - bbox[1] > bh) and size > 10:
        size -= 4
        font = ImageFont.truetype(FONT_BOLD, size)
        bbox = d.textbbox((0, 0), ch, font=font)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    tx = cx - (bbox[0] + bbox[2]) / 2
    ty = cy - (bbox[1] + bbox[3]) / 2
    d.text((tx, ty), ch, font=font, fill=accent + (255,))


APPS = {
    "writer": (MUC, glyph_writer),
    "calc": (CALC_GREEN, glyph_calc),
    "impress": (DO_SON, glyph_impress),
    "base": (MUC, glyph_base),
    "math": (DO_DAI, glyph_math),
}


def render(app: str) -> Image.Image:
    tile = build_tile()
    if app == "draw":
        body = draw_card(tile, VANG_TAM)
        glyph_draw(tile, body, VANG_TAM, MUC)
        return tile
    accent, fn = APPS[app]
    body = draw_card(tile, accent)
    fn(tile, body, accent)
    return tile


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    apps = ["writer", "calc", "impress", "draw", "base", "math"]
    written_sizes: list[tuple[str, int, str]] = []

    for app in apps:
        master = render(app)
        master_path = os.path.join(OUT_DIR, f"NaMiOffice_{app.capitalize()}_1024.png")
        master.save(master_path, "PNG")
        print(f"wrote master {master_path} ({master.size})")

        for size in SHIP_SIZES:
            apps_dir = os.path.join(ICONS_ROOT, f"{size}x{size}", "apps")
            if not os.path.isdir(apps_dir):
                print(f"  !! skip size {size}: {apps_dir} không tồn tại")
                continue
            icon = master.resize((size, size), Image.LANCZOS)
            target = os.path.join(apps_dir, f"namioffice-{app}.png")
            icon.save(target, "PNG")
            written_sizes.append((app, size, target))

    print(f"total: {len(written_sizes)} icon files ghi vào hicolor/<N>x<N>/apps")


if __name__ == "__main__":
    main()
