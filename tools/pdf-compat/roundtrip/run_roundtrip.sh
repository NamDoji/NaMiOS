#!/usr/bin/env bash
# Harness round-trip cho vertical-slice NaMiPDF (xem
# docs/specs/namipdf-v18/05_PROMPT_CLAUDE_CODE.md bước "Vertical slice":
# "mở PDF đa trang trong worker sandbox, tìm/copy tiếng Việt, thêm chú
# thích, sắp xếp trang, lưu bản sao atomically, mở lại trong NaMiPDF và
# viewer độc lập, in một trang qua CUPS").
#
# Thực hiện từng bước với các công cụ CLI THẬT (pdfinfo/pdftotext từ
# poppler-utils, qpdf, ocrmypdf, lp/lpr từ CUPS) — các công cụ này KHÔNG có
# trong môi trường build hiện tại (xem CLAUDE.md "No rendering engine
# installed in THIS environment — GUI/render steps run in CI/pilot, not
# here"). Script GUARD từng bước bằng `command -v`: nếu thiếu công cụ, in
# dòng "runs in CI only" và BỎ QUA bước đó nhưng VẪN CHẠY TIẾP các bước
# khác (không dừng giữa chừng) — đúng kiểu guard đã dùng ở
# tools/office-compat/roundtrip/run_roundtrip.sh cho `soffice`.
#
# Dùng:  tools/pdf-compat/roundtrip/run_roundtrip.sh [out_dir]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES_DIR="$(cd "$HERE/../fixtures" && pwd)"
OUT_DIR="${1:-$HERE/out}"
PY="${PYTHON:-python3}"

mkdir -p "$OUT_DIR"

echo "== NaMiPDF vertical-slice round-trip harness =="
echo "fixtures : $FIXTURES_DIR"
echo "out dir  : $OUT_DIR"
echo

OVERALL_STATUS=0

# ---------------------------------------------------------------------------
# Bước 0: self-check tĩnh (pikepdf/pypdf) — LUÔN chạy, không phụ thuộc công
# cụ ngoài. Đây là bước TƯƠNG ĐƯƠNG compare.py selfcheck bên office-compat.
echo "--- [0/6] self-check tĩnh (pikepdf + pypdf, không cần công cụ ngoài) ---"
if "$PY" "$HERE/check_fixtures.py"; then
  echo "self-check: PASS"
else
  echo "self-check: FAIL (xem chi tiết ở trên)"
  OVERALL_STATUS=1
fi
echo

F01="$FIXTURES_DIR/01_text_vn.pdf"
F04="$FIXTURES_DIR/04_multipage_bookmarks.pdf"
F12="$FIXTURES_DIR/12_vn_heavy_diacritics.pdf"
F02="$FIXTURES_DIR/02_scanned_image_only.pdf"

for f in "$F01" "$F04" "$F12" "$F02"; do
  if [[ ! -f "$f" ]]; then
    echo "THIẾU fixture: $f (chạy fixtures/make_fixtures.py trước)"
    OVERALL_STATUS=1
  fi
done

# ---------------------------------------------------------------------------
# Bước 1: mở/validate bằng pdfinfo (poppler-utils) — "mở PDF đa trang".
echo "--- [1/6] pdfinfo: mở/validate PDF-04 (đa trang + bookmark) ---"
if command -v pdfinfo >/dev/null 2>&1; then
  pdfinfo "$F04" | tee "$OUT_DIR/pdfinfo_04.txt"
  echo "pdfinfo: OK"
else
  echo "pdfinfo not present — step runs in CI only (cần poppler-utils)"
fi
echo

