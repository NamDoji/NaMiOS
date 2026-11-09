#!/usr/bin/env python3
"""Sinh ảnh "rebrand" LibreOffice -> NaMiOffice (ĐỔI TÊN HIỂN THỊ, không build
lại mã nguồn LibreOffice) từ bộ nhận diện v2 "Sen Việt"
(branding/logo-sen-viet-v2/). Nền NGÀ (ivory) — KHÔNG BAO GIỜ đặt hoa sen/logo
trên nền đen (QĐ 09/11/2026 của Cuong, xem branding/plymouth/make-plymouth-assets.py).

LibreOffice đọc 2 vị trí "branding override" tại nơi cài đặt thật (xác nhận qua
tài liệu cộng đồng TDF + layout gói Debian — xem docs/branding/NAMIOFFICE.md
§"Nguồn xác minh", verified_on_host: NO vì repo này không có LibreOffice cài
sẵn để đối chiếu trực tiếp):
  - /usr/lib/libreoffice/program/intro.png       -> màn hình splash lúc khởi động
  - /usr/lib/libreoffice/program/shell/about.svg  -> ảnh nền hộp thoại "About"

Sinh 3 file vào OUT_DIR (branding/office/out/) rồi COPY NGUYÊN VĂN sang
CHROOT_DIR (distro/live-build/config/includes.chroot/usr/share/namios/office-brand/)
để hook 0450-namioffice-brand.hook.chroot chép tiếp vào đúng 2 đường dẫn trên
lúc build chroot (không ghi thẳng vào /usr/lib/libreoffice/... từ máy build vì
LibreOffice KHÔNG được cài trên máy soạn gói này):
  - intro.png   : 500x360 — nền ngà, biểu tượng sen + chữ "NaMiOffice"
                  ("NaMi" mực #182E3B + "Office" đỏ son #C93643) + dòng tín
                  dụng nhỏ "dựa trên LibreOffice".
  - about.png   : 640x400 — bản raster thuần của ảnh nền hộp thoại About
                  (fallback, dùng để xem trước / nếu about.svg không ổn).
  - about.svg   : wrapper SVG hợp lệ nhúng CHÍNH about.png ở trên qua thẻ
                  <image> base64 (KHÔNG vẽ path vector tay — sandbox này
                  không có SVG rasterizer để đối chiếu hình, giống lý do nêu
                  trong make-plymouth-assets.py; nhúng raster là cách tái lập
                  được + chắc hình trông y PIL render ra). Ghi rõ trong
                  docs/branding/NAMIOFFICE.md đây KHÔNG phải SVG vector tay.

Màu "Sen Việt" (khớp branding/design-system/tokens.json + logo-sen-viet-v2):
  - Ngà sáng/ấm   #FBF8F2 -> #EFE3D1  (gradient nền, KHÔNG BAO GIỜ nền đen)
  - Đỏ son        #C93643  (chữ "Office", gạch nhấn)
  - Đỏ đài (chữ)  #92212E  (dòng tín dụng — đỏ AN TOÀN WCAG trên nền sáng,
                            ≥7.5:1 theo branding/design-system/tokens.json)
  - Vàng tâm      #F2C66D  (gạch trang trí mỏng)
  - Mực chữ       #182E3B  (chữ "NaMi", viền đậm)

Tái lập: python3 branding/office/make-namioffice-brand.py
"""
from __future__ import annotations

import base64
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOTUS = os.path.join(ROOT, "branding/logo-sen-viet-v2/NaMiOS_Sen_Viet_Symbol_1024.png")
FONT_BOLD = os.path.join(ROOT, "branding/fonts/DejaVuSans-Bold.ttf")
FONT_REGULAR = os.path.join(ROOT, "branding/fonts/DejaVuSans.ttf")

OUT_DIR = os.path.join(ROOT, "branding/office/out")
CHROOT_DIR = os.path.join(
    ROOT,
    "distro/live-build/config/includes.chroot/usr/share/namios/office-brand",
)

