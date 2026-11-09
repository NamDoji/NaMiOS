#!/usr/bin/env python3
"""Đóng gói 20 hình nền Việt Nam (bộ Brand UI/UX v1 do Cuong gửi) thành các gói
wallpaper KDE Plasma 6 trong lõi NaMiOS, để hiện trong phần Chọn hình nền
(System Settings) cho người dùng Việt chọn.

Nguồn ảnh 4K (3840x2160, JPG) truyền qua biến SRC_DIR (mặc định thư mục giải
nén tạm). Mỗi ảnh -> /usr/share/wallpapers/NaMiOS-<NN>-<AsciiName>/ gồm:
  - metadata.json  (KPlugin: Id, Name tiếng Việt, License, Authors)
  - contents/images/3840x2160.jpg
  - contents/screenshot.png  (thu nhỏ ~400x225 cho ô xem trước)

TRUNG THỰC: bộ ảnh là "ảnh minh hoạ TẠO BẰNG AI, bản 4K nội suy từ 1672x941"
(theo contact sheet của bộ) — ghi rõ trong License, không nói là ảnh chụp thật.

Chạy: SRC_DIR=/tmp/brandux/NaMiOS_Brand_UIUX_v1/01_Wallpapers_3840x2160 \
      python3 branding/wallpaper/install-vn-wallpapers.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.environ.get(
    "SRC_DIR", "/tmp/brandux/NaMiOS_Brand_UIUX_v1/01_Wallpapers_3840x2160"
)
DEST_ROOT = os.path.join(
    ROOT, "distro/live-build/config/includes.chroot/usr/share/wallpapers"
)
LICENSE = "Tài sản thương hiệu NaMiOS — ảnh minh hoạ tạo bằng AI (chưa tuyên bố nhãn hiệu đã đăng ký)."

# Tên hiển thị tiếng Việt theo số thứ tự file (01..20).
VI_NAMES = {
    1: "Sen Việt", 2: "Vịnh Hạ Long", 3: "Biển Đà Nẵng", 4: "Vịnh Nha Trang",
    5: "Biển Phú Quốc", 6: "Biển Côn Đảo", 7: "Tràng An", 8: "Hội An",
    9: "Cố Đô Huế", 10: "Ruộng Bậc Thang Sa Pa", 11: "Cao Nguyên Hà Giang",
    12: "Thác Bản Giốc", 13: "Phong Nha", 14: "Đà Lạt", 15: "Miền Tây Sông Nước",
    16: "Cao Nguyên Cà Phê", 17: "Hoa Văn Trống Đồng Sơn", 18: "Tháp Mỹ Sơn",
    19: "Hồ Gươm", 20: "Biển Đảo Việt Nam",
}

NUM_RE = re.compile(r"^(\d{2})_(.+)\.jpe?g$", re.IGNORECASE)


def main() -> None:
    if not os.path.isdir(SRC_DIR):
        raise SystemExit(f"SRC_DIR không tồn tại: {SRC_DIR}")
    files = sorted(f for f in os.listdir(SRC_DIR) if f.lower().endswith((".jpg", ".jpeg")))
    n = 0
    for fname in files:
        m = NUM_RE.match(fname)
        if not m:
            print(f"bỏ qua (tên không theo NN_Ten): {fname}")
            continue
        num = int(m.group(1))
        ascii_name = m.group(2)  # vd Sen_Viet
        vi_name = VI_NAMES.get(num, ascii_name.replace("_", " "))
        pkg_id = f"NaMiOS-{num:02d}-{ascii_name.replace('_', '-')}"
        pkg_dir = os.path.join(DEST_ROOT, pkg_id)
        img_dir = os.path.join(pkg_dir, "contents", "images")
        os.makedirs(img_dir, exist_ok=True)

        src_path = os.path.join(SRC_DIR, fname)
        im = Image.open(src_path)
        w, h = im.size
        # Ảnh gốc (giữ nguyên JPG 4K) -> contents/images/<WxH>.jpg
        shutil.copyfile(src_path, os.path.join(img_dir, f"{w}x{h}.jpg"))

        # Ảnh xem trước thu nhỏ.
        thumb = im.convert("RGB").resize((400, round(400 * h / w)), Image.LANCZOS)
        thumb.save(os.path.join(pkg_dir, "contents", "screenshot.png"), "PNG")

        meta = {
            "KPlugin": {
                "Authors": [{"Name": "NaMiOS"}],
                "Id": pkg_id,
                "License": LICENSE,
                "Name": vi_name,
            }
        }
        with open(os.path.join(pkg_dir, "metadata.json"), "w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=2)
        n += 1
        print(f"[{num:02d}] {vi_name}  ->  {pkg_id}/ ({w}x{h})")

    print(f"\nĐóng gói {n} hình nền Việt Nam vào {DEST_ROOT}")


if __name__ == "__main__":
    main()
