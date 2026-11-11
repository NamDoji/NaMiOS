# NaMiOffice — bảng tên app (nhãn hiển thị, nền LibreOffice)

**Nguồn chốt tên:** `docs/specs/namioffice-v2/01_PHAM_VI_VA_MA_TRAN.md` §1 (ma trận chức năng) — **CẬP NHẬT 11/11/2026 (Cuong):** đổi kiểu đặt tên app sang "n"+chức năng kiểu Windows (xem bảng dưới); dòng đó của spec `01_PHAM_VI_VA_MA_TRAN.md` + `docs/specs/namios-pl20/01_DANH_MUC_VA_THUONG_HIEU.md` §1 chưa đồng bộ lại — ưu tiên bảng ở file này cho 5 app Office.
**Áp dụng bởi:** override tĩnh `distro/live-build/config/includes.chroot/usr/share/applications/libreoffice-{writer,calc,impress,draw,startcenter}.desktop` (copy SAU khi gói cài, là nguồn nhãn chính — ghi đè file gốc của gói) + hook `distro/live-build/config/hooks/normal/0450-namioffice-brand.hook.chroot` (sed `Name=`/`Name[vi]=`/`GenericName=` trên file gói — lớp dự phòng cùng tên, phòng khi thứ tự includes/hooks khác) + hook `0451-namioffice-icons.hook.chroot` (đổi `Icon=`, không đổi theo đợt 11/11 này).
**Trạng thái:** `partial` — rebrand mức hiển thị trên nền LibreOffice chưa patch mã nguồn; `verified_on_host: NO`. Exec=/MimeType= trong 5 file override là **tái lập thận trọng** (xem comment đầu mỗi file `.desktop`), cần đối chiếu `dpkg-deb -c` gói trixie thật trước phát hành.

## Bảng đối chiếu

| App Microsoft Office | Nhãn app (từ 11/11/2026) | Nhãn cũ (trước 11/11/2026) | Binary / .desktop LibreOffice | File icon (hicolor, không đổi tên) |
|---|---|---|---|---|
| Word | **nDoc** (`Name[vi]=`Văn bản) | ~~NaMiWriter~~, ~~nWord~~ | `libreoffice-writer.desktop` (soffice --writer) | `namioffice-writer` |
| Excel | **nSheet** (`Name[vi]=`Bảng tính) | ~~NaMiSheet~~, ~~nExcel~~ | `libreoffice-calc.desktop` (soffice --calc) | `namioffice-calc` |
| PowerPoint | **nSlide** (`Name[vi]=`Trình chiếu) | ~~NaMiSlides~~, ~~nPowerPoint~~ | `libreoffice-impress.desktop` (soffice --impress) | `namioffice-impress` |
| *(không có tương đương 1-1 — vẽ/sơ đồ)* | **nDraw** (`Name[vi]=`Vẽ) | ~~NaMiDraw~~ | `libreoffice-draw.desktop` (soffice --draw) | `namioffice-draw` |
| Access | **nData** (`Name[vi]=`Cơ sở dữ liệu) | ~~NaMiData~~, ~~nAccess~~ (đổi 11/11/2026) | `libreoffice-base.desktop` (soffice --base) | `namioffice-base` |
| *(không có tương đương 1-1 — soạn công thức)* | **nFormula** (`Name[vi]=`Công thức) | ~~NaMiMath~~ | `libreoffice-math.desktop` (soffice --math) | `namioffice-math` |
| *(trang chủ bộ Office)* | **nOffice** (`Name[vi]=`Văn phòng) | ~~NaMiOffice~~ | `libreoffice-startcenter.desktop` | theme icon mặc định upstream (`libreoffice-startcenter`) — chưa có icon NaMiOffice riêng cho màn hình chủ suite |

