"""OCR ảnh chụp màn hình lỗi -> văn bản, dùng ``tesseract`` đã đóng gói sẵn
trong ảnh NaMiOS (gói ``tesseract-ocr`` + ``tesseract-ocr-vie``, xem
``package-lists/0420-pdf.list.chroot``) qua ``namios_security.run_argv``
(argv tĩnh, KHÔNG shell, đúng quy ước WP8).

FAIL-SAFE: thiếu lệnh ``tesseract`` trên máy (ảnh rút gọn/gỡ gói) -> trả
``OcrResult(available=False, ...)``, KHÔNG raise, KHÔNG bịa văn bản — UI gọi
hàm này rồi tự hỏi người dùng dán văn bản lỗi thủ công thay vì OCR."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from namios_security import ExecPolicyError, redact_text, run_argv

__all__ = ["OcrResult", "ocr_image"]

#: Tesseract hỗ trợ cả tiếng Việt lẫn tiếng Anh cùng lúc (``-l vie+eng``) —
#: lỗi hệ thống thường trộn cả hai (thông báo gốc tiếng Anh, ghi chú người
#: dùng thêm tiếng Việt), nhận cả hai cho một lần OCR duy nhất.
_DEFAULT_OCR_LANG = "vie+eng"

_OCR_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class OcrResult:
    """Kết quả một lần OCR ảnh. ``text=None`` khi KHÔNG lấy được văn bản
    (thiếu tesseract, ảnh không có chữ, hay OCR lỗi) — ``detail`` giải thích
    lý do (đã redact) để UI hiển thị trung thực thay vì im lặng thất bại."""

    text: str | None
    available: bool
    detail: str


def ocr_image(image_path: Path | str, *, lang: str = _DEFAULT_OCR_LANG) -> OcrResult:
    tesseract_bin = shutil.which("tesseract")
    if tesseract_bin is None:
        return OcrResult(
            text=None,
            available=False,
            detail=(
                "Chưa có công cụ OCR (gói tesseract-ocr) trên máy này — hãy dán "
                "trực tiếp văn bản lỗi thay vì ảnh."
            ),
        )

    path = Path(image_path)
    if not path.is_file():
        return OcrResult(text=None, available=False, detail=f"Không tìm thấy file ảnh: {path}")

    try:
        result = run_argv(
            [tesseract_bin, str(path), "stdout", "-l", lang],
            timeout=_OCR_TIMEOUT_SECONDS,
        )
    except ExecPolicyError as exc:
        return OcrResult(
            text=None,
            available=False,
            detail=redact_text(f"Không chạy được tesseract: {exc.reason_vi}"),
        )

    if result.returncode != 0:
        stderr_text = result.stderr.decode("utf-8", "replace").strip()
        return OcrResult(
            text=None,
            available=False,
            detail=redact_text(f"tesseract trả mã lỗi {result.returncode}: {stderr_text}"),
        )

    text = result.stdout.decode("utf-8", "replace").strip()
    if not text:
        return OcrResult(
            text=None,
            available=True,
            detail="OCR chạy được nhưng không nhận ra chữ nào trong ảnh — thử ảnh rõ/to hơn.",
        )
    return OcrResult(text=text, available=True, detail="OCR thành công.")
