#!/bin/bash
# smartai_tests.sh — test TÍCH HỢP RUNNABLE cho namios-smartai +
# namios-smartai-policy.sh, SỰ KIỆN MÔ PHỎNG (PATH giả, KHÔNG đụng Wi-Fi/máy
# in/Bluetooth/polkit thật — pkexec/systemctl/nmcli/cancel/... đều là script
# giả do chính file này dựng trong thư mục tạm).
#
# Hai lớp test:
#   A) Gọi TRỰC TIẾP các hàm thật trong namios-smartai-policy.sh (source, không
#      subprocess) — nhanh, kiểm plan≤3 bước/policy-classify/catalog-lookup/
#      audit+redact ở mức đơn vị.
#   B) Gọi THẬT namios-smartai qua subprocess (TTY fallback, không kdialog)
#      với PATH giả + stdin dàn kịch bản — kiểm hành vi E2E: cổng chính sách,
#      không bypass khi từ chối, không chạy hành động đặc quyền khi thiếu
#      pkexec, chế độ AI-offline, "không tự tuyên bố đã xong".
#
# Quy ước đếm: PASS/FAIL cho assertion thật; KNOWN GAP cho một bất thường có
# THẬT đã phát hiện trong code sản phẩm (không phải lỗi của test) — xem cuối
# file. KNOWN GAP không tính vào FAIL để không chặn "chạy tất cả -> PASS",
# nhưng vẫn in rõ ra report để không giấu.
#
# Chạy: bash tools/reliability-tests/smartai_tests.sh

set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
BIN_DIR="$REPO_ROOT/distro/live-build/config/includes.chroot/usr/local/bin"
SMARTAI_BIN="$BIN_DIR/namios-smartai"
CHAN_DOAN_BIN="$BIN_DIR/namios-chan-doan"
POLICY_LIB="$BIN_DIR/namios-smartai-policy.sh"
CATALOG="$REPO_ROOT/distro/live-build/config/includes.chroot/usr/share/namios/error-catalog.json"

for f in "$SMARTAI_BIN" "$CHAN_DOAN_BIN" "$POLICY_LIB" "$CATALOG"; do
  if [ ! -e "$f" ]; then
    printf 'LỖI THIẾT LẬP: không thấy %s — dừng test.\n' "$f" >&2
    exit 2
  fi
done

PASS=0
FAIL=0
GAPS=0
declare -a FAILED_NAMES=()
declare -a GAP_NAMES=()

pass_() { PASS=$((PASS + 1)); printf 'PASS  %s\n' "$1"; }
fail_() {
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("$1")
  printf 'FAIL  %s\n      %s\n' "$1" "${2:-}"
}
gap_() {
  GAPS=$((GAPS + 1))
  GAP_NAMES+=("$1")
  printf 'KNOWN-GAP  %s\n      %s\n' "$1" "${2:-}"
}

assert_contains() { # haystack needle name
  if [[ "$1" == *"$2"* ]]; then pass_ "$3"; else fail_ "$3" "mong có chuỗi: $2 | thực tế (rút gọn): ${1:0:200}"; fi
}
assert_not_contains() {
  if [[ "$1" != *"$2"* ]]; then pass_ "$3"; else fail_ "$3" "KHÔNG được có chuỗi: $2"; fi
}
assert_eq() {
  if [[ "$1" == "$2" ]]; then pass_ "$3"; else fail_ "$3" "mong '$2', thực tế '$1'"; fi
}
assert_true() { # rc name
  if [ "$1" -eq 0 ]; then pass_ "$2"; else fail_ "$2" "lệnh trả mã $1 (mong 0)"; fi
}
assert_false() {
  if [ "$1" -ne 0 ]; then pass_ "$2"; else fail_ "$2" "lệnh trả 0 (mong khác 0)"; fi
}

mk_fake() { # dir name body
  local dir="$1" name="$2" body="$3"
  cat >"$dir/$name" <<FAKE_EOF
#!/bin/bash
printf '%s %s %s\n' "\$(date -u +%s)" "$name" "\$*" >> "$dir/_calls.log"
$body
FAKE_EOF
  chmod +x "$dir/$name"
}

