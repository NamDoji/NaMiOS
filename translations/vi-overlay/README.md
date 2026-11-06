# NaMiOS — Lớp phủ dịch tiếng Việt (vi_NM overlay)

Thư mục này là **nguồn** của lớp phủ dịch tiếng Việt do NaMiOS kiểm soát, dùng để
**ghi đè + lấp** những chuỗi mà bản dịch tiếng Việt upstream (đi kèm gói KDE/Debian)
còn thiếu (đang rơi về tiếng Anh). Cơ chế đầy đủ: [`docs/l10n/UPSTREAM-VI-OVERLAY-SPEC.md`](../../docs/l10n/UPSTREAM-VI-OVERLAY-SPEC.md) §4.1.

## Cách hoạt động (tóm tắt)

- Mỗi domain gettext một file `po/<domain>.vi_NM.po` — **tên file (bỏ `.vi_NM.po`)
  PHẢI = đúng textdomain của app** (vd `plasmanetworkmanagement.vi_NM.po`), nếu
  không `.mo` sẽ không được nạp.
- `scripts/build-l10n-overlay.sh` biên dịch `.po → .mo` vào
  `distro/live-build/config/includes.chroot/usr/share/locale/vi_NM/LC_MESSAGES/`
  (đường dẫn MỚI, không gói Debian nào sở hữu → không xung đột). `.mo` là sản phẩm
  build, **không commit** (đã `.gitignore`); CI/host sinh lại từ `.po`.
- `LANGUAGE=vi_NM:vi:en_US` (hook `0100-locale-vi` + `plasma-localerc`) → gettext +
  ki18n fallback **theo từng chuỗi**: `vi_NM` (NaMiOS) thắng → `vi` upstream → `en`.

## Quy tắc chất lượng (bắt buộc)

1. msgid **byte-exact** với chuỗi gốc upstream — lấy từ catalog KDE thật, KHÔNG bịa
   msgid (bịa thì `.mo` biên dịch ra vẫn không khớp lúc chạy → vô dụng).
2. Giữ nguyên `msgctxt`; header `Plural-Forms: nplurals=1; plural=0;` (tiếng Việt).
3. Thuật ngữ theo [`GLOSSARY-and-batch1.md`](GLOSSARY-and-batch1.md) — nhất quán,
   tiếng Việt kỹ thuật phổ thông, không lai căng.
4. Dịch xong chạy `msgfmt -c` để chắc chắn biên dịch được.

## Đo độ phủ (trung thực)

`python3 scripts/l10n-coverage.py --root / --baseline translations/vi-overlay/coverage-baseline.json`
→ bảng `vi upstream | +lớp phủ | hiệu dụng | tổng | %`. Chỉ báo số **đo được**;
chỗ còn tiếng Anh là giới hạn thật của hệ sinh thái dịch — không tô hồng "100%".
