# NaMiOffice — bảng tên app (nhãn hiển thị, nền LibreOffice)

**Nguồn chốt tên:** `docs/specs/namioffice-v2/01_PHAM_VI_VA_MA_TRAN.md` §1 (ma trận chức năng).
**Áp dụng bởi:** hook `distro/live-build/config/hooks/normal/0450-namioffice-brand.hook.chroot` (đổi `Name=`/`Name[vi]=`/`GenericName=` trong `.desktop`) + hook `0451-namioffice-icons.hook.chroot` (đổi `Icon=`).
**Trạng thái:** `partial` — rebrand mức hiển thị trên nền LibreOffice chưa patch mã nguồn; `verified_on_host: NO`.

## Bảng đối chiếu

| App Microsoft Office | Nhãn app NaMiOffice | Binary / .desktop LibreOffice | File icon (hicolor, không đổi tên) |
|---|---|---|---|
| Word | **NaMiWriter** | `libreoffice-writer.desktop` (soffice --writer) | `namioffice-writer` |
| Excel | **NaMiSheet** | `libreoffice-calc.desktop` (soffice --calc) | `namioffice-calc` |
| PowerPoint | **NaMiSlides** | `libreoffice-impress.desktop` (soffice --impress) | `namioffice-impress` |
| *(không có tương đương 1-1 — vẽ/sơ đồ)* | **NaMiDraw** | `libreoffice-draw.desktop` (soffice --draw) | `namioffice-draw` |
| Access | **NaMiData** | `libreoffice-base.desktop` (soffice --base) | `namioffice-base` |
| *(không có tương đương 1-1 — soạn công thức)* | **NaMiMath** | `libreoffice-math.desktop` (soffice --math) | `namioffice-math` |
| *(trang chủ bộ Office)* | **NaMiOffice** | `libreoffice-startcenter.desktop` | theme icon mặc định của suite |

Ghi chú đọc bảng:
- Cột "File icon" là **tên file**, không phải nhãn hiển thị — không đổi khi tên hiển thị đổi (vd: `libreoffice-calc.desktop` dùng icon file `namioffice-calc` nhưng hiển thị nhãn **NaMiSheet**). Xem comment "FILE ↔ NHÃN" trong hook `0450` để tránh nhầm khi sửa sau này.
- `libreoffice-xsltfilter.desktop` (bộ lọc XML nội bộ, không phải app người dùng mở trực tiếp) giữ nhãn chung "NaMiOffice – Bộ lọc XSLT", không nằm trong ma trận app ở trên.

## Tên suite

**NaMiOffice** = tên bộ ứng dụng (suite), áp cho màn Start Center + splash + About + tín dụng "dựa trên LibreOffice".

## Tên RESERVED — chưa gán cho bất kỳ app nào

Theo kit §1, các nhãn sau được **giữ riêng (reserved)** cho sản phẩm thật trong tương lai — **KHÔNG** được gắn vào LibreOffice hay bất kỳ ứng dụng nào ở bước rebrand hiển thị này, vì chưa có sản phẩm thật đứng sau tên đó:

| Nhãn reserved | Nhu cầu (kit §1) | Trạng thái |
|---|---|---|
| NaMiMail | Outlook — thư, lịch, danh bạ, tác vụ | **10/11/2026: KHÔNG CÒN reserved** — đã gán cho **Thunderbird** (gói `thunderbird`+`thunderbird-l10n-vi`, `0405-mail-notes.list.chroot`). Tên đầy đủ PHẢI ghi "NaMiMail (dựa trên Mozilla Thunderbird)", KHÔNG gọi tương thích Outlook/Exchange. UI `.desktop` CHƯA đổi tên hiển thị (chỉ mới thêm gói) — xem `docs/office/ECOSYSTEM-MAIL-NOTES-FORMS.md` §1 |
| NaMiNotes | OneNote — sổ ghi chú, mực số | vẫn reserved; chưa có app; KHÔNG ship (đã rà soát trixie/main, không app nào đủ F1 — xem `docs/office/ECOSYSTEM-MAIL-NOTES-FORMS.md` §2) |
| NaMiForms | Forms — thu thập phản hồi, kiểm tra | chưa có app/dịch vụ; KHÔNG ship |
| NaMiData (service) | Dịch vụ dữ liệu/backend riêng cho Access (ngoài LibreOffice Base) | chưa có; nhãn NaMiData hiện CHỈ dùng cho LibreOffice Base (xem bảng trên) |
| NaMiDrive/Collab | Lưu đám mây & cộng tác | chưa có dịch vụ; KHÔNG ship |
| NaMiPDF | PDF — xem, xuất, ký, chú thích | chưa có thành phần riêng; KHÔNG ship |

Khi một trong các sản phẩm trên được dựng thật (có nền triển khai, không chỉ đổi nhãn LibreOffice), tên mới áp dụng cho sản phẩm đó — không tái sử dụng tên "NaMiData" đang gắn cho LibreOffice Base nếu dịch vụ Access thật ra đời khác tên.
