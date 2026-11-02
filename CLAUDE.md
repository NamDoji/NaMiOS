# NaMiOS — quy tắc kỹ thuật cho agent

**Thương hiệu/repo:** NaMiOS. **Tên làm việc trong đặc tả:** VietDesk OS (giữ nguyên để truy vết requirement IDs; namespace code hiện là `vietdesk_*`, có thể rebrand sau bằng một pass cơ học).

## Nguồn sự thật
- Đặc tả chính (BẮT BUỘC đọc trước khi code): `docs/specs/DAC_TA_HE_DIEU_HANH.md`.
- Bộ tài liệu gốc (prompt giao việc, backlog, test matrix, contracts): `docs/spec-package/`.
- Hợp đồng dữ liệu: `contracts/*.json`.
- Inventory môi trường M0: `docs/_m0_inventory_raw.md`.
- Trạng thái thật: `docs/STATUS.md` (do pha M0 tạo). Quyết định: `docs/adr/`. Việc còn lại: backlog.

## Môi trường build hiện tại (sự thật, 02/11/2026)
Debian 12, python 3.11, git, node — **CÓ**. qemu/KVM/wine/live-build/debootstrap/xorriso — **KHÔNG**. `/dev/kvm` **vắng**.
→ **M0 + M1 (lõi Python thuần) làm được ở đây.** M2 (Wine/.NET), M3 (ISO/boot), M4 (app thương mại) **BLOCKED** — cần build host Linux amd64 có nested-virt + bộ cài có quyền dùng do chủ dự án cấp. Ghi `blocked_external_dependency`, KHÔNG giả lập để báo đạt.

## Điều kiện KHÔNG được bỏ qua (từ đặc tả)
- Không root Wine; không `shell=True`, `eval`, `curl|bash`, manifest chứa shell/URL-script/template nội suy. Truyền tham số bằng argv; kiểm soát path/symlink/TOCTOU/race/permission (FD-based, không chỉ check chuỗi `..`).
- Prefix KHÔNG phải sandbox. Bảo vệ home/credentials/DB; mọi ngoại lệ display/clipboard/device/network phải ghi + test.
- Validation 2 tầng: JSON Schema (cấu trúc) + **semantic validator** (chặn profile TBD, runner chưa pin, dependency chưa duyệt, unknown keys, chứng nhận thiếu evidence, hash/revocation). "Schema hợp lệ" ≠ "an toàn để chạy".
- Không bypass license/activation; không nhúng key/secret/installer thương mại/DB thật/prefix có token vào repo.
- `task_verified` chỉ khi đủ evidence cho đúng tuple (app-mode-version) **và** có QA phê duyệt độc lập. Mock/stub KHÔNG phải bằng chứng app chạy.
- Không tự gửi tin/liên hệ vendor/đăng nhập/mua license/upload/phát hành public. Thao tác local/reversible trong phạm vi được tiếp tục chủ động.

## Chuẩn hoàn thành task
Code chạy được trong môi trường ghi rõ; test liên quan đã chạy (pass **hoặc** blocked có lý do — không đổi skipped thành pass); docs/backlog cập nhật; không TODO giả làm chức năng; không secret trong source. JSON output có `api_version/operation_id/status/data/warnings/error`, không trộn log vào stdout JSON, exit code theo CLI-003.

## Quy ước đội agent (fleet)
- Mỗi dev sở hữu MỘT module, chỉ sửa trong thư mục module của mình + file được chỉ định; không đụng module người khác.
- Branch/worktree cô lập; interface chung do pha M0 chốt trong `docs/specs/M1-INTERFACES.md`.
- Tester xác minh độc lập (ưu tiên negative/adversarial) trước khi gộp; log evidence vào `qa/evidence-index/`.