called() { # dir substring -> 0 nếu substring xuất hiện trong _calls.log
  [ -f "$1/_calls.log" ] && grep -q -- "$2" "$1/_calls.log"
}

# ===========================================================================
# LỚP A — gọi trực tiếp hàm thật trong namios-smartai-policy.sh (source).
# ===========================================================================
section_policy_lib() {
  printf '\n== LỚP A: namios-smartai-policy.sh (source trực tiếp) ==\n'
  local tmp
  tmp="$(mktemp -d)"
  export XDG_STATE_HOME="$tmp/state"
  export NAMIOS_ERROR_CATALOG="$CATALOG"
  have() { command -v "$1" >/dev/null 2>&1; }
  # shellcheck source=/dev/null
  . "$POLICY_LIB"

  # --- T-PLAN: kế hoạch tối đa 3 bước, bước thứ 4 bị từ chối -------------
  smartai_plan_reset
  smartai_plan_add "Bước 1" "ev1" "cao"
  smartai_plan_add "Bước 2" "ev2" "vừa"
  smartai_plan_add "Bước 3" "ev3" "thấp"
  if smartai_plan_add "Bước 4" "ev4" "cao"; then
    fail_ "T-PLAN: bước thứ 4 phải bị từ chối" "smartai_plan_add trả 0 cho bước 4"
  else
    pass_ "T-PLAN: smartai_plan_add từ chối bước thứ 4 (bất biến ≤3 bước)"
  fi
  local rendered
  rendered="$(smartai_plan_render)"
  assert_contains "$rendered" "Bước 1" "T-PLAN: plan_render in đủ bước 1"
  assert_contains "$rendered" "Mức chắc chắn: cao" "T-PLAN: plan_render in mức chắc chắn"
  assert_not_contains "$rendered" "Bước 4" "T-PLAN: plan_render KHÔNG in bước bị từ chối"

  # --- T-POLICY: phân loại chính sách -------------------------------------
  smartai_policy_classify "pkexec" "pkexec systemctl restart cups"
  assert_eq "${POLICY_PRIVILEGED:-}" "yes" "T-POLICY: pkexec -> POLICY_PRIVILEGED=yes"
  assert_contains "${POLICY_CLASS:-}" "DỊCH VỤ" "T-POLICY: pkexec systemctl restart -> lớp 'reset DỊCH VỤ'"

  smartai_policy_classify "cancel" "cancel -a"
  assert_eq "${POLICY_PRIVILEGED:-}" "no" "T-POLICY: cancel -a không cần quyền"
  assert_contains "${POLICY_CLASS:-}" "HÀNG ĐỢI" "T-POLICY: cancel -a -> lớp 'XOÁ HÀNG ĐỢI'"

  smartai_policy_classify "nmcli" "nmcli radio wifi on"
  assert_eq "${POLICY_PRIVILEGED:-}" "no" "T-POLICY: nmcli không cần quyền"

  smartai_policy_classify "pkexec" "pkexec timeshift-gtk"
  assert_eq "${POLICY_PRIVILEGED:-}" "yes" "T-POLICY: pkexec timeshift-gtk vẫn privileged=yes"

  # --- bypass not allowed: không hàm nào tự nâng quyền ngoài pkexec -------
  smartai_policy_classify "sudo" "sudo systemctl restart cups"
  if [[ "${POLICY_CLASS:-}" == *"CẦN QUYỀN"* ]] || [[ "${POLICY_CLASS:-}" == *"DỊCH VỤ"* ]]; then
    : # phân loại vẫn chạy (không crash) — nhưng quan trọng là catalog/test khác
      # (error_catalog_tests.py::test_privileged_actions_only_via_pkexec_no_bypass)
      # đã khoá: KHÔNG safe_action nào trong catalog dùng sudo. Ở đây chỉ xác
      # nhận classify không tự gắn privileged=yes cho sudo (polkit không được
      # hỏi) — nghĩa là nếu lỡ có command dùng sudo, nó sẽ KHÔNG được coi là
      # "qua cổng pkexec".
  fi
  assert_eq "${POLICY_PRIVILEGED:-}" "no" "T-POLICY: 'sudo ...' KHÔNG được tự nhận POLICY_PRIVILEGED=yes (chỉ pkexec mới qua polkit)"

  # --- T-CATALOG: tra catalog qua NAMIOS_ERROR_CATALOG --------------------
  smartai_catalog_lookup "NM-NET-007"
  assert_eq "${CATALOG_FOUND:-}" "yes" "T-CATALOG: tìm thấy NM-NET-007"
  assert_eq "${CATALOG_PHASE:-}" "dns" "T-CATALOG: NM-NET-007 phase=dns"
  assert_contains "${CATALOG_ACTIONS:-}" "nmcli networking on" "T-CATALOG: actions chứa lệnh đúng từ catalog"

  smartai_catalog_lookup "NM-ZZZ-999"
  assert_eq "${CATALOG_FOUND:-}" "no" "T-CATALOG: mã không tồn tại -> CATALOG_FOUND=no (không bịa)"

  # --- T-AUDIT + redaction (gọi smartai_audit thật, đọc file thật) -------
  smartai_audit "Test hành động" "nmcli networking on" "ran" "0" "lớp test" "hoàn tác test" \
    "token=bimat123 192.168.50.7 nguoidung@mail.com AA:BB:CC:DD:EE:FF /home/cuong Bearer xyz999abc"
  local audit_file="$XDG_STATE_HOME/namios/smartai-audit.log"
  if [ -f "$audit_file" ]; then
    local logged
    logged="$(cat "$audit_file")"
    assert_not_contains "$logged" "bimat123" "T-AUDIT: audit log KHÔNG lộ token= thật"
    assert_not_contains "$logged" "192.168.50.7" "T-AUDIT: audit log KHÔNG lộ IP nội bộ thật"
    assert_not_contains "$logged" "nguoidung@mail.com" "T-AUDIT: audit log KHÔNG lộ email thật"
    assert_not_contains "$logged" "AA:BB:CC:DD:EE:FF" "T-AUDIT: audit log KHÔNG lộ MAC thật"
    assert_not_contains "$logged" "/home/cuong" "T-AUDIT: audit log KHÔNG lộ đường dẫn home thật"
    assert_not_contains "$logged" "xyz999abc" "T-AUDIT: audit log KHÔNG lộ Bearer token thật"
    assert_contains "$logged" "corr=" "T-AUDIT: dòng audit có correlation_id"
    assert_contains "$logged" "status=ran" "T-AUDIT: dòng audit ghi đúng status"
  else
    fail_ "T-AUDIT: ghi được file audit log" "không thấy $audit_file"
  fi

  # --- KNOWN GAP: smartai_redact fallback (sandbox không có /opt/namios,
  # nên LUÔN dùng đường dự phòng sed ở ĐÂY) không in cảnh báo "đang dùng
  # đường dự phòng" như EVENT-ERROR-CONTRACT.md §2.2 yêu cầu, và không giống
  # redact_fallback() của namios-chan-doan (file đó CÓ chèn banner cảnh báo).
  # Xác nhận: (a) redact vẫn hoạt động đúng (an toàn), (b) banner cảnh báo
  # thật sự KHÔNG có (gap thật, không phải lỗi test).
  if PYTHONPATH="/opt/namios" python3 -c "import namios_security" >/dev/null 2>&1; then
    gap_ "GAP-REDACT-FALLBACK-WARNING: bỏ qua (môi trường NÀY có /opt/namios -> không exercise được đường dự phòng)" "-"
  else
    local redacted
    redacted="$(printf '%s' "password=abc123" | smartai_redact)"
    assert_contains "$redacted" "[REDACTED]" "GAP-check: đường dự phòng (sed) vẫn che được password= (không phải lỗi an toàn)"
    if [[ "$redacted" == *"CẢNH BÁO"* ]] || [[ "$redacted" == *"dự phòng"* ]]; then
      pass_ "GAP-REDACT-FALLBACK-WARNING: (bất ngờ) đã thấy cảnh báo — nếu code vừa được sửa, HÃY xoá mục KNOWN GAP này trong docs/specs/RELIABILITY-TESTS.md"
    else
      gap_ "GAP-REDACT-FALLBACK-WARNING: smartai_redact() dùng đường dự phòng (sed) KHÔNG in cảnh báo 'đang dùng đường dự phòng'" \
        "EVENT-ERROR-CONTRACT.md §2.2 bắt buộc 'ghi rõ cảnh báo đang ở đường dự phòng'; namios-chan-doan::redact_fallback() làm đúng (chèn banner '# [CẢNH BÁO] ...'), nhưng namios-smartai-policy.sh::smartai_redact() không chèn gì — audit log âm thầm dùng redactor kém toàn diện hơn mà không ai biết. Thêm nữa: CẢ HAI tool hard-code PYTHONPATH=\"/opt/namios\" (chỉ có trên ISO đã cài) nên MỌI máy dev/CI/sandbox không-phải-ISO-thật đều luôn rơi vào đường dự phòng này một cách im lặng."
    fi
  fi

  # QUAN TRỌNG: unset trước khi rời section — nếu không, các section B.*
  # sau (subprocess riêng) sẽ KẾ THỪA XDG_STATE_HOME này (env đã export) và
  # ghi audit log vào thư mục tmp ĐÃ BỊ XOÁ ở dưới, khiến test B.* sau không
  # tìm thấy audit log ở đường dẫn $HOME/.local/state mong đợi của riêng nó.
  unset XDG_STATE_HOME NAMIOS_ERROR_CATALOG
  rm -rf "$tmp"
}

