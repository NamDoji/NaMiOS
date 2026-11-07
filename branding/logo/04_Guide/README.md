# NaMiOS Logo Standard v1.0 — Sen bừng sáng

**Ngày đóng gói:** 07/11/2026. **Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam.  
**Phạm vi:** bộ file chuẩn kỹ thuật của **phương án hoa sen đã được chọn để chuẩn hóa**. Đây chưa phải chứng nhận đăng ký nhãn hiệu hoặc kết luận độc quyền.

## Mở file nào?

| Nhu cầu | File ưu tiên |
| --- | --- |
| Logo ngang trên nền sáng | `01_Master/NaMiOS_Logo_Master_Outlined.svg` |
| Logo ngang trên nền tối | `01_Master/NaMiOS_Logo_Master_Outlined_Dark.svg` |
| Chỉ hình sen, nền trong suốt | `01_Master/NaMiOS_Symbol_Color.svg` |
| Icon hệ điều hành/kho ứng dụng | `02_Icons/NaMiOS_App_Icon_Master.svg` |
| Icon 16–32 px | `02_Icons/NaMiOS_App_Icon_Small_Master.svg` hoặc PNG đúng cỡ |
| In một màu trên nền sáng | `01_Master/NaMiOS_Symbol_OneColor_Dark.svg` |
| In một màu trên nền tối | `01_Master/NaMiOS_Symbol_OneColor_White.svg` |
| Web favicon | `02_Icons/NaMiOS_Favicon.ico` |
| Xem trước | `04_Guide/NaMiOS_Logo_Standard_Preview.png` |

Các file `Master_Outlined` đã chuyển chữ thành **vector path**, không cần máy nhận có font Noto Sans. File `Editable_Text` giữ chữ chưa outline để nhà thiết kế sửa tên nếu cần; **không dùng nó làm bản phát hành**.

## Hình và màu

Biểu tượng gồm 5 cánh: giữa vàng như ánh sáng, hai cánh san hô như lửa, hai cánh xanh ngọc ngoài cùng tạo dáng V. Không thêm sao/cờ hoặc mô tả NaMiOS như sản phẩm được cơ quan Nhà nước bảo trợ. Không tuyên bố hoa sen là biểu tượng quốc gia được chỉ định chính thức.

| Vai trò | Tham chiếu |
| --- | --- |
| Nền icon | `#254A60` → `#0B2034` |
| Cánh vàng | `#FFE1A1` → `#E5A53E` |
| Cánh san hô | `#FF8B6C` → `#D94D43` |
| Cánh xanh ngọc | `#64C3AA` → `#168A82` |
| Chữ nền sáng | `#172C3D`; chữ “OS” `#168D82` |
| Chữ nền tối | `#F7F6F1`; chữ “OS” `#75D9C4` |

## Quy tắc sử dụng

1. Giữ khoảng trống quanh toàn logo tối thiểu bằng **1/8 chiều cao biểu tượng sen** ở bốn phía. Không bóp méo, xoay, đổi thứ tự cánh, đặt thêm chữ trong hình sen hoặc tô một màu lạ cho từng cánh.
2. Trên màn hình, logo ngang nên rộng **ít nhất 240 px**; dưới ngưỡng này dùng biểu tượng riêng. Icon dưới **48 px** dùng bản màu phẳng `Small_Master`, không thu trực tiếp bản gradient 1024 xuống 16 px.
3. Nền ảnh cần đủ sạch để nhận chữ và cánh; nếu không, dùng nền đơn sắc. Bản tối phải có nền tối thật; không đặt chữ trắng trên nền sáng.
4. Bản một màu dùng cho in đơn sắc, dập nổi, khắc. Kiểm bản in thử ở kích thước thực; không tự suy từ bản PNG trên màn hình sang màu in CMYK. Nhà in chuyển màu theo profile vật liệu/thiết bị của họ, giữ một bản proof đã duyệt.
5. Không dùng hình sen tách rời để làm logo đối tác khi chưa ghi rõ nguồn/quan hệ; file logo không chứng minh quyền dùng tên của dịch vụ thứ ba.

## Chất lượng và bước còn cần

- SVG và PNG đã được kiểm bằng trình dựng hình, PNG có nền trong suốt khi cần, favicon có 16/32/48 px.
- Bản chuẩn kỹ thuật này **chưa** thay thử nhận diện với người Việt hoặc tra cứu nhãn hiệu tương tự. Trước phát hành thương mại, thử mù 3 giây ở 16/32/128 px, so với các logo hoa sen khác và kiểm pháp lý thương hiệu.
- Nếu người dùng không đọc ra hoa sen hoặc nhầm với logo một tổ chức khác, chỉnh hình master rồi xuất lại **toàn bộ** biến thể trong gói; tăng phiên bản thay vì sửa lẻ từng PNG.

## Cấu trúc thư mục

- `01_Master`: SVG vector nền sáng/tối, bản chỉ hình, một màu, và bản chữ chỉnh sửa.
- `02_Icons`: icon SVG, PNG 16–1024 px, favicon ICO.
- `03_Print`: PNG một màu để tham khảo proof in; SVG vector trong `01_Master` là nguồn in ưu tiên.
- `04_Guide`: bản xem nhanh, file này và manifest hash.
