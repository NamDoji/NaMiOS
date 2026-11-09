# NaMiOffice — Ma trận tương thích (COMPAT-MATRIX) · M0 baseline

**Ngày:** 10/11/2026 · **Mốc:** M0 (baseline — PHÂN TÍCH, không phải tuyên bố tính năng đã hoàn tất).
**Bản LibreOffice được pin:** **25.2.3** — Debian 13 trixie, gói `libreoffice` = `4:25.2.3-2+deb13u8`
(nguồn: `distro/live-build/config/package-lists/0400-office-browser.list.chroot`).
**Tài liệu đầu vào:** `docs/specs/namioffice-v2/` (01→05).
**Bản máy-đọc song song:** `docs/office/feature-registry.json` (mỗi dòng dưới = một phần tử `rows[]`).

> **Cảnh báo trung thực — đọc trước.** Mức C ở bảng này được **ĐÁNH GIÁ từ hành vi
> đã biết của LibreOffice 25.2**, **CHƯA** có dòng nào được xác minh bằng
> **round-trip test đối chiếu Microsoft Office có giấy phép** hay **pilot người
> dùng thật** trong môi trường này. Theo chính tài liệu kit (`01_PHAM_VI §3`):
> *"Một tính năng chỉ được đánh dấu 'Đã hỗ trợ' khi có unit/integration,
> round-trip và thử tương tác; **'Có nút menu' chưa đủ**."* Vì vậy ngay cả các
> dòng **C0** ở đây phải hiểu là *"LO round-trip tốt theo hiểu biết, chờ xác
> nhận bằng tệp thật"*, không phải chứng nhận.

---

## Chú giải (legend)

### Mức tính năng (F) — theo kit
- **F0** — dùng thường ngày, bắt buộc cho bản đầu.
- **F1** — chuyên nghiệp, sau pilot.
- **F2** — nâng cao, phụ thuộc dữ liệu & nguồn lực.

### Mức tương thích (C) — theo kit (gán theo **tệp/phiên bản/tính năng**, không theo tên app)
- **C0** — kết quả và **round-trip xác minh**. *(Ở đây: LO round-trip thật; còn chờ đối chiếu Office có giấy phép.)*
- **C1** — đáp ứng chức năng, **sai khác được giới hạn**.
- **C2** — **một phần, có cảnh báo** / mất một phần khi round-trip.
- **C3** — **không thực hiện được bằng fork LibreOffice**, có fallback; cần **Windows / Microsoft 365** hoặc **engine/sản phẩm riêng**.

> Theo chỉ thị dự án: **VBA đầy đủ, COM/VSTO/ActiveX, Office.js, Power Query,
> Power Pivot/DAX, Exchange/M365, đồng tác giả thời gian thực, IRM** → **C3**
> (không khả thi bằng bản fork; cần Windows/M365 hoặc engine riêng).

### Mức nghiêm trọng (Severity)
- **P0** — **cổng tuyệt đối** (kit §04.3): mất dữ liệu không cảnh báo / sai tổng kiểm soát kế toán / phá chữ ký / tự chạy macro / mở kết nối ngoài ngoài ý muốn.
- **P1** — tác vụ F0 hằng ngày. · **P2** — tác vụ chuyên nghiệp F1. · **P3** — nâng cao/ít dùng F2.

### Cột "Fixture"
Tên **tệp kiểm thử CẦN CÓ** (chưa tạo ở M0). Đây là *yêu cầu phát triển*, không phải bằng chứng đã test.

---

## Bảng tổng hợp

### Đếm theo mức C (tổng **119** dòng yêu cầu)

| Mức C | Số dòng | Ý nghĩa |
|---|---|---|
| **C0** | **17** | Round-trip tốt (chờ xác nhận Office thật) |
| **C1** | **46** | Đạt chức năng, sai khác giới hạn *(10/11/2026: +2 — ML-01/ML-02 chuyển từ C3 sau khi đóng gói Thunderbird)* |
| **C2** | **30** | Một phần, cần cảnh báo/patch |
| **C3** | **26** | Không khả thi bằng fork — cần Windows/M365/engine/sản phẩm riêng |
| **Tổng** | **119** | |

### Đếm theo ứng dụng × mức C

| Nhóm | C0 | C1 | C2 | C3 | Tổng |
|---|---|---|---|---|---|
| NaMiWriter (Writer) | 6 | 16 | 6 | 1 | 29 |
| NaMiSheet (Calc) | 11 | 15 | 8 | 9 | 43 |
| NaMiSlides (Impress) | 0 | 10 | 5 | 3 | 18 |
| Interop (xuyên app) | 0 | 3 | 2 | 0 | 5 |
| NaMiMail | 0 | 2 | 0 | 1 | 3 |
| NaMiNotes | 0 | 0 | 0 | 3 | 3 |
| NaMiForms | 0 | 0 | 0 | 2 | 2 |
| NaMiData (Base) | 0 | 0 | 2 | 1 | 3 |
| NaMiCollab | 0 | 0 | 1 | 4 | 5 |
| Add-in/Macro/Automation | 0 | 0 | 3 | 2 | 5 |
| SmartAI-in-Office | 0 | 0 | 2 | 0 | 2 |
| Hạ tầng xuyên suốt | 0 | 0 | 1 | 0 | 1 |
| **Tổng** | **17** | **46** | **30** | **26** | **119** |

### Đếm theo severity & F-level

| Severity | Số dòng | | F-level | Số dòng |
|---|---|---|---|---|
| P0 | 8 | | F0 | 41 |
| P1 | 37 | | F1 | 47 |
| P2 | 42 | | F2 | 31 |
| P3 | 32 | | | |

### 8 dòng P0 (cổng tuyệt đối — phải cảnh báo/giữ dữ liệu, KHÔNG được âm thầm)

| ID | Tác vụ | Vì sao P0 |
|---|---|---|
| `WR-F2-06` | Giữ chữ ký số hợp đồng | Sửa tệp đã ký → chữ ký mất hiệu lực; không tự chạm metadata, yêu cầu ký lại |
| `SH-F0-20` | Tách công thức/cached, locale, hệ ngày | Sai số/ngày/làm tròn = sai sổ kế toán |
| `SH-F2-03` | Chặn truy vấn mạng khi mở | Không mở kết nối ngoài ngoài ý muốn |
| `SH-F0-21` | Kiểm soát kế toán trước/sau mở-lưu | Không sai tổng kiểm soát fixture kế toán |
| `IX-03` | Dán liên kết dữ liệu | Không tự truy cập path mạng/cloud |
| `IX-05` | Đính kèm mail mở sandbox | 0 thực thi macro tự động |
| `AI-02` | An toàn SmartAI (prompt-injection) | Prompt trong tệp không điều khiển được AI đọc tệp khác/gửi mạng |
| `PIPE-01` | Fidelity pipeline / Compatibility Inspector | Trụ của mọi gate "không mất dữ liệu không cảnh báo" |

---

## Ma trận chi tiết

> Mỗi dòng dưới đây tương ứng 1 phần tử trong `docs/office/feature-registry.json`.

### NaMiWriter — Soạn thảo (Writer)

