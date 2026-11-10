"""PDF Compatibility/Safety Inspector — lõi phân tích (xem docstring ``__init__.py``).

An toàn: chỉ đọc cấu trúc object PDF qua pikepdf (ưu tiên)/pypdf (dự phòng khi
pikepdf không cài được hoặc không mở nổi tệp); KHÔNG bao giờ thực thi
JavaScript/action, KHÔNG render trang, KHÔNG mở socket, KHÔNG cố vượt mật
khẩu/quyền của tệp mã hoá. Mọi bước phân tích được cô lập trong try/except
riêng (một bước lỗi không được làm sập cả báo cáo) và có giới hạn độ sâu đệ
quy/số object quét để tránh treo máy trên tệp cố ý làm hỏng cấu trúc (zip-bomb
kiểu PDF: object graph lặp vòng, cây /Names sâu vô hạn...).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

try:
    import pikepdf

    _HAVE_PIKEPDF = True
except Exception:  # noqa: BLE001 — môi trường thiếu pikepdf vẫn phải chạy được (degrade)
    pikepdf = None  # type: ignore[assignment]
    _HAVE_PIKEPDF = False

try:
    import pypdf

    _HAVE_PYPDF = True
except Exception:  # noqa: BLE001
    pypdf = None  # type: ignore[assignment]
    _HAVE_PYPDF = False

__all__ = [
    "CompatLevel",
    "Severity",
    "DocumentStatus",
    "SEVERITY_EXIT_CODE",
    "Finding",
    "InspectionReport",
    "inspect_file",
]


# ---------------------------------------------------------------------------
# Hợp đồng dữ liệu: C0–C3 + severity + trạng thái tài liệu (05_PROMPT nhiệm vụ
# NaMiPDF; cùng khuôn với tools/office-compat/namioffice_inspect/inspector.py).
# ---------------------------------------------------------------------------


class CompatLevel(str, Enum):
    """Mức rủi ro của MỘT tính năng phát hiện được.

    C0 — không có dấu hiệu rủi ro (không tạo Finding).
    C1 — tính năng nâng cao/đáng chú ý nhưng ít rủi ro khi sửa/lưu lại.
    C2 — tính năng có thể cần bước xử lý riêng (OCR, kiểm NeedAppearances...)
         trước khi coi là "đã sẵn sàng sửa".
    C3 — rủi ro cao/chưa hỗ trợ an toàn (mã hoá, chữ ký số, JavaScript,
         action khởi chạy ngoài, XFA): phải cảnh báo rõ, không tự xử lý,
         không tự lưu đè.
    """

    C0 = "C0"
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"


_COMPAT_ORDER: dict[CompatLevel, int] = {
    CompatLevel.C0: 0,
    CompatLevel.C1: 1,
    CompatLevel.C2: 2,
    CompatLevel.C3: 3,
}


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


_SEVERITY_ORDER: dict[Severity, int] = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}

#: Mã thoát CLI theo severity cao nhất (xem tools/pdf-compat/namipdf-inspect).
SEVERITY_EXIT_CODE: dict[Severity, int] = {
    Severity.INFO: 0,
    Severity.LOW: 0,
    Severity.MEDIUM: 1,
    Severity.HIGH: 2,
    Severity.CRITICAL: 3,
}


class DocumentStatus(str, Enum):
    """Trạng thái bắt buộc hiển thị TRƯỚC KHI SỬA theo
    ``01_TINH_NANG_UIUX.md`` §3: "Text PDF / Scan image / Mixed / Signed /
    Protected". Thứ tự ưu tiên khi nhiều điều kiện cùng đúng (xem
    ``_document_status`` phía dưới): PROTECTED > SIGNED > (nội dung trang)."""

    TEXT_PDF = "text_pdf"
    SCAN_IMAGE = "scan_image"
    MIXED = "mixed"
    SIGNED = "signed"
    PROTECTED = "protected"
    UNKNOWN = "unknown"


_STATUS_VI: dict[DocumentStatus, str] = {
    DocumentStatus.TEXT_PDF: "Text PDF (có lớp chữ trích xuất được)",
    DocumentStatus.SCAN_IMAGE: "Scan image (toàn ảnh quét, chưa có lớp chữ)",
    DocumentStatus.MIXED: "Mixed (một số trang là ảnh quét, một số có chữ)",
    DocumentStatus.SIGNED: "Signed (đã có chữ ký số)",
    DocumentStatus.PROTECTED: "Protected (được bảo vệ bằng mật khẩu/quyền)",
    DocumentStatus.UNKNOWN: "Không xác định (không đọc được cấu trúc trang)",
}


@dataclass
class Finding:
    feature_id: str
    name_vi: str
    compat_level: CompatLevel
    severity: Severity
    detail_vi: str
    recommended_action_vi: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "feature_id": self.feature_id,
            "name": self.name_vi,
            "compat_level": self.compat_level.value,
            "severity": self.severity.value,
            "detail": self.detail_vi,
            "recommended_action": self.recommended_action_vi,
            "evidence": list(self.evidence),
        }


@dataclass
class InspectionReport:
    """Kết quả kiểm tra TĨNH một tệp PDF."""

    path: str
    engine: str  # "pikepdf" | "pypdf-fallback" | "none"
    pdf_version: str | None
    page_count: int | None
    producer: str | None
    creator: str | None
    is_linearized: bool | None
    requires_user_password: bool
    content_class: DocumentStatus  # chỉ 1 trong TEXT_PDF/SCAN_IMAGE/MIXED/UNKNOWN
    document_status: DocumentStatus  # trạng thái cuối cùng hiển thị cho UI
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def max_compat_level(self) -> CompatLevel:
        if not self.findings:
            return CompatLevel.C0
        return max((f.compat_level for f in self.findings), key=lambda level: _COMPAT_ORDER[level])

    @property
    def max_severity(self) -> Severity:
        if not self.findings:
            return Severity.INFO
        return max((f.severity for f in self.findings), key=lambda sev: _SEVERITY_ORDER[sev])

    @property
    def safe_to_overwrite(self) -> bool:
        """"An toàn để lưu đè bản gốc?" — quy tắc atomic-save của kit
        (04_KIEN_TRUC_KIEM_THU tương tự NaMiOffice + 05_PROMPT_CLAUDE_CODE.md:
        "cảnh báo khi tài liệu ký số/đã khóa và không ghi đè bản gốc").

        CHẶN lưu đè (False) khi:
          - trạng thái tài liệu là Signed hoặc Protected (chặn tường minh,
            bất kể mức C-level, để không phụ thuộc duy nhất vào thứ tự
            Finding — phòng thủ kép theo đúng yêu cầu nhiệm vụ), HOẶC
          - mức rủi ro cao nhất trong các Finding > C1.
        Ngược lại coi là an toàn lưu đè trực tiếp (vẫn nên giữ bản sao lưu
        thông thường theo chính sách autosave của NaMiPDF)."""
        if self.document_status in (DocumentStatus.SIGNED, DocumentStatus.PROTECTED):
            return False
        return _COMPAT_ORDER[self.max_compat_level] <= _COMPAT_ORDER[CompatLevel.C1]

    def find(self, feature_id: str) -> Finding | None:
        for f in self.findings:
            if f.feature_id == feature_id:
                return f
        return None

    def has_feature(self, prefix: str) -> bool:
        return any(f.feature_id == prefix or f.feature_id.startswith(prefix + ".") for f in self.findings)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "engine": self.engine,
            "pdf_version": self.pdf_version,
            "page_count": self.page_count,
            "producer": self.producer,
            "creator": self.creator,
            "is_linearized": self.is_linearized,
            "requires_user_password": self.requires_user_password,
            "content_class": self.content_class.value,
            "document_status": self.document_status.value,
            "findings": [f.to_dict() for f in self.findings],
            "notes": list(self.notes),
            "errors": list(self.errors),
            "max_compat_level": self.max_compat_level.value,
            "max_severity": self.max_severity.value,
            "safe_to_overwrite": self.safe_to_overwrite,
        }

    def to_text_vi(self) -> str:
        lines: list[str] = []
        lines.append("=== BÁO CÁO PDF COMPATIBILITY / SAFETY INSPECTOR (NaMiPDF) ===")
        lines.append(f"Tệp: {self.path}")
        lines.append(f"Engine phân tích: {self.engine}")
        lines.append(
            f"Phiên bản PDF: {self.pdf_version or '(không xác định)'} | "
            f"Số trang: {self.page_count if self.page_count is not None else '(không đọc được)'}"
        )
        lines.append(f"Producer: {self.producer or '(không có)'} | Creator: {self.creator or '(không có)'}")
        lines.append(
            "Linearized (tối ưu mở nhanh theo trang): "
            + ("CÓ" if self.is_linearized else ("KHÔNG" if self.is_linearized is not None else "(không xác định)"))
        )
        lines.append("")
        lines.append(f"TRẠNG THÁI TÀI LIỆU (bắt buộc hiển thị trước khi sửa): {_STATUS_VI[self.document_status]}")
        if self.content_class != self.document_status:
            lines.append(f"  (phân loại nội dung trang tham khảo thêm: {_STATUS_VI[self.content_class]})")
        lines.append("")

        if not self.findings:
            lines.append(
                "Không phát hiện tính năng rủi ro nào trong danh sách công cụ này kiểm tra. "
                "(Đây KHÔNG phải bảo đảm tuyệt đối — xem giới hạn trung thực ở __init__.py.)"
            )
        else:
            lines.append(f"Phát hiện {len(self.findings)} tính năng rủi ro/cần chú ý:")
            for f in self.findings:
                lines.append(f"  - [{f.compat_level.value}][{f.severity.value.upper()}] {f.feature_id} — {f.name_vi}")
                lines.append(f"      Chi tiết: {f.detail_vi}")
                lines.append(f"      Khuyến nghị: {f.recommended_action_vi}")
                if f.evidence:
                    shown = f.evidence[:8]
                    lines.append(f"      Bằng chứng: {', '.join(shown)}" + (" ..." if len(f.evidence) > 8 else ""))

        if self.notes:
            lines.append("")
            lines.append("Ghi chú/giới hạn khi phân tích:")
            for n in self.notes:
                lines.append(f"  * {n}")

        if self.errors:
            lines.append("")
            lines.append("Lỗi khi phân tích (không chặn, nhưng báo cáo có thể thiếu):")
            for e in self.errors:
                lines.append(f"  ! {e}")

        lines.append("")
        lines.append(
            f"TỔNG KẾT: mức rủi ro cao nhất = {self.max_compat_level.value}, "
            f"mức độ nghiêm trọng cao nhất = {self.max_severity.value.upper()}"
        )
        if self.safe_to_overwrite:
            lines.append("AN TOÀN GHI ĐÈ BẢN GỐC? CÓ (rủi ro thấp) — vẫn khuyến nghị giữ bản sao lưu thông thường.")
        else:
            lines.append(
                "AN TOÀN GHI ĐÈ BẢN GỐC? KHÔNG — khuyến nghị LƯU BẢN SAO (Save-As) sang tệp mới, "
                "GIỮ NGUYÊN bản gốc không đổi (không ghi đè im lặng)."
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Hằng số/giới hạn an toàn.
# ---------------------------------------------------------------------------

_HEADER_RE = re.compile(rb"%PDF-(\d\.\d)")
_HEADER_SCAN_BYTES = 2048  # PDF spec cho phép junk trước %PDF- trong vài byte đầu

#: Operator "hiển thị chữ" trong content stream (PDF 2.0 §9.4.3). Chỉ các
#: operator này mới tính là "trang có lớp chữ" — KHÔNG suy luận từ việc có
#: /Font trong Resources (nhiều công cụ tạo PDF khai báo Font dù không vẽ
#: chữ nào lên trang — đã xác minh trực tiếp với ReportLab khi test module).
_TEXT_SHOW_OPS = {"Tj", "TJ", "'", '"'}

_MAX_XOBJECT_DEPTH = 12
_MAX_ACTION_DEPTH = 10
_MAX_PAGES_SCANNED = 3000
_MAX_OBJECTS_FOR_ATTACHMENT_SCAN = 50_000
_MAX_NAME_TREE_DEPTH = 16

#: Loại action nguy hiểm (PDF 2.0 Annex) ngoài JavaScript — không tự thực thi
#: BẤT KỲ loại nào trong số này (03_KIEN_TRUC_BAO_MAT.md §2/§4).
_EXTERNAL_REF_ACTION_TYPES = {"/SubmitForm", "/ImportData", "/GoToR"}


# ---------------------------------------------------------------------------
# Helper cấp thấp dùng chung.
# ---------------------------------------------------------------------------


def _read_header_version(path: str, errors: list[str]) -> str | None:
    """Đọc version PDF trực tiếp từ magic header ``%PDF-x.y`` trong vài KB
    đầu tệp — KHÔNG cần giải mã/mở tệp, nên vẫn dùng được cả khi tệp yêu cầu
    mật khẩu người dùng mà ta chưa có (phần header không bao giờ bị mã hoá)."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(_HEADER_SCAN_BYTES)
    except OSError as exc:
        errors.append(f"không đọc được byte đầu tệp: {exc}")
        return None
    m = _HEADER_RE.search(head)
    if not m:
        return None
    return m.group(1).decode("ascii")


