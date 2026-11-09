#!/bin/bash
# NaMiOS SmartAI — thư viện CHÍNH SÁCH (sourced helper cho namios-smartai).
#
# Mục đích: tách phần "mô hình an toàn" (kế hoạch ≤3 bước + mức chắc chắn + cổng
# chính sách + AUDIT + UNDO + đọc error-catalog.json) ra một file riêng, để sửa
# hành vi chính sách KHÔNG phải động vào 10 playbook đã có trong namios-smartai.
# namios-smartai `source` file này nếu có; nếu file vắng, namios-smartai vẫn chạy
# (nó tự định nghĩa stub). => thay đổi tối thiểu + hoàn tác được.
#
# ===================== BẤT BIẾN (khớp SMARTAI-ORCHESTRATOR §3-§4) ============
#   - Mặc định CHỈ ĐỌC. Chẩn đoán uỷ cho namios-chan-doan (U13-08).
#   - Hành động CÓ THAY ĐỔI (đổi cấu hình / cài backend / reset dịch vụ / xoá
#     queue / cấp quyền) BẮT BUỘC: (a) qua policy_classify, (b) hiện KẾ HOẠCH +
#     lệnh argv TĨNH + mức chắc chắn + cách HOÀN TÁC, (c) hỏi đồng ý, (d) chạy,
#     (e) KIỂM kết quả (read-only, nếu có VERIFY_CMD), (f) ghi AUDIT đã che bí
#     mật, (g) nêu UNDO (Timeshift cho thay đổi hệ thống).
#   - CHỈ argv tĩnh. KHÔNG eval, KHÔNG lệnh do AI/log/web sinh, KHÔNG curl|bash,
#     KHÔNG tải driver từ nguồn không tin cậy.
#   - Hoạt động OFFLINE và khi KHÔNG có LLM: toàn bộ hàm dưới là rule-based.
# ===========================================================================
#
# verified_on_host: NO — review bằng `bash -n` + đọc lại; chưa chạy qua lb build
# + máy thật. Audit log ghi vào thư mục state của người dùng (không cần root).

# Guard: nếu file bị CHẠY trực tiếp thay vì được source, không làm gì nguy hiểm.
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  printf '%s\n' "Đây là thư viện chính sách của NaMiOS SmartAI (sourced helper)." \
    "Hãy chạy 'namios-smartai' thay vì chạy trực tiếp file này." >&2
  exit 0
fi

# ---------------------------------------------------------------------------
# Hạ tầng dùng chung (giả định namios-smartai đã định nghĩa have(); nếu chưa,
# định nghĩa phòng hờ để lib tự đứng được khi test độc lập).
# ---------------------------------------------------------------------------
if ! declare -f have >/dev/null 2>&1; then
  have() { command -v "$1" >/dev/null 2>&1; }
fi

# Đường dẫn catalog lỗi máy-đọc (cài trong ISO ở /usr/share/namios). Cho phép
# override bằng NAMIOS_ERROR_CATALOG để test với fixture.
smartai_catalog_path() {
  local p
  for p in "${NAMIOS_ERROR_CATALOG:-}" \
           "/usr/share/namios/error-catalog.json"; do
    [ -n "$p" ] && [ -f "$p" ] && { printf '%s' "$p"; return 0; }
  done
  return 1
}

# Correlation id cho một phiên SmartAI — liên kết chẩn đoán→giải thích→hành động.
smartai_new_correlation_id() {
  local rnd
  rnd="${RANDOM:-0}${RANDOM:-0}"
  printf '%s-%s-%s' "$(date '+%Y%m%d-%H%M%S' 2>/dev/null || echo 00000000-000000)" \
    "$$" "$rnd"
}

# Thư mục state ghi được của người dùng (không cần root).
smartai_state_dir() {
  local d="${XDG_STATE_HOME:-${HOME:-/tmp}/.local/state}/namios"
  mkdir -p "$d" 2>/dev/null || d="/tmp"
  printf '%s' "$d"
}

