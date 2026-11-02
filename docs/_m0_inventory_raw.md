# M0 Inventory thô (host build hiện tại) — 02/11/2026

- Host: Debian GNU/Linux 12 (bookworm), kernel 5.14.0 (host RHEL9), x86_64, container.
- CPU: AMD EPYC-Rome 4 nhân. RAM: 7.5 GiB (≈5.8 available). Disk workspace: 169G, trống 70G.
- Toolchain CÓ: git 2.39.5, python 3.11.2, pip 26.2.1, venv, node v24.16.0.
- Toolchain THIẾU: qemu-system-x86_64, lb (live-build), debootstrap, mmdebstrap, xorriso, fakeroot, wine, winetricks, mkisofs.
- Ảo hóa: /dev/kvm ABSENT; CPU không có cờ vmx/svm → KHÔNG chạy nested VM/KVM ở đây.
- pytest: chưa cài (cài được qua pip trong venv).
- Mạng: egress tới github.com HTTP 200 (~0.1s) OK.

## Hệ quả cho mốc
- M0 (inventory/ADR/threat model/plan): CHẠY ĐƯỢC tại đây.
- M1 (lõi phần mềm Python thuần: validator, CLI doctor, state store, catalog, security/redaction, evidence model): CHẠY + TEST ĐƯỢC tại đây (venv + pytest).
- M2 (Wine/.NET fixture), M3 (ISO live-build/boot QEMU), M4 (app thương mại Office/Zalo/MISA): BLOCKED tại đây — thiếu KVM, wine, live-build, qemu, và bộ cài có quyền dùng. Cần build host Linux amd64 (bare-metal hoặc VM có nested virt) + bộ cài hợp lệ do chủ dự án cấp.
