# ADR 0010 — Chiến lược thiết bị và driver

- **Trạng thái:** proposed
- **Ngày:** 02/11/2026
- **Liên quan:** §27 (DEV-001..008), §30 (HWPLUS-001/002); test DEV-01..08, HWPLUS; backlog B040, B041; assumptions A67–A79
- **Bổ sung đặc tả:** SUPERSET §27 + §30 (delta vòng 2)

## Bối cảnh

Người dùng kỳ vọng "cắm là chạy" cho máy in, máy quét, USB token và thiết bị ngoại vi. Nhưng driver `.sys` kernel-mode của Windows KHÔNG mặc nhiên nạp/chạy trên nhân Linux [S17], và Wine là lớp chạy ứng dụng user-mode, KHÔNG phủ driver phần cứng. Cần chiến lược rõ ràng để tránh câu "mọi thiết bị kết nối đều chạy" khi chưa có ma trận model × chức năng + evidence.

## Quyết định

1. **Device DB (DEV-001):** cơ sở dữ liệu thiết bị khóa theo `vendor_id × product_id × revision × firmware × connection × kernel × driver/backend × license × tested_functions × support_status × verified_by`. Một nhà sản xuất có nhiều model → KHÔNG dùng kết quả model A để chứng nhận model B.
2. **Ưu tiên giao thức chuẩn:** in qua **IPP Everywhere / AirPrint / Mopria** trên CUPS [S14], thử **IPP over USB** cho máy in tương thích [S15]; scan qua **eSCL/AirScan / SANE / backend hợp lệ** theo model [S16]; token qua **PKCS#11 / PCSC** + driver Linux chính thức khi có. Thiết bị cũ có thể cần Printer Application hoặc driver Linux chính thức theo model.
3. **Nhận-diện ≠ chứng-nhận:** hiển thị USB ID / model chỉ là nhận diện; chỉ gắn nhãn hỗ trợ khi có evidence theo đúng model × chức năng. Khả năng *nhận máy in/scanner* và khả năng *in/scan đúng nghiệp vụ* là HAI phép thử khác nhau.
4. **Máy đa chức năng:** chứng nhận phần in và phần quét RIÊNG. **Thiết bị chuyên dụng** (máy in tem, POS...) nghiệm thu CÙNG phần mềm Windows điều khiển nó — hai tầng (thiết bị + app) phải cùng đạt.
5. **An toàn firmware/update (DEV-007):** KHÔNG flash firmware mặc định; firmware chỉ tải từ nguồn có quyền + kiểm chữ ký/hash theo hướng dẫn nhà cung cấp. Secure Boot phải kiểm module bên thứ ba + chuỗi chữ ký trên thiết bị thật. Cập nhật kernel/firmware/driver phải chạy lại test thiết bị có rủi ro; mất Wi-Fi/máy in sau cập nhật là lỗi CHẶN phát hành tới model đã chứng nhận.
6. **Không tải driver nguồn lạ**; truy cập token bằng user thường với quyền thiết bị hẹp.
7. **Trung tâm thiết bị (DEV-008):** tiếng Việt, nhãn "hoạt động đầy đủ / một phần / chưa kiểm thử / không hỗ trợ" theo **model × chức năng** + cách in/scan thử + driver/backend đang dùng + ngày chứng nhận. KHÔNG viết "đã hỗ trợ" khi mới nhận diện USB ID.
8. **USB token (DEV-005):** ma trận `hãng × model × firmware × middleware × trình duyệt × ứng dụng × nghiệp vụ`. Không cam kết ký số chạy chỉ vì token hiện trong `lsusb`; middleware Windows-only có thể buộc môi trường Windows hợp lệ (VM/remote có license). Chỉ ký ở **sandbox/giả lập**, không ký chứng từ pháp lý thật trong lab.

## Lý do

- Kernel-mode Windows driver [S17] không chạy trên Linux → chỉ con đường chuẩn (IPP/eSCL/SANE/PKCS#11) hoặc vendor-supported Linux mới bền.
- Khóa theo tuple model × chức năng ngăn kế thừa nhãn sai (model/firmware khác → đánh giá lại).
- Không flash firmware / không tải driver lạ bảo vệ máy người dùng và chuỗi chữ ký Secure Boot.

## Hệ quả

- Device DB + Trung tâm thiết bị là deliverable M3/M4; schema device record + semantic rule (chặn "supported" khi thiếu evidence) **viết + test được ở M1** bằng Python thuần.
- Lab ≥20 model (HWPLUS-001) là TARGET lập kế hoạch, KHÔNG thay yêu cầu ≥5 máy tính + ≥2 máy in ở §16.
- Lỗi in sai/thiếu nội dung hay sai chứng từ là **P0** cho workflow dùng chứng từ đó (HWPLUS-002).

## Bối cảnh môi trường hiện tại (từ inventory M0)

- Host Debian 12 container KHÔNG có thiết bị thật, KHÔNG có nested-virt. Schema device DB + validator + nhãn Trung tâm thiết bị: **M1 làm được**.
- In/scan/token/hotplug/sleep-resume/IPP-over-USB/in-từ-Wine/cập-nhật-kernel trên thiết bị thật (DEV-01..08, HWPLUS-002): **M4 BLOCKED** — cần lab ≥20 model + build host nested-virt + token/middleware hợp lệ. Ghi `blocked_external_dependency`.

## Spike cần làm + điều kiện chấp nhận

- **Spike S-DEV-1:** schema device record + nhập thử vài model giả → validator CHẶN gán `support_status=supported` khi thiếu `tested_functions`/evidence (mới chỉ có USB ID).
- **Spike S-DEV-2:** mô hình nhãn Trung tâm thiết bị theo model × chức năng; thử case "model A đạt, model B cùng hãng" → KHÔNG tự lan nhãn sang B.
- **Spike S-DEV-3 (khi có lab, M4):** DEV-02/03/04 in IPP + A4/A5/hai mặt/font Việt/QR + scan ADF; DEV-06 token sandbox (PIN sai/hết hạn/ngắt/phục hồi); DEV-08 chạy lại test sau cập nhật kernel.
- **Điều kiện chấp nhận:** không nhãn "hỗ trợ" nào tồn tại mà thiếu evidence đúng model × chức năng; không flash firmware/tải driver lạ; token không tạo chữ ký pháp lý thật trong lab; tests DEV-01..08 + HWPLUS `not_run` cho tới khi có lab.
