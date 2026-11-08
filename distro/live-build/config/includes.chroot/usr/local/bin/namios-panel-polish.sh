#!/bin/sh
# NaMiOS — ĐỀ XUẤT (CHƯA GHÉP). Canh GIỮA panel nổi (mục 3 yêu cầu: "panel
# nổi tinh chỉnh: ... canh giữa hoặc gọn"), dùng ĐÚNG cơ chế Plasma Scripting
# API (evaluateScript qua D-Bus) mà NaMiOS đã dùng cho widget SmartAI
# (xem usr/local/bin/namios-add-widgets.sh thật trong repo) — KHÔNG đoán số
# nguyên thô trong appletsrc (khoá "alignment" lưu dạng gì tuỳ phiên bản,
# API scripting .alignment="center" là cách CHÍNH THỨC/tài liệu hoá của
# KDE, an toàn hơn ghi thẳng ini).
#
# verified_on_host: NO — cần boot thật để xem panel thật sự canh giữa +
# không bị Plasma ghi đè lại giá trị ở lần đăng nhập kế (containment có
# thể đổi số index, xem comment "containment pre-seed có thể bị đánh số
# lại" trong appletsrc thật).
#
# AN TOÀN: set -eu; không curl|bash; không eval nội dung từ xa; JS truyền
# vào evaluateScript là literal cố định trong file này, không ghép biến
# người dùng/mạng.
set -eu

MARKER_DIR="$HOME/.config/namios"
MARKER="$MARKER_DIR/panel-polish-applied"
SELF_DESKTOP="$HOME/.config/autostart/namios-panel-polish.desktop"

mkdir -p "$MARKER_DIR" 2>/dev/null || exit 0
if [ -f "$MARKER" ]; then
  rm -f "$SELF_DESKTOP" 2>/dev/null || true
  exit 0
fi

# panel.alignment nhận "left" | "center" | "right" (tài liệu
# develop.kde.org/docs/plasma/scripting/api — API Panel, thuộc tính
# "alignment"). Không đổi panel.length/panel.height ở đây (giữ nguyên để
# tránh đụng bố cục icon dock/kickoff/systemtray đã dựng sẵn).
JS='var all = panels();
for (var i = 0; i < all.length; i++) {
  all[i].alignment = "center";
}'

QB=""
for q in qdbus6 qdbus-qt6 qdbus; do
  command -v "$q" >/dev/null 2>&1 && QB="$q" && break
done
[ -z "$QB" ] && exit 0

i=0
while [ "$i" -lt 30 ]; do
  if "$QB" org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$JS" >/dev/null 2>&1; then
    touch "$MARKER" 2>/dev/null || true
    rm -f "$SELF_DESKTOP" 2>/dev/null || true
    exit 0
  fi
  i=$((i + 1))
  sleep 3
done
exit 0

# ── GHI CHÚ TRUNG THỰC — "phóng icon dock khi hover" (mục 3, phần còn lại
# của yêu cầu): KHÔNG có cách nào làm việc này bằng CONFIG thuần với applet
# org.kde.plasma.icontasks đang dùng (plasma-org.kde.plasma.desktop-
# appletsrc thật, [Containments][1][Applets][3]). Xác nhận qua thảo luận
# chính thức KDE (discuss.kde.org "Please add zoom effect for icon only
# task manager"): đội Plasma CHỦ ĐỘNG không có ý định thêm hiệu ứng zoom
# kiểu macOS Dock vào Task Manager chuẩn. 2 hướng thay thế đều KHÔNG phải
# "chỉ config":
#   (a) Latte Dock — fork gốc ĐÃ NGỪNG phát triển, không chạy trên Plasma
#       6; có fork cộng đồng "Lattecotta Dock" port sang Plasma 6/Qt6 NHƯNG
#       CHỈ chạy Wayland (Wayland-only). NaMiOS hiện ép phiên X11
#       (Session=plasmax11 trong hook 0400, vì QEMU/TCG không GPU cần X11 +
#       software raster) — nghĩa là Lattecotta sẽ KHÔNG chạy được trong
#       kiến trúc hiện tại dù cài vào máy thật, trừ khi đổi hẳn sang phiên
#       Wayland mặc định (quyết định kiến trúc lớn hơn, cần ADR riêng,
#       NGOÀI phạm vi "config nhỏ" của yêu cầu này).
#   (b) Plasmoid Task Manager cộng đồng có zoom-on-hover (vd dự án GitHub
#       "GridyushkoF/MacOS-Like-dock-for-KDE-Plasma", "Rbanh/
#       plasma-taskmanager-zoom") — QML, không phải binary biên dịch nên
#       nhẹ rủi ro hơn Latte, nhưng vẫn là package/applet NGOÀI Debian
#       repos, chưa ai kiểm tra tương thích NaMiOS-Lotus icon theme + font
#       Việt, và đổi plugin= của Applets][3] là đổi ứng dụng chứ không còn
#       là "chỉnh config" nữa.
# ĐỀ XUẤT: bỏ qua "zoom-on-hover" ở wave này (gọn + canh giữa là đủ cho mục
# tiêu "nổi như iPadOS dock"); ghi lại thành mục backlog riêng nếu Cuong
# muốn theo hướng (b) sau khi có desktop thật để pilot-test.
