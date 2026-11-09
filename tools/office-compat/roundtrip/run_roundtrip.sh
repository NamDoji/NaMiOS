#!/usr/bin/env bash
# Harness round-trip cho vertical-slice NaMiOffice v2 (xem
# docs/specs/namioffice-v2/05_PROMPT_CLAUDE_CODE.md bước 3).
#
# Với mỗi fixture (LongDoc.docx, WorkBook.xlsx, Deck.pptx):
#   1. soffice --headless --convert-to pdf   (xuất PDF — kiểm in/preview)
#   2. soffice --headless --convert-to <cùng-đuôi>  (mở rồi LƯU LẠI cùng
#      định dạng — đây chính là "round-trip": mở an toàn → không sửa gì ở
#      bước này → lưu bản sao → so kết quả bằng compare.py)
#   3. gọi compare.py ở chế độ `roundtrip` để diff bản gốc vs bản đã lưu lại.
#
# GUARD: nếu máy KHÔNG có `soffice` (như máy dev hiện tại), script VẪN chạy
# được — nó in rõ "soffice not present — round-trip step runs in CI only",
# bỏ qua bước convert/diff, nhưng VẪN chạy xong bước self-check tĩnh (không
# cần soffice) của compare.py. Round-trip thật với soffice (và, xa hơn, với
# Microsoft Office có giấy phép) chỉ chạy trong CI/QEMU — xem README.md.
#
# Dùng:  tools/office-compat/roundtrip/run_roundtrip.sh [out_dir]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES_DIR="$(cd "$HERE/../fixtures" && pwd)"
OUT_DIR="${1:-$HERE/out}"
COMPARE_PY="$HERE/compare.py"
PY="${PYTHON:-python3}"

mkdir -p "$OUT_DIR"

echo "== NaMiOffice vertical-slice round-trip harness =="
echo "fixtures : $FIXTURES_DIR"
echo "out dir  : $OUT_DIR"
echo

OVERALL_STATUS=0

# ---------------------------------------------------------------------------
# Bước 0: self-check tĩnh — LUÔN chạy, không phụ thuộc soffice.
echo "--- [0/2] self-check tĩnh (python-docx/openpyxl/python-pptx) ---"
if "$PY" "$COMPARE_PY" selfcheck \
    --fixtures-dir "$FIXTURES_DIR" \
    --report "$OUT_DIR/selfcheck.json"; then
  echo "self-check: PASS"
else
  echo "self-check: FAIL"
  OVERALL_STATUS=1
fi
echo

# ---------------------------------------------------------------------------
# Bước 1+2: convert + diff — CHỈ chạy khi có soffice (CI/QEMU).
if ! command -v soffice >/dev/null 2>&1; then
  echo "soffice not present — round-trip step runs in CI only"
  echo "(bỏ qua convert-to-pdf + resave + diff; self-check tĩnh ở trên đã chạy xong)"
  exit "$OVERALL_STATUS"
fi

echo "--- [1/2] soffice có sẵn: convert-to PDF + resave cùng định dạng ---"

# Mỗi phiên soffice headless dùng profile riêng để không giẫm phiên khác
# (vd CI chạy song song nhiều job) và tránh khoá "soffice đang chạy".
SOFFICE_PROFILE_DIR="$(mktemp -d)"
trap 'rm -rf "$SOFFICE_PROFILE_DIR"' EXIT

soffice_headless() {
  # Gọi soffice với timeout để không treo CI khi có file hỏng/soffice kẹt.
  timeout 120 soffice --headless --norestore \
    -env:UserInstallation="file://$SOFFICE_PROFILE_DIR" \
    "$@"
}

declare -A KIND_OF=(
  ["LongDoc.docx"]="docx"
  ["WorkBook.xlsx"]="xlsx"
  ["Deck.pptx"]="pptx"
)

for fname in "${!KIND_OF[@]}"; do
  kind="${KIND_OF[$fname]}"
  src="$FIXTURES_DIR/$fname"
  if [[ ! -f "$src" ]]; then
    echo "BỎ QUA $fname: không thấy fixture (chạy fixtures/make_*.py trước)"
    OVERALL_STATUS=1
    continue
  fi

  fname_dir="$OUT_DIR/${fname%.*}"
  mkdir -p "$fname_dir"

  echo "  -> $fname : convert-to pdf"
  soffice_headless --convert-to pdf --outdir "$fname_dir" "$src" \
    || { echo "  LỖI: convert-to pdf thất bại cho $fname"; OVERALL_STATUS=1; }

  echo "  -> $fname : resave (mở lại, lưu lại cùng định dạng $kind)"
  soffice_headless --convert-to "$kind" --outdir "$fname_dir" "$src" \
    || { echo "  LỖI: resave $kind thất bại cho $fname"; OVERALL_STATUS=1; continue; }

  resaved="$fname_dir/$fname"
  if [[ ! -f "$resaved" ]]; then
    echo "  LỖI: không thấy bản resave $resaved"
    OVERALL_STATUS=1
    continue
  fi

  echo "  -> $fname : diff bản gốc vs bản resave bằng compare.py"
  if "$PY" "$COMPARE_PY" roundtrip \
      --kind "$kind" \
      --orig "$src" \
      --new "$resaved" \
      --report "$fname_dir/roundtrip-diff.json"; then
    echo "  diff: PASS"
  else
    echo "  diff: FAIL (xem $fname_dir/roundtrip-diff.json)"
    OVERALL_STATUS=1
  fi
  echo
done

echo "--- [2/2] Lưu ý ---"
echo "Round-trip ở trên là NaMiOffice/LibreOffice mở-lưu-lại CHÍNH NÓ (soffice"
echo "convert-to). Round-trip đối chiếu với MICROSOFT OFFICE CÓ GIẤY PHÉP là"
echo "bước pilot RIÊNG (cần máy có Office licensed) — CHƯA chạy ở đây. Xem"
echo "README.md mục giới hạn."

exit "$OVERALL_STATUS"
