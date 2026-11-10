#!/bin/sh
# NaMiOS — demo lần đăng nhập ĐẦU: chứng minh BỘ GÕ TIẾNG VIỆT (fcitx5 + Unikey,
# kiểu Telex) cho ảnh chụp QEMU. Chạy 1 lần rồi tự xoá autostart của chính nó.
#
# LÝ DO TÁCH RA FILE SCRIPT (không nhét vào Exec= của .desktop nữa): trường Exec
# trong .desktop CẤM ký tự nháy kép " — bản demo cũ nhét `xdotool ... "KWrite"`
# vào Exec làm hỏng cú pháp .desktop -> autostart KHÔNG chạy (không cửa sổ nào
# hiện). Đưa logic ra script .sh thì .desktop chỉ cần Exec=<đường-dẫn>, hết lỗi.
#
# verified_on_host: NO — gõ tổng hợp (xdotool) qua fcitx tuỳ frontend Qt có bắt
# được phím XTEST không; nếu không chuyển được Telex -> chữ có dấu, vẫn còn 2 bằng
# chứng: (1) bảng điều khiển fcitx5 hiện engine Unikey tiếng Việt, (2) biểu tượng
# bộ gõ ở khay. AN TOÀN: không mạng, không tải gì, chỉ mở app sẵn có.

LOG=/tmp/namios-demo-ime.log
exec >"$LOG" 2>&1
echo "namios-demo-ime: bắt đầu $(date 2>/dev/null || true)"

# 1) Chờ Plasma ổn định
sleep 60

# 2) Bảo đảm fcitx5 chạy (để có biểu tượng khay + xử lý IME)
fcitx5 -d >/dev/null 2>&1 &
sleep 10

# 3) Mở bảng điều khiển bộ gõ — BẰNG CHỨNG CHẮC CHẮN: hiện engine Unikey (VN).
#    (re/-r reload cấu hình trước cho chắc)
fcitx5-remote -r >/dev/null 2>&1 || true
fcitx5-config-qt >/dev/null 2>&1 &
sleep 20

# 4) Mở trình soạn thảo để gõ thử Telex sống
EDITOR_BIN=kwrite
command -v kwrite >/dev/null 2>&1 || EDITOR_BIN=kate
"$EDITOR_BIN" >/dev/null 2>&1 &
sleep 25

# 5) Đưa focus vào trình soạn thảo
WIN=$(xdotool search --name 'KWrite' 2>/dev/null | head -n1)
[ -z "$WIN" ] && WIN=$(xdotool search --name 'Kate' 2>/dev/null | head -n1)
[ -z "$WIN" ] && WIN=$(xdotool search --class 'kwrite' 2>/dev/null | head -n1)
if [ -n "$WIN" ]; then
  xdotool windowactivate --sync "$WIN" 2>/dev/null || xdotool windowactivate "$WIN" 2>/dev/null
  sleep 2
fi

# 6) Gõ dòng nhãn (TẮT bộ gõ, ký tự UTF-8 nguyên văn) để chứng minh render dấu
fcitx5-remote -c 2>/dev/null || true
sleep 1
xdotool type --clearmodifiers --delay 110 'NaMiOS — bộ gõ tiếng Việt (fcitx5 + Unikey, kiểu Telex):'
xdotool key Return
sleep 1

# 7) BẬT Unikey rồi gõ Telex ASCII -> kỳ vọng ra tiếng Việt có dấu:
#    "Xin chào Việt Nam! Tôi gõ tiếng Việt bằng bộ gõ NaMiOS."
fcitx5-remote -s unikey 2>/dev/null || true
fcitx5-remote -o 2>/dev/null || true
sleep 2
xdotool type --clearmodifiers --delay 170 'Xin chaof Vieejt Nam! Tooi gox tieesng Vieejt bawfng booj gox NaMiOS.'
sleep 2

# 8) Giữ màn hình đủ lâu cho collector chụp
sleep 30

# 9) Tự xoá autostart để các lần đăng nhập sau không lặp lại
rm -f "$HOME/.config/autostart/namios-demo-first-login.desktop"
echo "namios-demo-ime: xong"
