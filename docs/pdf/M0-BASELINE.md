# NaMiPDF — Báo cáo M0 (baseline)

**Ngày:** 10/11/2026 · **Loại:** báo cáo mốc **M0 khảo sát** (kit `04 §3`: *"M0 khảo sát: chọn engine/license, chạy renderer trên corpus, thiết kế UI, nguồn model OCR tiếng Việt"*). · **Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam.

> **M0 KHÔNG code tính năng.** Đây là bước **chọn stack + audit license + kiểm kê hiện trạng + lập ma trận**. Mọi phát biểu "có/chưa có" dưới đây là **đánh giá hiện trạng**, không phải tuyên bố đã hoàn tất. Theo kit (`README §19`): *"'Đạt' phải có tệp thử, kết quả mở/lưu lại và bằng chứng."* **KHÔNG** dấu nào ở đây được coi là "chạy đầy đủ như Acrobat"; đó là điều kiện cấm của kit (`05 §Đầu ra`).

---

## 1. ISO hiện CÓ gì cho PDF (kiểm kê trung thực)

| Hạng mục | Hiện trạng | Nguồn khai báo |
|---|---|---|
| **Okular** (viewer/annotation/AcroForm/print, nền Poppler) | **ĐÃ ship** | `distro/live-build/config/package-lists/0100-desktop-kde.list.chroot` (dòng `okular`) |
| In CUPS/IPP + print-manager | Đã ship | `0500-print.list.chroot` (`cups`, `cups-filters`, `print-manager`, `printer-driver-all`) |
| Scan SANE/eSCL (eScan) | Đã ship | `0500-print.list.chroot` (`sane-airscan`, `sane-utils`, `skanlite`, `ipp-usb`) |
| LibreOffice (xuất PDF, Draw) | Đã ship | `0400-office-browser.list.chroot` (`libreoffice`) |
| MIME `pdf → Okular` | Đã khai | `includes.chroot/etc/skel/.config/mimeapps.list` |
| **poppler-utils, qpdf, tesseract-ocr(+vie), ocrmypdf, img2pdf** | **ĐÃ** thêm (phần việc packaging song song) | `0420-pdf.list.chroot` — versions đã xác minh madison (poppler-utils 25.03.0, qpdf 12.2.0, tesseract 5.5.0, ocrmypdf 16.7.0, img2pdf 0.6.1); xem `docs/pdf/NAMIPDF-PACKAGING.md` |
| **pikepdf, veraPDF** | **CHƯA** — bổ sung ở M1/M3 | thêm vào `0420-pdf.list.chroot` (python3-pikepdf); veraPDF cần Java/Update Center |
| App "NaMiPDF" riêng (4 chế độ + workflow) | **CHƯA** tồn tại | — |

**Trạng thái build cho mọi tên gói:** `verified_on_host: NO` — phải `apt-cache show` trên snapshot trixie trước `lb build`; tên sai → `lb build` báo "unable to locate package", sửa tên rồi build lại.

---

## 2. Stack đã chọn (ADR-0001 NaMiPDF)

```
Okular (view · annotate · AcroForm fill · print · hiển thị chữ ký)      GPL-2.0+
  ├─ Poppler / poppler-utils  → render, extract, pdftoppm/pdftotext/… GPL-2.0+
  ├─ qpdf + pikepdf           → merge/split/rotate/reorder/crop/       Apache-2.0 / MPL-2.0
  │                             encrypt/linearize (lossless)
  ├─ tesseract-ocr-vie + ocrmypdf → OCR vi offline → searchable PDF    Apache-2.0 / MPL-2.0
  │                                (+ Ghostscript — ⚠ AGPL-3.0)
  ├─ img2pdf                  → ảnh → PDF lossless                     LGPL-3.0+
  └─ veraPDF                  → GATE kiểm PDF/A & PDF/UA (nhãn khi PASS) MPL-2.0 / GPL-3.0+
```

Triết lý = **tái dùng Okular + adapter đã kiểm license** (giống NaMiMail tái dùng Thunderbird), KHÔNG viết mới PDF app. Chi tiết benchmark ≥2 stack/concern + audit SPDX đầy đủ: `docs/pdf/ADR-0001-namipdf-engine.md`. Bằng chứng license đã xác minh từ nguồn gốc: qpdf=Apache-2.0, pikepdf=MPL-2.0, ocrmypdf=MPL-2.0 (cần Ghostscript+Tesseract), veraPDF=dual MPL/GPL, pyHanko=MIT.

**Cờ AGPL (phải ghi SBOM):** Ghostscript (dep OCR/PDF-A) và MuPDF (nếu dùng cho redaction/edit) là **AGPL-3.0**. Với app **desktop offline**, nghĩa vụ = ship source + notices (apt thoả); **điều khoản mạng chỉ kích hoạt nếu đưa lên dịch vụ mạng** → **cấm** dựng PDF-service hosted proprietary trên chúng.

