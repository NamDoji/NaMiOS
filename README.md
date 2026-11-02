# NaMiOS

> Hệ điều hành miễn phí cho người Việt — mã nguồn mở, có chiều sâu kỹ thuật và tính cộng đồng.
> Mục tiêu: chạy được trên số lượng người dùng thật, tương thích với phần mềm người dùng đang sử dụng.

**Trạng thái:** 🟡 Khởi tạo workspace — chờ *file yêu cầu* từ anh Cường để chốt phạm vi và bắt đầu pha đặc tả.

---

## Mô hình đội ngũ (agent fleet)

Dự án được tổ chức theo pipeline nhiều lớp agent, chạy tuần tự qua các pha:

| Pha | Đội | Model | Đầu ra |
|-----|-----|-------|--------|
| 1. Đặc tả | 2 chuyên gia phân tích nghiệp vụ (BA) | Opus | `docs/spec/` — tài liệu đặc tả, kiến trúc, phạm vi |
| 2. Phát triển | 10 dev | Sonnet | `src/` — code theo module được chia sẻ, mỗi dev một vùng sở hữu |
| 3. Kiểm thử | 5 tester | — | `tests/` — test + báo cáo lỗi, cổng tích hợp (integration gate) |

Nguyên tắc: mỗi dev làm trên vùng module riêng (tránh giẫm chân), tích hợp qua cổng review; tester xác minh độc lập trước khi gộp.

## Cấu trúc thư mục

- `docs/spec/` — tài liệu đặc tả do 2 BA Opus soạn
- `docs/research/` — nghiên cứu nền (SOTA các distro, compat layer…)
- `src/` — mã nguồn
- `tests/` — kiểm thử
- `.fleet/` — ghi chú điều phối đội agent (module ownership, log pha)

## Nguyên tắc cốt lõi

1. Chính xác & có chiều sâu — không làm ẩu.
2. Phải chạy được trên người dùng thật ở quy mô.
3. Mã nguồn mở, tính cộng đồng.
4. Bàn phương án/SOTA trước khi build lớn.