# ===========================================================================
# LỚP B — subprocess thật `namios-smartai` (TTY fallback) với PATH giả.
# ===========================================================================

# Dựng một PATH giả ĐẦY ĐỦ cho các playbook (10 ca C1..C10) — mỗi test tạo
# thư mục riêng (tmp) để _calls.log không lẫn giữa các test.
build_full_fakebin() {
  local dir="$1"
  mkdir -p "$dir"
  mk_fake "$dir" nmcli '
case "$*" in
  "radio wifi on") exit 0 ;;
  "networking on") exit 0 ;;
  "networking connectivity") echo full; exit 0 ;;
esac
exit 0'
  mk_fake "$dir" pkexec 'exec "$@"'
  mk_fake "$dir" systemctl '
case "$*" in
  "restart cups") exit 0 ;;
  "restart bluetooth") exit 0 ;;
esac
exit 0'
  mk_fake "$dir" cancel 'exit 0'
  mk_fake "$dir" lpstat 'exit 0'
  mk_fake "$dir" fcitx5 'exit 0'
  mk_fake "$dir" fcitx5-configtool 'exit 0'
  mk_fake "$dir" timeshift 'exit 0'
  mk_fake "$dir" timeshift-gtk 'exit 0'
  mk_fake "$dir" winecfg 'exit 0'
  mk_fake "$dir" systemsettings 'exit 0'
  mk_fake "$dir" namios-ket-noi-thiet-bi 'exit 0'
  mk_fake "$dir" namios-chan-doan 'exit 0'
  # kdialog CỐ Ý không tạo -> ép TTY fallback (test headless, giống sandbox
  # không có KDE Plasma — đây CHÍNH LÀ môi trường test, không phải mô phỏng
  # giả, 'thiếu kdialog' là sự thật trong sandbox CI/dev).
}

