#!/usr/bin/env python3
"""NaMi — BỘ ICON kiểu macOS × nhận diện Đông Sơn (bản MẪU để duyệt phong cách).

Cuong (#18381, 12/11/2026): "thiết kế bộ icon hoàn chỉnh xuyên suốt cho cả hệ
điều hành… đẹp như macOS, hiện đại, thiện cảm + ấn tượng từ đầu… apply toàn HĐH,
khi nào bảo build thì mới làm." Vì em KHÔNG render thấy trong sandbox, đây là
bản MẪU 8 icon cốt lõi để anh chấm phong cách TRƯỚC khi nhân ra cả bộ + apply.

Ngôn ngữ thiết kế: ô bo "squircle" (superellipse) kiểu macOS Big Sur, nền
gradient chéo (sáng trên-trái → đậm dưới-phải), lớp gloss mềm phía trên tạo
chiều sâu, glyph trắng/ngà hình học sạch; bảng màu lấy từ Đông Sơn (navy/gold/
vermilion/teal) hoà với dải màu app quen thuộc. Icon "Trợ lý" = ngôi sao trống
đồng vàng trên navy (biểu tượng thương hiệu).

Tái lập: python3 branding/dongson-v3-render/make_app_icons_macos_v3.py
Đầu ra:  branding/dongson-v3-render/app-icons-preview/*.png + contact-sheet.png
"""
from __future__ import annotations

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "app-icons-preview")
os.makedirs(OUT, exist_ok=True)

FINAL = 512
WORK = 1536  # 3x supersample -> downscale LANCZOS
R_RATIO = 0.445  # bán kính superellipse so với WORK (ô chiếm ~0.89 canvas)
N_SE = 5.0       # số mũ superellipse (macOS ~5)

FONT_PATH = "/tmp/vnfonts/Roboto-Medium.ttf"
FONT_BOLD = "/tmp/vnfonts/Roboto-Medium.ttf"


def hx(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def squircle_alpha(size, r_ratio=R_RATIO, n=N_SE):
    cx = cy = (size - 1) / 2.0
    R = size * r_ratio
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64)
    nx = (xx - cx) / R
    ny = (yy - cy) / R
    f = (np.abs(nx) ** n + np.abs(ny) ** n) ** (1.0 / n)
    sd = (1.0 - f) * R  # ~ khoảng cách pixel tới mép (dương = trong)
    a = np.clip(sd / 1.4 + 0.5, 0.0, 1.0)
    return a


def diagonal_gradient(size, top, bottom):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64)
    t = (xx + yy) / (2.0 * (size - 1))
    t = t[..., None]
    top = np.array(top, dtype=np.float64)
    bot = np.array(bottom, dtype=np.float64)
    rgb = top * (1.0 - t) + bot * t
    return rgb.astype(np.uint8)


def base_tile(top, bottom):
    rgb = diagonal_gradient(WORK, top, bottom)
    a = squircle_alpha(WORK)
    img = np.dstack([rgb, (a * 255).astype(np.uint8)])
    tile = Image.fromarray(img, "RGBA")

    # Gloss mềm phía trên (ánh sáng macOS).
    gloss = Image.new("L", (WORK, WORK), 0)
    gd = ImageDraw.Draw(gloss)
    gd.ellipse(
        [WORK * 0.07, -WORK * 0.30, WORK * 0.93, WORK * 0.52],
        fill=70,
    )
    gloss = gloss.filter(ImageFilter.GaussianBlur(WORK * 0.03))
    ga = np.minimum(np.array(gloss, np.float64), a * 255).astype(np.uint8)
    white = Image.new("RGBA", (WORK, WORK), (255, 255, 255, 0))
    white.putalpha(Image.fromarray(ga, "L"))
    tile = Image.alpha_composite(tile, white)
    return tile


def _rr(d, box, rad, **kw):
    d.rounded_rectangle(box, radius=rad, **kw)


# ----- glyph: mỗi hàm vẽ vào layer RGBA (WORK), tâm (C,C), bán kính glyph E ---
C = WORK / 2.0
E = WORK * 0.255
IV = (255, 249, 239, 255)   # ngà
WH = (255, 255, 255, 255)


