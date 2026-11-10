# 03. Nghiệm thu và prompt Claude Code

## 1. Các ca kiểm thử bắt buộc

| ID | Tình huống | Kết quả |
|---|---|---|
| U19-01 | Máy stable có bản đúng kiến trúc | Thông báo một lần, phiên bản/changelog/size thật |
| U19-02 | Bốn chế độ cập nhật và giờ yên tĩnh | Hành động thực đúng cấu hình, lịch được giữ qua reboot |
| U19-03 | Mạng ngắt giữa tải rồi nối lại | Resume chunk hợp lệ, chưa stage payload thiếu |
| U19-04 | Hash/chữ ký/metadata sai, cũ, hết hạn, bị thu hồi | Chặn 100%, không bypass UI/AI/API |
| U19-05 | Thiếu dung lượng, pin yếu, dual boot, mã hóa | Preflight chặn đúng, không xóa file |
| U19-06 | Có tài liệu NaMiOffice/NaMiPDF chưa lưu | Không reboot bất ngờ, chọn giờ khác |
| U19-07 | Kill service/mất điện ở download, stage, boot switch | Boot bản cũ hoặc recovery, journal không sai |
| U19-08 | Bản mới boot loop hoặc desktop crash | Tự rollback, report, không xóa rollback target |
| U19-09 | Migration dữ liệu không tương thích rollback | Chặn trước hoặc restore được từ backup đã thử |
| U19-10 | Bản mới lỗi Wi-Fi trên một model | Dừng ring, chẩn đoán đúng model, không ảnh hưởng ring khác |
| U19-11 | Cập nhật NaMiOffice/NaMiPDF riêng | App đổi version, OS giữ version, file người dùng còn |
| U19-12 | Firmware nằm trong danh sách mới | Không tự cài; yêu cầu xác nhận, pin/nguồn/model |
| U19-13 | Máy offline lâu và cập nhật bằng USB | Chỉ chấp nhận bundle có chain tin cậy/phù hợp |
| U19-14 | SmartAI bị tắt hoặc đề nghị bỏ chữ ký | Update vẫn hoạt động, đề nghị nguy hiểm bị từ chối |

Gate stable: không có ca làm mất dữ liệu, sai verifier, không thể boot/recovery trên máy đã chứng nhận hoặc tự reboot khi tài liệu chưa lưu. Ghi số liệu boot success, update success, rollback, thời gian phục hồi và mức ảnh hưởng mạng/ổ trên máy pilot; ngưỡng định lượng chốt sau baseline, không tạo số pass giả.

## 2. Prompt nguyên văn

> Hãy đọc Phụ lục 15 và Phụ lục 19 này. Kiểm kê repo NaMiOS, distro, package manager, bootloader, Update Center, backup, firmware path và thiết bị thử trước. Viết ADR chọn cơ chế staged OS update/rollback phù hợp nền thực; không coi OSTree là đã dùng khi repo chưa dùng.
>
> Triển khai luồng người dùng 01 trong Cài đặt: thông báo phiên bản mới, 4 chế độ, tải/kiểm/chọn giờ restart, lịch sử, thông báo lỗi tiếng Việt. Tạo Update Service theo state machine và API ở 02, không để UI hoặc SmartAI cài từ URL tùy ý.
>
> Làm vertical slice trên VM bằng signed test metadata (khóa test), một bản OS A → B, resume download, preflight, stage, reboot, health check, commit và fault injection để rollback B → A. Chứng minh dữ liệu thử không mất. Sau đó thử trên máy pilot x86_64, SSD/HDD, Wi-Fi, dual boot/mã hóa khi có thiết bị và cho từng loại app/firmware riêng. Không dùng khóa test cho production.
>
> Chạy U19-01–U19-14. Mỗi milestone giao commit, build, screenshot UI, video/trace rollback, log đã lọc, report pass/fail, các blocker và release gate. Nếu chưa có repo hoặc ISO, tạo prototype/state machine/test harness, ghi rõ chưa cập nhật máy thật. Không công bố “NaMiOS tự cập nhật an toàn” trước khi gate đạt.

## 3. Nguồn kỹ thuật tham khảo

- OSTree atomic rollbacks và deployments: https://ostreedev.github.io/ostree/atomic-rollbacks/ ; https://ostreedev.github.io/ostree/deployment/
- TUF security và metadata: https://theupdateframework.io/docs/security/ ; https://theupdateframework.io/docs/metadata/
- fwupd power/battery errors: https://fwupd.github.io/libfwupd/error.Error.html

Đây là lựa chọn tham khảo; quyết định cuối do ADR, repo và thử nghiệm phần cứng NaMiOS.