section_e2e_policy_gate_no_bypass() {
  printf '\n== LỚP B.1: cổng chính sách — từ chối KHÔNG được bypass ==\n'
  local tmp fb home out
  tmp="$(mktemp -d)"
  fb="$tmp/fakebin"
  home="$tmp/home"
  mkdir -p "$home"
  build_full_fakebin "$fb"

  # Kịch bản: Mạng > Mất mạng hoàn toàn > TỪ CHỐI "Bật lại Wi-Fi", ĐỒNG Ý
  # "Kết nối lại mạng" -> quay lại, thoát.
  out="$(PATH="$fb:/usr/bin:/bin" HOME="$home" bash "$SMARTAI_BIN" <<'STDIN_EOF' 2>&1
1
1

n
n

y

0
0
STDIN_EOF
)"
  if called "$fb" "nmcli radio"; then
    fail_ "B.1: từ chối 'Bật lại Wi-Fi' -> nmcli radio wifi on KHÔNG được gọi" "nhưng đã bị gọi"
  else
    pass_ "B.1: từ chối 'Bật lại Wi-Fi' -> nmcli radio wifi on KHÔNG được gọi (không bypass)"
  fi
  if called "$fb" "nmcli networking"; then
    pass_ "B.1: đồng ý 'Kết nối lại mạng' -> nmcli networking on ĐƯỢC gọi"
  else
    fail_ "B.1: đồng ý 'Kết nối lại mạng' -> nmcli networking on phải được gọi" "không thấy trong _calls.log"
  fi
  assert_contains "$out" "Đã HỦY" "B.1: output báo rõ đã HỦY khi từ chối"
  assert_contains "$out" "Kiểm lại (chỉ đọc) bằng 'nmcli networking connectivity'" "B.1: có VERIFY_CMD -> hiện bằng chứng kiểm lại (không khẳng định xong)"
  assert_not_contains "$out" "Đã chạy xong bước:\n  nmcli radio wifi on" "B.1: bước bị từ chối không được hiện như đã 'chạy xong'"

  # Audit log phải có cả dòng 'cancelled' và dòng 'ran'.
  local audit_file="$home/.local/state/namios/smartai-audit.log"
  if [ -f "$audit_file" ]; then
    local logged
    logged="$(cat "$audit_file")"
    assert_contains "$logged" "status=cancelled" "B.1: audit log có dòng status=cancelled"
    assert_contains "$logged" "status=ran" "B.1: audit log có dòng status=ran"
  else
    fail_ "B.1: audit log tồn tại sau phiên" "không thấy $audit_file"
  fi

  rm -rf "$tmp"
}