def g_doc(d, accent):
    w, h = E * 1.42, E * 1.78
    x0, y0 = C - w / 2, C - h / 2
    fold = w * 0.34
    pts = [(x0, y0), (x0 + w - fold, y0), (x0 + w, y0 + fold),
           (x0 + w, y0 + h), (x0, y0 + h)]
    d.polygon(pts, fill=WH)
    d.polygon([(x0 + w - fold, y0), (x0 + w - fold, y0 + fold),
               (x0 + w, y0 + fold)], fill=(226, 232, 240, 255))
    lx0, lx1 = x0 + w * 0.16, x0 + w * 0.84
    ly = y0 + h * 0.50
    gap = h * 0.135
    for i in range(3):
        xe = lx1 if i < 2 else x0 + w * 0.6
        d.line([(lx0, ly + i * gap), (xe, ly + i * gap)],
               fill=accent + (255,), width=int(E * 0.052))


def g_sheet(d, accent):
    s = E * 1.62
    x0, y0 = C - s / 2, C - s / 2
    rad = s * 0.12
    _rr(d, [x0, y0, x0 + s, y0 + s], rad, fill=WH)
    hdr = s * 0.26
    # hàng tiêu đề tô màu app
    head = Image.new("RGBA", (int(s), int(hdr)), accent + (255,))
    # vẽ grid
    col = accent + (255,)
    for i in range(1, 3):
        xx = x0 + s * i / 3
        d.line([(xx, y0), (xx, y0 + s)], fill=col, width=int(E * 0.045))
    for i in range(1, 3):
        yy = y0 + hdr + (s - hdr) * (i - 1) / 2
        d.line([(x0, yy), (x0 + s, yy)], fill=col, width=int(E * 0.045))
    d.rectangle([x0, y0, x0 + s, y0 + hdr], fill=accent + (255,))
    _rr(d, [x0, y0, x0 + s, y0 + s], rad, outline=col, width=int(E * 0.05))


def g_slide(d, accent):
    w, h = E * 1.86, E * 1.30
    x0, y0 = C - w / 2, C - h / 2
    _rr(d, [x0, y0, x0 + w, y0 + h], w * 0.07, fill=WH)
    # nút play tam giác màu app
    t = E * 0.52
    tx = C - t * 0.30
    d.polygon([(tx - t * 0.45, C - t * 0.55),
               (tx - t * 0.45, C + t * 0.55),
               (tx + t * 0.62, C)], fill=accent + (255,))


def g_star(d, gold):
    # Ngôi sao trống đồng + vòng — biểu tượng thương hiệu (Trợ lý).
    pts = 12
    rO, rI = E * 1.18, E * 0.5
    poly = []
    for i in range(pts * 2):
        ang = math.pi * i / pts - math.pi / 2
        r = rO if i % 2 == 0 else rI
        poly.append((C + r * math.cos(ang), C + r * math.sin(ang)))
    d.polygon(poly, fill=gold + (255,))
    d.ellipse([C - E * 0.34, C - E * 0.34, C + E * 0.34, C + E * 0.34],
              fill=None, outline=gold + (255,), width=int(E * 0.11))
    rr = E * 1.42
    d.ellipse([C - rr, C - rr, C + rr, C + rr], outline=gold + (200,),
              width=int(E * 0.075))


def g_calendar(d, accent):
    s = E * 1.66
    x0, y0 = C - s / 2, C - s / 2
    rad = s * 0.12
    _rr(d, [x0, y0, x0 + s, y0 + s], rad, fill=WH)
    band = s * 0.30
    top = Image.new("RGBA", (WORK, WORK), (0, 0, 0, 0))
    td = ImageDraw.Draw(top)
    _rr(td, [x0, y0, x0 + s, y0 + s], rad, fill=accent + (255,))
    td.rectangle([x0, y0 + band, x0 + s, y0 + s], fill=(0, 0, 0, 0))
    # rings
    for rx in (x0 + s * 0.3, x0 + s * 0.7):
        d.rounded_rectangle([rx - s * 0.03, y0 - s * 0.07,
                             rx + s * 0.03, y0 + s * 0.09],
                            radius=s * 0.03, fill=(210, 214, 222, 255))
    # số ngày
    try:
        fnt = ImageFont.truetype(FONT_BOLD, int(s * 0.44))
    except Exception:
        fnt = ImageFont.load_default()
    d2 = None
    txt = "12"
    bb = d.textbbox((0, 0), txt, font=fnt)
    tw, th2 = bb[2] - bb[0], bb[3] - bb[1]
    d.text((C - tw / 2 - bb[0], y0 + band + (s - band) / 2 - th2 / 2 - bb[1]),
           txt, font=fnt, fill=accent + (255,))
    return top