def _vi_permissions(allow) -> str:
    """Diễn giải tiếng Việt cho ``pikepdf.Pdf.allow`` (Permissions) — chỉ
    LIỆT KÊ quyền bị tệp giới hạn, không bao giờ dùng để TỰ GỠ giới hạn."""
    labels = {
        "print_lowres": "in (độ phân giải thấp)",
        "print_highres": "in (độ phân giải cao)",
        "modify_annotation": "thêm/sửa chú thích",
        "modify_assembly": "chèn/xoá/sắp xếp trang",
        "modify_form": "điền/sửa biểu mẫu",
        "modify_other": "sửa nội dung khác",
        "extract": "trích xuất nội dung (copy text/ảnh)",
        "accessibility": "trích xuất cho công cụ hỗ trợ tiếp cận",
    }
    denied = [vi for attr, vi in labels.items() if getattr(allow, attr, True) is False]
    if not denied:
        return "không giới hạn quyền nào (chỉ mã hoá, không hạn chế thao tác)"
    return "BỊ CHẶN: " + ", ".join(denied)


def _name_tree_entries(node, depth: int = 0) -> list[tuple[str, object]]:
    """Duyệt một PDF name tree (``/Names`` [+ ``/Kids``]) — dùng cho cả
    ``/Names/EmbeddedFiles`` và ``/Names/JavaScript``. Có giới hạn độ sâu để
    chống cây lồng vô hạn/vòng lặp cố ý."""
    if node is None or depth > _MAX_NAME_TREE_DEPTH:
        return []
    out: list[tuple[str, object]] = []
    try:
        names = node.get("/Names")
    except Exception:  # noqa: BLE001
        names = None
    if names is not None:
        try:
            items = list(names)
        except Exception:  # noqa: BLE001
            items = []
        for i in range(0, len(items) - 1, 2):
            try:
                key = str(items[i])
            except Exception:  # noqa: BLE001
                key = f"(tên #{i // 2})"
            out.append((key, items[i + 1]))
    try:
        kids = node.get("/Kids")
    except Exception:  # noqa: BLE001
        kids = None
    if kids is not None:
        try:
            kid_list = list(kids)
        except Exception:  # noqa: BLE001
            kid_list = []
        for kid in kid_list:
            out.extend(_name_tree_entries(kid, depth + 1))
    return out