# Ngà ấm — KHỚP wallpaper/plymouth đã đổi 09/11/2026 ("hoa sen quý KHÔNG đặt
# trên nền đen"). KHÔNG dùng mực đêm/nền tối cho bất kỳ asset office nào.
IVORY_TOP = (0xFB, 0xF8, 0xF2)
IVORY_BOT = (0xEF, 0xE3, 0xD1)
SON = (0xC9, 0x36, 0x43)     # đỏ son — chữ "Office"
DAI = (0x92, 0x21, 0x2E)     # đỏ đài — dòng tín dụng (chữ an toàn nền sáng)
VANG = (0xF2, 0xC6, 0x6D)    # vàng tâm — gạch nhấn mỏng
MUC = (0x18, 0x2E, 0x3B)     # mực chữ — "NaMi"

INTRO_W, INTRO_H = 500, 360
ABOUT_W, ABOUT_H = 640, 400


def _gradient(w: int, h: int) -> Image.Image:
    """Gradient ngà dọc trên->dưới, giống công thức trong make-plymouth-assets.py
    (nhất quán màu splash boot <-> splash Office)."""
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        row = (
            int(IVORY_TOP[0] + (IVORY_BOT[0] - IVORY_TOP[0]) * t),
            int(IVORY_TOP[1] + (IVORY_BOT[1] - IVORY_TOP[1]) * t),
            int(IVORY_TOP[2] + (IVORY_BOT[2] - IVORY_TOP[2]) * t),
        )
        for x in range(w):
            px[x, y] = row
    return img


def _wordmark(draw: "ImageDraw.ImageDraw", center_x: int, top_y: int, font_px: int) -> int:
    """Vẽ 'NaMi' (mực) + 'Office' (đỏ son) canh giữa theo center_x, bắt đầu ở
    top_y. Trả về y ngay dưới chữ (để layout dòng kế tiếp)."""
    f = ImageFont.truetype(FONT_BOLD, font_px)
    bbox_full = draw.textbbox((0, 0), "NaMiOffice", font=f)
    bbox_nami = draw.textbbox((0, 0), "NaMi", font=f)
    full_w = bbox_full[2] - bbox_full[0]
    full_h = bbox_full[3] - bbox_full[1]
    nami_w = bbox_nami[2] - bbox_nami[0]

    x0 = center_x - full_w // 2
    y0 = top_y - bbox_full[1]
    draw.text((x0, y0), "NaMi", font=f, fill=MUC)
    draw.text((x0 + nami_w, y0), "Office", font=f, fill=SON)
    return top_y + full_h