| ID | App | Tác vụ | F | Hành vi kỳ vọng | Hiện trạng LO 25.2 | Cần viết thêm | C | Fixture | Sev | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|
| `WR-F0-01` | NaMiWriter | Style đoạn/ký tự, font, màu chữ | F0 | Áp style đoạn & ký tự, đổi font/màu, giữ khi lưu DOCX | Writer hỗ trợ đầy đủ paragraph/character styles; round-trip DOCX tốt cho style cơ bản | Không cần viết thêm (polish UX tiếng Việt) | **C0** | `writer/f0_styles_vi.docx` | P1 | Tên style ánh xạ Word<->Writer có thể khác chuỗi hiển thị |
| `WR-F0-02` | NaMiWriter | Căn lề, tab, thụt đầu dòng, danh sách đa cấp | F0 | Căn lề/tab/indent/list nhiều cấp giữ nguyên qua DOCX | Hỗ trợ đầy đủ; danh sách đa cấp round-trip tốt, đôi khi lệch numbering restart | Patch nhỏ nếu phát hiện lệch numbering | **C1** | `writer/f0_multilevel_list.docx` | P1 | List numbering/restart là điểm lệch DOCX hay gặp |
| `WR-F0-03` | NaMiWriter | Dán không định dạng (Paste Special) | F0 | Dán văn bản thuần, giữ phím tắt quen | Paste Special có sẵn (Ctrl+Shift+V) | UX/phím tắt tiếng Việt | **C0** | `writer/f0_paste_special.docx` | P1 |  |
| `WR-F0-04` | NaMiWriter | Tìm/thay thế (regex), navigation theo heading | F0 | Find&Replace có regex; Navigator nhảy theo heading | Find&Replace + 'Other options' regex; Navigator theo heading đầy đủ | Không cần viết thêm | **C0** | `writer/f0_find_replace.docx` | P1 |  |
| `WR-F0-05` | NaMiWriter | Đếm từ | F0 | Đếm từ/ký tự, hiện ở status bar | Tools > Word Count + status bar có sẵn | Không cần viết thêm | **C0** | `writer/f0_wordcount.docx` | P2 |  |
| `WR-F0-06` | NaMiWriter | Unicode không mất dấu tiếng Việt | F0 | Gõ Telex/VNI, dấu tổ hợp, không mất dấu khi lưu/mở | Unicode đầy đủ; phụ thuộc font có glyph tiếng Việt | Kiểm font hợp pháp có đủ dấu (F0 gate UX) | **C0** | `writer/f0_unicode_vi.docx` | P1 | Bộ gõ là tầng NaMiOS, không phải Writer |
| `WR-F0-07` | NaMiWriter | A4/A3, lề, cột, section/page break, header/footer, số trang | F0 | Dàn trang & header/footer theo section round-trip DOCX | Hỗ trợ; header/footer 'link-to-previous' và một số section property lệch nhẹ | Patch fidelity header/footer theo section | **C1** | `writer/f0_page_sections.docx` | P1 | Section/odd-even header là điểm lệch DOCX quen thuộc |
| `WR-F0-08` | NaMiWriter | Xem trước, vùng in, PDF có bookmark & liên kết | F0 | In đúng; PDF có bookmark theo heading + hyperlink giữ | Export PDF có bookmark/hyperlink; preview có sẵn | Không cần viết thêm (polish mẫu) | **C1** | `writer/f0_pdf_bookmarks.docx` | P1 |  |
| `WR-F0-09` | NaMiWriter | 10 mẫu hành chính in A4 không cắt chữ | F0 | 10 template VN in ra không tràn/cắt chữ ở font mặc định | Writer in tốt; rủi ro font drift khi thiếu font Microsoft | Dựng 10 mẫu + font hợp pháp + fixture in | **C1** | `writer/f0_templates_10x.docx` | P1 | Font drift (Calibri/Cambria) là nguồn cắt chữ chính |
| `WR-F0-10` | NaMiWriter | Bảng: chèn/gộp/tách ô, lặp dòng tiêu đề, độ rộng, border/shading | F0 | Thao tác bảng + lặp header qua trang, round-trip DOCX | Hỗ trợ; nested table & một số border style lệch khi round-trip | Patch fidelity bảng phức tạp | **C1** | `writer/f0_tables.docx` | P1 |  |
| `WR-F0-11` | NaMiWriter | Ảnh crop/alt text, caption; DOCX không rớt đối tượng | F0 | Ảnh + alt text + caption giữ nguyên, không mất đối tượng neo | Hỗ trợ; anchor/wrap đôi khi dời vị trí khi round-trip | Patch fidelity anchor ảnh | **C1** | `writer/f0_images_alt.docx` | P1 |  |
| `WR-F1-01` | NaMiWriter | Comments (ghi chú) | F1 | Thêm/sửa/xóa comment, hiện tên tác giả, round-trip DOCX | Comments đầy đủ, round-trip tốt | Không cần viết thêm | **C1** | `writer/f1_comments.docx` | P2 |  |
| `WR-F1-02` | NaMiWriter | Track changes nhiều tác giả, accept/reject theo vùng | F1 | Theo dõi thay đổi nhiều tác giả, accept/reject chọn vùng | Track changes mạnh; round-trip DOCX tốt; màu/tên tác giả ổn | Patch nhỏ accept-by-region | **C1** | `writer/f1_trackchanges_multi.docx` | P2 |  |
| `WR-F1-03` | NaMiWriter | Compare/merge hai bản | F1 | So sánh & trộn hai phiên bản tài liệu | Edit > Track Changes > Compare/Merge có sẵn | Kiểm fidelity merge phức tạp | **C1** | `writer/f1_compare_merge.docx` | P2 |  |
| `WR-F1-04` | NaMiWriter | Tìm sửa đồng loạt | F1 | Replace all + regex nhiều vùng | Hỗ trợ đầy đủ | Không cần viết thêm | **C0** | `writer/f1_massreplace.docx` | P2 |  |
| `WR-F1-05` | NaMiWriter | Version history & conflict resolution | F1 | Lịch sử phiên bản + giải quyết xung đột nhiều tác giả | ODF có Versions nội bộ; DOCX không mang version; conflict resolution yếu | Cần lớp lịch sử/khóa file (phần Collab giai đoạn 1) | **C2** | `writer/f1_versions.odt` | P2 | DOCX không có version store như ODF |
| `WR-F1-06` | NaMiWriter | TOC, foot/endnote, cross-reference | F1 | Mục lục tự động, chú thích, tham chiếu chéo cập nhật | Hỗ trợ đầy đủ; round-trip DOCX tốt | Không cần viết thêm | **C1** | `writer/f1_toc_notes_xref.docx` | P2 |  |
| `WR-F1-07` | NaMiWriter | Bibliography/citation, index | F1 | Thư mục tham khảo + chỉ mục; tương thích Zotero | Bibliography DB nội bộ; Zotero qua extension; định dạng citation khác Word | Patch/extension citation style | **C1** | `writer/f1_biblio_index.docx` | P2 |  |
| `WR-F1-08` | NaMiWriter | Equations MathML/OMML | F1 | Công thức toán round-trip với Word (OMML) | Math đọc/ghi OMML cơ bản; công thức phức tạp lệch hoặc thành ảnh | Patch fidelity OMML | **C2** | `writer/f1_equations_omml.docx` | P2 | OMML<->StarMath không 1:1 |
| `WR-F1-09` | NaMiWriter | Fields | F1 | Field (ngày, số trang, doc property, if-field) cập nhật | Hỗ trợ nhiều field; một vài Word field (ví dụ phức tạp) không map | Patch field map DOCX | **C1** | `writer/f1_fields.docx` | P2 |  |
| `WR-F1-10` | NaMiWriter | Mail merge | F1 | Trộn thư từ nguồn CSV/ODB/XLSX, xuất tài liệu/PDF/email | Mail Merge Wizard đầy đủ | Polish UX + nguồn dữ liệu VN | **C1** | `writer/f1_mailmerge.odt` | P2 |  |
| `WR-F1-11` | NaMiWriter | Templates và styles | F1 | Quản lý mẫu & style set doanh nghiệp | Template manager + styles đầy đủ | Dựng bộ mẫu VN + công bố nguồn/giấy phép | **C1** | `writer/f1_templates.ott` | P2 |  |
| `WR-F1-12` | NaMiWriter | Content controls/checkbox/date/dropdown, khóa vùng, field mapping/export | F1 | Biểu mẫu tương tác round-trip DOCX, khóa vùng, map field | Content control (7.4+ đến 25.2) hỗ trợ rich-text/checkbox/dropdown/date/combo/picture; khóa vùng & một số control degrade khi round-trip | Patch content-control fidelity + fallback chỉ-xem khi mất tương tác | **C2** | `writer/f1_content_controls.docx` | P2 | Kit: khi không giữ tương tác -> chuyển chỉ xem/cảnh báo |
| `WR-F2-01` | NaMiWriter | Drawing groups | F2 | Nhóm hình vẽ giữ cấu trúc nhóm | Hỗ trợ group/ungroup; round-trip DOCX khá | Patch nhỏ | **C1** | `writer/f2_drawing_groups.docx` | P3 |  |
| `WR-F2-02` | NaMiWriter | SmartArt | F2 | Sửa SmartArt như đồ họa động của Office | Import thành ảnh/metafile tĩnh hoặc nhóm hình; KHÔNG sửa như SmartArt | Không khả thi 1:1; giữ preview + cấm Save phá cấu trúc | **C3** | `writer/f2_smartart.docx` | P3 | dgm: XML của Microsoft |
| `WR-F2-03` | NaMiWriter | OLE nhúng | F2 | Đối tượng OLE (Excel/biểu đồ nhúng) sửa & giữ | Mở được; mất một phần khi round-trip; sửa OLE Office hạn chế | Patch + fallback preview | **C2** | `writer/f2_ole_embed.docx` | P3 |  |
| `WR-F2-04` | NaMiWriter | Advanced typography | F2 | Ligature/kerning/opentype features | Hỗ trợ OpenType features khá tốt | Không cần viết thêm | **C1** | `writer/f2_typography.docx` | P3 |  |
| `WR-F2-05` | NaMiWriter | Embedded media, publisher layout | F2 | Media nhúng + dàn trang kiểu publisher | Media nhúng hạn chế; dàn trang phức tạp dùng Draw | Fallback + cảnh báo | **C2** | `writer/f2_media_layout.docx` | P3 |  |
| `WR-F2-06` | NaMiWriter | Giữ chữ ký số / metadata hợp đồng | F2 | Không tự sửa metadata/gỡ chữ ký; sau sửa yêu cầu ký lại | Hỗ trợ chữ ký số ODF/PDF; sửa tài liệu làm chữ ký mất hiệu lực (đúng chuẩn) | Cần UX cảnh báo 'ký lại' + không tự chạm metadata (Save-Safety) | **C2** | `writer/f2_signed_contract.docx` | P0 | Gate P0: tệp được ký không giữ nhãn hợp lệ sau chỉnh sửa |