# ---------------------------------------------------------------------------
# Che bí mật cho AUDIT log — cùng nguyên tắc error-codes.md §5:
# ưu tiên namios_security.redact_text (+ email/MAC); thiếu thì sed dự phòng.
# Nhận văn bản qua stdin, in ra stdout.
# ---------------------------------------------------------------------------
smartai_redact() {
  if have python3 && PYTHONPATH="/opt/namios" python3 -c "import namios_security" >/dev/null 2>&1; then
    PYTHONPATH="/opt/namios" python3 - <<'PYEOF' 2>/dev/null && return 0
import re, sys
from namios_security import redact_text
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_MAC_RE = re.compile(r"\b([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b")
data = sys.stdin.read()
data = redact_text(data)
data = _EMAIL_RE.sub("[REDACTED-EMAIL]", data)
data = _MAC_RE.sub("[REDACTED-MAC]", data)
sys.stdout.write(data)
PYEOF
  fi
  # Dự phòng (kém toàn diện hơn — giống redact_fallback của namios-chan-doan).
  # CÔNG KHAI (A4): cảnh báo MỘT LẦN mỗi phiên khi phải dùng bộ che yếu hơn
  # (thiếu /opt/namios hoặc python3). Trên ISO đã dựng thì namios_security có sẵn
  # -> nhánh python ở trên chạy, KHÔNG rơi vào đây. Ghi ra stderr nên không làm
  # bẩn chuỗi đã che.
  _nm_warn="${XDG_RUNTIME_DIR:-/tmp}/.namios-redact-fallback-warned"
  if [ ! -e "$_nm_warn" ]; then
    printf '%s\n' "⚠ NaMiOS: đang dùng bộ che bí mật DỰ PHÒNG (sed) — kém toàn diện hơn namios_security. Cần /opt/namios + python3 để dùng bộ đầy đủ." >&2
    : > "$_nm_warn" 2>/dev/null || true
  fi
  sed -E '
    /PRIVATE KEY/{ s/.*/[REDACTED-PRIVATE-KEY-LINE]/ }
    s/([Bb]earer)[[:space:]]+[A-Za-z0-9._=-]+/\1 [REDACTED]/g
    s/([Pp]assword|[Pp]asswd|[Pp]wd|[Ss]ecret|[Tt]oken|[Aa]pi[_-]?[Kk]ey|[Oo][Tt][Pp]|[Cc]ookie|[Cc]redential)[[:space:]]*[:=][[:space:]]*[^[:space:],;]+/\1=[REDACTED]/g
    s/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/[REDACTED-EMAIL]/g
    s#/home/[^/[:space:]]+#/home/[REDACTED]#g
    s/\b([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b/[REDACTED-MAC]/g
    s/\b(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3}|127\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\b/[REDACTED-IP]/g
  ' 2>/dev/null || cat
}

# ---------------------------------------------------------------------------
# AUDIT log — mỗi hành động (chạy/huỷ/bỏ qua) ghi MỘT dòng đã che bí mật.
# smartai_audit <tag> <command> <status> <rc> <class> <undo> <result_snippet>
#   status ∈ ran|cancelled|skipped|launched
# Ghi vào $state/smartai-audit.log; không làm sập tool nếu không ghi được.
# ---------------------------------------------------------------------------
smartai_audit() {
  local tag="${1:-}" cmd="${2:-}" status="${3:-}" rc="${4:--}" \
        class="${5:-}" undo="${6:-}" snippet="${7:-}"
  local dir file ts line
  dir="$(smartai_state_dir)"
  file="$dir/smartai-audit.log"
  ts="$(date '+%F %T %Z' 2>/dev/null || echo unknown)"
  # Một dòng, các trường ngăn bằng ' | ', đã che bí mật (cmd tĩnh nhưng snippet
  # có thể chứa output nhạy cảm -> che cả dòng cho chắc).
  line="$(printf 'ts=%s | corr=%s | tag=%s | status=%s | rc=%s | class=%s | cmd=%s | undo=%s | result=%s' \
      "$ts" "${SMARTAI_CORRELATION_ID:-?}" "$tag" "$status" "$rc" \
      "$class" "$cmd" "$undo" "$(printf '%s' "$snippet" | tr '\n' ' ')" \
    | smartai_redact)"
  printf '%s\n' "$line" >> "$file" 2>/dev/null || true
}

# Đọc nhanh N dòng audit gần nhất (cho mục "Lịch sử" trên UI/menu).
smartai_audit_tail() {
  local n="${1:-20}" file
  file="$(smartai_state_dir)/smartai-audit.log"
  if [ -f "$file" ]; then
    tail -n "$n" "$file" 2>/dev/null
  else
    printf '%s\n' "(chưa có lịch sử hành động nào — audit log trống)"
  fi
}

# ---------------------------------------------------------------------------
# Phân loại chính sách cho một hành động THAY ĐỔI. Đặt:
#   POLICY_CLASS       — mô tả loại thay đổi (tiếng Việt)
#   POLICY_UNDO_HINT   — gợi ý hoàn tác chuẩn theo loại
#   POLICY_PRIVILEGED  — yes nếu đi qua pkexec/polkit
# smartai_policy_classify <argv0> <cmd_display>
# ---------------------------------------------------------------------------
smartai_policy_classify() {
  local a0="${1:-}" disp="${2:-}"
  POLICY_CLASS=""; POLICY_UNDO_HINT=""; POLICY_PRIVILEGED="no"
  case "$a0 $disp" in
    pkexec*|*" pkexec "*)
      POLICY_PRIVILEGED="yes"
      case "$disp" in
        *systemctl*restart*|*systemctl*start*|*systemctl*stop*)
          POLICY_CLASS="reset DỊCH VỤ hệ thống (cần quyền quản trị qua pkexec)"
          POLICY_UNDO_HINT="dịch vụ tự chạy lại; nếu cần sâu hơn: Timeshift" ;;
        *apt*|*pkcon*install*|*dpkg*)
          POLICY_CLASS="CÀI/ĐỔI GÓI hệ thống (cần quyền quản trị)"
          POLICY_UNDO_HINT="hoàn tác về bản trước bằng Timeshift (U13-02)" ;;
        *timeshift*)
          POLICY_CLASS="mở công cụ KHÔI PHỤC (người dùng tự chọn điểm)"
          POLICY_UNDO_HINT="không bấm Restore là không đổi gì" ;;
        *)
          POLICY_CLASS="hành động CẦN QUYỀN quản trị (qua pkexec/polkit)"
          POLICY_UNDO_HINT="tuỳ hành động; thay đổi hệ thống: Timeshift" ;;
      esac ;;
    *systemctl*restart*|*systemctl*start*|*systemctl*stop*)
      POLICY_CLASS="reset DỊCH VỤ"
      POLICY_UNDO_HINT="dịch vụ tự chạy lại; nếu cần: Timeshift" ;;
    cancel*|*" cancel "*|*lprm*)
      POLICY_CLASS="XOÁ HÀNG ĐỢI in"
      POLICY_UNDO_HINT="không hoàn tác được lệnh in đã huỷ — chỉ cần In lại; cấu hình máy in không đổi" ;;
    nmcli*radio*|nmcli*networking*|nmcli*wifi*)
      POLICY_CLASS="BẬT/TẮT trạng thái mạng (tạm thời, không lưu lâu dài)"
      POLICY_UNDO_HINT="bật lại trạng thái cũ; không có cấu hình lâu dài để hoàn tác" ;;
    fcitx5*|*ibus*restart*)
      POLICY_CLASS="khởi động lại BỘ GÕ trong phiên người dùng"
      POLICY_UNDO_HINT="đăng xuất/đăng nhập lại là trạng thái sạch; không đụng hệ thống" ;;
    *)
      POLICY_CLASS="thay đổi cục bộ"
      POLICY_UNDO_HINT="nếu cần, bật lại trạng thái cũ như mô tả" ;;
  esac
}

