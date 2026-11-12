#!/bin/sh
# NaMi — mở thư mục "Tài liệu" của người dùng cho icon desktop "Tài liệu của tôi".
# Tách ra script riêng để KHÔNG phải nhồi lệnh nhiều nháy-lồng vào Exec= của
# file .desktop (bộ parse Desktop Entry hiểu nháy khác shell -> lỗi cú pháp,
# đúng lỗi pilot 12/11/2026 trên máy thật). Dò theo thứ tự: XDG_DOCUMENTS_DIR
# (xdg-user-dirs, tôn trọng bản địa hoá) -> ~/Documents -> ~/Tài liệu -> ~.
set -eu
d=""
if command -v xdg-user-dir >/dev/null 2>&1; then
  d="$(xdg-user-dir DOCUMENTS 2>/dev/null || true)"
fi
[ -n "$d" ] && [ -d "$d" ] || d="$HOME/Documents"
[ -d "$d" ] || d="$HOME/Tài liệu"
[ -d "$d" ] || d="$HOME"
exec dolphin "$d"
