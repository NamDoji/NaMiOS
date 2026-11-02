# Index runbook — NaMiOS

Runbook = hướng dẫn tái lập cho người vận hành/đội IT, khác với đặc tả (`docs/specs/`) và ADR (`docs/adr/`) vốn ghi quyết định/yêu cầu, không phải bước thao tác tay.

| Runbook | Phạm vi | Trạng thái |
| --- | --- | --- |
| [`BUILD-HOST-SETUP.md`](BUILD-HOST-SETUP.md) | Dựng build host Linux amd64 (Debian 13 trixie, nested-virt, `/dev/kvm`) để build ISO NaMiOS bằng Debian live-build + boot-test bằng QEMU; cài/xác minh toolchain (live-build, debootstrap/mmdebstrap, xorriso, squashfs-tools, qemu + OVMF, wine + winetricks, fakeroot); checklist map BUILD-001..003 + INSTALL-001/002. | `verified_on_host: NO` — soạn từ đặc tả + inventory M0 thật; CHƯA chạy hết trên build host thật. Script đi kèm `scripts/preflight-build-host.sh` đã chạy thật trên container agent (kết quả MISSING đúng với inventory M0). |

## Quy ước

- Mỗi runbook ghi rõ trạng thái `verified_on_host` ở đầu file: `NO` (chưa chạy trên host thật, chỉ soạn từ đặc tả) hoặc `YES — ngày/host/evidence` (đã chạy thật, có bằng chứng).
- Không runbook nào được tuyên bố "đã build ISO"/"đã boot" nếu không có evidence thật (build log, boot log, ảnh/video, checksum) — xem `docs/specs/DAC_TA_HE_DIEU_HANH.md` §18 (Chiến lược kiểm thử và bằng chứng).
- Khi một runbook được chạy thật trên build host, cập nhật dòng "Trạng thái" trong bảng trên và mục `verified_on_host` trong runbook, kèm liên kết evidence (ví dụ `qa/evidence-index/`).