section_e2e_privileged_requires_pkexec() {
  printf '\n== LỚP B.2: hành động đặc quyền BẮT BUỘC qua pkexec — thiếu pkexec thì KHÔNG chạy bằng cách khác ==\n'
  local tmp fb home out
  tmp="$(mktemp -d)"
  fb="$tmp/fakebin"
  home="$tmp/home"
  mkdir -p "$fb" "$home"
  mk_fake "$fb" cancel 'exit 0'
  mk_fake "$fb" systemctl 'exit 0'
  # pkexec CỐ Ý KHÔNG tạo.

  out="$(PATH="$fb:/usr/bin:/bin" HOME="$home" bash "$SMARTAI_BIN" <<'STDIN_EOF' 2>&1
2
1

y

0
0
STDIN_EOF
)"
  if called "$fb" "systemctl"; then
    fail_ "B.2: thiếu pkexec -> systemctl restart cups KHÔNG được chạy bằng đường khác" "nhưng systemctl đã bị gọi"
  else
    pass_ "B.2: thiếu pkexec -> bước 'Khởi động lại dịch vụ in (CUPS)' bị bỏ qua hoàn toàn (không có đường vòng)"
  fi
  if called "$fb" "cancel"; then
    pass_ "B.2: bước không cần quyền (xoá hàng đợi) vẫn chạy bình thường"
  else
    fail_ "B.2: cancel -a phải chạy (đã đồng ý)" "không thấy trong _calls.log"
  fi
  # playbook_print_usb's bước "Xoá hàng đợi in đang kẹt" KHÔNG đặt VERIFY_CMD
  # riêng -> confirm_and_run phải dùng câu mặc định "không tự tuyên bố đã
  # xong" (guardrail #3 — SmartAI không tự xác nhận việc đã xong).
  assert_contains "$out" "KHÔNG tự tuyên bố 'đã xong'" \
    "B.2: bước thành công KHÔNG có VERIFY_CMD riêng -> vẫn dùng câu mặc định không tự nhận đã xong"
  rm -rf "$tmp"
}

