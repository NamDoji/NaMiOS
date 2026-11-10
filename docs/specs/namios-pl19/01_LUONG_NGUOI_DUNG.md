# 01. Luồng cập nhật người dùng nhìn thấy

## 1. Phát hiện và thông báo

NaMiOS kiểm tra định kỳ qua metadata đã xác thực, theo kênh stable/pilot phù hợp; có nút “Kiểm tra ngay”. Không thông báo khi chỉ thấy gói chưa đúng kiến trúc, bản bị thu hồi hoặc bản không áp dụng cho phần cứng. Một thông báo gọn có **phiên bản, lợi ích chính, mức độ khẩn, dung lượng, cần khởi động lại hay không, link xem thay đổi**. Sau khi người dùng bỏ qua, Update Center lưu thông báo và nhắc theo chính sách, không spam mỗi lần kiểm.

Ví dụ minh họa: “Có bản nâng cấp NaMiOS. Bản này sửa kết nối Wi-Fi và tăng độ an toàn. Cần khởi động lại để hoàn tất. [Xem thay đổi] [Cài tối nay] [Để sau]”. Không đưa số phiên bản/dung lượng giả vào sản phẩm; UI chỉ hiển thị dữ liệu manifest thật.

## 2. Bốn lựa chọn dễ hiểu

| Chế độ | Máy tự làm gì | Cần người dùng làm gì |
|---|---|---|
| Thông báo, tôi tự quyết định | Kiểm tra và thông báo | Bấm tải/cài, chọn giờ khởi động |
| Tự tải, hỏi trước khi cài (mặc định pilot) | Kiểm tra, tải khi mạng/ổ đủ, xác minh | Chọn cài ngay hoặc lịch cài |
| Tự cài bản an toàn | Cài bản ứng dụng/vá không cần reboot; chuẩn bị OS | Chọn hoặc chấp nhận lịch restart OS |
| Tự động theo lịch của tôi | Kiểm, tải, cài OS trong cửa sổ đã chọn | Chọn giờ yên tĩnh, mạng tính phí và quyền hoãn |

Cùng màn hình có tùy chọn “Tạm dừng đến ngày…”, giới hạn tải trên mạng tính phí, chỉ tải khi cắm sạc, giờ yên tĩnh và “Kiểm tra lịch sử”. Bản vá khẩn vẫn được thông báo dù đã tạm dừng tự cài; chính sách tổ chức có thể đặt thời hạn, phải hiển thị ai quản lý. Không dùng một công tắc “Tự động tất cả” bao gồm firmware.

## 3. Trước lúc cài

Màn hình xác nhận hiển thị: “Tệp cá nhân không bị xóa bởi thao tác nâng cấp OS; một số ứng dụng có thể cần chuyển dữ liệu. NaMiOS sẽ kiểm tra bản sao lưu/khả năng khôi phục.” Danh sách kiểm thực tế gồm dung lượng tải + bản staged + rollback, pin/nguồn, mã hóa ổ, bootloader/dual boot, mạng nếu chưa tải xong, ứng dụng/tài liệu chưa lưu, migration cần backup. Từng mục có Đạt/Chưa đạt và nút xử lý; không ép người mới hiểu thuật ngữ kỹ thuật.

Người dùng chọn **Cài ngay**, **Cài tối nay** hoặc **Để sau**. “Cài ngay” vẫn tải/xác minh/chuẩn bị rồi mới đề nghị khởi động; chưa gọi là “cập nhật xong”. Máy ghi giờ dự kiến và có thể nhắc trước restart. Nếu đang họp, in tài liệu, ký số, làm việc với file chưa lưu, hoãn theo policy. “Khởi động và cập nhật” chỉ khả dụng khi preflight đạt.

## 4. Trong và sau quá trình nâng cấp

Các trạng thái UI: Có bản mới → Đang tải → Đang xác minh → Sẵn sàng cài → Đang chuẩn bị → Cần khởi động lại → Đang kiểm tra bản mới → Hoàn tất / Đã khôi phục / Cần hỗ trợ. Thanh tiến trình phản ánh pha thật; không đứng ở 99% vô hạn, hiển thị thời gian ước lượng nếu đủ số liệu. Có nút tạm dừng tải, không có nút hủy trong pha boot switch không an toàn.

Sau boot, Update Center hiển thị phiên bản thực đang chạy, ngày cập nhật, trạng thái kiểm tra, changelog và “Xem lịch sử”. Nếu bản mới lỗi, thông báo “NaMiOS đã quay về bản trước vì không vượt qua kiểm tra khởi động. Tệp cá nhân cần được kiểm tra ở các ứng dụng có chuyển dữ liệu. [Xem báo cáo] [Liên hệ hỗ trợ]”. Không hứa dữ liệu chắc chắn nguyên vẹn nếu chưa kiểm. Có đường vào recovery từ boot menu và USB cứu hộ đã ký khi tự rollback không thành công.

## 5. Thông báo lỗi bằng tiếng Việt

| Tình huống | Nội dung ngắn | Hành động |
|---|---|---|
| Mất mạng | “Tải bị gián đoạn; NaMiOS sẽ tiếp tục từ phần đã xác minh.” | Thử lại, xem mạng |
| Thiếu dung lượng | “Cần thêm khoảng X GB để giữ cả bản cũ.” | Xem dung lượng, không tự xóa file cá nhân |
| Sai chữ ký/hash | “Bản cập nhật không vượt qua kiểm tra bảo mật; chưa cài.” | Báo sự cố, không có nút bỏ qua |
| Sai thiết bị | “Bản này chưa dành cho mẫu máy của bạn.” | Xem bản phù hợp, kiểm tra thiết bị |
| Chưa lưu việc | “Có tài liệu đang mở; hãy lưu trước khi khởi động.” | Mở ứng dụng, cài tối nay |
| Kiểm tra boot lỗi | “Đã quay lại phiên bản trước.” | Xem báo cáo, hỗ trợ |

SmartAI có thể giải thích release notes và mã lỗi tối đa vài bước, nhưng không được tự đổi chính sách, trust root, bỏ xác minh chữ ký, cài firmware hoặc xóa rollback target.