### NaMiSheet — Bảng tính (Calc)

| ID | App | Tác vụ | F | Hành vi kỳ vọng | Hiện trạng LO 25.2 | Cần viết thêm | C | Fixture | Sev | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|
| `SH-F0-01` | NaMiSheet | Nhập/sửa/paste theo vùng | F0 | Paste vùng, giữ giá trị/kiểu | Hỗ trợ đầy đủ | Không cần viết thêm | **C0** | `sheet/f0_paste_range.xlsx` | P1 |  |
| `SH-F0-02` | NaMiSheet | Autofill | F0 | Kéo chuỗi số/ngày/list | Fill series đầy đủ | Không cần viết thêm | **C0** | `sheet/f0_autofill.xlsx` | P1 |  |
| `SH-F0-03` | NaMiSheet | Flash Fill tương đương | F0 | Tự suy mẫu tách/ghép chuỗi như Flash Fill | Calc KHÔNG có Flash Fill; chỉ Text-to-Columns + công thức | Cần viết tính năng suy mẫu (engine mới) hoặc tuyến thay thế | **C3** | `sheet/f0_flashfill.xlsx` | P2 | Kit: 'nếu làm được' — hiện chưa có |
| `SH-F0-04` | NaMiSheet | Sort/filter multi-column | F0 | Sắp xếp & lọc nhiều cột, AutoFilter | Hỗ trợ đầy đủ; AutoFilter round-trip tốt | Không cần viết thêm | **C1** | `sheet/f0_sort_filter.xlsx` | P1 |  |
| `SH-F0-05` | NaMiSheet | Conditional formatting (cơ bản) | F0 | Highlight theo điều kiện giá trị/công thức | Hỗ trợ; cơ bản round-trip tốt | Không cần viết thêm (xem SH-F1-11 cho nâng cao) | **C1** | `sheet/f0_condformat.xlsx` | P1 |  |
| `SH-F0-06` | NaMiSheet | Data validation | F0 | Giới hạn nhập, danh sách thả | Hỗ trợ; dependent list hạn chế (xem SH-F1-12) | Không cần viết thêm cho cơ bản | **C1** | `sheet/f0_validation.xlsx` | P1 |  |
| `SH-F0-07` | NaMiSheet | Named ranges | F0 | Đặt tên vùng, dùng trong công thức | Hỗ trợ đầy đủ; scope sheet/workbook | Không cần viết thêm | **C0** | `sheet/f0_named_ranges.xlsx` | P1 |  |
| `SH-F0-08` | NaMiSheet | Freeze panes, split | F0 | Đóng băng hàng/cột, chia khung | Hỗ trợ đầy đủ | Không cần viết thêm | **C0** | `sheet/f0_freeze_split.xlsx` | P1 |  |
| `SH-F0-09` | NaMiSheet | Hide/unhide, group/outline | F0 | Ẩn/hiện, nhóm hàng cột, outline | Hỗ trợ đầy đủ | Không cần viết thêm | **C0** | `sheet/f0_group_outline.xlsx` | P1 |  |
| `SH-F0-10` | NaMiSheet | Table với structured references (Excel Table / ListObject) | F0 | Table1[Cột], tự mở rộng, total row, calculated column | Calc KHÔNG có Excel Table object; chỉ 'Database range'. Structured references không được hỗ trợ native -> khi mở XLSX có bảng, tham chiếu dạng Table1[Col] có thể lỗi/đổi về địa chỉ | Cần engine Table object + structured ref (lớn) | **C2** | `sheet/f0_structured_table.xlsx` | P1 | Khoảng trống kiến trúc quan trọng, hay bị overclaim |
| `SH-F0-11` | NaMiSheet | Print area, print titles, page setup | F0 | Vùng in, lặp tiêu đề, dàn trang in | Hỗ trợ đầy đủ | Không cần viết thêm | **C1** | `sheet/f0_print_setup.xlsx` | P1 |  |
| `SH-F0-12` | NaMiSheet | CSV import có preview encoding/delimiter | F0 | Xem trước encoding/delimiter khi nhập CSV | Text Import dialog đầy đủ (encoding, delimiter, kiểu cột) | Không cần viết thêm | **C0** | `sheet/f0_csv_import.csv` | P1 |  |
| `SH-F0-13` | NaMiSheet | Undo kéo công thức/chèn cột | F0 | Hoàn tác mọi thao tác fill/insert | Undo stack đầy đủ | Không cần viết thêm | **C0** | `sheet/f0_undo.xlsx` | P1 |  |
| `SH-F0-14` | NaMiSheet | Họ SUM/SUMIFS/COUNTIFS/AVERAGEIFS | F0 | Tính đúng theo Excel | Hỗ trợ đầy đủ (có trong KiemTra_Ham_Office.xlsx tự chấm) | Không cần viết thêm | **C0** | `sheet/KiemTra_Ham_Office.xlsx` | P1 | Đã có file tự kiểm 79 hàm |
| `SH-F0-15` | NaMiSheet | IF/IFS/IFERROR/IFNA/SWITCH | F0 | Logic đúng Excel | Hỗ trợ đầy đủ (file tự chấm) | Không cần viết thêm | **C0** | `sheet/KiemTra_Ham_Office.xlsx` | P1 |  |
| `SH-F0-16` | NaMiSheet | INDEX/MATCH/XLOOKUP | F0 | Tra cứu đúng; XLOOKUP như Excel | INDEX/MATCH đầy đủ; XLOOKUP/XMATCH có từ LO 24.8 -> 25.2 có; trả 1 giá trị OK, trả MẢNG không spill | Spill cần engine mảng động (xem SH-F1-02) | **C1** | `sheet/KiemTra_Ham_Office.xlsx` | P1 | XLOOKUP single-value ổn; array-return là C3 |
| `SH-F0-17` | NaMiSheet | Text/date/round/financial thường dùng | F0 | LEFT/MID/TEXT/DATE/ROUND/PMT/FV/PV/NPV/IRR/RATE... đúng | Hỗ trợ đầy đủ (file tự chấm; ngưỡng ROUND 1e-6) | Không cần viết thêm | **C0** | `sheet/KiemTra_Ham_Office.xlsx` | P1 | IRR/RATE lặp số -> lệch chữ số rất nhỏ |
| `SH-F0-18` | NaMiSheet | Tham chiếu tương đối/tuyệt đối, tên vùng, cross-sheet | F0 | $A$1, Sheet!A1, name refs đúng | Hỗ trợ đầy đủ; .xcu đã đặt cú pháp Excel A1 | Không cần viết thêm | **C0** | `sheet/f0_refs.xlsx` | P1 | registrymodifications.xcu Grammar=1 |
| `SH-F0-19` | NaMiSheet | Array cũ (CSE) & giá trị lỗi Excel | F0 | Array Ctrl+Shift+Enter; #DIV/0!, #N/A, #VALUE!... | Legacy array đầy đủ; mã lỗi map Excel | Không cần viết thêm | **C1** | `sheet/f0_legacy_array.xlsx` | P1 |  |
| `SH-F0-20` | NaMiSheet | Tách formula/cached/format; locale vi-VN, ngày 1900/1904, precision, circular refs | F0 | Phân biệt công thức vs giá trị cache vs định dạng; đúng locale & hệ ngày | Calc tính lại khi mở (xcu RecalcMode=0); dấu thập phân theo locale; 1904 flag đọc được; circular ref có cảnh báo/iteration setting | Cần Compatibility Inspector so cached vs recalc (P0 kế toán) | **C1** | `sheet/f0_locale_dates.xlsx` | P0 | Liên quan gate tổng kiểm soát kế toán |
| `SH-F1-01` | NaMiSheet | Mảng động: FILTER/SORT/UNIQUE/SEQUENCE (spill) | F1 | Hàm spill tràn ô, tính lại động như Excel 365 | Calc 25.2 KHÔNG có dynamic array spill; các hàm này không nhận dạng -> Err:508/#NAME?; công thức không round-trip đúng | Cần engine mảng động (thay đổi kiến trúc lớn) — không có sẵn | **C3** | `sheet/f1_dynamic_arrays.xlsx` | P1 | Kit: 'trả cached values không được giả là có engine'. Điểm overclaim trong doc cũ cần sửa |
| `SH-F1-02` | NaMiSheet | XLOOKUP array/spill, A1# reference | F1 | XLOOKUP trả mảng tràn, tham chiếu vùng tràn A1# | Không spill; A1# không hỗ trợ | Phụ thuộc engine mảng động (SH-F1-01) | **C3** | `sheet/f1_spill_ref.xlsx` | P1 |  |
| `SH-F1-03` | NaMiSheet | LET | F1 | LET gán biến trong công thức | LO 24.8+ hỗ trợ LET -> 25.2 có | Kiểm round-trip | **C1** | `sheet/f1_let.xlsx` | P2 |  |
| `SH-F1-04` | NaMiSheet | LAMBDA/BYROW/BYCOL/MAP/REDUCE/SCAN | F1 | Hàm tự định nghĩa LAMBDA + helper | Calc 25.2 KHÔNG hỗ trợ LAMBDA và nhóm helper -> #NAME? | Cần engine LAMBDA (lớn) — không có sẵn | **C3** | `sheet/f1_lambda.xlsx` | P2 | Doc cũ gộp LAMBDA vào 'có từ 24.8+' là sai — cần đính chính |
| `SH-F1-05` | NaMiSheet | Spill range, #SPILL!, implicit intersection (@) | F1 | Vùng tràn, lỗi #SPILL!, giao ngầm @ | Không có khái niệm spill -> không áp dụng | Phụ thuộc engine mảng động | **C3** | `sheet/f1_spill_semantics.xlsx` | P2 |  |
| `SH-F1-06` | NaMiSheet | Table object (header/total/calculated column/structured refs) | F1 | Bảng Excel đầy đủ tính năng | Không có (xem SH-F0-10) | Engine Table object | **C2** | `sheet/f1_table_object.xlsx` | P2 |  |
| `SH-F1-07` | NaMiSheet | PivotTable | F1 | Pivot tạo/refresh/grouping như Excel | Calc có Pivot Table (DataPilot); round-trip Excel pivot mất một phần tùy chọn/định dạng | Patch pivot fidelity | **C1** | `sheet/f1_pivot.xlsx` | P2 |  |
| `SH-F1-08` | NaMiSheet | PivotChart | F1 | Biểu đồ gắn pivot, cập nhật theo pivot | Calc không có PivotChart gắn động như Excel; chart từ pivot là chart thường | Patch/engine pivot chart | **C2** | `sheet/f1_pivotchart.xlsx` | P2 |  |
| `SH-F1-09` | NaMiSheet | Pivot refresh/grouping/calculated field | F1 | Refresh giữ nguồn, group ngày/số, calculated field | Grouping & một phần calculated field có; refresh nguồn ngoài hạn chế | Patch + cảnh báo nguồn không truy cập được | **C2** | `sheet/f1_pivot_refresh.xlsx` | P2 | Kit: nguồn không truy cập -> nêu kết quả cũ + thời điểm |
| `SH-F1-10` | NaMiSheet | Slicer/Timeline | F1 | Slicer & timeline lọc pivot/table | Calc không có Slicer/Timeline native; import XLSX bỏ qua | Cần viết tính năng UI slicer | **C3** | `sheet/f1_slicer.xlsx` | P2 |  |
| `SH-F1-11` | NaMiSheet | Conditional formatting nâng cao (data bar/icon set/biểu thức lồng) | F1 | Data bar, icon set, thang màu, công thức lồng round-trip | Có data bar/color scale/icon set; round-trip XLSX đôi khi mất tùy chọn/ngưỡng | Patch fidelity round-trip | **C2** | `sheet/f1_cf_advanced.xlsx` | P2 |  |
| `SH-F1-12` | NaMiSheet | Dependent data validation list | F1 | Danh sách phụ thuộc (cascading) | Calc làm được bằng INDIRECT + named ranges nhưng không phải tính năng gói sẵn như Excel | Patch UX/wizard | **C2** | `sheet/f1_dependent_list.xlsx` | P2 |  |
| `SH-F1-13` | NaMiSheet | Goal Seek | F1 | Tìm giá trị để đạt mục tiêu | Tools > Goal Seek có sẵn | Không cần viết thêm | **C1** | `sheet/f1_goalseek.xlsx` | P2 |  |
| `SH-F1-14` | NaMiSheet | Solver | F1 | Tối ưu ràng buộc | Calc có Solver (linear/nonlinear) | Không cần viết thêm; khác solver Excel ở thuật toán | **C1** | `sheet/f1_solver.xlsx` | P3 |  |
| `SH-F1-15` | NaMiSheet | Scenario | F1 | Kịch bản what-if | Tools > Scenarios có sẵn; round-trip XLSX hạn chế | Patch round-trip | **C1** | `sheet/f1_scenario.xlsx` | P3 |  |
| `SH-F1-16` | NaMiSheet | Biểu đồ cơ bản + combo/secondary axis/data labels | F1 | Column/bar/line/area/pie/scatter/bubble, combo, trục phụ, nhãn | Hỗ trợ đầy đủ; combo & secondary axis có; round-trip XLSX khá, đôi chỗ lệch style | Patch chart fidelity | **C1** | `sheet/f1_charts_basic.xlsx` | P2 |  |
| `SH-F1-17` | NaMiSheet | Error bars, trendline | F1 | Thanh sai số, đường xu hướng | Hỗ trợ | Không cần viết thêm | **C1** | `sheet/f1_chart_trend.xlsx` | P3 |  |
| `SH-F1-18` | NaMiSheet | Sparklines | F1 | Sparkline trong ô | LO 24.8+ hỗ trợ sparklines -> 25.2 có; round-trip XLSX khá | Kiểm fidelity | **C1** | `sheet/f1_sparklines.xlsx` | P3 |  |
| `SH-F2-01` | NaMiSheet | Power Query / Get & Transform | F2 | Kết nối CSV/JSON/SQL/web, bước biến đổi tái lập, refresh, cache | Calc KHÔNG có Power Query. Có CSV import + một ít kết nối DB qua Base; không phải pipeline M-steps | Cần pipeline ETL mở riêng (engine/sản phẩm) — không khả thi bằng fork | **C3** | `sheet/f2_powerquery.xlsx` | P2 | Không tự nhận 'hỗ trợ Power Query' chỉ vì có CSV import |
| `SH-F2-02` | NaMiSheet | Data Model / Power Pivot / DAX | F2 | Quan hệ nhiều bảng, measures, DAX | Calc KHÔNG có Data Model/DAX | Engine mô hình dữ liệu riêng — không khả thi bằng fork | **C3** | `sheet/f2_datamodel.xlsx` | P2 |  |
| `SH-F2-03` | NaMiSheet | Chặn truy vấn mạng khi mở + consent nguồn dữ liệu | F2 | Mở tệp không tự kết nối ngoài; xin đồng ý & chỉ rõ dữ liệu gửi | Calc có thể có external link/web query tự refresh — rủi ro | Cần Compatibility Inspector chặn/hỏi (phần Save-Safety/security) | **C2** | `sheet/f2_external_query.xlsx` | P0 | Gate P0: không mở kết nối ngoài ngoài ý muốn |
| `SH-F2-04` | NaMiSheet | Biểu đồ mới của Excel (waterfall/treemap/sunburst/boxplot/funnel/map/histogram/stock) | F2 | Các loại chart Excel 2016+ dựng & sửa được | Calc 25.2 không có native các loại chart mới; import XLSX các chart này mất/thành ảnh hoặc rỗng | Cần engine chart mới hoặc preview+cảnh báo | **C3** | `sheet/f2_new_charts.xlsx` | P3 | Box plot/funnel/map không có native |
| `SH-F0-21` | NaMiSheet | Kiểm soát kế toán: so trước/sau mở-lưu (ô công thức/lỗi/đổi kiểu/làm tròn/link ngoài/tổng đối chiếu) | F0 | Báo cáo so sánh trước/sau để người dùng quyết định; không tự nộp/ký | Chưa có công cụ so sánh; cần dựng | Cần Compatibility Inspector + diff report (M1 Save-Safety) | **C2** | `sheet/f0_accounting_control.xlsx` | P0 | Gate P0: không sai tổng kiểm soát fixture kế toán |