@dataclass
class _ActionHit:
    source: str
    is_auto: bool  # True = tự chạy theo tài liệu/trang (OpenAction/AA cấp catalog|trang); False = cần tương tác
    subtype: str | None
    action: object


def _collect_actions(pdf) -> list[_ActionHit]:
    """Thu thập MỌI action dict tiếp cận được qua các đường chuẩn (catalog
    OpenAction/AA, name tree JavaScript, trang AA, annotation A/AA, field
    AA), theo chuỗi ``/Next`` có giới hạn độ sâu + chống vòng lặp. KHÔNG bao
    giờ gọi/diễn giải nội dung action — chỉ đọc ``/S``/``/JS``/... làm bằng
    chứng tĩnh."""
    hits: list[_ActionHit] = []
    visited_objgens: set[tuple[int, int]] = set()

    def _objgen(obj) -> tuple[int, int] | None:
        try:
            return obj.objgen
        except Exception:  # noqa: BLE001
            return None

    def _walk(action, source: str, is_auto: bool, depth: int) -> None:
        if action is None or depth > _MAX_ACTION_DEPTH:
            return
        if isinstance(action, pikepdf.Array):
            return  # OpenAction kiểu "destination" (mảng), không phải action dict
        og = _objgen(action)
        if og is not None:
            if og in visited_objgens:
                return
            visited_objgens.add(og)
        try:
            subtype_obj = action.get("/S")
        except Exception:  # noqa: BLE001
            subtype_obj = None
        subtype = str(subtype_obj) if subtype_obj is not None else None
        hits.append(_ActionHit(source=source, is_auto=is_auto, subtype=subtype, action=action))
        try:
            nxt = action.get("/Next")
        except Exception:  # noqa: BLE001
            nxt = None
        if nxt is None:
            return
        next_list = list(nxt) if isinstance(nxt, pikepdf.Array) else [nxt]
        for i, n in enumerate(next_list):
            _walk(n, f"{source}.Next[{i}]", is_auto, depth + 1)

    def _walk_aa_dict(aa, source_prefix: str, is_auto: bool) -> None:
        if aa is None:
            return
        try:
            items = list(aa.items())
        except Exception:  # noqa: BLE001
            return
        for trigger, act in items:
            _walk(act, f"{source_prefix}.AA[{trigger}]", is_auto, 0)

    try:
        _walk(pdf.Root.get("/OpenAction"), "catalog.OpenAction", True, 0)
    except Exception:  # noqa: BLE001
        pass
    try:
        _walk_aa_dict(pdf.Root.get("/AA"), "catalog", True)
    except Exception:  # noqa: BLE001
        pass
    try:
        names = pdf.Root.get("/Names")
        js_tree = names.get("/JavaScript") if names is not None else None
        for name_key, entry in _name_tree_entries(js_tree):
            _walk(entry, f"names.JavaScript[{name_key}]", True, 0)
    except Exception:  # noqa: BLE001
        pass

    try:
        pages = pdf.pages
    except Exception:  # noqa: BLE001
        pages = []
    for p_idx, page in enumerate(pages):
        try:
            _walk_aa_dict(page.get("/AA"), f"page{p_idx}", True)
        except Exception:  # noqa: BLE001
            pass
        try:
            annots = page.get("/Annots") or []
            annot_list = list(annots)
        except Exception:  # noqa: BLE001
            annot_list = []
        for a_idx, annot in enumerate(annot_list):
            try:
                _walk(annot.get("/A"), f"page{p_idx}.annot{a_idx}.A", False, 0)
            except Exception:  # noqa: BLE001
                pass
            try:
                _walk_aa_dict(annot.get("/AA"), f"page{p_idx}.annot{a_idx}", False)
            except Exception:  # noqa: BLE001
                pass

    def _walk_fields(fields_array, prefix: str) -> None:
        try:
            items = list(fields_array)
        except Exception:  # noqa: BLE001
            return
        for f_idx, fld in enumerate(items):
            try:
                t_val = fld.get("/T")
                label = str(t_val) if t_val is not None else f"#{f_idx}"
            except Exception:  # noqa: BLE001
                label = f"#{f_idx}"
            try:
                _walk_aa_dict(fld.get("/AA"), f"{prefix}field[{label}]", False)
            except Exception:  # noqa: BLE001
                pass
            try:
                kids = fld.get("/Kids")
            except Exception:  # noqa: BLE001
                kids = None
            if kids is not None:
                _walk_fields(kids, f"{prefix}field[{label}].")

    try:
        acroform = pdf.Root.get("/AcroForm")
        if acroform is not None:
            _walk_fields(acroform.get("/Fields") or [], "")
    except Exception:  # noqa: BLE001
        pass

    return hits


# ---------------------------------------------------------------------------
# Các bước kiểm tra (mỗi hàm trả list[Finding], không ném lỗi ra ngoài khi
# được gọi qua wrapper try/except của ``inspect_file``).
# ---------------------------------------------------------------------------


def _check_encryption(pdf) -> list[Finding]:
    if not pdf.is_encrypted:
        return []
    enc = pdf.encryption
    detail_bits = [f"R={enc.R}, V={enc.V}, {enc.bits} bit, phương thức={enc.stream_method}"]
    detail_bits.append(f"quyền: {_vi_permissions(pdf.allow)}")
    if pdf.owner_password_matched:
        detail_bits.append("đã mở bằng mật khẩu CHỦ SỞ HỮU được cấp")
    elif pdf.user_password_matched:
        detail_bits.append("mở được bằng mật khẩu người dùng rỗng/đã cấp (không cần hỏi thêm)")
    return [Finding(
        feature_id="security.encryption",
        name_vi="Mã hoá / mật khẩu / giới hạn quyền (/Encrypt)",
        compat_level=CompatLevel.C3,
        severity=Severity.HIGH,
        detail_vi="; ".join(detail_bits),
        recommended_action_vi=(
            "Tệp được bảo vệ (mã hoá + có thể kèm giới hạn quyền). KHÔNG cố vượt mật khẩu "
            "hoặc gỡ giới hạn quyền dưới bất kỳ hình thức nào. Tôn trọng cờ quyền (in/copy/"
            "sửa/assembly) do chủ sở hữu đặt; chỉ cho thao tác bị giới hạn khi người dùng "
            "cung cấp đúng mật khẩu chủ sở hữu qua hộp thoại chính thức."
        ),
        evidence=detail_bits,
    )]