# ---------------------------------------------------------------------------
# KẾ HOẠCH tối đa 3 bước, mỗi bước kèm bằng chứng + mức chắc chắn.
# Dùng:
#   smartai_plan_reset
#   smartai_plan_add "<nhãn bước>" "<bằng chứng>" "<cao|vừa|thấp>"   # ≤3 bước
#   smartai_plan_render   # trả chuỗi KẾ HOẠCH (dùng cho show_text)
# Bước thứ 4 trở đi bị TỪ CHỐI (in cảnh báo) — ép bất biến "tối đa 3 bước".
# ---------------------------------------------------------------------------
SMARTAI_PLAN_STEPS=()
smartai_plan_reset() { SMARTAI_PLAN_STEPS=(); }
smartai_plan_add() {
  local label="${1:-}" evidence="${2:-theo chẩn đoán chỉ đọc + triệu chứng bạn mô tả}" \
        conf="${3:-vừa}"
  if [ "${#SMARTAI_PLAN_STEPS[@]}" -ge 3 ]; then
    # Bất biến: không cho kế hoạch phình quá 3 bước.
    return 1
  fi
  case "$conf" in cao|vừa|thấp) : ;; *) conf="vừa" ;; esac
  SMARTAI_PLAN_STEPS+=( "${label}"$'\x1f'"${evidence}"$'\x1f'"${conf}" )
  return 0
}
smartai_plan_render() {
  local i=0 out="KẾ HOẠCH (tối đa 3 bước — SmartAI chỉ đề xuất, bạn quyết):" s
  if [ "${#SMARTAI_PLAN_STEPS[@]}" -eq 0 ]; then
    printf '%s\n' "(chưa có bước nào)"
    return 0
  fi
  for s in "${SMARTAI_PLAN_STEPS[@]}"; do
    i=$((i+1))
    local label evidence conf
    label="${s%%$'\x1f'*}"
    conf="${s##*$'\x1f'}"
    evidence="${s#*$'\x1f'}"; evidence="${evidence%$'\x1f'*}"
    out="${out}"$'\n'"  ${i}) ${label}"$'\n'"     • Bằng chứng: ${evidence}"$'\n'"     • Mức chắc chắn: ${conf}"
  done
  printf '%s\n' "$out"
}