def _credit_line(draw: "ImageDraw.ImageDraw", center_x: int, top_y: int, font_px: int, text: str) -> int:
    f = ImageFont.truetype(FONT_REGULAR, font_px)
    bbox = draw.textbbox((0, 0), text, font=f)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((center_x - w // 2, top_y - bbox[1]), text, font=f, fill=DAI)
    return top_y + h


def make_intro() -> Image.Image:
    """intro.png — splash khởi động LibreOffice (~500x360, kích thước điển
    hình LibreOffice dùng cho program/intro.png)."""
    img = _gradient(INTRO_W, INTRO_H).convert("RGBA")
    draw = ImageDraw.Draw(img)
    cx = INTRO_W // 2

    # Biểu tượng sen — cao ~130px, canh giữa phía trên.
    lotus = Image.open(LOTUS).convert("RGBA")
    lotus_h = 130
    lotus_w = round(lotus.width * lotus_h / lotus.height)
    lotus_r = lotus.resize((lotus_w, lotus_h), Image.LANCZOS)
    img.alpha_composite(lotus_r, (cx - lotus_w // 2, 36))

    y = _wordmark(draw, cx, 36 + lotus_h + 18, 46)

    # Gạch nhấn vàng tâm mỏng, ngắn, canh giữa.
    rule_w = 110
    rule_y = y + 14
    draw.line([(cx - rule_w // 2, rule_y), (cx + rule_w // 2, rule_y)], fill=VANG, width=3)

    _credit_line(draw, cx, rule_y + 14, 15, "dựa trên LibreOffice")

    return img.convert("RGB")


def make_about() -> Image.Image:
    """about.png — ảnh nền hộp thoại "About" (~640x400). LibreOffice vẽ chữ
    phiên bản/build ĐÈ LÊN ảnh này ở dải dưới cùng -> cố tình để 1/4 dưới
    trống/nhạt để chữ đè lên vẫn đọc được (không có cách verify chính xác vị
    trí LO đặt chữ build từ sandbox này, xem docs/branding/NAMIOFFICE.md)."""
    img = _gradient(ABOUT_W, ABOUT_H).convert("RGBA")
    draw = ImageDraw.Draw(img)
    cx = ABOUT_W // 2

    lotus = Image.open(LOTUS).convert("RGBA")
    lotus_h = 160
    lotus_w = round(lotus.width * lotus_h / lotus.height)
    lotus_r = lotus.resize((lotus_w, lotus_h), Image.LANCZOS)
    img.alpha_composite(lotus_r, (cx - lotus_w // 2, 40))

    y = _wordmark(draw, cx, 40 + lotus_h + 20, 56)

    rule_w = 130
    rule_y = y + 16
    draw.line([(cx - rule_w // 2, rule_y), (cx + rule_w // 2, rule_y)], fill=VANG, width=3)

    _credit_line(
        draw, cx, rule_y + 16, 16,
        "NaMiOffice — dựa trên LibreOffice (The Document Foundation)",
    )

    # Dải dưới cùng (~25% chiều cao) cố tình để trống/ngà thuần, dành cho
    # LibreOffice đè chữ "Version: ..." / "Build ID: ..." lên.
    return img.convert("RGB")


def _wrap_as_svg(png_path: str, w: int, h: int, svg_path: str) -> None:
    """Bọc 1 ảnh PNG đã sinh vào SVG hợp lệ (thẻ <image> nhúng base64) để có
    file .svg LibreOffice có thể đọc tại program/shell/about.svg. KHÔNG phải
    SVG vector vẽ tay — xem lưu ý ở docstring module + NAMIOFFICE.md."""
    with open(png_path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}">\n'
        "  <!-- NaMiOS — nền hộp thoại About NaMiOffice. Ảnh nhúng base64 sinh "
        "bởi branding/office/make-namioffice-brand.py (bản raster PIL, KHÔNG "
        "phải path vector tay — xem docs/branding/NAMIOFFICE.md). -->\n"
        f'  <image x="0" y="0" width="{w}" height="{h}" '
        f'href="data:image/png;base64,{b64}"/>\n'
        "</svg>\n"
    )
    with open(svg_path, "w", encoding="utf-8") as fh:
        fh.write(svg)


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(CHROOT_DIR, exist_ok=True)

    intro = make_intro()
    intro_path = os.path.join(OUT_DIR, "intro.png")
    intro.save(intro_path, "PNG")
    print(f"wrote {intro_path} ({intro.width}x{intro.height}, {os.path.getsize(intro_path) // 1024} KB)")

    about = make_about()
    about_png_path = os.path.join(OUT_DIR, "about.png")
    about.save(about_png_path, "PNG")
    print(f"wrote {about_png_path} ({about.width}x{about.height}, {os.path.getsize(about_png_path) // 1024} KB)")

    about_svg_path = os.path.join(OUT_DIR, "about.svg")
    _wrap_as_svg(about_png_path, about.width, about.height, about_svg_path)
    print(f"wrote {about_svg_path} ({os.path.getsize(about_svg_path) // 1024} KB)")

    # Copy nguyên văn 3 file sang CHROOT_DIR để hook 0450 chép tiếp vào
    # /usr/lib/libreoffice/... lúc build chroot (máy soạn gói này KHÔNG có
    # LibreOffice cài để ghi thẳng).
    for name in ("intro.png", "about.png", "about.svg"):
        src = os.path.join(OUT_DIR, name)
        dst = os.path.join(CHROOT_DIR, name)
        with open(src, "rb") as fh_in, open(dst, "wb") as fh_out:
            fh_out.write(fh_in.read())
        print(f"copied -> {dst} ({os.path.getsize(dst) // 1024} KB)")


if __name__ == "__main__":
    main()