### NaMiSlides — Trình chiếu (Impress)

| ID | App | Tác vụ | F | Hành vi kỳ vọng | Hiện trạng LO 25.2 | Cần viết thêm | C | Fixture | Sev | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|
| `SL-F0-01` | NaMiSlides | Theme/master/layout, text/shape/image, align, layer/group, table, chart | F0 | Biên tập slide đầy đủ, round-trip PPTX | Impress hỗ trợ; round-trip PPTX tốt cho nội dung tĩnh; master/layout đôi khi lệch | Patch master/layout fidelity | **C1** | `slides/f0_edit_basic.pptx` | P1 |  |
| `SL-F0-02` | NaMiSlides | Chọn nhiều đối tượng, copy/paste từ Sheet | F0 | Multi-select; dán bảng/biểu đồ từ Calc | Hỗ trợ; dán từ Calc có tùy chọn OLE/ảnh | Không cần viết thêm | **C1** | `slides/f0_paste_from_sheet.pptx` | P1 |  |
| `SL-F0-03` | NaMiSlides | Slide sorter, notes, presenter view, dual display, laser/pen | F0 | Trình chiếu đầy đủ công cụ người giảng | Impress có Presenter Console, dual display, pen/pointer | Không cần viết thêm | **C1** | `slides/f0_present.pptx` | P1 |  |
| `SL-F0-04` | NaMiSlides | Tỉ lệ 4:3/16:9/tùy ý, xuất PDF/ảnh | F0 | Đổi tỉ lệ; export PDF & ảnh | Hỗ trợ đầy đủ | Không cần viết thêm | **C1** | `slides/f0_export.pptx` | P1 |  |
| `SL-F0-05` | NaMiSlides | Không lộ notes trên màn chiếu | F0 | Notes chỉ ở màn người giảng | Presenter Console tách notes đúng | Không cần viết thêm | **C1** | `slides/f0_notes_privacy.pptx` | P1 |  |
| `SL-F1-01` | NaMiSlides | Transition | F1 | Hiệu ứng chuyển slide round-trip | Nhiều transition cơ bản; một số nâng cao khác PowerPoint | Patch fidelity | **C1** | `slides/f1_transitions.pptx` | P2 |  |
| `SL-F1-02` | NaMiSlides | Animation/timing/trigger | F1 | Hoạt cảnh theo timing/trigger khớp PowerPoint | Impress đọc animation OOXML cơ bản; timing/easing/trigger lệch; animation path phức tạp mất | Patch animation engine fidelity | **C2** | `slides/f1_animation.pptx` | P2 |  |
| `SL-F1-03` | NaMiSlides | Video/audio với codec có quyền, phụ đề | F1 | Media nhúng phát được + phụ đề | Phụ thuộc codec GStreamer hệ thống; nhúng vs liên kết media khác nhau; phụ đề hạn chế | Patch + đóng gói codec hợp pháp | **C2** | `slides/f1_media.pptx` | P2 |  |
| `SL-F1-04` | NaMiSlides | Record slide show & xuất video | F1 | Ghi trình chiếu + xuất MP4 đồng bộ audio/timing | Impress không xuất video native | Cần pipeline ghi/encode riêng — không có sẵn | **C3** | `slides/f1_record_video.pptx` | P3 | Kit: chỉ công bố khi audio/timing đã test |
| `SL-F1-05` | NaMiSlides | Comments | F1 | Ghi chú cộng tác round-trip | Impress có comments; round-trip PPTX khá | Không cần viết thêm | **C1** | `slides/f1_comments.pptx` | P2 |  |
| `SL-F1-06` | NaMiSlides | Compare versions | F1 | So sánh phiên bản slide | Impress không có compare mạnh như Writer | Cần viết/patch | **C2** | `slides/f1_compare.pptx` | P3 |  |
| `SL-F1-07` | NaMiSlides | Share/export, template bài giảng & báo cáo | F1 | Mẫu + xuất chia sẻ | Template & export đầy đủ | Dựng bộ mẫu VN | **C1** | `slides/f1_templates.potx` | P2 |  |
| `SL-F1-08` | NaMiSlides | Accessibility checker | F1 | Kiểm trợ năng (alt text, contrast, thứ tự đọc) | LO có Accessibility Check tool | Không cần viết thêm | **C1** | `slides/f1_a11y.pptx` | P3 |  |
| `SL-F2-01` | NaMiSlides | Morph transition | F2 | Hiệu ứng Morph như PowerPoint | Impress không có Morph | Không khả thi 1:1; fallback transition thường + cảnh báo | **C3** | `slides/f2_morph.pptx` | P3 |  |
| `SL-F2-02` | NaMiSlides | 3D | F2 | Đối tượng 3D models/extrude | Impress có 3D cơ bản; 3D model (glTF/PowerPoint 3D) không tương thích | Fallback preview | **C2** | `slides/f2_3d.pptx` | P3 |  |
| `SL-F2-03` | NaMiSlides | Diagram phức tạp / SmartArt | F2 | SmartArt sửa được | Hiện thành ảnh/nhóm hình tĩnh (như Writer SmartArt) | Không khả thi 1:1; preview + cấm Save phá cấu trúc | **C3** | `slides/f2_smartart.pptx` | P3 |  |
| `SL-F2-04` | NaMiSlides | Chart nhúng có dữ liệu | F2 | Biểu đồ nhúng sửa dữ liệu trong slide | Mở được; round-trip mất một phần; sửa dữ liệu chart nhúng Office hạn chế | Patch + fallback | **C2** | `slides/f2_embedded_chart.pptx` | P3 |  |
| `SL-F2-05` | NaMiSlides | Tương tác / kiosk | F2 | Trình chiếu tự chạy kiosk + tương tác | Impress có chế độ auto/kiosk + hyperlink interaction | Không cần viết thêm | **C1** | `slides/f2_kiosk.pptx` | P3 |  |