def _check_signatures(pdf) -> list[Finding]:
    sig_sources: list[str] = []
    has_docmdp = False
    try:
        perms = pdf.Root.get("/Perms")
        if perms is not None and perms.get("/DocMDP") is not None:
            has_docmdp = True
            sig_sources.append("catalog.Perms.DocMDP (chữ ký CHỨNG THỰC — certification signature)")
    except Exception:  # noqa: BLE001
        pass

    def _walk_fields(fields_array, prefix: str) -> None:
        try:
            items = list(fields_array)
        except Exception:  # noqa: BLE001
            return
        for f_idx, fld in enumerate(items):
            try:
                t_val = fld.get("/T")
                label = str(t_val) if t_val is not None else f"#{f_idx}"
            except Exception:  # noqa: BLE001
                label = f"#{f_idx}"
            try:
                v = fld.get("/V")
                ft = fld.get("/FT")
                is_sig_value = v is not None and (
                    (ft is not None and str(ft) == "/Sig")
                    or (hasattr(v, "get") and v.get("/Type") is not None and str(v.get("/Type")) == "/Sig")
                )
                if is_sig_value:
                    byte_range = v.get("/ByteRange") if hasattr(v, "get") else None
                    detail = f"field[{prefix}{label}]"
                    if byte_range is not None:
                        detail += f" ByteRange={list(byte_range)}"
                    sig_sources.append(detail)
            except Exception:  # noqa: BLE001
                pass
            try:
                kids = fld.get("/Kids")
            except Exception:  # noqa: BLE001
                kids = None
            if kids is not None:
                _walk_fields(kids, f"{prefix}{label}.")

    try:
        acroform = pdf.Root.get("/AcroForm")
        if acroform is not None:
            _walk_fields(acroform.get("/Fields") or [], "")
    except Exception:  # noqa: BLE001
        pass

    if not sig_sources:
        return []
    return [Finding(
        feature_id="signature.digital",
        name_vi="Chữ ký số (trường /Sig và/hoặc /Perms /DocMDP)",
        compat_level=CompatLevel.C3,
        severity=Severity.HIGH,
        detail_vi=(
            f"tìm thấy {len(sig_sources)} vị trí chữ ký số"
            + (" (có chữ ký CHỨNG THỰC DocMDP)" if has_docmdp else "")
            + f": {', '.join(sig_sources)}"
        ),
        recommended_action_vi=(
            "Tài liệu ĐÃ CÓ chữ ký số. Sửa nội dung — kể cả lưu lại bằng NaMiPDF — sẽ làm "
            "MẤT HIỆU LỰC chữ ký hiện có (và có thể vi phạm giới hạn DocMDP nếu có). KHÔNG "
            "tự ý sửa; nếu cần sửa, lưu BẢN SAO riêng và yêu cầu ký lại từ người có thẩm "
            "quyền. LƯU Ý: công cụ này CHỈ phát hiện SỰ TỒN TẠI chữ ký — KHÔNG xác thực "
            "chuỗi tin cậy/OCSP/CRL/thu hồi/thời gian; không hiển thị huy hiệu 'hợp lệ' chỉ "
            "từ kết quả này (việc xác thực chữ ký thật là engine riêng — mốc M3)."
        ),
        evidence=sig_sources,
    )]


def _check_scripts_and_actions(action_hits: list[_ActionHit]) -> list[Finding]:
    findings: list[Finding] = []

    def _evidence_for_js(hit: _ActionHit) -> str:
        try:
            js_val = hit.action.get("/JS")
        except Exception:  # noqa: BLE001
            js_val = None
        if js_val is None:
            return hit.source
        try:
            text = bytes(js_val).decode("utf-8", errors="replace") if hasattr(js_val, "read_bytes") or isinstance(js_val, (bytes, bytearray)) else str(js_val)
        except Exception:  # noqa: BLE001
            text = "(không đọc được nội dung)"
        text = text.strip().replace("\n", " ")[:60]
        return f"{hit.source} JS[:60]={text!r}"

    js_hits = [h for h in action_hits if h.subtype == "/JavaScript"]
    if js_hits:
        findings.append(Finding(
            feature_id="script.javascript",
            name_vi="JavaScript nhúng trong PDF (/JavaScript, /JS)",
            compat_level=CompatLevel.C3,
            severity=Severity.HIGH,
            detail_vi=f"tìm thấy {len(js_hits)} action JavaScript trong tài liệu.",
            recommended_action_vi=(
                "KHÔNG bao giờ tự chạy bất kỳ JavaScript nào trong PDF (03_KIEN_TRUC_BAO_MAT.md "
                "§4: 'Tắt PDF JavaScript ... mặc định'). Chỉ hiển thị sự tồn tại cho người dùng "
                "nâng cao xem mã nguồn (read-only), không có nút 'Chạy'."
            ),
            evidence=[_evidence_for_js(h) for h in js_hits][:20],
        ))

    launch_hits = [h for h in action_hits if h.subtype == "/Launch"]
    if launch_hits:
        findings.append(Finding(
            feature_id="action.launch_external",
            name_vi="Action /Launch — khởi chạy chương trình/tệp ngoài",
            compat_level=CompatLevel.C3,
            severity=Severity.CRITICAL,
            detail_vi=f"tìm thấy {len(launch_hits)} action /Launch: {', '.join(h.source for h in launch_hits[:10])}",
            recommended_action_vi=(
                "Loại action NGUY HIỂM NHẤT trong PDF — có thể khởi chạy tệp thực thi/tài liệu "
                "ngoài. KHÔNG bao giờ tự thực thi dưới bất kỳ hình thức nào (kể cả khi người "
                "dùng bấm — cần hộp thoại cảnh báo tường minh riêng biệt, không phải xác nhận "
                "thường)."
            ),
            evidence=[h.source for h in launch_hits],
        ))

    auto_hits = [h for h in action_hits if h.is_auto]
    if auto_hits:
        triggers = sorted({h.source.split(".")[0] + (".AA" if ".AA" in h.source else ".OpenAction" if "OpenAction" in h.source else ".Names") for h in auto_hits})
        findings.append(Finding(
            feature_id="action.auto_open",
            name_vi="Hành động tự động khi mở/đóng tài liệu hoặc trang (/OpenAction, /AA, Names/JavaScript)",
            compat_level=CompatLevel.C2,
            severity=Severity.MEDIUM,
            detail_vi=f"tìm thấy {len(auto_hits)} action tự động, ví dụ nguồn: {', '.join(triggers[:10])}",
            recommended_action_vi=(
                "KHÔNG tự thực thi BẤT KỲ action nào gắn ở sự kiện mở/đóng tài liệu hoặc "
                "trang, bất kể loại action là gì. Nếu NaMiPDF có tuỳ chọn cho phép auto-action "
                "(mặc định tắt), phải hiển thị rõ loại action và xin xác nhận trước mỗi lần."
            ),
            evidence=[h.source for h in auto_hits][:20],
        ))

    ext_hits = [h for h in action_hits if h.subtype in _EXTERNAL_REF_ACTION_TYPES]
    if ext_hits:
        by_type: dict[str, int] = {}
        for h in ext_hits:
            by_type[h.subtype or "?"] = by_type.get(h.subtype or "?", 0) + 1
        findings.append(Finding(
            feature_id="action.external_reference",
            name_vi="Action tham chiếu/gửi dữ liệu ra ngoài (/SubmitForm, /ImportData, /GoToR)",
            compat_level=CompatLevel.C2,
            severity=Severity.MEDIUM,
            detail_vi="; ".join(f"{k}×{v}" for k, v in sorted(by_type.items())),
            recommended_action_vi=(
                "Các action này có thể gửi dữ liệu biểu mẫu ra URL ngoài (/SubmitForm), nhập dữ "
                "liệu từ nguồn ngoài (/ImportData), hoặc điều hướng sang tệp PDF khác "
                "(/GoToR). KHÔNG tự thực thi/tự fetch mạng; hiển thị đích rõ ràng và xin xác "
                "nhận trước khi cho phép."
            ),
            evidence=[h.source for h in ext_hits][:20],
        ))

    uri_hits = [h for h in action_hits if h.subtype == "/URI"]
    if uri_hits:
        targets = []
        for h in uri_hits:
            try:
                targets.append(str(h.action.get("/URI")))
            except Exception:  # noqa: BLE001
                targets.append("(không đọc được URI)")
        findings.append(Finding(
            feature_id="link.external_uri",
            name_vi="Liên kết ngoài (action /URI)",
            compat_level=CompatLevel.C1,
            severity=Severity.LOW,
            detail_vi=f"{len(uri_hits)} liên kết URI: {', '.join(targets[:5])}" + (" ..." if len(targets) > 5 else ""),
            recommended_action_vi=(
                "Liên kết ra Internet/giao thức ngoài. KHÔNG tự mở; hiển thị RÕ tên miền đích và "
                "xác nhận trước khi điều hướng, như quy định ở 01_TINH_NANG_UIUX.md §1."
            ),
            evidence=targets,
        ))

    return findings


