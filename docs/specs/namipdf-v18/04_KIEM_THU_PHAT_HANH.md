# 04. Kiểm thử, phát hành và nguồn đối chiếu

## 1. Corpus có quyền

Tối thiểu pilot đề xuất: 100 PDF text, 50 bản scan tiếng Việt, 30 biểu mẫu, 30 PDF ký số, 20 PDF/A/PDF/UA, 20 tài liệu bị mã hóa/có embedded content, 20 file lỗi/fuzz, 20 file lớn/ảnh nhiều trang. Lấy mẫu từ trường học, kế toán, văn phòng, hành chính đã ẩn danh/được cho phép; không đưa hồ sơ thật lên repo hoặc cloud AI. Ghi nguồn, bản PDF, generator, font, page count, feature inventory, expected, checksum và quyền sử dụng.

## 2. Test theo công việc

| ID | Tác vụ và dữ liệu | Kết quả bắt buộc |
|---|---|---|
| PDF-01 | Mở PDF 200 trang, bookmarks, link, ảnh và vector | Render, search/copy, navigation, print không mất trang; worker không khóa desktop |
| PDF-02 | Thêm/chỉnh/xóa comment; save/reopen bằng hai viewer | Annotation và author/appearance còn, không lẫn text gốc |
| PDF-03 | Sửa một dòng text/vector ảnh, save/reopen | Text cũ không còn tìm/copy được, layout vùng lân cận không vỡ; nếu không thể thì cảnh báo trước |
| PDF-04 | Merge/split/reorder/rotate/crop nhiều file | Đủ trang đúng thứ tự, metadata và bookmarks theo chính sách |
| PDF-05 | OCR scan có dấu, tài liệu Việt–Anh, bảng số | Tìm/copy đúng theo thước đo accuracy; bản scan gốc giữ nguyên, vùng số sai được báo |
| PDF-06 | Điền/tạo AcroForm và mở viewer thứ hai | Giá trị, appearance, tab order và quyền còn đúng |
| PDF-07 | XFA động | Phát hiện, cảnh báo và không hỏng tệp gốc |
| PDF-08 | Chữ ký hợp lệ/hết hạn/thu hồi/sửa sau ký/offline | 5 trạng thái phân biệt; không báo xanh sai; ký test qua token/service đã chứng nhận |
| PDF-09 | Redact tên/CCCD/ảnh/OCR trong file có incremental revisions | Không trích xuất được từ content, object, metadata, attachment, lịch sử; kiểm độc lập |
| PDF-10 | PDF/A và PDF/UA | Validator profile đạt; screen reader đọc đúng thứ tự ca mẫu |
| PDF-11 | In USB/LAN, A4/A3, duplex, lỗi máy offline/khổ sai | Bản giấy đúng; thông báo nguyên nhân/hướng xử lý |
| PDF-12 | File hỏng/đính kèm thực thi/JS/decompression bomb | Không thực thi hoặc kết nối mạng; parser có quota, không hỏng file khác |
| PDF-13 | Mất điện/hết dung lượng/xung đột SMB khi Save | Khôi phục bản gốc hoặc bản nháp, không gọi file dở là đã lưu |

OCR accuracy đo riêng CER/WER cho chữ tiếng Việt và exact match cho trường số/ngày; ngưỡng cần hiệu chỉnh theo chất lượng ảnh của corpus, không cam kết một tỷ lệ cho mọi scan. Redaction và trạng thái chữ ký là **gate tuyệt đối**, không lấy tỷ lệ trung bình bù lỗi.

## 3. Cổng phát hành

**M0 khảo sát:** chọn engine/license, chạy renderer trên corpus, thiết kế UI, nguồn model OCR tiếng Việt. **M1 viewer P0:** đọc, search, print, annotation, sắp xếp trang, save an toàn, sandbox. **M2 chuyên nghiệp:** sửa text/image có kiểm, OCR, form và conversion. **M3 tin cậy:** PAdES, PDF/A/UA, redaction độc lập; chỉ bật theo feature flag sau chứng nhận. **M4 doanh nghiệp:** batch, admin policy, token/vendor integration và quản trị nhiều máy.

Không phát hành nhãn “full” nếu chỉ có viewer + chú thích. Release notes công bố từng feature, định dạng, hạn chế và ngày kiểm; P0 viewer có thể phát hành trước P1/P2 với tên trạng thái trung thực. Stop release khi mất dữ liệu, che thông tin vẫn khôi phục được, xác nhận chữ ký sai, JS/attachment chạy hoặc file hỏng ảnh hưởng hệ thống.

## 4. Nguồn kỹ thuật chính thức

- PDF Association standards PDF, PDF/A, PDF/UA: https://pdfa.org/pdf-standards/
- PDF Association high-security redactions: https://pdfa.org/wp-content/uploads/2020/06/High-Security-PDF-Redactions-v4a_2.pdf
- ETSI ESI/PAdES: https://www.etsi.org/technical-groups/esi/
- veraPDF validation project: https://github.com/veraPDF/veraPDF-library
- OCRmyPDF documentation: https://ocrmypdf.readthedocs.io/
- QPDF documentation: https://qpdf.readthedocs.io/
- MuPDF license: https://mupdf.com/releases

Kiểm phiên bản và giấy phép thực tế ở thời điểm triển khai. PDF/A/UA có nhiều phần/profile, ký số có tiêu chuẩn và yêu cầu tin cậy thay đổi; bản yêu cầu không thay kết quả thẩm định pháp lý/nghiệp vụ.
