#!/bin/bash
# NaMiOS — biên dịch LỚP PHỦ DỊCH tiếng Việt (vi_NM) từ .po -> .mo và đặt vào
# includes.chroot để live-build copy thẳng vào ảnh. Cơ chế: locale phủ riêng
# `vi_NM` (đường dẫn MỚI, không gói Debian nào sở hữu) + LANGUAGE=vi_NM:vi:en_US
# => per-message fallback: chuỗi NaMiOS thắng -> vi upstream -> tiếng Anh.
# Xem docs/l10n/UPSTREAM-VI-OVERLAY-SPEC.md §4.1 + §5.2.
#
# Chạy TRÊN BUILD HOST / runner CI (cần `gettext` = msgfmt), TRƯỚC khi lb build.
# KHÔNG cần gettext trong ảnh cuối (chỉ copy .mo tĩnh).
#
# Nguồn .po: translations/vi-overlay/po/<domain>.vi_NM.po
#   -> tên file (bỏ đuôi .vi_NM.po) PHẢI = đúng textdomain gettext của app,
#      nếu không .mo sẽ không được nạp (vd plasmanetworkmanagement.vi_NM.po).
# Đích .mo: distro/live-build/config/includes.chroot/usr/share/locale/vi_NM/LC_MESSAGES/<domain>.mo
#
# AN TOÀN (CLAUDE.md): set -euo pipefail; không curl|bash; không tải từ xa; chỉ
# dùng msgfmt đã cài. TOLERANT: 1 file .po hỏng -> cảnh báo to + bỏ qua, build
# tiếp các file hợp lệ; cuối in tổng + danh sách hỏng (exit 0 để không chặn ảnh).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/translations/vi-overlay/po"
OUT="$ROOT/distro/live-build/config/includes.chroot/usr/share/locale/vi_NM/LC_MESSAGES"

if ! command -v msgfmt >/dev/null 2>&1; then
    echo "LỖI: không có 'msgfmt' (gói gettext). Cài: apt-get install -y gettext" >&2
    exit 1
fi

if [ ! -d "$SRC" ]; then
    echo "namios-l10n: không thấy $SRC — chưa có .po overlay nào, bỏ qua." >&2
    exit 0
fi

mkdir -p "$OUT"
# Dọn .mo cũ để không giữ lại domain đã xoá (idempotent).
rm -f "$OUT"/*.mo 2>/dev/null || true

# Lấy danh sách textdomain ĐÍCH cho 1 file .po:
#   1) header "X-NaMiOS-Source-Domains:" (nhiều domain — file hợp nhất, 1 app/
#      KCM một domain; vd plasma-nm gồm 4 domain) -> copy .mo cho TỪNG domain.
#   2) header "X-NaMiOS-Gettext-Domain:" (một domain thật, khác tên file;
#      vd kscreen -> kcm_kscreen).
#   3) fallback: tên file (bỏ .vi_NM.po) = domain.
# msgctxt trong .mo đảm bảo mỗi app chỉ khớp chuỗi của mình -> mục thừa vô hại.
target_domains() {
    local po="$1" line=""
    line="$(grep -m1 -E 'X-NaMiOS-Source-Domains:' "$po" 2>/dev/null || true)"
    [ -z "$line" ] && line="$(grep -m1 -E 'X-NaMiOS-Gettext-Domain:' "$po" 2>/dev/null || true)"
    if [ -n "$line" ]; then
        # cắt sau dấu ':' đầu, bỏ \n" cuối + nháy + dấu phẩy -> danh sách word.
        printf '%s' "$line" \
            | sed -E 's/.*(X-NaMiOS-Source-Domains|X-NaMiOS-Gettext-Domain):[[:space:]]*//' \
            | sed -E 's/\\n.*$//; s/".*$//; s/,/ /g'
    else
        basename "$po" .vi_NM.po
    fi
}

n_ok=0
n_fail=0
n_mo=0
total_tr=0
failed_list=""
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

shopt -s nullglob
for po in "$SRC"/*.vi_NM.po; do
    base="$(basename "$po" .vi_NM.po)"
    tmpmo="$TMP/$base.mo"
    # msgfmt --statistics in "N translated messages" ra stderr -> bắt lấy để báo.
    if stats="$(msgfmt --check-format --check-domain --statistics "$po" -o "$tmpmo" 2>&1)"; then
        tr="$(printf '%s\n' "$stats" | grep -oE '[0-9]+ translated' | grep -oE '[0-9]+' | head -1 || true)"
        tr="${tr:-0}"
        total_tr=$((total_tr + tr))
        n_ok=$((n_ok + 1))
        doms="$(target_domains "$po")"
        dom_show=""
        for d in $doms; do
            [ -n "$d" ] || continue
            cp -f "$tmpmo" "$OUT/$d.mo"
            n_mo=$((n_mo + 1))
            dom_show="$dom_show $d.mo"
        done
        printf '  [OK]   %-28s %4s chuỗi ->%s\n' "$base" "$tr" "$dom_show"
    else
        n_fail=$((n_fail + 1))
        failed_list="$failed_list $base"
        printf '  [HỎNG] %-28s msgfmt lỗi:\n' "$base"
        printf '%s\n' "$stats" | sed 's/^/           /'
    fi
done

echo "-----------------------------------------------------------"
echo "namios-l10n overlay vi_NM: $n_ok domain OK ($total_tr chuỗi dịch), $n_fail hỏng."
[ -n "$failed_list" ] && echo "   Hỏng:$failed_list (xem log trên, SỬA .po rồi chạy lại)."
echo "   .mo đặt tại: $OUT"
exit 0