def _check_embedded_files(pdf) -> list[Finding]:
    found: dict[tuple[int, int] | str, str] = {}

    try:
        names = pdf.Root.get("/Names")
        ef_tree = names.get("/EmbeddedFiles") if names is not None else None
        for name_key, filespec in _name_tree_entries(ef_tree):
            key = _safe_objgen(filespec) or f"names:{name_key}"
            found[key] = f"Names/EmbeddedFiles[{name_key}]"
    except Exception:  # noqa: BLE001
        pass

    try:
        for p_idx, page in enumerate(pdf.pages):
            try:
                annots = list(page.get("/Annots") or [])
            except Exception:  # noqa: BLE001
                annots = []
            for a_idx, annot in enumerate(annots):
                try:
                    subtype = annot.get("/Subtype")
                except Exception:  # noqa: BLE001
                    subtype = None
                if subtype is not None and str(subtype) == "/FileAttachment":
                    try:
                        fs = annot.get("/FS")
                    except Exception:  # noqa: BLE001
                        fs = None
                    key = _safe_objgen(fs) or f"page{p_idx}annot{a_idx}"
                    found.setdefault(key, f"page{p_idx}.annot{a_idx} (FileAttachment)")
    except Exception:  # noqa: BLE001
        pass

    try:
        count = 0
        for obj in pdf.objects:
            count += 1
            if count > _MAX_OBJECTS_FOR_ATTACHMENT_SCAN:
                break
            try:
                if not hasattr(obj, "get"):
                    continue
                type_val = obj.get("/Type")
                has_ef = obj.get("/EF") is not None
            except Exception:  # noqa: BLE001
                continue
            if (type_val is not None and str(type_val) == "/Filespec") or has_ef:
                key = _safe_objgen(obj) or f"obj:{count}"
                found.setdefault(key, f"object quét toàn cục #{count} (Filespec/EF)")
    except Exception:  # noqa: BLE001
        pass

    if not found:
        return []
    return [Finding(
        feature_id="attachment.embedded_file",
        name_vi="Tệp đính kèm/nhúng (/EmbeddedFile, /Filespec)",
        compat_level=CompatLevel.C2,
        severity=Severity.MEDIUM,
        detail_vi=f"tìm thấy {len(found)} tệp đính kèm: {', '.join(list(found.values())[:10])}",
        recommended_action_vi=(
            "Tệp đính kèm KHÔNG được tự mở/tự chạy dưới bất kỳ định dạng nào (kể cả tưởng như "
            "vô hại như .txt/.csv). Chỉ hiển thị danh sách + cho phép người dùng chủ động lưu "
            "ra đĩa rồi tự mở bằng ứng dụng họ chọn; quét virus theo chính sách hệ thống trước "
            "khi lưu nếu NaMiOS có dịch vụ đó."
        ),
        evidence=list(found.values())[:20],
    )]


def _safe_objgen(obj) -> tuple[int, int] | None:
    if obj is None:
        return None
    try:
        return obj.objgen
    except Exception:  # noqa: BLE001
        return None


def _check_forms(pdf) -> list[Finding]:
    findings: list[Finding] = []
    try:
        acroform = pdf.Root.get("/AcroForm")
    except Exception:  # noqa: BLE001
        acroform = None
    if acroform is None:
        return findings

    xfa = None
    try:
        xfa = acroform.get("/XFA")
    except Exception:  # noqa: BLE001
        xfa = None
    if xfa is not None:
        findings.append(Finding(
            feature_id="form.xfa",
            name_vi="Biểu mẫu XFA (XML Forms Architecture, /AcroForm /XFA)",
            compat_level=CompatLevel.C3,
            severity=Severity.HIGH,
            detail_vi="AcroForm có khoá /XFA (biểu mẫu động kiểu Adobe LiveCycle).",
            recommended_action_vi=(
                "XFA (biểu mẫu động) KHÔNG được Poppler/Okular và phần lớn renderer mã nguồn mở "
                "hỗ trợ điền đầy đủ/an toàn. CHỈ cho xem (nếu có bản trình bày tĩnh kèm theo), "
                "KHÔNG cho điền qua đường XFA, KHÔNG xoá /XFA khi lưu (02_PDF_CHUYEN_SAU.md §2: "
                "'không làm mất XFA khi lưu'). Đề nghị người dùng dùng Adobe Reader thật nếu cần "
                "điền đúng."
            ),
            evidence=["AcroForm.XFA"],
        ))

    try:
        field_list_raw = acroform.get("/Fields")
        field_list = list(field_list_raw) if field_list_raw is not None else []
    except Exception:  # noqa: BLE001
        field_list = []
    if field_list:
        needs_appearances = False
        try:
            na = acroform.get("/NeedAppearances")
            needs_appearances = bool(na)
        except Exception:  # noqa: BLE001
            pass
        compat = CompatLevel.C2 if needs_appearances else CompatLevel.C1
        severity = Severity.MEDIUM if needs_appearances else Severity.LOW
        detail = f"AcroForm có {len(field_list)} field gốc (không tính Kids lồng)."
        if needs_appearances:
            detail += (
                " /NeedAppearances=true: trình xem PHẢI tự sinh lại hình thức hiển thị trường — "
                "một số renderer không làm (hoặc làm sai), có thể hiển thị trường trống/sai."
            )
        findings.append(Finding(
            feature_id="form.acroform",
            name_vi="Biểu mẫu AcroForm (/AcroForm /Fields)",
            compat_level=compat,
            severity=severity,
            detail_vi=detail,
            recommended_action_vi=(
                "Điền được, nhưng PHẢI kiểm lại giá trị/appearance/tab order sau khi lưu bằng "
                "một trình xem PDF độc lập trước khi tin là đã giữ đúng "
                "(02_PDF_CHUYEN_SAU.md §2)." + (
                    " Vì có /NeedAppearances=true, nên chủ động sinh appearance stream khi lưu "
                    "(không chỉ đặt cờ) để tránh phụ thuộc hành vi renderer khác."
                    if needs_appearances else ""
                )
            ),
            evidence=[f"fields={len(field_list)}", f"NeedAppearances={needs_appearances}"],
        ))
    return findings


def _check_pdfa_hint(pdf) -> list[Finding]:
    evidence: list[str] = []
    try:
        output_intents = pdf.Root.get("/OutputIntents")
        if output_intents is not None:
            for oi in list(output_intents):
                try:
                    s_val = oi.get("/S")
                except Exception:  # noqa: BLE001
                    s_val = None
                if s_val is not None and str(s_val).startswith("/GTS_PDFA"):
                    evidence.append(f"OutputIntent.S={s_val}")
    except Exception:  # noqa: BLE001
        pass
    try:
        with pdf.open_metadata() as meta:
            for key in meta.keys():
                if "pdfa/ns/id" in key:
                    evidence.append(f"XMP {key}={meta[key]!r}")
    except Exception:  # noqa: BLE001
        pass
    if not evidence:
        return []
    return [Finding(
        feature_id="format.pdfa_hint",
        name_vi="Gợi ý khai báo PDF/A (/OutputIntent GTS_PDFA*, XMP pdfaid)",
        compat_level=CompatLevel.C1,
        severity=Severity.INFO,
        detail_vi=f"tìm thấy {len(evidence)} dấu hiệu: {', '.join(evidence[:10])}",
        recommended_action_vi=(
            "Đây CHỈ LÀ GỢI Ý tài liệu TỰ KHAI PDF/A — KHÔNG phải xác nhận tuân thủ thật. CHỈ "
            "gắn nhãn 'PDF/A' sau khi chạy validator độc lập (veraPDF) và lưu report "
            "(02_PDF_CHUYEN_SAU.md §5: 'không ghi PDF/A chỉ vì có dropdown')."
        ),
        evidence=evidence,
    )]


