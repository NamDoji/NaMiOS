"""namipdf_inspect — PDF Compatibility/Safety Inspector cho NaMiPDF (vertical slice).

Đọc TRƯỚC: docs/specs/namipdf-v18/03_KIEN_TRUC_BAO_MAT.md ("Sniff thay vì tin
phần mở rộng; kiểm ... embedded file, JavaScript và link ngoài ... Read-only
khi tài liệu không chắc an toàn") + 01_TINH_NANG_UIUX.md §3 ("Trước khi sửa
hiển thị trạng thái Text PDF / Scan image / Mixed / Signed / Protected") +
05_PROMPT_CLAUDE_CODE.md ("cảnh báo khi tài liệu ký số/đã khóa và không ghi
đè bản gốc").

Module này triển khai bước "Document Inspector" trong kiến trúc 4 lớp của
03_KIEN_TRUC_BAO_MAT.md §1 ("NaMiPDF UI → Document Inspector (sniff,
permission, chữ ký, form, annotation, OCR, PDF/A/UA) → PDF core → ...") —
CHỈ bước sniff/inventory TĨNH, KHÔNG mở bằng trình xem PDF thật, KHÔNG render,
KHÔNG thực thi bất kỳ JavaScript/action nào, KHÔNG gọi mạng.

An toàn (xem docstring ``inspector.py`` để biết chi tiết từng bước):
  - Chỉ dùng pikepdf (ưu tiên, QPDF binding) để đọc cấu trúc object graph;
    pypdf dùng làm phương án dự phòng khi pikepdf không đọc được tệp (hai
    engine có thể bao dung lỗi cấu trúc khác nhau). KHÔNG dùng bất kỳ thư
    viện nào có khả năng render/thực thi (không PDF.js, không trình xem).
  - KHÔNG bao giờ cố vượt mật khẩu/quyền của tệp được mã hoá — nếu tệp yêu
    cầu mật khẩu người dùng mà không được cung cấp, công cụ DỪNG phân tích
    nội dung và chỉ báo cáo "Protected", không đoán nội dung bên trong.
  - KHÔNG bao giờ thực thi JavaScript/action tìm thấy trong tệp — chỉ đọc
    tên khoá (``/JS``, ``/JavaScript``, ``/Launch``, ``/OpenAction``, ``/AA``)
    và báo cáo SỰ TỒN TẠI, không diễn giải/chạy nội dung script.

Giới hạn trung thực (đọc kỹ trước khi dựa vào kết quả — xem cũng README.md
cùng thư mục và phần "caveats" trong báo cáo bàn giao):
  - Đây là kiểm tra TĨNH theo cấu trúc object PDF (catalog, trailer,
    content stream operator, tên part) — KHÔNG tương đương render/mở thật
    bằng Poppler/MuPDF/Acrobat. Không đo được độ trung thực hiển thị.
  - Phân loại "Text PDF / Scan image / Mixed" dựa trên: có operator HIỂN
    THỊ CHỮ (Tj/TJ/'/") trong content stream của trang hay không, VÀ có
    XObject /Subtype /Image hay không (đệ quy có giới hạn độ sâu qua Form
    XObject). Đây là CHỈ BÁO, không phải bằng chứng tuyệt đối — một trang có
    thể có text ẩn (white-on-white), font không nhúng khiến copy ra ký tự
    rác, hoặc text nằm trong Form XObject sâu hơn giới hạn đệ quy.
  - KHÔNG kiểm tra TÍNH HỢP LỆ/ĐỘ TIN CẬY của chữ ký số (trust chain, OCSP/
    CRL, timestamp, revocation) — module này CHỈ báo "có tồn tại trường
    chữ ký /Sig hoặc /Perms /DocMDP trong cấu trúc tệp". Việc xác thực chữ
    ký thật (02_PDF_CHUYEN_SAU.md §3: "chuỗi tin cậy ... tình trạng thu
    hồi ... timestamp/LTV") là một engine RIÊNG, thuộc mốc M3, KHÔNG nằm
    trong phạm vi công cụ này.
  - Danh sách action nguy hiểm (``/Launch``, ``/JavaScript``, ``/SubmitForm``,
    ``/ImportData``, ``/GoToR``) là danh sách CỐ ĐỊNH theo PDF 1.7/2.0 Annex
    — có thể thiếu action type hiếm/độc quyền của một số trình tạo PDF.
  - PDF/A: module này CHỈ báo "có dấu hiệu khai PDF/A" (``/OutputIntent``
    S=GTS_PDFA*, XMP ``pdfaid:part``/``pdfaid:conformance``) — KHÔNG xác
    nhận tệp THẬT SỰ tuân thủ PDF/A; việc đó cần validator độc lập như
    veraPDF (04_KIEM_THU_PHAT_HANH.md §4), ngoài phạm vi công cụ này.
"""

from __future__ import annotations

from .inspector import (
    CompatLevel,
    DocumentStatus,
    Finding,
    InspectionReport,
    Severity,
    inspect_file,
)

__all__ = [
    "CompatLevel",
    "Severity",
    "DocumentStatus",
    "Finding",
    "InspectionReport",
    "inspect_file",
]