def g_globe(d, accent):
    r = E * 1.14
    lw = int(E * 0.08)
    d.ellipse([C - r, C - r, C + r, C + r], outline=WH, width=lw)
    d.line([(C - r, C), (C + r, C)], fill=WH, width=lw)
    d.ellipse([C - r * 0.52, C - r, C + r * 0.52, C + r], outline=WH, width=lw)
    for fy in (0.46,):
        yy = r * fy
        import math as _m
        xhalf = r * _m.sqrt(max(0.0, 1 - fy * fy))
        d.arc([C - xhalf, C - yy - r * 0.0, C + xhalf, C + yy + r * 0.9],
              0, 180, fill=WH, width=lw)
        d.arc([C - xhalf, C - yy - r * 0.9, C + xhalf, C + yy],
              180, 360, fill=WH, width=lw)


def g_folder(d, accent):
    w, h = E * 1.9, E * 1.4
    x0, y0 = C - w / 2, C - h / 2 + E * 0.08
    tab_w, tab_h = w * 0.42, h * 0.22
    d.polygon([(x0, y0), (x0 + tab_w, y0),
               (x0 + tab_w + tab_h * 0.8, y0 + tab_h),
               (x0 + w, y0 + tab_h), (x0 + w, y0 + h), (x0, y0 + h)],
              fill=IV)
    _rr(d, [x0, y0 + tab_h, x0 + w, y0 + h], w * 0.05,
        fill=(255, 255, 255, 255))
    d.rectangle([x0, y0 + tab_h, x0 + w, y0 + tab_h + h * 0.12],
                fill=(234, 238, 244, 255))