---

## 3. Mốc P-level (go/no-go, mỗi mốc phải có build + test + fixture + bug + quyết định)

Theo kit `04 §3` + `05 §Mở rộng`. Không dự đoán ngày phát hành khi chưa có repo/nhân lực.

- **M1 — Viewer P0 (có thể phát hành trước).** Đọc/search (có+không dấu)/copy vi, **annotation** lưu vào PDF, **sắp xếp trang** (qpdf/pikepdf), **in** CUPS, **atomic save** + sandbox worker không mạng, cảnh báo tài liệu ký/khóa, không ghi đè bản gốc. Pipeline gói đã có qua `0420-pdf.list.chroot` (bổ sung `python3-pikepdf`). *(Phủ chủ yếu dòng C0/C1 của ma trận.)*
- **M2 — Chuyên nghiệp.** **Sửa text/image có kiểm** (Document Inspector + overlay "thêm nội dung" trung thực; object-edit vẫn C3), **OCR vi-VN** (ocrmypdf), **AcroForm** điền/flatten, **conversion** (ảnh↔PDF, PDF→ảnh/text/HTML/ODT). Batch P1.
- **M3 — Tin cậy (bật theo feature-flag SAU chứng nhận).** **PAdES** ký thật (pyHanko + token + test vector + viewer độc lập), **PDF/A** (gate veraPDF), **PDF/UA** tagged, **redaction** chứng minh xóa độc lập. **Không bật nút** khi chưa pass test độc lập.
- **M4 — Doanh nghiệp.** Batch/admin policy, token/vendor integration, quản trị nhiều máy.

**Vertical slice ưu tiên (kit `05 §Vertical slice`):** mở PDF đa trang trong worker sandbox → tìm/copy tiếng Việt → thêm chú thích → sắp xếp trang → **lưu bản sao atomically** → mở lại ở NaMiPDF **và** viewer độc lập → in 1 trang qua CUPS; có cảnh báo khi tài liệu ký/khóa, không ghi đè bản gốc.

---

## 4. Tuyên bố trung thực (bắt buộc)

**Không dấu nào trong ma trận được coi là "hoàn tất".** Điều kiện tối thiểu để một dòng chuyển "Đã hỗ trợ":

1. **Pass fixture `PDF-01..13`** trên **máy thật** (chưa chạy được trong môi trường này) + mở lại ở **viewer độc lập** — không phải từ mockup.
2. **Pilot corpus có quyền** (kit `04 §1`: 100 text / 50 scan vi / 30 form / 30 ký số / 20 PDF-A·UA / 20 mã hóa / 20 lỗi-fuzz / 20 file lớn), ẩn danh, không đưa hồ sơ thật lên repo/cloud AI.
3. Vượt **gate tuyệt đối** (kit `04 §3`): không mất dữ liệu không cảnh báo; **redaction** chứng minh text/object/ảnh/OCR/metadata/old-revision không khôi phục; **chữ ký** phân biệt 5 trạng thái, không báo xanh sai; không JS/attachment tự chạy; không ghi đè bản gốc.

**Nghiệm thu thật = PDF-01..13 fixtures + pilot**, KHÔNG phải "đánh dấu done-like-Acrobat từ mockup."

Mức C trong ma trận = **đánh giá kỹ thuật** theo hành vi đã biết của stack, là **điểm khởi đầu** viết fixture & test — **không** phải kết quả đo. Con số (C0=7, C1=22, C2=28, C3=9 / tổng 66) = **số dòng yêu cầu**, không phải tính năng đã đạt.

---

## 5. Deliverable M0

| File | Nội dung |
|---|---|
| `docs/pdf/ADR-0001-namipdf-engine.md` | ADR chọn engine/stack: benchmark ≥2 FOSS/concern + audit SPDX + quyết định + giới hạn C3 edit/sign/redact |
| `docs/pdf/COMPAT-MATRIX.md` | Ma trận **66 dòng** (12 nhóm) × (ID/Mode/P/Expected/Available-now-via/Gap/C/Fixture/Severity/Notes) + tổng hợp |
| `docs/pdf/M0-BASELINE.md` | Báo cáo này |

**Blocker đã biết (ghi rõ, tiếp tục phần độc lập):** không chạy được fixture trên máy/phần cứng thật trong môi trường này; thiếu **hardware token** cho PAdES; **veraPDF** cần Java (xác nhận đóng gói trixie); chưa có **corpus pilot có quyền**. Các phần khảo sát/ADR/ma trận độc lập đã hoàn thành.