# ---------------------------------------------------------------------------
# Bước 2: trích text + kiểm tra dấu tiếng Việt còn nguyên qua pdftotext.
echo "--- [2/6] pdftotext: trích + grep tiếng Việt (PDF-01, PDF-12) ---"
if command -v pdftotext >/dev/null 2>&1; then
  pdftotext "$F01" "$OUT_DIR/01_text_vn.txt"
  pdftotext "$F12" "$OUT_DIR/12_vn_heavy.txt"
  if grep -q "đường phố Hà Nội" "$OUT_DIR/01_text_vn.txt" \
     && grep -q "Thừa Thiên Huế" "$OUT_DIR/12_vn_heavy.txt"; then
    echo "pdftotext: dấu tiếng Việt CÒN NGUYÊN sau trích xuất — PASS"
  else
    echo "pdftotext: MẤT DẤU hoặc sai nội dung — FAIL"
    OVERALL_STATUS=1
  fi
else
  echo "pdftotext not present — step runs in CI only (cần poppler-utils)"
fi
echo

# ---------------------------------------------------------------------------
# Bước 3: thêm annotation / reorder / split-merge bằng qpdf — LUÔN lưu vào
# BẢN SAO trong $OUT_DIR, KHÔNG BAO GIỜ ghi đè file gốc trong fixtures/.
echo "--- [3/6] qpdf: reorder trang + split/merge (atomic, ghi vào bản sao) ---"
if command -v qpdf >/dev/null 2>&1; then
  REORDERED="$OUT_DIR/04_reordered.pdf"
  TMP_REORDERED="$REORDERED.tmp.$$"
  # Đảo 3 trang đầu (1,2,3 -> 3,2,1), giữ nguyên các trang còn lại — "sắp xếp
  # lại trang" theo đúng bước vertical-slice. Ghi ra file tạm rồi `mv` atomic
  # để không bao giờ để lại một bản dở dang có cùng tên nếu qpdf bị ngắt giữa
  # chừng (mô phỏng yêu cầu "lưu bản sao atomically").
  # "." = file infile chính ("$F04" truyền ở đầu lệnh). Chỉ MỘT "--" duy
  # nhất tách danh sách (file,range) khỏi tên file đích (cú pháp qpdf
  # --pages chuẩn: https://qpdf.readthedocs.io/en/stable/cli.html#option-pages).
  qpdf "$F04" --pages . 3,2,1 . 4-z -- "$TMP_REORDERED"
  mv -f "$TMP_REORDERED" "$REORDERED"
  echo "  -> đã reorder: $REORDERED"

  SPLIT_DIR="$OUT_DIR/split"
  mkdir -p "$SPLIT_DIR"
  qpdf "$F04" --pages "$F04" 1-5 -- "$SPLIT_DIR/04_part1.pdf"
  qpdf "$F04" --pages "$F04" 6-z -- "$SPLIT_DIR/04_part2.pdf"
  echo "  -> đã split: $SPLIT_DIR/04_part1.pdf + 04_part2.pdf"

  MERGED_TMP="$OUT_DIR/04_merged.pdf.tmp.$$"
  MERGED="$OUT_DIR/04_merged.pdf"
  qpdf --empty --pages "$SPLIT_DIR/04_part1.pdf" "$SPLIT_DIR/04_part2.pdf" -- "$MERGED_TMP"
  mv -f "$MERGED_TMP" "$MERGED"
  echo "  -> đã merge lại: $MERGED"

  if command -v qpdf >/dev/null 2>&1; then
    qpdf --check "$MERGED" && echo "qpdf --check bản merge: OK" \
      || { echo "qpdf --check bản merge: FAIL"; OVERALL_STATUS=1; }
  fi
else
  echo "qpdf not present — step runs in CI only"
fi
echo

# ---------------------------------------------------------------------------
# Bước 4: reopen + re-validate bản đã sửa (đảm bảo không hỏng sau round-trip).
echo "--- [4/6] reopen + validate lại bản đã reorder/merge ---"
if command -v pdfinfo >/dev/null 2>&1 && [[ -f "$OUT_DIR/04_merged.pdf" ]]; then
  pdfinfo "$OUT_DIR/04_merged.pdf" > "$OUT_DIR/pdfinfo_04_merged.txt"
  echo "reopen + pdfinfo bản merge: OK"
elif [[ -f "$OUT_DIR/04_merged.pdf" ]]; then
  "$PY" - "$OUT_DIR/04_merged.pdf" <<'PYEOF'