### Tương tác xuyên ứng dụng (Interop)

| ID | App | Tác vụ | F | Hành vi kỳ vọng | Hiện trạng LO 25.2 | Cần viết thêm | C | Fixture | Sev | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|
| `IX-01` | Interop | Copy Sheet->Writer/Slides: tùy chọn ảnh tĩnh | F0 | Dán như ảnh tĩnh rõ ràng | Paste Special có 'Bitmap/GDI metafile' | UX 3-lựa-chọn thống nhất | **C1** | `interop/ix_paste_image.odt` | P2 |  |
| `IX-02` | Interop | Copy Sheet->Writer/Slides: đối tượng chỉnh được (OLE) | F1 | Dán OLE sửa được | Paste Special OLE có; sửa OLE giữa app LO ổn, round-trip Office hạn chế | Patch fidelity | **C2** | `interop/ix_paste_ole.odt` | P2 |  |
| `IX-03` | Interop | Copy Sheet->Writer/Slides: liên kết dữ liệu + thông báo refresh, không tự truy cập mạng | F1 | Dán link; đổi nguồn -> hỏi refresh; không tự mở path mạng/cloud | DDE/link có; kiểm soát 'không tự truy cập mạng' chưa có UX | Cần UX refresh + chặn auto network (security) | **C2** | `interop/ix_paste_link.odt` | P0 | Gate P0: không tự truy cập path mạng/cloud |
| `IX-04` | Interop | Trải nghiệm thống nhất: file picker/print/PDF/phím tắt/theme/Help/update/autosave/SmartAI | F0 | Các app chia sẻ UX, phím tắt, theme, autosave | LO chia sẻ nhiều UX cốt lõi; theme/branding NaMiOffice một phần (hook 0450, icons); SmartAI chưa nhúng | Tích hợp UX NaMiOS + SmartAI (một phần đã làm branding) | **C1** | `interop/ix_unified_ux.md` | P2 | Branding hiển thị đã có; title bar còn 'LibreOffice' |
| `IX-05` | Interop | CSV/XLSX đính kèm mail mở trong sandbox, không auto-run macro | F0 | Mở tệp lạ không tự chạy macro, cô lập | xcu đặt MacroSecurityLevel=1 (hỏi trước khi chạy); sandbox tiến trình chưa có | Cần sandbox parser (fidelity pipeline) + giữ mức bảo mật macro | **C1** | `security/ix_attachment_sandbox.xlsx` | P0 | Gate P0: 0 thực thi macro tự động |