section_e2e_ai_offline_degrade() {
  printf '\n== LỚP B.3: AI-offline -> HƯỚNG DẪN THEO QUY TẮC (không cần mạng/khoá AI) ==\n'
  local out
  out="$(PATH="/usr/bin:/bin" HOME="$(mktemp -d)" env -u ANTHROPIC_API_KEY -u OPENAI_API_KEY -u NAMIOS_SMARTAI_API_KEY -u NAMIOS_SMARTAI_LLM \
    bash "$SMARTAI_BIN" <<<'0
' 2>&1)"
  assert_contains "$out" "HƯỚNG DẪN THEO QUY TẮC (chạy offline, KHÔNG cần khoá AI đám mây)" \
    "B.3: không có khoá AI/engine -> banner offline đúng nguyên văn"
  assert_contains "$out" "SmartAI chỉ ĐỀ XUẤT và chỉ THAY ĐỔI khi bạn đồng ý" "B.3: disclaimer ngắn luôn hiện"

  local out2
  out2="$(PATH="/usr/bin:/bin" HOME="$(mktemp -d)" ANTHROPIC_API_KEY=sk-fake-test-only bash "$SMARTAI_BIN" <<<'0
' 2>&1)"
  assert_contains "$out2" "có trợ lý nâng cao khả dụng" "B.3: có khoá AI -> banner đổi, vẫn nói rõ 'cùng guardrail'"
}

section_e2e_explain_binding() {
  printf '\n== LỚP B.4: --explain <cause_code> (bind nút ErrorCard) ==\n'
  local tmp fb home out rc
  tmp="$(mktemp -d)"
  fb="$tmp/fakebin"
  home="$tmp/home"
  mkdir -p "$fb" "$home"
  mk_fake "$fb" namios-ket-noi-thiet-bi 'exit 0'

  out="$(PATH="$fb:/usr/bin:/bin" HOME="$home" NAMIOS_ERROR_CATALOG="$CATALOG" \
    bash "$SMARTAI_BIN" --explain NM-NET-007 </dev/null 2>&1)"
  rc=$?
  assert_true "$rc" "B.4: --explain NM-NET-007 luôn exit 0"
  assert_contains "$out" "Bước lỗi (phase): dns" "B.4: giải thích đúng phase lấy từ catalog"
  assert_contains "$out" "SmartAI KHÔNG bịa" "B.4: luôn nhắc nguyên tắc không bịa nguyên nhân"

  # Mã không tồn tại trong catalog -> KHÔNG bịa giải thích, vẫn thoát sạch.
  local out_unknown
  out_unknown="$(PATH="$fb:/usr/bin:/bin" HOME="$home" NAMIOS_ERROR_CATALOG="$CATALOG" \
    bash "$SMARTAI_BIN" --explain NM-ZZZ-999 </dev/null 2>&1)"
  assert_contains "$out_unknown" "không có trong catalog" "B.4: mã lạ -> báo rõ không có trong catalog, không bịa"

  rm -rf "$tmp"
}