def _check_pdf_version(pdf) -> list[Finding]:
    try:
        version = pdf.pdf_version
    except Exception:  # noqa: BLE001
        return []
    if version != "2.0":
        return []
    return [Finding(
        feature_id="format.pdf20",
        name_vi="PDF 2.0 (ISO 32000-2)",
        compat_level=CompatLevel.C1,
        severity=Severity.LOW,
        detail_vi="Tệp khai phiên bản PDF 2.0.",
        recommended_action_vi=(
            "PDF 2.0 còn ít phổ biến; một số renderer/thư viện (bản Poppler/MuPDF cũ) hỗ trợ "
            "chưa đầy đủ các tính năng mới (mã hoá AES-256 R6, chữ ký mới...). Kiểm bằng tệp "
            "thật trên phiên bản engine PIN cụ thể trước khi khẳng định tương thích."
        ),
        evidence=[f"version={version}"],
    )]


def _scan_has_text(owner, resources, depth: int, visited: set) -> bool:
    if depth > _MAX_XOBJECT_DEPTH:
        return False
    try:
        instrs = pikepdf.parse_content_stream(owner)
    except Exception:  # noqa: BLE001
        return False
    for instr in instrs:
        try:
            if str(instr.operator) in _TEXT_SHOW_OPS:
                return True
        except Exception:  # noqa: BLE001
            continue
    xobject_dict = None
    if resources is not None:
        try:
            xobject_dict = resources.get("/XObject")
        except Exception:  # noqa: BLE001
            xobject_dict = None
    if xobject_dict is None:
        return False
    try:
        keys = list(xobject_dict.keys())
    except Exception:  # noqa: BLE001
        return False
    for key in keys:
        try:
            xobj = xobject_dict.get(key)
        except Exception:  # noqa: BLE001
            continue
        if xobj is None or not hasattr(xobj, "get"):
            continue
        try:
            subtype = xobj.get("/Subtype")
        except Exception:  # noqa: BLE001
            subtype = None
        if subtype is None or str(subtype) != "/Form":
            continue
        og = _safe_objgen(xobj)
        if og is not None:
            if og in visited:
                continue
            visited.add(og)
        try:
            child_resources = xobj.get("/Resources") or resources
        except Exception:  # noqa: BLE001
            child_resources = resources
        if _scan_has_text(xobj, child_resources, depth + 1, visited):
            return True
    return False


def _classify_content(pdf, notes: list[str]) -> tuple[DocumentStatus, list[str], list[str]]:
    """Trả (content_class, trang_scan_only, trang_co_chu) — xem giới hạn
    trung thực đầy đủ ở docstring ``__init__.py``."""
    try:
        pages = pdf.pages
        total = len(pages)
    except Exception as exc:  # noqa: BLE001
        notes.append(f"không đọc được danh sách trang để phân loại nội dung: {exc!r}")
        return DocumentStatus.UNKNOWN, [], []

    if total == 0:
        notes.append("tài liệu không có trang nào.")
        return DocumentStatus.UNKNOWN, [], []

    scan_count = 0
    text_count = 0
    scan_pages: list[str] = []
    text_pages: list[str] = []
    scanned_total = min(total, _MAX_PAGES_SCANNED)
    if scanned_total < total:
        notes.append(
            f"tài liệu có {total} trang, chỉ phân loại nội dung {scanned_total} trang đầu "
            f"(giới hạn an toàn {_MAX_PAGES_SCANNED} trang/lần quét)."
        )

    for idx in range(scanned_total):
        page = pages[idx]
        try:
            has_image = bool(page.get_images(recursive=True))
        except Exception:  # noqa: BLE001
            has_image = False
        try:
            resources = page.get("/Resources")
        except Exception:  # noqa: BLE001
            resources = None
        has_text = _scan_has_text(page, resources, 0, set())
        if has_text:
            text_count += 1
            text_pages.append(f"trang {idx + 1}")
        elif has_image:
            scan_count += 1
            scan_pages.append(f"trang {idx + 1}")

    if scan_count == 0:
        return DocumentStatus.TEXT_PDF, scan_pages, text_pages
    if text_count == 0:
        return DocumentStatus.SCAN_IMAGE, scan_pages, text_pages
    return DocumentStatus.MIXED, scan_pages, text_pages


def _content_findings(content_class: DocumentStatus, scan_pages: list[str], text_pages: list[str]) -> list[Finding]:
    if content_class == DocumentStatus.SCAN_IMAGE:
        return [Finding(
            feature_id="content.scan_image",
            name_vi="Toàn bộ trang là ảnh quét, không có lớp chữ trích xuất được",
            compat_level=CompatLevel.C2,
            severity=Severity.MEDIUM,
            detail_vi=f"{len(scan_pages)} trang không có operator hiển thị chữ (Tj/TJ) nhưng có ảnh.",
            recommended_action_vi=(
                "Đây là bản SCAN (ảnh), không phải văn bản có thể sửa trực tiếp. Cần chạy OCR "
                "tiếng Việt để tạo lớp chữ có toạ độ TRƯỚC KHI cho phép sửa/tìm/copy văn bản; "
                "giữ nguyên ảnh gốc khi tạo 'PDF có thể tìm kiếm' (02_PDF_CHUYEN_SAU.md §1)."
            ),
            evidence=scan_pages[:20],
        )]
    if content_class == DocumentStatus.MIXED:
        return [Finding(
            feature_id="content.mixed_pages",
            name_vi="Tài liệu hỗn hợp: có cả trang chữ và trang ảnh quét",
            compat_level=CompatLevel.C2,
            severity=Severity.MEDIUM,
            detail_vi=(
                f"{len(text_pages)} trang có lớp chữ, {len(scan_pages)} trang chỉ có ảnh "
                f"(scan): {', '.join(scan_pages[:10])}" + (" ..." if len(scan_pages) > 10 else "")
            ),
            recommended_action_vi=(
                "Sửa nội dung thực chỉ an toàn trên các trang có lớp chữ; các trang scan cần "
                "OCR riêng trước khi sửa. KHÔNG áp dụng 'sửa toàn tài liệu' một lượt mà không "
                "phân biệt hai loại trang này."
            ),
            evidence=scan_pages[:20],
        )]
    return []


# ---------------------------------------------------------------------------
# Hàm công khai chính — nhánh pikepdf (đầy đủ tính năng).
# ---------------------------------------------------------------------------


def _document_status(is_encrypted: bool, requires_password: bool, has_signature: bool,
                      content_class: DocumentStatus) -> DocumentStatus:
    """Thứ tự ưu tiên trạng thái UI bắt buộc (01_TINH_NANG_UIUX.md §3):
    Protected > Signed > (Text/Scan/Mixed/Unknown). Protected đứng đầu vì có
    thể chặn hoàn toàn việc đọc nội dung; Signed đứng sau vì luôn chặn sửa
    bất kể nội dung là gì."""
    if requires_password or is_encrypted:
        return DocumentStatus.PROTECTED
    if has_signature:
        return DocumentStatus.SIGNED
    return content_class


