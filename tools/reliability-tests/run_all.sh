#!/bin/bash
# run_all.sh — chạy TOÀN BỘ bộ test độ tin cậy (reliability-tests, roadmap A4)
# và in tổng kết cuối. KHÔNG cần máy thật/Wi-Fi/máy in/Bluetooth — mọi sự
# kiện đều MÔ PHỎNG (xem docs/specs/RELIABILITY-TESTS.md).
#
# Chạy: bash tools/reliability-tests/run_all.sh
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
cd "$REPO_ROOT" || exit 2

PY_FILES=(
  "tools/reliability-tests/error_catalog_tests.py"
  "tools/reliability-tests/sim_network.py"
  "tools/reliability-tests/sim_printer.py"
  "tools/reliability-tests/sim_bluetooth.py"
)

PYTHON_BIN="python3"
if [ -x "$REPO_ROOT/.venv/bin/python3" ]; then
  PYTHON_BIN="$REPO_ROOT/.venv/bin/python3"
fi

overall_rc=0

printf '=========================================================\n'
printf '  A4 reliability-tests — pytest (catalog + sự kiện mô phỏng)\n'
printf '=========================================================\n'
"$PYTHON_BIN" -m pytest "${PY_FILES[@]}" -v
pytest_rc=$?
[ "$pytest_rc" -ne 0 ] && overall_rc=1

printf '\n=========================================================\n'
printf '  A4 reliability-tests — smartai_tests.sh (bash, policy+E2E)\n'
printf '=========================================================\n'
bash "$HERE/smartai_tests.sh"
smartai_rc=$?
[ "$smartai_rc" -ne 0 ] && overall_rc=1

printf '\n=========================================================\n'
printf '  TỔNG KẾT run_all.sh\n'
printf '=========================================================\n'
printf 'pytest (4 file, catalog+net+printer+bluetooth): %s\n' "$([ "$pytest_rc" -eq 0 ] && echo "PASS" || echo "FAIL")"
printf 'smartai_tests.sh (policy lib + E2E namios-smartai): %s\n' "$([ "$smartai_rc" -eq 0 ] && echo "PASS" || echo "FAIL")"
printf '\nLƯU Ý THẬT: toàn bộ test trên dùng SỰ KIỆN MÔ PHỎNG (PATH giả,\n'
printf 'không đụng Wi-Fi/máy in/Bluetooth/polkit thật). Máy thật là bước\n'
printf 'pilot RIÊNG — xem docs/specs/RELIABILITY-TESTS.md và\n'
printf 'EVENT-ERROR-CONTRACT.md §7 "Máy thật (để lên completed, chưa làm)".\n'

exit "$overall_rc"
