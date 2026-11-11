#!/usr/bin/env python3
"""NaMiOS — bo render dung chung cho cac tai san raster "Dong Son v3" (navy +
hoa van trong dong + song bien teal/gold) dung cho nhung noi KHONG the doc SVG
truc tiep (Plymouth two-step plugin, GRUB theme.txt desktop-image, isolinux
splash.png) — khac voi SDDM Main.qml/Background.qml va Plasma Splash.qml, ca
hai CO THE doc .svg truc tiep qua Qt Quick Image (da co tien le trong chinh
repo nay: Splash.qml dung source "../images/trongdong.svg").

LY DO co file nay: sandbox build khong co rsvg-convert/inkscape/imagemagick, va
cairosvg cai qua pip nhung thieu thu vien he thong libcairo.so.2 (da kiem tra
11/11/2026) — giong chinh ly do branding/plymouth/make-plymouth-assets.py da
ghi trong docstring cua no ("Khong co SVG rasterizer trong sandbox"). File nay
noi tiep dung tien le do: toa do duoi day CHEP LAI CHINH XAC tu cac file SVG
nguon trong branding/kit/NaMi_Brand_DongSon_v1/ (khong doan/ve lai tu do),
roi dung Pillow (ImageDraw polygon/ellipse/line + bezier sampler tu viet) ve
lai dung hinh hoc, render o do phan giai sieu mau (supersample) roi downsample
LANCZOS de co net chong rang (AA) gan dung vector.

NGUON toa do (doi chieu truc tiep, sha256 trong branding/kit/.../manifest.json):
  - nami-symbol-dark-background.svg (bien the "nen toi": vong/net mau ivory
    #FFF9EF thay vi navy #092D4F cua nami-symbol-color.svg — dung dung bien
    the nay cho MOI nen navy, vi ban "color" co vong navy se "navy-on-navy"
    vo hinh tren nen navy).
  - login-background.svg / boot-splash.svg: 2 duong song (Quadratic Bezier
    "Q...T..." — da khai trien lenh "T" smooth-quadratic bang cong thuc phan
    chieu diem dieu khien 2*end-control) tren canvas goc 1920x1080, scale ty
    le theo canvas dich (x theo W/1920, y theo H/1080) khi dung cho GRUB
    (800x600)/isolinux (640x480).

verified_on_host: NO — chua xem qua man hinh thuc/anh chup boot, chi kiem bang
Read tool (xem PNG) ngay trong phien lam viec nay.
"""
from __future__ import annotations

from PIL import Image, ImageDraw

# ---- mau v3 "Dong Son" (xem chi dan nhiem vu + 05_design_tokens/colors.css) --
NAVY = "#092D4F"
GOLD = "#DEA93E"
VERMILION = "#D64C3E"
TEAL = "#278F8D"
IVORY = "#FFF9EF"


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _hex_to_rgba(h: str, alpha: float = 1.0) -> tuple[int, int, int, int]:
    r, g, b = _hex_to_rgb(h)
    return (r, g, b, round(255 * alpha))