def _empty_report(path: str, engine: str, errors: list[str], notes: list[str] | None = None,
                   requires_user_password: bool = False, header_version: str | None = None) -> InspectionReport:
    status = DocumentStatus.PROTECTED if requires_user_password else DocumentStatus.UNKNOWN
    return InspectionReport(
        path=path, engine=engine, pdf_version=header_version, page_count=None,
        producer=None, creator=None, is_linearized=None,
        requires_user_password=requires_user_password,
        content_class=DocumentStatus.UNKNOWN, document_status=status,
        findings=[_protected_password_finding()] if requires_user_password else [],
        notes=notes or [], errors=errors,
    )


def _protected_password_finding() -> Finding:
    return Finding(
        feature_id="security.encryption",
        name_vi="Mã hoá / mật khẩu / giới hạn quyền (/Encrypt)",
        compat_level=CompatLevel.C3,
        severity=Severity.CRITICAL,
        detail_vi="Tệp yêu cầu MẬT KHẨU NGƯỜI DÙNG để mở mà không có/không đúng mật khẩu được cấp.",
        recommended_action_vi=(
            "KHÔNG cố vượt mật khẩu dưới bất kỳ hình thức nào (không brute-force, không dò, "
            "không dùng công cụ bên thứ ba để bẻ khoá). Dừng phân tích nội dung; chỉ tiếp tục "
            "khi người dùng cung cấp đúng mật khẩu qua hộp thoại chính thức của NaMiPDF."
        ),
        evidence=["PasswordError khi mở không mật khẩu/mật khẩu không đúng"],
    )


def inspect_file(path: str, password: str | None = None) -> InspectionReport:
    """Kiểm tra TĨNH một tệp PDF — KHÔNG render, KHÔNG thực thi JavaScript/
    action, KHÔNG gọi mạng, KHÔNG cố vượt mật khẩu nếu không được cung cấp.

    ``password``: mật khẩu do NGƯỜI DÙNG chủ động cung cấp qua hộp thoại
    chính thức (ví dụ họ là chủ sở hữu tệp) — KHÔNG phải cơ chế bẻ khoá; nếu
    bỏ trống, công cụ chỉ thử mật khẩu rỗng (hành vi mặc định của pikepdf),
    đúng với tệp chỉ giới hạn QUYỀN mà không yêu cầu mật khẩu người dùng.

    Trả về :class:`InspectionReport`; không ném lỗi ra ngoài — lỗi được gom
    vào ``report.errors`` để báo cáo vẫn trả về được (trừ khi bản thân tệp
    không đọc được từ đĩa — lỗi OSError hiếm, vẫn trả report rỗng kèm lỗi)."""
    errors: list[str] = []
    notes: list[str] = []
    header_version = _read_header_version(path, errors)
    if header_version is None:
        notes.append(
            "không tìm thấy magic header '%PDF-x.y' trong "
            f"{_HEADER_SCAN_BYTES} byte đầu — tệp có thể không phải PDF hoặc hỏng nặng."
        )

    if not _HAVE_PIKEPDF:
        notes.append("pikepdf KHÔNG cài được trong môi trường này — dùng pypdf làm phương án dự phòng (giảm độ chính xác).")
        return _inspect_with_pypdf_fallback(path, password, header_version, notes, errors)

    try:
        pdf = pikepdf.open(path, password=password or "")
    except pikepdf.PasswordError:
        return _empty_report(path, "pikepdf", errors, notes, requires_user_password=True, header_version=header_version)
    except FileNotFoundError as exc:
        errors.append(f"không đọc được tệp: {exc}")
        return _empty_report(path, "pikepdf", errors, notes, header_version=header_version)
    except Exception as exc:  # noqa: BLE001 — pikepdf.PdfError hoặc lỗi cấu trúc khác
        errors.append(f"pikepdf không mở được tệp (cấu trúc PDF hỏng?): {exc!r}")
        if _HAVE_PYPDF:
            notes.append("thử phương án dự phòng bằng pypdf sau khi pikepdf báo lỗi.")
            return _inspect_with_pypdf_fallback(path, password, header_version, notes, errors)
        return _empty_report(path, "pikepdf", errors, notes, header_version=header_version)

    try:
        findings: list[Finding] = []

        try:
            page_count = len(pdf.pages)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"không đếm được số trang: {exc!r}")
            page_count = None

        producer = creator = None
        try:
            if pdf.docinfo is not None:
                p_val = pdf.docinfo.get("/Producer")
                c_val = pdf.docinfo.get("/Creator")
                producer = str(p_val) if p_val is not None else None
                creator = str(c_val) if c_val is not None else None
        except Exception as exc:  # noqa: BLE001
            errors.append(f"không đọc được docinfo: {exc!r}")

        try:
            pdf_version = pdf.pdf_version or header_version
        except Exception:  # noqa: BLE001
            pdf_version = header_version

        try:
            is_linearized = bool(pdf.is_linearized)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"không kiểm tra được linearization: {exc!r}")
            is_linearized = None

        steps = [
            ("encryption", lambda: _check_encryption(pdf)),
            ("signatures", lambda: _check_signatures(pdf)),
            ("forms", lambda: _check_forms(pdf)),
            ("embedded_files", lambda: _check_embedded_files(pdf)),
            ("pdfa_hint", lambda: _check_pdfa_hint(pdf)),
            ("pdf_version", lambda: _check_pdf_version(pdf)),
        ]
        for step_name, step_fn in steps:
            try:
                findings.extend(step_fn())
            except Exception as exc:  # noqa: BLE001 — cách ly lỗi theo bước
                errors.append(f"lỗi ở bước '{step_name}': {exc!r}")

        try:
            action_hits = _collect_actions(pdf)
            findings.extend(_check_scripts_and_actions(action_hits))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"lỗi khi thu thập action/JavaScript: {exc!r}")

        try:
            content_class, scan_pages, text_pages = _classify_content(pdf, notes)
            findings.extend(_content_findings(content_class, scan_pages, text_pages))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"lỗi khi phân loại nội dung trang: {exc!r}")
            content_class = DocumentStatus.UNKNOWN

        has_signature = any(f.feature_id == "signature.digital" for f in findings)
        document_status = _document_status(
            is_encrypted=bool(pdf.is_encrypted), requires_password=False,
            has_signature=has_signature, content_class=content_class,
        )

        return InspectionReport(
            path=path, engine="pikepdf", pdf_version=pdf_version, page_count=page_count,
            producer=producer, creator=creator, is_linearized=is_linearized,
            requires_user_password=False,
            content_class=content_class, document_status=document_status,
            findings=findings, notes=notes, errors=errors,
        )
    finally:
        try:
            pdf.close()
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# Nhánh dự phòng pypdf — dùng khi pikepdf không cài được HOẶC không mở nổi
# tệp. Độ chính xác THẤP HƠN nhánh pikepdf (xem giới hạn trong __init__.py
# và README cùng thư mục) — không đệ quy Form XObject, không duyệt chuỗi
# /Next, không có API Permissions/Encryption chi tiết bằng pikepdf.
# ---------------------------------------------------------------------------