### NaMiMail — Thư (sản phẩm riêng)

| ID | App | Tác vụ | F | Hành vi kỳ vọng | Hiện trạng LO 25.2 | Cần viết thêm | C | Fixture | Sev | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|
| `ML-01` | NaMiMail | IMAP/SMTP TLS, OAuth, nhiều tài khoản, thư mục, tìm kiếm cục bộ | F1 | Client mail đa tài khoản an toàn | **10/11/2026: ĐÃ ĐÓNG GÓI** `thunderbird` + `thunderbird-l10n-vi` + `hunspell-vi` (`0405-mail-notes.list.chroot`) — IMAP/SMTP/TLS/nhiều tài khoản/thư mục/tìm kiếm cục bộ là tính năng lõi Thunderbird, không phải code NaMiOS | Rebrand UI (.desktop Name=) + kiểm tài khoản IMAP/SMTP thật trên host | **C1** | `mail/ml_imap_smtp.mock` | P2 | Kit: có thể tích hợp mail Linux đáng tin, gắn nguồn — ĐÃ LÀM (Thunderbird, xem `docs/office/ECOSYSTEM-MAIL-NOTES-FORMS.md` §1). verified_on_host: NO cho hành vi app, nhưng tên gói đã xác nhận qua Packages.gz thật trixie/main |
| `ML-02` | NaMiMail | CardDAV/CalDAV, lời mời họp, task | F1 | Danh bạ & lịch chuẩn mở + invite | **10/11/2026:** CardDAV/CalDAV + ICS invite là tính năng lõi Thunderbird ≥102 (gộp sẵn, không cần add-on rời) — đã có qua gói `thunderbird` | Kiểm CardDAV/CalDAV + ICS invite thật trên host; chưa có task UI kiểm riêng | **C1** | `mail/ml_carddav_caldav.mock` | P2 | verified_on_host: NO cho hành vi app; xem ECOSYSTEM-MAIL-NOTES-FORMS.md §1 |
| `ML-03` | NaMiMail | S/MIME & PGP, rules, shared calendar, delegated mailbox, Exchange/M365 | F2 | Bảo mật mail nâng cao + Exchange/M365 | Thunderbird hỗ trợ S/MIME/PGP native nhưng NaMiOS chưa kiểm UX khóa; Exchange/M365 cần API được cấp quyền & kiểm tenant policy | Không khả thi bằng rebrand gói; cần UX khóa đã kiểm + giấy phép/API Microsoft | **C3** | `mail/ml_exchange.mock` | P3 | Không gọi 'tương thích Outlook' khi mới có IMAP đọc mail — vẫn đúng dù đã đóng gói Thunderbird (ML-01/02) |

