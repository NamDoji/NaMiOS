# NaMiOS

> Hệ điều hành miễn phí, mã nguồn mở cho người Việt. Nền Debian 13 + KDE + Wine, giao diện tiếng Việt, ưu tiên chạy các tác vụ thiết yếu của Word/Excel, Zalo, MISA và ứng dụng .NET theo **hồ sơ tương thích được kiểm chứng**.
>
> Tên làm việc trong đặc tả: **NaMiOS**. Đặc tả đầy đủ: [`docs/specs/DAC_TA_HE_DIEU_HANH.md`](docs/specs/DAC_TA_HE_DIEU_HANH.md).

**Nguyên tắc số 1:** không có ISO giả, không nhãn "đạt" khi chưa có bằng chứng thật. Thiếu môi trường/bộ cài → ghi `blocked`, không bịa.

## Mốc & trạng thái

| Mốc | Nội dung | Build ở môi trường hiện tại? |
|-----|----------|------------------------------|
| M0 | Inventory, ADR, threat model, kế hoạch, phân rã công việc | ✅ Được |
| M1 | Lõi phần mềm Python: validator 2 tầng, CLI doctor, state/journal, catalog, security/redaction, evidence model | ✅ Được (venv + pytest) |
| M2 | Wine/.NET runner + prefix + sandbox proof | ⛔ BLOCKED — cần Linux host có nested-virt + wine |
| M3 | ISO live-build + desktop tiếng Việt + boot/install QEMU | ⛔ BLOCKED — cần live-build + qemu/KVM |
| M4 | App thương mại (Office/Zalo/MISA/.NET), hardware pilot | ⛔ BLOCKED — cần bộ cài có quyền dùng + máy pilot |
| M5 | Governance phát hành, ký/thu hồi, EOL | sau G2 |

Gate: **G0** khả thi → **G1** alpha kỹ thuật → **G2** pilot nghiệp vụ → **G3** phát hành công khai.

## Đội ngũ (agent fleet)

| Pha | Đội | Model | Đầu ra |
|-----|-----|-------|--------|
| M0 | 2 chuyên gia phân tích (BA) | Opus | `docs/STATUS.md`, `docs/assumptions.md`, `docs/adr/`, `docs/specs/M1-INTERFACES.md`, QA plan, phân rã 10 gói M1 |
| M1 | 10 dev | Sonnet | `src/` — mỗi dev một module, worktree cô lập |
| QA | 5 tester | — | `tests/` + `qa/evidence-index/` — xác minh độc lập, ưu tiên negative/adversarial |

Quy tắc kỹ thuật & non-negotiables: [`CLAUDE.md`](CLAUDE.md).

## Cấu trúc
Theo §19 đặc tả: `src/namios_*`, `contracts/`, `catalog/`, `tests/{unit,integration,system,security}`, `qa/`, `distro/live-build`, `packaging/debian`, `docs/{specs,adr,runbooks,releases}`.

## Đóng góp & cộng đồng

NaMiOS là dự án cộng đồng — mọi đóng góp đều được hoan nghênh:

- **Bắt đầu từ đâu:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (bản đồ module + bất biến) → [`CONTRIBUTING.md`](CONTRIBUTING.md) (dựng môi trường + cổng chất lượng).
- **Báo cáo app Windows chạy ra sao:** đóng góp quý nhất — [`docs/community/COMPATIBILITY-CONTRIBUTION.md`](docs/community/COMPATIBILITY-CONTRIBUTION.md). Lưu ý: "máy mình chạy ngon" là *phản hồi chưa kiểm*, chưa phải *chứng nhận*.
- **Ứng xử:** [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). **Bảo mật:** báo riêng theo [`docs/SECURITY.md`](docs/SECURITY.md), không mở issue công khai.

Cổng chất lượng (CI): `ruff check src` · `black --check src` · `mypy src/namios_core` · `pytest`.