def _inspect_with_pypdf_fallback(path: str, password: str | None, header_version: str | None,
                                  notes: list[str], errors: list[str]) -> InspectionReport:
    if not _HAVE_PYPDF:
        errors.append("pypdf CŨNG không cài được trong môi trường này — không thể phân tích tệp.")
        return _empty_report(path, "none", errors, notes, header_version=header_version)

    try:
        reader = pypdf.PdfReader(path)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"pypdf cũng không mở được tệp: {exc!r}")
        return _empty_report(path, "none", errors, notes, header_version=header_version)

    findings: list[Finding] = []
    requires_password = False
    if reader.is_encrypted:
        decrypted_ok = False
        try:
            result = reader.decrypt(password or "")
            decrypted_ok = bool(result)
        except Exception:  # noqa: BLE001
            decrypted_ok = False
        if not decrypted_ok:
            requires_password = True
            findings.append(_protected_password_finding())
            return InspectionReport(
                path=path, engine="pypdf-fallback", pdf_version=header_version, page_count=None,
                producer=None, creator=None, is_linearized=None,
                requires_user_password=True,
                content_class=DocumentStatus.UNKNOWN, document_status=DocumentStatus.PROTECTED,
                findings=findings, notes=notes, errors=errors,
            )
        findings.append(Finding(
            feature_id="security.encryption",
            name_vi="Mã hoá / mật khẩu / giới hạn quyền (/Encrypt)",
            compat_level=CompatLevel.C3,
            severity=Severity.HIGH,
            detail_vi="Tệp được mã hoá (pypdf fallback — không có chi tiết quyền/bits chi tiết như nhánh pikepdf).",
            recommended_action_vi=(
                "Tệp được bảo vệ. KHÔNG cố vượt mật khẩu/quyền. (Phân tích bằng nhánh dự phòng "
                "pypdf — cài pikepdf để có chi tiết quyền/mã hoá đầy đủ hơn.)"
            ),
            evidence=["pypdf: is_encrypted=True, decrypt() thành công với mật khẩu đã cấp"],
        ))

    try:
        page_count = len(reader.pages)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"pypdf không đếm được số trang: {exc!r}")
        page_count = None

    producer = creator = None
    try:
        meta = reader.metadata
        if meta is not None:
            producer = meta.get("/Producer")
            creator = meta.get("/Creator")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"pypdf không đọc được metadata: {exc!r}")

    try:
        root = reader.trailer["/Root"]
    except Exception:  # noqa: BLE001
        root = None

    if root is not None:
        try:
            acroform = root.get("/AcroForm")
        except Exception:  # noqa: BLE001
            acroform = None
        if acroform is not None:
            try:
                if acroform.get("/XFA") is not None:
                    findings.append(Finding(
                        feature_id="form.xfa",
                        name_vi="Biểu mẫu XFA (/AcroForm /XFA)",
                        compat_level=CompatLevel.C3,
                        severity=Severity.HIGH,
                        detail_vi="AcroForm có khoá /XFA (phát hiện qua nhánh dự phòng pypdf).",
                        recommended_action_vi="Chỉ xem, không điền qua XFA; không xoá /XFA khi lưu.",
                        evidence=["AcroForm.XFA (pypdf)"],
                    ))
                else:
                    fields = acroform.get("/Fields")
                    if fields:
                        findings.append(Finding(
                            feature_id="form.acroform",
                            name_vi="Biểu mẫu AcroForm (/AcroForm /Fields)",
                            compat_level=CompatLevel.C1,
                            severity=Severity.LOW,
                            detail_vi=f"AcroForm có {len(list(fields))} field gốc (phát hiện qua nhánh dự phòng pypdf).",
                            recommended_action_vi="Kiểm lại giá trị/appearance sau khi lưu bằng trình xem độc lập.",
                            evidence=[f"fields={len(list(fields))} (pypdf)"],
                        ))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"pypdf: lỗi khi đọc AcroForm: {exc!r}")

        try:
            open_action = root.get("/OpenAction")
        except Exception:  # noqa: BLE001
            open_action = None
        if open_action is not None:
            findings.append(Finding(
                feature_id="action.auto_open",
                name_vi="Hành động tự động khi mở tài liệu (/OpenAction)",
                compat_level=CompatLevel.C2,
                severity=Severity.MEDIUM,
                detail_vi="Catalog có /OpenAction (phát hiện qua nhánh dự phòng pypdf — không duyệt sâu /AA/annotation).",
                recommended_action_vi="Không tự thực thi; xem chi tiết loại action cần cài pikepdf.",
                evidence=["catalog.OpenAction (pypdf)"],
            ))
            try:
                if str(open_action.get("/S")) == "/JavaScript":
                    findings.append(Finding(
                        feature_id="script.javascript",
                        name_vi="JavaScript nhúng trong PDF (/JavaScript, /JS)",
                        compat_level=CompatLevel.C3,
                        severity=Severity.HIGH,
                        detail_vi="OpenAction có Subtype /JavaScript (phát hiện qua nhánh dự phòng pypdf).",
                        recommended_action_vi="Không bao giờ tự chạy JavaScript trong PDF.",
                        evidence=["catalog.OpenAction.JS (pypdf)"],
                    ))
            except Exception:  # noqa: BLE001
                pass

    try:
        attachments = reader.attachments
        if attachments and len(attachments) > 0:
            findings.append(Finding(
                feature_id="attachment.embedded_file",
                name_vi="Tệp đính kèm/nhúng (/EmbeddedFile, /Filespec)",
                compat_level=CompatLevel.C2,
                severity=Severity.MEDIUM,
                detail_vi=f"tìm thấy {len(attachments)} tệp đính kèm (phát hiện qua nhánh dự phòng pypdf).",
                recommended_action_vi="Không tự mở/chạy tệp đính kèm.",
                evidence=list(attachments.keys())[:20],
            ))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"pypdf: lỗi khi đọc attachments: {exc!r}")

    content_class = DocumentStatus.UNKNOWN
    scan_pages: list[str] = []
    text_pages: list[str] = []
    try:
        total = len(reader.pages)
        scanned_total = min(total, _MAX_PAGES_SCANNED)
        if scanned_total < total:
            notes.append(f"tài liệu có {total} trang, chỉ phân loại {scanned_total} trang đầu (nhánh dự phòng pypdf).")
        scan_count = text_count = 0
        for idx in range(scanned_total):
            page = reader.pages[idx]
            try:
                text = page.extract_text() or ""
            except Exception:  # noqa: BLE001
                text = ""
            try:
                images = page.images
            except Exception:  # noqa: BLE001
                images = []
            has_text = bool(text.strip())
            has_image = bool(images)
            if has_text:
                text_count += 1
                text_pages.append(f"trang {idx + 1}")
            elif has_image:
                scan_count += 1
                scan_pages.append(f"trang {idx + 1}")
        if total == 0:
            content_class = DocumentStatus.UNKNOWN
        elif scan_count == 0:
            content_class = DocumentStatus.TEXT_PDF
        elif text_count == 0:
            content_class = DocumentStatus.SCAN_IMAGE
        else:
            content_class = DocumentStatus.MIXED
        findings.extend(_content_findings(content_class, scan_pages, text_pages))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"pypdf: lỗi khi phân loại nội dung trang: {exc!r}")

    has_signature = False  # nhánh dự phòng pypdf không duyệt AcroForm fields tìm /Sig (xem notes)
    notes.append(
        "nhánh dự phòng pypdf KHÔNG kiểm tra chữ ký số (/Sig, /Perms /DocMDP) và KHÔNG duyệt "
        "sâu action /AA trên trang/annotation/field — cài pikepdf để có phân tích đầy đủ."
    )
    document_status = _document_status(
        is_encrypted=bool(reader.is_encrypted), requires_password=requires_password,
        has_signature=has_signature, content_class=content_class,
    )

    return InspectionReport(
        path=path, engine="pypdf-fallback", pdf_version=header_version, page_count=page_count,
        producer=producer, creator=creator, is_linearized=None,
        requires_user_password=requires_password,
        content_class=content_class, document_status=document_status,
        findings=findings, notes=notes, errors=errors,
    )