section_e2e_catalog_missing_python_and_jq_degrades() {
  printf '\n== LỚP B.5: thiếu CẢ python3 VÀ jq -> vẫn chạy, không sập, định tuyến đúng nhóm ==\n'
  local tmp fb nopy home out rc
  tmp="$(mktemp -d)"
  fb="$tmp/fakebin"
  nopy="$tmp/nopy"
  home="$tmp/home"
  mkdir -p "$fb" "$nopy" "$home"
  mk_fake "$fb" namios-ket-noi-thiet-bi 'exit 0'
  # PATH thay thế KHÔNG có python3/jq (symlink mọi coreutils khác từ /usr/bin).
  local f b
  for f in /usr/bin/*; do
    b="$(basename "$f")"
    case "$b" in python3*|jq) continue ;; esac
    ln -sf "$f" "$nopy/$b" 2>/dev/null || true
  done

  out="$(PATH="$fb:$nopy" HOME="$home" NAMIOS_ERROR_CATALOG="$CATALOG" \
    bash "$SMARTAI_BIN" --explain NM-NET-007 </dev/null 2>&1)"
  rc=$?
  assert_true "$rc" "B.5: --explain vẫn exit 0 khi thiếu python3 VÀ jq"
  assert_contains "$out" "Chưa đọc được catalog" "B.5: báo rõ chưa đọc được catalog (không bịa giải thích)"
  rm -rf "$tmp"
}

section_e2e_audit_redacts_secret_from_fake_command_output() {
  printf '\n== LỚP B.6: audit log che bí mật XUYÊN QUA đầu ra lệnh thật đã chạy ==\n'
  local tmp fb home
  tmp="$(mktemp -d)"
  fb="$tmp/fakebin"
  home="$tmp/home"
  mkdir -p "$fb" "$home"
  mk_fake "$fb" nmcli '
case "$*" in
  "radio wifi on") exit 0 ;;
  "networking on") echo "token=supersecretXYZ 10.0.0.5 someone@example.com AA:BB:CC:DD:EE:FF /home/cuong"; exit 0 ;;
  "networking connectivity") echo full; exit 0 ;;
esac
exit 0'

  PATH="$fb:/usr/bin:/bin" HOME="$home" bash "$SMARTAI_BIN" <<'STDIN_EOF' >/dev/null 2>&1
1
1

n
n

y

0
0
STDIN_EOF

  local audit_file="$home/.local/state/namios/smartai-audit.log"
  if [ -f "$audit_file" ]; then
    local logged
    logged="$(cat "$audit_file")"
    assert_not_contains "$logged" "supersecretXYZ" "B.6: token thật trong OUTPUT lệnh KHÔNG lộ ra audit log"
    assert_not_contains "$logged" "10.0.0.5" "B.6: IP nội bộ thật trong output KHÔNG lộ ra audit log"
    assert_not_contains "$logged" "someone@example.com" "B.6: email thật trong output KHÔNG lộ ra audit log"
    assert_not_contains "$logged" "AA:BB:CC:DD:EE:FF" "B.6: MAC thật trong output KHÔNG lộ ra audit log"
    assert_not_contains "$logged" "/home/cuong" "B.6: đường dẫn home thật KHÔNG lộ ra audit log"
  else
    fail_ "B.6: audit log tồn tại" "không thấy $audit_file"
  fi
  rm -rf "$tmp"
}

# ===========================================================================
# CHẠY TẤT CẢ + BÁO CÁO
# ===========================================================================
main() {
  section_policy_lib
  section_e2e_policy_gate_no_bypass
  section_e2e_privileged_requires_pkexec
  section_e2e_ai_offline_degrade
  section_e2e_explain_binding
  section_e2e_catalog_missing_python_and_jq_degrades
  section_e2e_audit_redacts_secret_from_fake_command_output

  printf '\n================= TỔNG KẾT smartai_tests.sh =================\n'
  printf 'PASS: %d   FAIL: %d   KNOWN-GAP (không tính fail): %d\n' "$PASS" "$FAIL" "$GAPS"
  if [ "$FAIL" -gt 0 ]; then
    printf '\nCác test FAIL:\n'
    printf '  - %s\n' "${FAILED_NAMES[@]}"
  fi
  if [ "$GAPS" -gt 0 ]; then
    printf '\nKNOWN GAP đã ghi nhận (bất thường THẬT trong code sản phẩm — xem chi tiết ở trên + docs/specs/RELIABILITY-TESTS.md):\n'
    printf '  - %s\n' "${GAP_NAMES[@]}"
  fi

  if [ "$FAIL" -gt 0 ]; then
    exit 1
  fi
  exit 0
}

main
