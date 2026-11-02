# Bộ yêu cầu phát triển NaMiOS

Phiên bản 1.1 ngày 02/11/2026. Soạn cho ông Đỗ Chí Cường và Đỗ Bảo Nam để giao Claude Code và đội kỹ thuật xây dựng hệ điều hành miễn phí cho người Việt, ưu tiên ứng dụng Windows và .NET.

## Bắt đầu

1. Giải nén toàn bộ gói vào một thư mục tài liệu riêng. Chưa có source hệ điều hành trong gói.
2. Mở Claude Code trong một workspace dự án mới hoặc repository được chỉ định.
3. Đưa thư mục tài liệu vào workspace, đọc `KHOI_DONG_CLAUDE.txt` và gửi nguyên nội dung cho Claude.
4. Claude đọc đặc tả, kiểm tra môi trường rồi thực hiện M0 và M1; tiếp tục phần độc lập nếu còn thiếu bộ cài thương mại.
5. Đọc `docs/STATUS.md` và báo cáo thật do Claude tạo để theo dõi tiến độ. Yêu cầu bằng chứng, không chỉ ảnh giao diện.

Nếu đã có CLAUDE.md trong repository, hãy hợp nhất quy tắc của gói này sau khi đọc nội dung hiện có; không ghi đè tự động.

## Các tệp

| Tệp | Mục đích |
| --- | --- |
| `specs/DAC_TA_HE_DIEU_HANH.md` | Đặc tả chính về phạm vi, kiến trúc, chức năng, dữ liệu, bảo mật và nghiệm thu |
| `KHOI_DONG_CLAUDE.txt` | Prompt giao việc để bắt đầu triển khai |
| `CLAUDE.md` | Quy tắc kỹ thuật và cách báo cáo cho agent |
| `planning/backlog.csv` | Tác vụ theo mốc, phụ thuộc, requirement IDs và đầu ra |
| `planning/ADR_KHOI_DAU.md` | Quyết định thiết kế ban đầu và các spike cần hoàn thành |
| `qa/test-matrix.csv` | Danh sách test ban đầu, tất cả chưa chạy |
| `qa/MAU_BAO_CAO.md` | Mẫu báo cáo tiến độ và chứng nhận theo tác vụ |
| `contracts/app-manifest.schema.json` | Hợp đồng cấu trúc manifest ứng dụng phiên bản đầu |
| `contracts/sample-misa-sme-wine.json` | Ví dụ hồ sơ MISA SME chưa kiểm thử, chưa đủ điều kiện cài |
| `contracts/evidence-report.schema.json` | Hợp đồng bằng chứng test |
| `contracts/sample-evidence-not-run.json` | Mẫu báo cáo chưa có bằng chứng, không phải kết quả đạt |
| `KIEM_TRA_GOI.json` | Kết quả kiểm tra tính nhất quán của tài liệu, không phải test hệ điều hành |
| `SHA256SUMS` | Hash tệp trong gói để kiểm tra toàn vẹn; không thay chữ ký phát hành |

## Phạm vi đã chốt để bắt đầu

Hai nhà sáng lập và chủ dự án: Đỗ Chí Cường và Đỗ Bảo Nam. Đặc tả có 30 mục, gồm phần bổ sung về thiết bị, giao diện và chuyển đổi người dùng.

Tên chính thức NaMiOS, Debian 13 amd64, KDE, tiếng Việt, Wine theo hồ sơ ứng dụng. Word/Excel, Zalo PC, MISA SME và các ứng dụng .NET được kiểm thử riêng từng phiên bản. Web và LibreOffice là các lựa chọn được ghi nhãn riêng, không được tính thành chạy thành công phần mềm desktop gốc.

Nhánh core không đòi mua Windows. Nhánh VM/remote tùy chọn vẫn phụ thuộc môi trường Windows có quyền sử dụng. Chưa có ứng dụng thương mại nào được chứng nhận trong bộ tài liệu này. Cần bộ cài có quyền dùng, phiên bản và mẫu tác vụ để chứng nhận sau.

Markdown là định dạng nguồn để Claude đọc, trích requirement IDs và cập nhật theo Git. Có thể mở bằng trình soạn thảo thông thường; không cần chuyển qua PDF trước khi giao Claude.