### NaMiNotes — Ghi chú (sản phẩm riêng)

**10/11/2026 — rà soát trixie/main, quyết định KHÔNG ship gói tạm.** Đã kiểm `zim`, `cherrytree`, `gnote`, `tomboy-ng`, `basket`, `xournalpp` (đều có trong Debian main) — không gói nào đáp ứng đồng thời notebook/section/page + rich content + ghi âm + vẽ bút + export PDF/MD/ODF của F1. Joplin (gần nhất về tính năng) không có trong Debian main. Chi tiết so sánh từng app: `docs/office/ECOSYSTEM-MAIL-NOTES-FORMS.md` §2.

| ID | App | Tác vụ | F | Hành vi kỳ vọng | Hiện trạng LO 25.2 | Cần viết thêm | C | Fixture | Sev | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|
| `NT-01` | NaMiNotes | Notebook/section/page, ink, offline, export PDF/MD/ODF | F1 | Ghi chú có cấu trúc, định dạng mở | Không có trong LO; đã rà soát `zim`/`cherrytree`/`gnote`/`tomboy-ng`/`basket`/`xournalpp` trong trixie/main — không app nào đủ F1 cùng lúc (xem bảng so sánh ECOSYSTEM doc) | Sản phẩm riêng (viết mới hoặc đóng gói có kiểm); KHÔNG ship gói tạm nào mặc định | **C3** | `notes/nt_notebook.mock` | P3 | Interim không cài sẵn, không gắn nhãn NaMiOS: `cherrytree` (gần nhất) hoặc `zim` — người dùng tự `apt install` |
| `NT-02` | NaMiNotes | OneNote round-trip | F2 | Nhập/xuất tệp OneNote độc quyền | Không hỗ trợ định dạng OneNote độc quyền | Không khả thi 1:1; không cam kết | **C3** | `notes/nt_onenote.mock` | P3 |  |
| `NT-03` | NaMiNotes | Đồng bộ nhiều thiết bị, mã hóa, xung đột, history | F2 | Sync bảo mật + resolve conflict | Không có; cần dịch vụ + account | Dịch vụ riêng — chỉ quảng bá sau khi có account & test | **C3** | `notes/nt_sync.mock` | P3 |  |

### NaMiForms — Biểu mẫu (dịch vụ riêng)

| ID | App | Tác vụ | F | Hành vi kỳ vọng | Hiện trạng LO 25.2 | Cần viết thêm | C | Fixture | Sev | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|
| `FM-01` | NaMiForms | Tạo form, nhánh điều kiện, anonymous/định danh, export CSV/XLSX, consent/retention | F1 | Dịch vụ thu thập phản hồi có quyền dữ liệu | Writer/Calc có form control nhưng không phải dịch vụ Forms; không có backend thu thập | Dịch vụ/app riêng (server, ACL, consent) — không phải tính năng fork | **C3** | `forms/fm_survey.mock` | P3 |  |
| `FM-02` | NaMiForms | Quiz/chấm điểm + workflow doanh nghiệp có audit | F2 | Chấm tự động + audit workflow | Không có | Dịch vụ riêng | **C3** | `forms/fm_quiz.mock` | P3 |  |

### NaMiData — Cơ sở dữ liệu (Base)

| ID | App | Tác vụ | F | Hành vi kỳ vọng | Hiện trạng LO 25.2 | Cần viết thêm | C | Fixture | Sev | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|
| `DT-01` | NaMiData | Bảng/khóa/quan hệ, form nhập, validation, query SQL, report (Base/ODB) | F2 | CSDL desktop với form & report | LibreOffice Base có (ODB + HSQLDB/Firebird embedded, JDBC/ODBC); form/report hoạt động | Đánh giá + polish; backend riêng nếu cần | **C2** | `data/dt_base.odb` | P3 | Phân biệt rõ Base/ODB với Access |
| `DT-02` | NaMiData | Đọc ACCDB/MDB | F2 | Mở/đọc dữ liệu Access | Không có driver native; mdbtools (đã thêm trong 0400 list) đọc/xuất .mdb, .accdb một phần; KHÔNG ghi | Chỉ đọc/xuất; lộ trình migrate thủ công + đối soát | **C2** | `data/dt_access_read.accdb` | P3 | mdbtools read-only |
| `DT-03` | NaMiData | Access forms/reports/VBA | F2 | Chạy form/report/VBA của Access | Không tương thích; ACCDB forms/reports/VBA là hệ riêng | Không khả thi; cần Windows/Access có giấy phép | **C3** | `data/dt_access_vba.accdb` | P3 |  |