Ghi chú đọc bảng:
- Cột "File icon" là **tên file**, không phải nhãn hiển thị — không đổi khi tên hiển thị đổi (vd: `libreoffice-calc.desktop` dùng icon file `namioffice-calc` nhưng hiển thị nhãn **nSheet**). Xem comment "FILE ↔ NHÃN" trong hook `0450` để tránh nhầm khi sửa sau này.
- `libreoffice-xsltfilter.desktop` (bộ lọc XML nội bộ, không phải app người dùng mở trực tiếp) giữ nhãn chung "NaMiOffice – Bộ lọc XSLT" (KHÔNG đổi — không phải app người dùng mở, ngoài phạm vi yêu cầu 11/11), không nằm trong ma trận app ở trên.
- **Nhãn hiệu Microsoft — ĐỌC TRƯỚC KHI DÙNG RỘNG RÃI:** tên hiện tại "nDoc"/"nSheet"/"nSlide"/"nDraw"/"nData" là **tên generic** ("n"+từ-chức-năng: Doc/Sheet/Slide/Draw/Data — đều là từ mô tả chung, không phải nhãn hiệu Microsoft). Đây là bản **đổi an toàn** của Cuong 11/11/2026 từ phương án nháp trước đó "nWord/nExcel/nPowerPoint" (vốn cố ý gợi thẳng Word/Excel/PowerPoint → rủi ro nhãn hiệu cao). Nhãn Base cũng đã được đổi từ `nAccess`/NaMiData (gợi Microsoft Access) sang generic **`nData`** (`Name[vi]=`Cơ sở dữ liệu) cùng ngày 11/11/2026 → **KHÔNG còn bất kỳ tên app Office nào gợi nhãn hiệu Microsoft**. Lưu ý rủi ro nhãn hiệu bên-thứ-ba này **khác loại** với mục đích bảng ở `TRADEMARK-LICENSE-COMPLIANCE.md` (tài liệu đó chỉ xử lý nghĩa vụ/quyền đổi tên theo giấy phép TDF khi rời khỏi tên "LibreOffice"). Tên generic đã giảm mạnh rủi ro nhưng **vẫn nên rà soát pháp lý (luật sư SHTT) trước khi phát hành công khai/thương mại** cho toàn bộ nhận diện (gồm cả tên "NaMi") — chưa thực hiện; `verified_on_host: NO` không thay thế được bước này.

## Tên suite

**nOffice** = nhãn **hiển thị** bộ ứng dụng (áp cho màn Start Center + splash + About + tín dụng "dựa trên LibreOffice") kể từ 11/11/2026. **"NaMiOffice"** vẫn là tên **dự án/tài liệu nội bộ** (thư mục `docs/specs/namioffice-v2/`, tiêu đề các file branding này, các bảng compat-matrix) — hai tên này được dùng song song có chủ đích: "NaMiOffice" cho văn bản kỹ thuật nội bộ, "nOffice" cho CHUỖI thật sự hiện trên màn hình người dùng.

## Tên RESERVED — chưa gán cho bất kỳ app nào

Theo kit §1, các nhãn sau được **giữ riêng (reserved)** cho sản phẩm thật trong tương lai — **KHÔNG** được gắn vào LibreOffice hay bất kỳ ứng dụng nào ở bước rebrand hiển thị này, vì chưa có sản phẩm thật đứng sau tên đó:

| Nhãn reserved | Nhu cầu (kit §1) | Trạng thái |
|---|---|---|
| NaMiMail | Outlook — thư, lịch, danh bạ, tác vụ | **10/11/2026: KHÔNG CÒN reserved** — đã gán cho **Thunderbird** (gói `thunderbird`+`thunderbird-l10n-vi`, `0405-mail-notes.list.chroot`). Tên đầy đủ PHẢI ghi "NaMiMail (dựa trên Mozilla Thunderbird)", KHÔNG gọi tương thích Outlook/Exchange. UI `.desktop` CHƯA đổi tên hiển thị (chỉ mới thêm gói) — xem `docs/office/ECOSYSTEM-MAIL-NOTES-FORMS.md` §1 |
| NaMiNotes | OneNote — sổ ghi chú, mực số | vẫn reserved; chưa có app; KHÔNG ship (đã rà soát trixie/main, không app nào đủ F1 — xem `docs/office/ECOSYSTEM-MAIL-NOTES-FORMS.md` §2) |
| NaMiForms | Forms — thu thập phản hồi, kiểm tra | chưa có app/dịch vụ; KHÔNG ship |
| NaMiData (service) | Dịch vụ dữ liệu/backend riêng cho Access (ngoài LibreOffice Base) | chưa có; LibreOffice Base nay dùng nhãn **nData** (đổi 11/11/2026) nên tên "NaMiData" hiện CHƯA gắn cho app/dịch vụ nào |
| NaMiDrive/Collab | Lưu đám mây & cộng tác | chưa có dịch vụ; KHÔNG ship |
| NaMiPDF | PDF — xem, xuất, ký, chú thích | chưa có thành phần riêng; KHÔNG ship |

Khi một trong các sản phẩm trên được dựng thật (có nền triển khai, không chỉ đổi nhãn LibreOffice), tên mới áp dụng cho sản phẩm đó. Tên "NaMiData" để riêng (reserved) cho dịch vụ dữ liệu tương lai — từ 11/11/2026 KHÔNG còn gắn cho LibreOffice Base (Base nay là **nData**); nếu dịch vụ Access thật ra đời khác tên thì cũng không tái sử dụng tên "NaMiData" một cách gây nhầm.