import sys
import pikepdf
with pikepdf.open(sys.argv[1]) as pdf:
    print(f"reopen bang pikepdf OK, pages={len(pdf.pages)}")
PYEOF
else
  echo "KHÔNG có bản merge để reopen (bước 3 đã bị bỏ qua vì thiếu qpdf)"
fi
echo

# ---------------------------------------------------------------------------
# Bước 5: OCR trên bản scan-image-only (PDF-02) bằng ocrmypdf (cần Tesseract).
echo "--- [5/6] ocrmypdf: OCR tiếng Việt trên PDF-02 (scan, không text layer) ---"
if command -v ocrmypdf >/dev/null 2>&1; then
  OCR_OUT="$OUT_DIR/02_ocr.pdf.tmp.$$"
  OCR_FINAL="$OUT_DIR/02_ocr.pdf"
  if ocrmypdf --language vie "$F02" "$OCR_OUT" 2> "$OUT_DIR/ocrmypdf.log"; then
    mv -f "$OCR_OUT" "$OCR_FINAL"
    echo "  -> OCR xong: $OCR_FINAL"
    if command -v pdftotext >/dev/null 2>&1; then
      pdftotext "$OCR_FINAL" "$OUT_DIR/02_ocr.txt"
      echo "  -> text sau OCR (xem $OUT_DIR/02_ocr.txt); ĐỘ CHÍNH XÁC (CER/WER)"
      echo "     cần đo riêng theo 04_KIEM_THU_PHAT_HANH.md — KHÔNG tự suy ra pass/fail ở đây."
    fi
  else
    echo "  ocrmypdf chạy lỗi (xem $OUT_DIR/ocrmypdf.log) — có thể thiếu gói ngôn ngữ 'vie'"
    OVERALL_STATUS=1
  fi
else
  echo "ocrmypdf not present — step runs in CI only (cần ocrmypdf + tesseract-ocr-vie)"
fi
echo

# ---------------------------------------------------------------------------
# Bước 6: in một trang qua CUPS (lp/lpr) tới PDF printer nếu có cấu hình sẵn.
echo "--- [6/6] in 1 trang qua CUPS (lp/lpr tới PDF printer nếu có) ---"
PRINT_TARGET="$F01"
if command -v lp >/dev/null 2>&1; then
  if lpstat -p 2>/dev/null | grep -qi "pdf"; then
    PDF_PRINTER="$(lpstat -p 2>/dev/null | grep -i pdf | head -1 | awk '{print $2}')"
    lp -d "$PDF_PRINTER" -o page-ranges=1 "$PRINT_TARGET" \
      && echo "lp: đã gửi job in trang 1 tới $PDF_PRINTER" \
      || { echo "lp: gửi job thất bại"; OVERALL_STATUS=1; }
  else
    echo "lp có sẵn nhưng KHÔNG tìm thấy PDF printer đã cấu hình — bỏ qua in thật"
    echo "(cần cấu hình CUPS-PDF hoặc máy in ảo trong CI/pilot)"
  fi
elif command -v lpr >/dev/null 2>&1; then
  echo "lpr có sẵn nhưng không có cách xác định PDF printer tự động ở đây — bỏ qua"
  echo "(cấu hình lprm/lpoptions cụ thể thuộc về bước CI/pilot)"
else
  echo "lp/lpr not present — step runs in CI only (cần CUPS + PDF virtual printer)"
fi
echo

echo "--- Lưu ý ---"
echo "Các bước ở trên dùng qpdf/pdfinfo/pdftotext/ocrmypdf/lp CLI THẬT khi có"
echo "sẵn, nhưng KHÔNG thay thế việc render/xem bằng Okular hoặc đối chiếu"
echo "Adobe Acrobat — đó là bước nghiệm thu PDF-01..PDF-13 đầy đủ, chạy ở"
echo "CI/pilot có GUI. Xem README.md mục giới hạn."

exit "$OVERALL_STATUS"