### Cộng tác & lưu trữ (dịch vụ riêng)

| ID | App | Tác vụ | F | Hành vi kỳ vọng | Hiện trạng LO 25.2 | Cần viết thêm | C | Fixture | Sev | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|
| `CL-01` | NaMiCollab | Giai đoạn 1: file local/SMB/WebDAV, locks, cảnh báo conflict, lịch sử cục bộ, link chia sẻ | F1 | Cộng tác qua file + khóa + cảnh báo xung đột, không cần cloud | LO mở SMB/WebDAV; có lock file (.~lock); cảnh báo mở đồng thời; lịch sử/so sánh phần Writer | Patch UX conflict + lịch sử bản cục bộ | **C2** | `collab/cl_file_lock.odt` | P2 |  |
| `CL-02` | NaMiCollab | Giai đoạn 2: server NaMiCollab, ACL theo tệp, version history, comments/mentions, share expiry, offline sync | F2 | Dịch vụ cộng tác có tài khoản/tổ chức | Không có server; cần xây hoặc tích hợp nền được phê duyệt | Dịch vụ riêng (server, account, ACL) — chưa có | **C3** | `collab/cl_server.mock` | P3 |  |
| `CL-03` | NaMiCollab | Giai đoạn 3: đồng tác giả thời gian thực (CRDT/OT) | F2 | 2-20 người cùng sửa, merge, không mất nội dung | LO desktop không có real-time coauthoring (Collabora Online là sản phẩm server riêng) | Cần engine CRDT/OT + server — không khả thi bằng desktop fork | **C3** | `collab/cl_realtime.mock` | P3 | Chỉ gắn 'cùng sửa trực tiếp' sau test mất mạng & merge |
| `CL-04` | NaMiCollab | Tích hợp OneDrive/SharePoint/Google Drive (scope tối thiểu) | F2 | Kết nối cloud với consent & scope tối thiểu | Không tích hợp sẵn; cần API & token refresh | Sản phẩm riêng + API được cấp quyền | **C3** | `collab/cl_cloud.mock` | P3 |  |
| `CL-05` | NaMiCollab | IRM / nhãn nhạy cảm Microsoft 365 | F2 | Mở/tuân thủ tệp có IRM/sensitivity label | Không mở được tệp IRM/RMS; không né bảo vệ | Không khả thi; cần client Microsoft hỗ trợ | **C3** | `collab/cl_irm.docx` | P1 | Gate: không cố vượt mật khẩu/IRM |

### Add-in / Macro / Tự động hóa

| ID | App | Tác vụ | F | Hành vi kỳ vọng | Hiện trạng LO 25.2 | Cần viết thêm | C | Fixture | Sev | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|
| `AX-01` | Add-in/Automation | NaMiOffice extension SDK (manifest, quyền, sandbox, signature, revoke) qua Python/UNO | F2 | SDK mở rộng có quản trị, không gọi là Office.js | LO có UNO API + Python/Basic scripting + extension (.oxt) với signing; thiếu lớp governance manifest/sandbox/revoke như kit yêu cầu | Xây lớp SDK governance trên UNO | **C2** | `addin/ax_sdk.oxt` | P3 | Nền tảng automation hợp pháp của NaMiOffice |
| `AX-02` | Add-in/Automation | VBA macro | F2 | Chạy macro VBA của Word/Excel/PowerPoint | LO Basic + tương thích VBA MỘT PHẦN (Option VBASupport); UserForm/ActiveX/Application.* phức tạp không chạy hoặc sai | Không khả thi đầy đủ; mặc định KHÔNG thực thi, bảo toàn project, chuyển thủ công + test | **C2** | `addin/ax_vba.xlsm` | P1 | Kit: không tự dịch bằng AI rồi chạy |
| `AX-03` | Add-in/Automation | COM/VSTO/ActiveX | F2 | Add-in COM/VSTO, control ActiveX | Phụ thuộc Windows/Office; không chạy native Linux | Không khả thi; cần Windows có giấy phép/VM/remote desktop | **C3** | `addin/ax_vsto.mock` | P2 |  |
| `AX-04` | Add-in/Automation | Office.js add-ins | F2 | Add-in Office.js (requirement sets) | Phụ thuộc host Office + dịch vụ Microsoft; không chạy trong LO | Không khả thi tổng quát; chỉ adapter cụ thể theo hợp đồng + test | **C3** | `addin/ax_officejs.mock` | P2 | Không gắn badge tổng quát |
| `AX-05` | Add-in/Automation | Script nội bộ: editor/debugger/log/dry-run/rollback | F2 | Soạn/gỡ lỗi script theo quyền, dry-run, rollback | LO có Basic IDE + Python script; thiếu dry-run/rollback/log theo quyền như kit | Xây lớp an toàn (không cho script tải-về đọc toàn home) | **C2** | `addin/ax_script.py` | P2 |  |

### SmartAI trong NaMiOffice

| ID | App | Tác vụ | F | Hành vi kỳ vọng | Hiện trạng LO 25.2 | Cần viết thêm | C | Fixture | Sev | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|
| `AI-01` | SmartAI-in-Office | Trợ lý: giải thích công thức, bắt lỗi tham chiếu, gợi ý chart, viết lại, dàn ý slide, tìm lệnh, lý giải incompat | F1 | Trợ lý trong app, không thay engine tính | Chưa nhúng vào NaMiOffice; SmartAI tồn tại ở tầng NaMiOS (PL04) nhưng chưa nối vào Writer/Calc/Impress | Xây tích hợp trợ lý (sidebar/UNO) + diff preview + undo | **C2** | `ai/ai_assistant.md` | P3 | Không thay engine tính; số thuế/kế toán phải đối soát |
| `AI-02` | SmartAI-in-Office | Local-first, cloud opt-in, chống prompt-injection (nội dung tài liệu = không tin cậy) | F1 | Chạy cục bộ khi phù hợp; cloud chỉ khi opt-in; prompt trong tài liệu không ra lệnh cho AI | Chưa có; cần thiết kế an toàn | Chính sách + sandbox dữ liệu chưa có | **C2** | `ai/ai_safety.md` | P0 | Gate P0: không để prompt trong tệp điều khiển AI đọc tệp khác/gửi mạng |

### Hạ tầng xuyên suốt

| ID | App | Tác vụ | F | Hành vi kỳ vọng | Hiện trạng LO 25.2 | Cần viết thêm | C | Fixture | Sev | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|
| `PIPE-01` | Cross-cutting | Fidelity pipeline / Compatibility Inspector (đọc trước khi Save) | F0 | Sniff + sandbox parse + inventory macro/OOXML parts/external links/signature/IRM + chấm C0-C3 + pre-save diff/cảnh báo + atomic save-as bản mới + reopen kiểm | CHƯA CÓ. LO không tự nhận diện & cảnh báo rủi ro mất-dữ-liệu theo cách kit mô tả; registrymodifications chỉ đặt recalc/macro-level | Đây là miếng M1 Save-Safety cốt lõi — cần XÂY mới | **C2** | `pipeline/pipe_inspector_suite/` | P0 | Trụ của mọi gate P0 'không mất dữ liệu không cảnh báo' |