# ---------------------------------------------------------------------------
# Tra catalog theo cause_code. Đặt (khi tìm thấy):
#   CATALOG_FOUND=yes ; CATALOG_PHASE ; CATALOG_MSG ; CATALOG_CONFIDENCE
#   CATALOG_ACTIONS (nhiều dòng "nhãn [kind] — lệnh")
# Degrade: thiếu catalog/python3/jq -> CATALOG_FOUND=no (tool vẫn chạy rule-based).
# smartai_catalog_lookup <cause_code>
# ---------------------------------------------------------------------------
smartai_catalog_lookup() {
  local code="${1:-}" cat out
  CATALOG_FOUND="no"; CATALOG_PHASE=""; CATALOG_MSG=""; CATALOG_ACTIONS=""
  CATALOG_CONFIDENCE=""
  cat="$(smartai_catalog_path)" || return 1
  [ -n "$code" ] || return 1

  if have python3; then
    out="$(python3 - "$cat" "$code" 2>/dev/null <<'PYEOF'
import json, sys
try:
    cat, code = sys.argv[1], sys.argv[2]
    d = json.load(open(cat, encoding="utf-8"))
except Exception:
    sys.exit(2)
e = d.get("entries", {}).get(code)
if not e:
    sys.exit(3)
print("PHASE\t" + str(e.get("phase", "")))
print("CONF\t" + str(e.get("default_confidence", "")))
print("MSG\t" + str(e.get("message_vi", "")).replace("\n", " "))
for a in e.get("safe_actions", []):
    print("ACT\t%s\t%s\t%s" % (a.get("label_vi", ""), a.get("kind", ""),
                               a.get("command", "")))
PYEOF
)"
    [ -z "$out" ] && return 1
    local line k v f1 f2 f3
    while IFS= read -r line; do
      k="${line%%$'\t'*}"; v="${line#*$'\t'}"
      case "$k" in
        PHASE) CATALOG_PHASE="$v" ;;
        CONF)  CATALOG_CONFIDENCE="$v" ;;
        MSG)   CATALOG_MSG="$v" ;;
        ACT)
          f1="${v%%$'\t'*}"; v="${v#*$'\t'}"
          f2="${v%%$'\t'*}"; f3="${v#*$'\t'}"
          if [ -n "$f3" ]; then
            CATALOG_ACTIONS="${CATALOG_ACTIONS}  • ${f1} [${f2}] — ${f3}"$'\n'
          else
            CATALOG_ACTIONS="${CATALOG_ACTIONS}  • ${f1} [${f2}]"$'\n'
          fi ;;
      esac
    done <<EOF
$out
EOF
    CATALOG_FOUND="yes"
    return 0
  elif have jq; then
    CATALOG_PHASE="$(jq -r --arg c "$code" '.entries[$c].phase // empty' "$cat" 2>/dev/null)"
    [ -z "$CATALOG_PHASE" ] && return 1
    CATALOG_CONFIDENCE="$(jq -r --arg c "$code" '.entries[$c].default_confidence // empty' "$cat" 2>/dev/null)"
    CATALOG_MSG="$(jq -r --arg c "$code" '.entries[$c].message_vi // empty' "$cat" 2>/dev/null)"
    CATALOG_ACTIONS="$(jq -r --arg c "$code" '.entries[$c].safe_actions[]? | "  • \(.label_vi) [\(.kind)]" + (if .command != "" then " — \(.command)" else "" end)' "$cat" 2>/dev/null)"
    CATALOG_FOUND="yes"
    return 0
  fi
  return 1
}
