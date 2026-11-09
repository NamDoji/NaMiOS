# -*- coding: utf-8 -*-
"""namioffice_inspect — Compatibility Inspector cho NaMiOffice (vertical slice).

Đọc TRƯỚC: docs/specs/namioffice-v2/04_KIEN_TRUC_KIEM_THU.md §2 (Fidelity
pipeline: "sniff và validation → sandbox parser → inventory macro/OOXML
parts/external links/signature/IRM → chấm rủi ro C0–C3 → import → ...") và
docs/specs/namioffice-v2/05_PROMPT_CLAUDE_CODE.md bước 2 ("Xây registry tính
năng theo format/phiên bản với C0–C3 và severity. Tạo bộ đọc trước khi Save
nhận biết macros, advanced formulas, dynamic arrays, Pivot/Data Model,
queries, charts, content controls, media, external links, signatures và
IRM.").

Module này triển khai ĐÚNG bước "sniff + inventory + chấm C0–C3" của pipeline
đó — KHÔNG mở file bằng LibreOffice/Office, KHÔNG thực thi macro/script,
KHÔNG gọi mạng. Chỉ dùng thư viện chuẩn (``zipfile`` + ``xml.etree``).

Giới hạn trung thực (đọc kỹ trước khi dựa vào kết quả):
  - Đây là kiểm tra TĨNH theo cấu trúc gói OOXML (tên part, namespace, nội
    dung text thô của vài part). KHÔNG tương đương việc mở thật trong
    LibreOffice/Microsoft Office — không đo được render, recalculation,
    hay round-trip fidelity.
  - Công cụ CHỈ báo "có tồn tại" một tính năng rủi ro; nó KHÔNG tự sửa,
    KHÔNG tự loại bỏ, KHÔNG tự vượt mật khẩu/IRM, KHÔNG chạy VBA.
  - Danh sách hàm "hiện đại"/"mảng động" nhận diện qua tiền tố ``_xlfn.``
    là danh sách CỐ ĐỊNH, có thể thiếu hàm mới; không suy đoán ngoài danh
    sách đã biết.
"""

from __future__ import annotations

from .inspector import (
    CompatLevel,
    Finding,
    InspectionReport,
    Severity,
    inspect_file,
)

__all__ = [
    "CompatLevel",
    "Severity",
    "Finding",
    "InspectionReport",
    "inspect_file",
]