def quad_bezier_points(p0, p1, p2, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
        y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    return pts


def cubic_bezier_points(p0, p1, p2, p3, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


# ---- 2 duong song (chep tu login-background.svg / boot-splash.svg, canvas
# goc 1920x1080) — da khai trien lenh "T" (smooth quadratic) thanh toa do
# diem-dieu-khien-phan-chieu tuong minh ------------------------------------
_WAVE_TEAL_1920 = {
    "start": (0, 900),
    "seg1": {"ctrl": (530, 655), "end": (1050, 905)},
    "seg2": {"ctrl": (1570, 1155), "end": (1920, 806)},  # T: 2*(1050,905)-(530,655)
    "color": TEAL,
    "alpha": 0.14,
}
_WAVE_GOLD_1920 = {
    "start": (0, 961),
    "seg1": {"ctrl": (510, 760), "end": (1050, 958)},
    "seg2": {"ctrl": (1590, 1156), "end": (1920, 881)},  # T: 2*(1050,958)-(510,760)
    "color": GOLD,
    "alpha": 0.10,
}


def _wave_polygon(wave: dict, w: int, h: int) -> list[tuple[float, float]]:
    sx, sy = w / 1920.0, h / 1080.0

    def sc(pt):
        return (pt[0] * sx, pt[1] * sy)

    start = sc(wave["start"])
    c1 = sc(wave["seg1"]["ctrl"])
    e1 = sc(wave["seg1"]["end"])
    c2 = sc(wave["seg2"]["ctrl"])
    e2 = sc(wave["seg2"]["end"])
    pts = [start]
    pts += quad_bezier_points(start, c1, e1)[1:]
    pts += quad_bezier_points(e1, c2, e2)[1:]
    pts += [(w, h), (0, h)]
    return pts


def draw_navy_wave_background(w: int, h: int, supersample: int = 4) -> Image.Image:
    """Nen navy #092D4F + 2 dai song (teal/gold, trong suot thap) o day man
    hinh — ty le lai theo (w,h) tu toa do goc 1920x1080 cua kit. KHONG co
    bieu tuong/chu (de lop goi dung o tren khong bi trung chu that)."""
    W, H = w * supersample, h * supersample
    img = Image.new("RGBA", (W, H), _hex_to_rgba(NAVY))
    for wave in (_WAVE_TEAL_1920, _WAVE_GOLD_1920):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        pts = _wave_polygon(wave, W, H)
        draw.polygon(pts, fill=_hex_to_rgba(wave["color"], wave["alpha"]))
        img = Image.alpha_composite(img, layer)
    if supersample > 1:
        img = img.resize((w, h), Image.LANCZOS)
    return img


# ---- bieu tuong trong dong (chep tu nami-symbol-dark-background.svg, canvas
# goc 512x512) --------------------------------------------------------------
_STAR_POINTS_512 = [
    (256.000, 140.000), (270.235, 202.874), (314.000, 155.541), (294.891, 217.109),
    (356.459, 198.000), (309.126, 241.765), (372.000, 256.000), (309.126, 270.235),
    (356.459, 314.000), (294.891, 294.891), (314.000, 356.459), (270.235, 309.126),
    (256.000, 372.000), (241.765, 309.126), (198.000, 356.459), (217.109, 294.891),
    (155.541, 314.000), (202.874, 270.235), (140.000, 256.000), (202.874, 241.765),
    (155.541, 198.000), (217.109, 217.109), (198.000, 155.541), (241.765, 202.874),
]

_TICKS_512 = [
    [(256.00, 87.00), (240.00, 115.00), (272.00, 115.00)],   # tren
    [(425.00, 256.00), (397.00, 240.00), (397.00, 272.00)],  # phai
    [(256.00, 425.00), (272.00, 397.00), (240.00, 397.00)],  # duoi
    [(87.00, 256.00), (115.00, 272.00), (115.00, 240.00)],   # trai
]

_CORNER_LINES_512 = [
    ((350.0, 135.1), (364.2, 149.2)),
    ((362.8, 147.8), (376.9, 162.0)),
    ((376.9, 350.0), (362.8, 364.2)),
    ((364.2, 362.8), (350.0, 376.9)),
    ((162.0, 376.9), (147.8, 362.8)),
    ((149.2, 364.2), (135.1, 350.0)),
    ((135.1, 162.0), (149.2, 147.8)),
    ((147.8, 149.2), (162.0, 135.1)),
]

# (p0, c1, c2, p3, c4, c5, p6=close-to-p0) — moi "flourish" la 1 duong M...C...C...Z
_FLOURISH_TOP_512 = [
    (89, 132), (155, 31), (314, 6), (414, 85),
    (453, 115), (476, 161), (480, 195),
    (442, 129), (373, 88), (291, 85),
    (211, 81), (147, 105), (89, 132),
]
_FLOURISH_BL_512 = [
    (72, 346), (96, 414), (167, 467), (257, 475),
    (298, 479), (331, 468), (363, 447),
    (267, 475), (164, 428), (100, 351),
]
_FLOURISH_BR_512 = [
    (351, 464), (419, 428), (465, 362), (469, 287),
    (484, 360), (447, 433), (383, 470),
]


def _flourish_polygon(pts_3n_plus_1: list[tuple[float, float]], scale: float) -> list[tuple[float, float]]:
    """pts la day M, C c1 c2 p, C c3 c4 p, ... (bo 3 diem/doan sau diem dau)."""
    pts = [(x * scale, y * scale) for x, y in pts_3n_plus_1]
    p0 = pts[0]
    out = [p0]
    i = 1
    cur = p0
    while i + 2 < len(pts):
        c1, c2, p3 = pts[i], pts[i + 1], pts[i + 2]
        out += cubic_bezier_points(cur, c1, c2, p3)[1:]
        cur = p3
        i += 3
    return out


def draw_trongdong_symbol(
    size: int,
    ring_color: str = IVORY,
    star_color: str = GOLD,
    tick_color: str = VERMILION,
    flourish_color: str = TEAL,
    flourish_alt_color: str = VERMILION,
    supersample: int = 4,
) -> Image.Image:
    """Bieu tuong trong dong day du mau (ban "nen toi"/dark-background) —
    RGBA trong suot, kich thuoc size x size. Dung cho Plymouth watermark/lock,
    GRUB/isolinux splash — nhung noi KHONG the doc SVG truc tiep."""
    S = size * supersample
    scale = S / 512.0
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    def pt(p):
        return (p[0] * scale, p[1] * scale)

    # 2 vong tron dong tam (stroke, khong fill) — rong vien ty le theo scale
    for r, width in ((204, 24), (155, 31)):
        r_s, w_s = r * scale, width * scale
        cx = cy = 256 * scale
        bbox = (cx - r_s, cy - r_s, cx + r_s, cy + r_s)
        draw.ellipse(bbox, outline=_hex_to_rgba(ring_color), width=round(w_s))

    # 3 hoa van "flourish" (ve TRUOC star/tick de nam duoi, giong thu tu khai
    # bao trong SVG nguon: 2 teal + 1 vermilion, ve trong cung z-order voi cac
    # vong/sao de hoa quyen — SVG nguon ve chung THEO SAU vong+sao+tick+line,
    # nen o day giu dung thu tu goc: flourish ve SAU CUNG, nam TREN cac vong
    # tron (dung y nhu file SVG — cac <path> flourish nam cuoi danh sach con).
    for pts_src, color in (
        (_FLOURISH_TOP_512, flourish_color),
        (_FLOURISH_BL_512, flourish_alt_color),
        (_FLOURISH_BR_512, flourish_color),
    ):
        poly = _flourish_polygon(pts_src, scale)
        draw.polygon(poly, fill=_hex_to_rgba(color))

    # sao nhieu canh trung tam
    draw.polygon([pt(p) for p in _STAR_POINTS_512], fill=_hex_to_rgba(star_color))

    # 4 tick tam giac (Bac/Dong/Nam/Tay)
    for tri in _TICKS_512:
        draw.polygon([pt(p) for p in tri], fill=_hex_to_rgba(tick_color))

    # 8 doan gach cheo o 4 goc (tung doi net doi)
    line_w = max(1, round(7 * scale))
    for a, b in _CORNER_LINES_512:
        draw.line([pt(a), pt(b)], fill=_hex_to_rgba(ring_color), width=line_w)
        # bo tron 2 dau net (stroke-linecap=round trong SVG) — xap xi bang 1
        # hinh tron nho o moi dau, ban kinh = nua do rong net
        for end in (pt(a), pt(b)):
            rr = line_w / 2
            draw.ellipse((end[0] - rr, end[1] - rr, end[0] + rr, end[1] + rr), fill=_hex_to_rgba(ring_color))

    if supersample > 1:
        img = img.resize((size, size), Image.LANCZOS)
    return img


if __name__ == "__main__":
    # tu-kiem: xuat 1 ban nen+song (640x360) + 1 ban bieu tuong (256) ra /tmp
    # de xem bang Read tool truoc khi dung vao pipeline chinh thuc.
    draw_navy_wave_background(640, 360).save("/tmp/_check_wave.png")
    draw_trongdong_symbol(256).save("/tmp/_check_symbol.png")
    print("wrote /tmp/_check_wave.png and /tmp/_check_symbol.png")
