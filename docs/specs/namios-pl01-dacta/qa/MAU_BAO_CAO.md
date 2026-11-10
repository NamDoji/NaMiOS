# Báo cáo mốc triển khai

Mốc: TBD. Ngày: TBD. Source commit: TBD. Người thực hiện: TBD. Người kiểm tra: TBD.

## Kết luận

Ghi rõ đạt gate nào, gate nào chưa đạt và lý do. Không đồng nhất hoàn thành scaffolding với hoàn thành hệ điều hành.

## Phạm vi đã làm

Liệt kê requirement IDs, file/module đã có, hành vi thực và phần chưa có. Ghi thay đổi so với đặc tả cùng ADR tương ứng.

## Môi trường

OS/architecture, CPU/RAM/disk, VM/KVM, kernel, desktop session, package snapshot, Wine/runtime/profile/app versions và hashes. Chỉ thu thông tin cần thiết, không chứa serial/bí mật.

## Lệnh và kết quả thực

| Run ID | Lệnh hoặc test | Exit code | Kết quả | Evidence |
| --- | --- | --- | --- | --- |
| TBD | Chưa chạy | N/A | not_run | Chưa có |

Mock hoặc unit test không dùng để chứng nhận binary Office/MISA chạy được. Chưa có bộ cài/môi trường/credentials phải ghi blocked_external_dependency với đầu vào cần bổ sung.

## Tình trạng ứng dụng

| App và build | Mode | Tác vụ bắt buộc | Kết quả | Giới hạn | Vendor support |
| --- | --- | --- | --- | --- | --- |
| Word build chưa chốt | wine | Chưa chốt | untested | Thiếu build và bộ cài hợp lệ | unknown |
| Excel build chưa chốt | wine | Chưa chốt | untested | VBA/add-in là nhóm riêng | unknown |
| Zalo PC build chưa chốt | wine | Chưa chốt | untested | Không gộp với web | unknown |
| MISA SME build chưa chốt | wine | Chưa chốt | untested | DB và ký số chưa kiểm chứng | unknown |
| Ứng dụng .NET chưa xác định | TBD | Chưa chốt | untested | Cần phân loại framework/phụ thuộc | unknown |

## Dữ liệu và phục hồi

Tập dữ liệu giả và expected values; kết quả round-trip; backup; các bước restore thực đã chạy; dữ liệu không thể hoàn nguyên nếu có. Không đưa file thật hoặc tài khoản vào báo cáo.

## Vấn đề còn lại

ID, severity, bước tái hiện, actual/expected, workaround, trách nhiệm và điều kiện đóng. Rủi ro P0/P1 trong phạm vi ngăn phát hành.

## Quyết định gate

Product owner: TBD. QA: TBD. Gate: pending. Phạm vi được công bố: chưa có. Các đầu vào cần bổ sung: TBD. Bước tiếp theo: TBD.