def g_gear(d, accent):
    teeth = 9
    rO, rIn, rhole = E * 1.16, E * 0.82, E * 0.42
    poly = []
    steps = teeth * 2
    for i in range(steps * 2):
        ang = 2 * math.pi * i / (steps * 2)
        seg = (i // 2) % 2
        r = rO if seg == 0 else rIn
        poly.append((C + r * math.cos(ang), C + r * math.sin(ang)))
    d.polygon(poly, fill=WH)
    d.ellipse([C - rhole, C - rhole, C + rhole, C + rhole], fill=(0, 0, 0, 0))


ICONS = [
    ("nDoc", "Văn bản", "#3E8BFF", "#1D4FB0", lambda d: g_doc(d, hx("#1D4FB0"))),
    ("nSheet", "Bảng tính", "#2BC06F", "#148049", lambda d: g_sheet(d, hx("#148049"))),
    ("nSlide", "Trình chiếu", "#F0663E", "#B23A2E", lambda d: g_slide(d, hx("#B23A2E"))),
    ("nAssistant", "Trợ lý", "#16528A", "#082742", lambda d: g_star(d, hx("#E8B64A"))),
    ("nCalendar", "Lịch", "#F15A5A", "#C22E2E", None),  # calendar trả overlay
    ("nBrowser", "Trình duyệt", "#2FB3AF", "#17726F", lambda d: g_globe(d, hx("#17726F"))),
    ("nFiles", "Tệp", "#F0BC57", "#CB8F2E", lambda d: g_folder(d, hx("#CB8F2E"))),
    ("nSettings", "Cài đặt", "#657085", "#333A45", lambda d: g_gear(d, hx("#333A45"))),
]


def render_icon(name, viet, top, bottom, glyphfn):
    tile = base_tile(hx(top), hx(bottom))
    glyph = Image.new("RGBA", (WORK, WORK), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glyph)
    overlay = None
    if name == "nCalendar":
        overlay = g_calendar(gd, hx(bottom))
    else:
        glyphfn(gd)
    # bóng mềm cho glyph (nổi khối)
    shadow = glyph.split()[3].filter(ImageFilter.GaussianBlur(WORK * 0.012))
    sh = Image.new("RGBA", (WORK, WORK), (0, 0, 0, 0))
    sh.putalpha(shadow.point(lambda v: int(v * 0.28)))
    sh = sh.filter(ImageFilter.GaussianBlur(WORK * 0.006))
    off = int(WORK * 0.012)
    tile.alpha_composite(sh, (0, off))
    if overlay is not None:
        tile = Image.alpha_composite(tile, overlay)
    tile = Image.alpha_composite(tile, glyph)
    # clip lại theo squircle (phòng glyph tràn mép)
    a = (squircle_alpha(WORK) * 255).astype(np.uint8)
    base_a = np.array(tile.split()[3], np.uint8)
    # giữ nguyên (glyph nằm trong), chỉ đảm bảo không vượt
    tile.putalpha(Image.fromarray(np.minimum(base_a, np.maximum(a, 0)), "L"))
    icon = tile.resize((FINAL, FINAL), Image.LANCZOS)
    icon.save(os.path.join(OUT, f"{name}.png"))
    return icon


def contact_sheet(icons):
    cols, rows = 4, 2
    cell = 300
    pad_top, pad_x, label_h = 150, 60, 86
    W = pad_x * 2 + cols * cell
    H = pad_top + rows * (cell + label_h) + 50
    bg = np.zeros((H, W, 3), np.float64)
    t = np.linspace(0, 1, H)[:, None, None]
    bg[:] = np.array(hx("#F4F6FA")) * (1 - t) + np.array(hx("#E4E8F0")) * t
    sheet = Image.fromarray(bg.astype(np.uint8), "RGB").convert("RGBA")
    dr = ImageDraw.Draw(sheet)
    try:
        ftitle = ImageFont.truetype(FONT_BOLD, 52)
        flabel = ImageFont.truetype(FONT_PATH, 34)
        fsub = ImageFont.truetype(FONT_PATH, 26)
    except Exception:
        ftitle = flabel = fsub = ImageFont.load_default()
    title = "NaMi — Bộ icon (mẫu phong cách macOS × Đông Sơn)"
    dr.text((pad_x, 48), title, font=ftitle, fill=hx("#092D4F") + (255,))
    isz = 188
    for idx, (name, viet, *_rest) in enumerate(icons):
        ic = Image.open(os.path.join(OUT, f"{name}.png")).resize((isz, isz), Image.LANCZOS)
        r, c = divmod(idx, cols)
        cx = pad_x + c * cell + (cell - isz) // 2
        cy = pad_top + r * (cell + label_h) + (cell - isz) // 2 - 10
        # bóng đổ dưới icon
        sh = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
        shm = ic.split()[3].filter(ImageFilter.GaussianBlur(16))
        shl = Image.new("RGBA", (isz, isz), (10, 25, 45, 0))
        shl.putalpha(shm.point(lambda v: int(v * 0.33)))
        sh.alpha_composite(shl, (cx, cy + 16))
        sh = sh.filter(ImageFilter.GaussianBlur(6))
        sheet = Image.alpha_composite(sheet, sh)
        sheet.alpha_composite(ic, (cx, cy))
        dr = ImageDraw.Draw(sheet)
        lb = viet
        bb = dr.textbbox((0, 0), lb, font=flabel)
        dr.text((pad_x + c * cell + (cell - (bb[2] - bb[0])) // 2,
                 cy + isz + 18), lb, font=flabel, fill=hx("#0E2238") + (255,))
        bb2 = dr.textbbox((0, 0), name, font=fsub)
        dr.text((pad_x + c * cell + (cell - (bb2[2] - bb2[0])) // 2,
                 cy + isz + 58), name, font=fsub, fill=hx("#6B7686") + (255,))
    out = os.path.join(OUT, "contact-sheet.png")
    sheet.convert("RGB").save(out, "PNG")
    return out


def main():
    for name, viet, top, bottom, fn in ICONS:
        render_icon(name, viet, top, bottom, fn)
        print(f"[OK] {name} ({viet})")
    cs = contact_sheet(ICONS)
    print(f"[OK] contact sheet -> {cs}")


if __name__ == "__main__":
    main()
