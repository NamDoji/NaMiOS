# ADR 0002 — Nền Debian 13 amd64

- **Trạng thái:** proposed
- **Ngày:** 02/11/2026
- **Liên quan:** §5.1, §14, ADR 0001, ADR 0003; requirement BUILD-001, BUILD-002, BUILD-004

## Bối cảnh

Cần chọn một nền tảng distro ổn định, có công cụ tạo ảnh Live và cơ chế cập nhật có chữ ký, để giảm thay đổi nền và tránh tự viết package manager/installer.

## Quyết định

Chọn **Debian 13 trixie amd64** làm nền. Dùng Debian **live-build** để tạo ISO; dùng **APT + repo có chữ ký** cho cập nhật gói. **Pin snapshot** nguồn gói cho build tái tạo, đồng thời vẫn phát hành image mới có security update theo cadence. Trình cài đặt: **Calamares** nếu spike đạt, nếu không dùng đường cài Debian được kiểm thử.

## Lý do

- Debian stable giảm biến động nền; live-build cho phép tự động hóa cấu hình ảnh Live ([S10]).
- Debian 13 có vòng đời upstream được công bố ([S09]) — nhưng đây KHÔNG tự trở thành cam kết bảo trì của NaMiOS.

## Hệ quả

- Phải xác minh version KDE/Qt/Wine và mức hỗ trợ từng gói trong snapshot thực; không lấy vòng đời distro thay cho mọi thành phần.
- Không pin snapshot cũ vô thời hạn cho máy người dùng; snapshot chỉ để tái tạo build lịch sử.
- Bit-for-bit reproducible ISO là mục tiêu sau (BUILD-004); nếu còn sai khác do timestamps/mirror/tooling, ghi rõ, không gọi là reproducible byte-for-byte.

## Bối cảnh môi trường hiện tại (từ inventory M0)

- Host hiện tại là **Debian 12 bookworm**, **không phải** Debian 13 mục tiêu.
- **Thiếu** `lb` (live-build), `debootstrap`, `mmdebstrap`, `xorriso`, `fakeroot`, `mkisofs`; **thiếu** qemu + `/dev/kvm`.
- → Build ISO và boot test thuộc M3, hiện **BLOCKED** tại đây. Cần build host Linux amd64 sạch có đủ công cụ + (cho boot test) nested-virt.

## Spike cần làm + điều kiện chấp nhận

- **Spike:** cài sạch VM Debian 13; kiểm package availability (KDE/Qt/Wine/Fcitx5), runtime architecture, bộ gõ và installer; build 1 ISO từ host sạch + lockfile.
- **Điều kiện chấp nhận:** package list + versions thật được ghi vào build manifest (không version giả vào lockfile); ISO build được hoặc ghi blocked host rõ; Calamares tích hợp đạt, nếu không → ADR thay đổi trước triển khai.

## Nguồn

- [S09] Debian 13 trixie — https://www.debian.org/releases/trixie/
- [S10] Debian Live Manual — https://live-team.pages.debian.net/live-manual/html/live-manual.en.html
