#!/bin/sh
# NaMiOS — ĐỀ XUẤT (CHƯA GHÉP VÀO includes.chroot). Mục tiêu: BẬT KWin
# compositing (OpenGL) CHỈ khi phiên đang chạy trên máy/VM CÓ GPU thật,
# để giữ nguyên hành vi an toàn hiện có (kwinrc mặc định Compositing
# Enabled=false + OpenGLIsUnsafe=true, xem distro/live-build/config/
# includes.chroot/etc/skel/.config/kwinrc) cho mọi trường hợp KHÔNG chắc
# chắn (QEMU/TCG, VM không GPU passthrough, lỗi phát hiện).
#
# FAIL-CLOSED: bất kỳ điều gì không chắc (thiếu lệnh, systemd-detect-virt
# báo lỗi, không có qdbus) => KHÔNG làm gì, giữ nguyên mặc định tắt compositing
# hiện có. Không bao giờ exit != 0 (không được chặn đăng nhập).
#
# verified_on_host: NO — cần boot thật (1) trong QEMU/TCG hiện tại để xác
# nhận script im lặng bỏ qua (compositing vẫn tắt), VÀ (2) trên máy thật có
# GPU (hoặc VM có GPU passthrough/virtio-gpu 3D) để xác nhận compositing
# được bật thật + KWin không crash + hiệu ứng (Blur/Contrast ở 01-kwinrc)
# hiển thị đúng. Thiếu bước (2) thì KHÔNG coi tính năng này là "đạt".
#
# AN TOÀN (CLAUDE.md): set -eu (không dùng pipefail vì dùng /bin/sh, không
# phải bash); KHÔNG curl|bash; KHÔNG eval nội dung tải về; chỉ gọi
# systemd-detect-virt + kwriteconfig6 + qdbus cục bộ, không có input từ xa.
set -eu

MARKER_DIR="$HOME/.config/namios"
MARKER="$MARKER_DIR/auto-compositing-applied"
SELF_DESKTOP="$HOME/.config/autostart/namios-auto-compositing.desktop"

# Chỉ áp dụng MỘT LẦN mỗi tài khoản (giống idiom namios-add-widgets.sh /
# namios-welcome: không muốn mỗi lần đăng nhập lại ghi đè lựa chọn người
# dùng tự đổi sau này trong Cài đặt > Hiệu ứng desktop).
mkdir -p "$MARKER_DIR" 2>/dev/null || exit 0
if [ -f "$MARKER" ]; then
  rm -f "$SELF_DESKTOP" 2>/dev/null || true
  exit 0
fi

# Cần kwriteconfig6 (gói kconfig, luôn có cùng Plasma 6) + systemd-detect-virt
# (gói systemd, luôn có trên Debian 13). Thiếu 1 trong 2 -> bỏ qua an toàn.
command -v kwriteconfig6 >/dev/null 2>&1 || exit 0
command -v systemd-detect-virt >/dev/null 2>&1 || exit 0

# systemd-detect-virt --vm: in tên công nghệ ảo hoá (vd "kvm","qemu") và
# exit 0 NẾU đang trong VM; in "none" + exit 1 NẾU là máy thật (bare-metal).
# Dùng --vm (không phải mặc định) để KHÔNG tính nhầm container (vd nếu sau
# này NaMiOS chạy trong container nào đó, đó không phải là "không GPU" theo
# nghĩa của quyết định này — chỉ quan tâm ranh giới VM-không-GPU vs máy thật).
#
# Nguồn: systemd-detect-virt(1) — xem thêm
# https://github.com/systemd/systemd/blob/main/man/systemd-detect-virt.xml
if systemd-detect-virt --vm --quiet; then
  # ĐANG LÀ VM — fail-closed: không đụng gì, không ghi marker (để lần đăng
  # nhập sau, nếu đổi sang máy thật, vẫn còn cơ hội chạy lại). Tự dọn
  # autostart cũng KHÔNG làm ở đây để logic này áp dụng lại mỗi lần đăng
  # nhập cho tới khi gặp máy thật.
  exit 0
fi

# TỪ ĐÂY: KHÔNG phải VM theo systemd-detect-virt (giả định có GPU thật hoặc
# VM có GPU passthrough đủ tốt). Bật compositing.
#
# Quan trọng: phải đổi CẢ HAI khoá — Enabled=true KHÔNG đủ nếu OpenGLIsUnsafe
# vẫn true (cờ này là chốt an toàn riêng của KWin, từng thấy KWin tự ghi true
# sau một lần compositing crash; NaMiOS cũng đặt true thủ công cho máy ảo).
kwriteconfig6 --file kwinrc --group Compositing --key Enabled true
kwriteconfig6 --file kwinrc --group Compositing --key OpenGLIsUnsafe false

# Yêu cầu KWin áp dụng lại cấu hình (reconfigure qua D-Bus) thay vì
# logout/login. Thử qdbus6 trước, rồi các biến thể cũ hơn; nếu không có cái
# nào, compositing vẫn đã ghi vào kwinrc và sẽ có hiệu lực ở lần đăng nhập
# kế tiếp (không mất tác dụng, chỉ là chậm hơn 1 phiên).
QB=""
for q in qdbus6 qdbus-qt6 qdbus; do
  command -v "$q" >/dev/null 2>&1 && QB="$q" && break
done
if [ -n "$QB" ]; then
  "$QB" org.kde.KWin /KWin org.kde.KWin.reconfigure >/dev/null 2>&1 || true
fi

# Đánh dấu đã áp dụng + tự xoá autostart (không chạy lại mỗi lần đăng nhập).
touch "$MARKER" 2>/dev/null || true
rm -f "$SELF_DESKTOP" 2>/dev/null || true
exit 0
