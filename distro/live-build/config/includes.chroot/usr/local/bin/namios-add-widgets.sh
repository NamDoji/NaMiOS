#!/bin/sh
# NaMiOS — thêm widget desktop (Trợ lý AI) vào containment ĐANG CHẠY
# của Plasma qua evaluateScript. Lý do: pre-seed trong appletsrc KHÔNG ăn vì
# Plasma sinh activityId (UUID) lúc chạy → containment pre-seed bị bỏ. Cách đúng
# = gọi API scripting của plasmashell lúc đã đăng nhập. Chạy 1 lần rồi tự xoá
# autostart (máy cài thật chỉ thêm 1 lần; live ISO mỗi boot thêm lại — vô hại).
# verified_on_boot: NO — D-Bus tới plasmashell dưới QEMU/TCG có thể chậm/không ăn;
# trên máy thật chạy đúng. Idempotent-ish: chỉ thêm khi plasmashell trả lời.
#
# AN TOÀN: không curl|bash, không eval nội dung từ xa; chỉ gọi API Plasma cục bộ.
SELF="$HOME/.config/autostart/namios-widgets.desktop"
JS='var all = desktops();
for (var i = 0; i < all.length; i++) {
  var d = all[i];
  d.addWidget("org.namios.smartai");
}'

QB=""
for q in qdbus6 qdbus-qt6 qdbus; do
  command -v "$q" >/dev/null 2>&1 && QB="$q" && break
done
[ -z "$QB" ] && exit 0

i=0
while [ "$i" -lt 30 ]; do
  if "$QB" org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$JS" >/dev/null 2>&1; then
    rm -f "$SELF"
    exit 0
  fi
  i=$((i + 1))
  sleep 3
done
exit 0
