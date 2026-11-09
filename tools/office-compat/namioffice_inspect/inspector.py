# -*- coding: utf-8 -*-
"""Compatibility Inspector — lõi phân tích (xem docstring ``__init__.py``).

An toàn: chỉ đọc (``zipfile`` + ``xml.etree.ElementTree``), không thực thi gì
từ nội dung tệp, không mở socket. Mọi phần nội dung được đọc có giới hạn kích
thước (``_MAX_PART_BYTES``) để tránh đọc vô hạn một part giả mạo/khổng lồ
(zip bomb thô sơ) — đây KHÔNG phải sandbox đầy đủ như pipeline thật sẽ cần
(04_KIEN_TRUC_KIEM_THU.md nói "sandbox parser"); công cụ này chỉ là bước
sniff/inventory tĩnh, chạy ngoài tiến trình mở file thật, trước khi file đó
có cơ hội được LibreOffice/Office thật sự mở.
"""

from __future__ import annotations

import os
import re
import zipfile
from dataclasses import dataclass, field
from enum import Enum
from xml.etree import ElementTree as ET

__all__ = [
    "CompatLevel",
    "Severity",
    "Finding",
    "InspectionReport",
    "inspect_file",
]

# ---------------------------------------------------------------------------
# Hợp đồng dữ liệu: C0–C3 + severity (05_PROMPT_CLAUDE_CODE.md bước 2).
# ---------------------------------------------------------------------------


class CompatLevel(str, Enum):
    """Mức tương thích/rủi ro của MỘT tính năng phát hiện được.

    C0 — không có dấu hiệu rủi ro ở mục này (không tạo Finding).
    C1 — tính năng nâng cao nhưng ít rủi ro (thường mở/hiển thị đúng, nên
         kiểm lại bằng mắt, không chặn gì).
    C2 — tính năng có thể mất độ trung thực (fidelity) khi mở lại/lưu lại;
         cần kiểm bằng tệp thật trước khi tuyên bố "đã hỗ trợ".
    C3 — chưa hỗ trợ / rủi ro cao (macro, mã hoá/IRM, Power Query/Data
         Model...): phải cảnh báo rõ, không tự xử lý, không tự lưu đè.
    """

    C0 = "C0"
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"


#: Thứ tự so sánh C0 < C1 < C2 < C3 (dùng để tính mức cao nhất của báo cáo).
_COMPAT_ORDER: dict[CompatLevel, int] = {
    CompatLevel.C0: 0,
    CompatLevel.C1: 1,
    CompatLevel.C2: 2,
    CompatLevel.C3: 3,
}


class Severity(str, Enum):
    """Mức độ nghiêm trọng của một Finding — độc lập với CompatLevel (một
    tính năng C2 có thể severity MEDIUM hoặc HIGH tuỳ tác động thực tế)."""

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

#: Mã thoát CLI theo severity cao nhất (xem tools/office-compat/namioffice-inspect).
SEVERITY_EXIT_CODE: dict[Severity, int] = {
    Severity.INFO: 0,
    Severity.LOW: 0,
    Severity.MEDIUM: 1,
    Severity.HIGH: 2,
    Severity.CRITICAL: 3,
}


@dataclass
class Finding:
    """Một tính năng rủi ro/nâng cao được phát hiện trong tệp."""

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
    """Kết quả kiểm tra một tệp OOXML."""

    path: str
    file_kind: str
    app: str | None
    is_zip: bool
    container_kind: str  # "ooxml_zip" | "ole_cfb" | "unknown"
    ooxml_conformance: str  # "transitional" | "strict" | "unknown" | "khong_ap_dung"
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)  # giới hạn/không chắc chắn, không chặn
    errors: list[str] = field(default_factory=list)  # lỗi phân tích không gây sập

    @property
    def max_compat_level(self) -> CompatLevel:
        if not self.findings:
            return CompatLevel.C0
        return max(
            (f.compat_level for f in self.findings),
            key=lambda level: _COMPAT_ORDER[level],
        )

    @property
    def max_severity(self) -> Severity:
        if not self.findings:
            return Severity.INFO
        return max(
            (f.severity for f in self.findings),
            key=lambda sev: _SEVERITY_ORDER[sev],
        )

    @property
    def safe_to_overwrite(self) -> bool:
        """"An toàn để lưu đè?" — quy tắc atomic-save của kit (04_KIEN_TRUC_
        KIEM_THU.md §2: "pre-save diff/cảnh báo → atomic save vào bản mới
        khi nguy cơ"): CHỈ coi là an toàn lưu đè trực tiếp khi mức rủi ro
        cao nhất là C0/C1 (tính năng nâng cao nhưng không mất fidelity khi
        lưu lại). Từ C2 trở lên LUÔN khuyến nghị lưu bản sao (Save-As),
        không lưu đè bản gốc."""
        return _COMPAT_ORDER[self.max_compat_level] <= _COMPAT_ORDER[CompatLevel.C1]

    def has_feature(self, prefix: str) -> bool:
        return any(f.feature_id == prefix or f.feature_id.startswith(prefix + ".")
                   for f in self.findings)

    def find(self, feature_id: str) -> Finding | None:
        for f in self.findings:
            if f.feature_id == feature_id:
                return f
        return None

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "file_kind": self.file_kind,
            "app": self.app,
            "is_zip": self.is_zip,
            "container_kind": self.container_kind,
            "ooxml_conformance": self.ooxml_conformance,
            "findings": [f.to_dict() for f in self.findings],
            "notes": list(self.notes),
            "errors": list(self.errors),
            "max_compat_level": self.max_compat_level.value,
            "max_severity": self.max_severity.value,
            "safe_to_overwrite": self.safe_to_overwrite,
        }

    def to_text_vi(self) -> str:
        lines: list[str] = []
        lines.append("=== BÁO CÁO COMPATIBILITY INSPECTOR (NaMiOffice) ===")
        lines.append(f"Tệp: {self.path}")
        lines.append(f"Loại tệp: {self.file_kind or '(không rõ)'} | Ứng dụng: {self.app or '(không rõ)'}")
        container_vi = {
            "ooxml_zip": "ZIP OOXML hợp lệ",
            "ole_cfb": "OLE/Compound File Binary (KHÔNG phải ZIP OOXML)",
            "unknown": "không xác định (không phải ZIP, không khớp OLE/CFB)",
        }.get(self.container_kind, self.container_kind)
        lines.append(f"Dạng container: {container_vi}")
        conform_vi = {
            "transitional": "OOXML Transitional (phổ biến)",
            "strict": "OOXML Strict (ít phổ biến, hỗ trợ hạn chế hơn)",
            "unknown": "không xác định được namespace của part chính",
            "khong_ap_dung": "không áp dụng (không đọc được phần chính)",
        }.get(self.ooxml_conformance, self.ooxml_conformance)
        lines.append(f"Chuẩn OOXML: {conform_vi}")
        lines.append("")

        if not self.findings:
            lines.append(
                "Không phát hiện tính năng rủi ro/nâng cao nào trong danh sách công cụ "
                "này kiểm tra. (Đây KHÔNG phải bảo đảm tuyệt đối — công cụ chỉ kiểm tra "
                "tĩnh theo danh sách tính năng đã biết, không mở file thật.)"
            )
        else:
            lines.append(f"Phát hiện {len(self.findings)} tính năng rủi ro/nâng cao:")
            for f in self.findings:
                lines.append(f"  - [{f.compat_level.value}][{f.severity.value.upper()}] "
                             f"{f.feature_id} — {f.name_vi}")
                lines.append(f"      Chi tiết: {f.detail_vi}")
                lines.append(f"      Khuyến nghị: {f.recommended_action_vi}")
                if f.evidence:
                    lines.append(f"      Bằng chứng: {', '.join(f.evidence[:8])}"
                                 + (" ..." if len(f.evidence) > 8 else ""))

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
        lines.append(f"TỔNG KẾT: mức tương thích cao nhất = {self.max_compat_level.value}, "
                     f"mức độ nghiêm trọng cao nhất = {self.max_severity.value.upper()}")
        if self.safe_to_overwrite:
            lines.append("AN TOÀN ĐỂ LƯU ĐÈ? CÓ (rủi ro thấp) — vẫn nên giữ bản sao lưu thông thường.")
        else:
            lines.append(
                "AN TOÀN ĐỂ LƯU ĐÈ? KHÔNG — khuyến nghị LƯU BẢN SAO (Save-As) sang tệp mới, "
                "GIỮ NGUYÊN bản gốc không đổi, theo quy tắc atomic-save của NaMiOffice."
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Hằng số định dạng.
# ---------------------------------------------------------------------------

#: Giới hạn an toàn khi đọc nội dung MỘT part trong zip để quét text/XML —
#: phòng một part khai kích thước khổng lồ (zip-bomb thô sơ) làm công cụ bị
#: treo/ngốn RAM. Vượt giới hạn → bỏ qua đọc nội dung, chỉ dùng TÊN part.
_MAX_PART_BYTES = 25 * 1024 * 1024  # 25 MB

#: Dấu hiệu Compound File Binary (OLE2) — Microsoft Office dùng để chứa gói
#: EncryptionInfo + EncryptedPackage khi tệp được mã hoá bằng mật khẩu hoặc
#: IRM/Azure Information Protection. Khi khớp, tệp KHÔNG phải ZIP OOXML.
_OLE_CFB_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

#: Đuôi tệp macro-enabled theo quy ước OOXML (ECMA-376/MS-OE376).
_MACRO_EXTENSIONS = {
    ".docm", ".dotm", ".xlsm", ".xltm", ".xlam", ".pptm", ".potm", ".ppsm", ".ppam",
}

#: ext -> (app, là đuôi macro-enabled?)
_EXT_INFO: dict[str, tuple[str, bool]] = {
    ".docx": ("writer", False), ".docm": ("writer", True),
    ".dotx": ("writer", False), ".dotm": ("writer", True),
    ".xlsx": ("sheet", False), ".xlsm": ("sheet", True),
    ".xltx": ("sheet", False), ".xltm": ("sheet", True),
    ".xlam": ("sheet", True),
    ".pptx": ("slides", False), ".pptm": ("slides", True),
    ".potx": ("slides", False), ".potm": ("slides", True),
    ".ppsx": ("slides", False), ".ppsm": ("slides", True),
    ".ppam": ("slides", True),
}

#: part "chính" của mỗi app — dùng để xác định Transitional vs Strict.
_MAIN_PART: dict[str, str] = {
    "writer": "word/document.xml",
    "sheet": "xl/workbook.xml",
    "slides": "ppt/presentation.xml",
}

#: namespace Transitional/Strict theo app (MS-OE376 + ISO/IEC 29500 Strict).
_NS_TRANSITIONAL: dict[str, str] = {
    "writer": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "sheet": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "slides": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
_NS_STRICT: dict[str, str] = {
    "writer": "http://purl.oclc.org/ooxml/wordprocessingml/main",
    "sheet": "http://purl.oclc.org/ooxml/spreadsheetml/main",
    "slides": "http://purl.oclc.org/ooxml/presentationml/main",
}

#: Hàm MẢNG ĐỘNG thật (spill nhiều ô) — rủi ro fidelity cao nhất trong nhóm
#: "_xlfn." vì cần engine hỗ trợ spill, không chỉ tính 1 giá trị.
_DYNAMIC_ARRAY_FUNCS = {
    "FILTER", "SORT", "SORTBY", "UNIQUE", "SEQUENCE", "RANDARRAY",
}
#: LAMBDA/LET và họ hàm bậc cao (BYROW/BYCOL/MAP/REDUCE/SCAN/MAKEARRAY) — gộp
#: cùng nhóm C2 với mảng động vì cùng cần engine công thức hiện đại.
_LAMBDA_FUNCS = {
    "LAMBDA", "LET", "BYROW", "BYCOL", "MAP", "REDUCE", "SCAN",
    "ISOMITTED", "MAKEARRAY",
}
#: Hàm "hiện đại" khác nhưng KHÔNG spill nhiều ô (trả về 1 giá trị) — rủi ro
#: thấp hơn, LibreOffice Calc bản gần đây thường có.
_MODERN_SCALAR_FUNCS = {
    "XLOOKUP", "XMATCH", "IFS", "MAXIFS", "MINIFS", "TEXTJOIN", "CONCAT",
    "SWITCH", "TEXTBEFORE", "TEXTAFTER", "TEXTSPLIT", "VSTACK", "HSTACK",
    "CHOOSEROWS", "CHOOSECOLS", "TOCOL", "TOROW", "WRAPROWS", "WRAPCOLS",
    "FILTERXML", "NUMBERVALUE", "ARRAYTOTEXT", "VALUETOTEXT",
}

#: Đuôi media coi là audio/video (để phân biệt với ảnh — ảnh nhúng không bị
#: coi là rủi ro trong công cụ này, chỉ audio/video mới được báo).
_AUDIO_EXT = {".wav", ".mp3", ".m4a", ".wma", ".aiff", ".aac"}
_VIDEO_EXT = {".mp4", ".wmv", ".avi", ".mov", ".m4v", ".mpg", ".mpeg", ".asf"}

_RELS_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_XLFN_RE = re.compile(r"_xlfn\.(?:_xlws\.)?([A-Za-z_][A-Za-z0-9_.]*)")


# ---------------------------------------------------------------------------
# Hàm phụ trợ.
# ---------------------------------------------------------------------------


def _safe_read(zf: zipfile.ZipFile, name: str, notes: list[str]) -> bytes | None:
    """Đọc nội dung một part có giới hạn kích thước (xem ``_MAX_PART_BYTES``).

    Trả ``None`` và ghi chú vào ``notes`` nếu part quá lớn hoặc không đọc
    được (không ném lỗi ra ngoài — một part hỏng không được làm sập cả báo
    cáo)."""
    try:
        info = zf.getinfo(name)
    except KeyError:
        return None
    if info.file_size > _MAX_PART_BYTES:
        notes.append(
            f"bỏ qua đọc nội dung '{name}' vì kích thước khai báo "
            f"({info.file_size} byte) vượt giới hạn an toàn {_MAX_PART_BYTES} byte."
        )
        return None
    try:
        return zf.read(name)
    except Exception as exc:  # noqa: BLE001 — part hỏng, không chặn cả báo cáo
        notes.append(f"không đọc được '{name}': {exc!r}")
        return None


def _local_name(tag: str) -> str:
    """Bỏ namespace '{...}' trong tag ElementTree, chỉ giữ tên local."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _iter_rels_files(names: list[str]) -> list[str]:
    return [n for n in names if n.lower().endswith(".rels")]


# ---------------------------------------------------------------------------
# Các bước inventory (mỗi hàm trả list[Finding], không ném lỗi ra ngoài).
# ---------------------------------------------------------------------------


def _check_macros(names: list[str], ext: str) -> list[Finding]:
    vba_names = [n for n in names if re.match(r"^(word|xl|ppt)/vbaProject\.bin$", n, re.IGNORECASE)]
    macro_ext = ext in _MACRO_EXTENSIONS
    if not vba_names and not macro_ext:
        return []

    detail_bits = []
    if vba_names:
        detail_bits.append(f"tìm thấy {len(vba_names)} vbaProject.bin: {', '.join(vba_names)}")
    else:
        detail_bits.append(
            "đuôi tệp khai báo macro-enabled nhưng KHÔNG tìm thấy vbaProject.bin trong "
            "gói — có thể macro đã bị gỡ hoặc tệp bất thường; vẫn coi là rủi ro macro vì "
            "đuôi tệp là tín hiệu chính thức."
        )
    if vba_names and not macro_ext:
        detail_bits.append(
            "BẤT THƯỜNG: có vbaProject.bin nhưng đuôi tệp không phải *m — có thể tệp bị "
            "đổi tên để né lọc theo đuôi; vẫn coi là có macro."
        )

    return [Finding(
        feature_id="macro.vba",
        name_vi="Macro VBA (vbaProject.bin / đuôi macro-enabled)",
        compat_level=CompatLevel.C3,
        severity=Severity.HIGH,
        detail_vi="; ".join(detail_bits),
        recommended_action_vi=(
            "VBA KHÔNG được thực thi trong NaMiOffice. Dự án macro (nếu có) phải được GIỮ "
            "NGUYÊN NHỊ PHÂN khi lưu lại (không xoá, không chỉnh), chỉ cho xem mã (nếu IDE "
            "Basic đọc được) — không chạy. Cảnh báo rõ cho người dùng TRƯỚC khi mở."
        ),
        evidence=list(vba_names) or [f"ext={ext}"],
    )]


def _check_encryption_markers_inside_zip(names: list[str]) -> list[Finding]:
    """Trường hợp hiếm/bất thường: EncryptionInfo/EncryptedPackage xuất hiện
    dưới dạng ENTRY trong một ZIP (bình thường Office gói chúng trong OLE/CFB
    bên ngoài ZIP — xem ``inspect_file``). Giữ kiểm tra này để phòng thủ."""
    hit = [n for n in names if re.search(r"(EncryptionInfo|EncryptedPackage)$", n, re.IGNORECASE)]
    if not hit:
        return []
    return [Finding(
        feature_id="encryption.markers_in_zip",
        name_vi="Dấu hiệu mã hoá (EncryptionInfo/EncryptedPackage) trong ZIP",
        compat_level=CompatLevel.C3,
        severity=Severity.CRITICAL,
        detail_vi=f"tìm thấy entry bất thường: {', '.join(hit)}",
        recommended_action_vi=(
            "Tệp có dấu hiệu mã hoá/IRM. KHÔNG cố vượt mật khẩu/IRM. Dừng xử lý, yêu cầu "
            "mật khẩu đúng qua kênh chính thức."
        ),
        evidence=hit,
    )]


def _check_signatures(names: list[str]) -> list[Finding]:
    sig_names = [n for n in names if n.lower().startswith("_xmlsignatures/")]
    if not sig_names:
        return []
    return [Finding(
        feature_id="signature.digital",
        name_vi="Chữ ký số (digital signature)",
        compat_level=CompatLevel.C2,
        severity=Severity.HIGH,
        detail_vi=f"tìm thấy {len(sig_names)} phần chữ ký số: {', '.join(sig_names)}",
        recommended_action_vi=(
            "Tài liệu ĐÃ CÓ chữ ký số. Sửa nội dung (kể cả lưu lại) sẽ làm MẤT HIỆU LỰC chữ "
            "ký hiện có. Nếu cần sửa: lưu bản sao riêng và yêu cầu ký lại từ người có thẩm "
            "quyền; KHÔNG hiển thị nhãn 'còn hợp lệ' cho bản đã sửa."
        ),
        evidence=sig_names,
    )]


def _check_external_workbook_links(names: list[str]) -> list[Finding]:
    ext_links = [n for n in names if n.lower().startswith("xl/externallinks/")]
    if not ext_links:
        return []
    return [Finding(
        feature_id="external.workbook_links",
        name_vi="Liên kết workbook ngoài (xl/externalLinks)",
        compat_level=CompatLevel.C2,
        severity=Severity.MEDIUM,
        detail_vi=f"{len(ext_links)} phần externalLinks: {', '.join(ext_links)}",
        recommended_action_vi=(
            "Công thức phụ thuộc workbook/tệp KHÁC không có mặt khi mở. KHÔNG tự fetch/"
            "refresh từ đường dẫn ngoài; giữ giá trị cache đã lưu và cảnh báo nguồn có thể "
            "lỗi thời."
        ),
        evidence=ext_links,
    )]


def _classify_rel_target(target: str, type_uri: str) -> str:
    """Trả 'network' | 'local_unc' | 'ole' | 'other' cho một Relationship
    TargetMode=External."""
    type_lower = type_uri.lower()
    if "oleobject" in type_lower:
        return "ole"
    if "hyperlink" in type_lower:
        t = target.strip()
        if re.match(r"^(https?|ftp|mailto)://?", t, re.IGNORECASE) or t.lower().startswith("mailto:"):
            return "network"
        if t.startswith("\\\\") or re.match(r"^[A-Za-z]:\\", t) or t.lower().startswith("file:"):
            return "local_unc"
        return "other"
    return "other"


def _check_external_relationships(zf: zipfile.ZipFile, names: list[str],
                                   notes: list[str]) -> list[Finding]:
    network: list[str] = []
    local_unc: list[str] = []
    ole: list[str] = []
    for rels_name in _iter_rels_files(names):
        data = _safe_read(zf, rels_name, notes)
        if data is None:
            continue
        try:
            root = ET.fromstring(data)
        except ET.ParseError as exc:
            notes.append(f"không phân tích được '{rels_name}' (.rels hỏng?): {exc}")
            continue
        for rel in root:
            if _local_name(rel.tag) != "Relationship":
                continue
            if rel.get("TargetMode") != "External":
                continue
            target = rel.get("Target", "")
            type_uri = rel.get("Type", "")
            kind = _classify_rel_target(target, type_uri)
            if kind == "network":
                network.append(target)
            elif kind == "local_unc":
                local_unc.append(target)
            elif kind == "ole":
                ole.append(target)

    findings: list[Finding] = []
    if network:
        findings.append(Finding(
            feature_id="link.hyperlink_network",
            name_vi="Liên kết ngoài tới mạng (http/https/mailto/ftp)",
            compat_level=CompatLevel.C1,
            severity=Severity.LOW,
            detail_vi=f"{len(network)} liên kết: {', '.join(network[:5])}"
                     + (" ..." if len(network) > 5 else ""),
            recommended_action_vi=(
                "Liên kết ra Internet/email. KHÔNG tự mở/tải; chỉ hiển thị, để người dùng "
                "bấm vào mới điều hướng (như trình soạn văn bản thường làm)."
            ),
            evidence=network,
        ))
    if local_unc:
        findings.append(Finding(
            feature_id="link.hyperlink_local_unc",
            name_vi="Liên kết tới đường dẫn cục bộ/UNC (\\\\server\\...) ",
            compat_level=CompatLevel.C2,
            severity=Severity.MEDIUM,
            detail_vi=f"{len(local_unc)} liên kết: {', '.join(local_unc[:5])}"
                     + (" ..." if len(local_unc) > 5 else ""),
            recommended_action_vi=(
                "Liên kết tới máy/đường dẫn khác (UNC hoặc đường dẫn tuyệt đối). KHÔNG tự "
                "theo link; đường dẫn Windows có thể không tồn tại/không hợp lệ trên máy "
                "đích. Cảnh báo người dùng trước khi mở."
            ),
            evidence=local_unc,
        ))
    if ole:
        findings.append(Finding(
            feature_id="object.ole_external",
            name_vi="Đối tượng OLE liên kết NGOÀI (externally linked)",
            compat_level=CompatLevel.C2,
            severity=Severity.MEDIUM,
            detail_vi=f"{len(ole)} liên kết OLE ngoài: {', '.join(ole[:5])}"
                     + (" ..." if len(ole) > 5 else ""),
            recommended_action_vi=(
                "Đối tượng OLE tham chiếu nguồn NGOÀI tệp. KHÔNG kích hoạt/mở lồng để thực "
                "thi; chỉ hiển thị biểu tượng/ảnh tĩnh nếu có sẵn trong gói."
            ),
            evidence=ole,
        ))
    return findings


def _check_embedded_ole_objects(names: list[str]) -> list[Finding]:
    embedded = [n for n in names if re.match(r"^(word|xl|ppt)/embeddings/", n, re.IGNORECASE)]
    if not embedded:
        return []
    return [Finding(
        feature_id="object.embedded_ole",
        name_vi="Đối tượng nhúng (embeddings/) — OLE nhúng trong gói",
        compat_level=CompatLevel.C2,
        severity=Severity.MEDIUM,
        detail_vi=f"{len(embedded)} đối tượng nhúng: {', '.join(embedded[:5])}"
                 + (" ..." if len(embedded) > 5 else ""),
        recommended_action_vi=(
            "Có thể là workbook/văn bản/trình chiếu khác nhúng bên trong, hoặc đối tượng "
            "OLE khác. KHÔNG kích hoạt để mở/chạy lồng; chỉ hiển thị ảnh/biểu tượng tĩnh đã "
            "có sẵn trong gói nếu có."
        ),
        evidence=embedded,
    )]


def _check_content_controls(zf: zipfile.ZipFile, app: str, names: list[str],
                             notes: list[str]) -> list[Finding]:
    if app != "writer" or "word/document.xml" not in names:
        return []
    data = _safe_read(zf, "word/document.xml", notes)
    if data is None:
        return []
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        notes.append(f"không phân tích được word/document.xml: {exc}")
        return []
    count = sum(1 for el in root.iter() if _local_name(el.tag) == "sdt")
    if count == 0:
        return []
    return [Finding(
        feature_id="writer.content_controls",
        name_vi="Content control (w:sdt) — biểu mẫu/trường cấu trúc",
        compat_level=CompatLevel.C1,
        severity=Severity.LOW,
        detail_vi=f"tìm thấy {count} content control (w:sdt) trong word/document.xml.",
        recommended_action_vi=(
            "Thường mở/hiển thị đúng, nhưng cần kiểm lại ràng buộc dữ liệu (data binding "
            "tới customXml), placeholder text, và trạng thái khoá (lock) sau khi mở lại."
        ),
        evidence=[f"count={count}"],
    )]


def _check_sheet_formulas(zf: zipfile.ZipFile, app: str, names: list[str],
                           notes: list[str]) -> list[Finding]:
    if app != "sheet":
        return []
    parts = [n for n in names if re.match(r"^xl/(worksheets/sheet\d+\.xml|sharedStrings\.xml|tables/table\d+\.xml)$", n, re.IGNORECASE)]
    dynamic_hits: dict[str, int] = {}
    modern_hits: dict[str, int] = {}
    for name in parts:
        data = _safe_read(zf, name, notes)
        if data is None:
            continue
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            notes.append(f"không đọc được văn bản '{name}': {exc!r}")
            continue
        for m in _XLFN_RE.finditer(text):
            fname = m.group(1).upper()
            if fname in _DYNAMIC_ARRAY_FUNCS or fname in _LAMBDA_FUNCS:
                dynamic_hits[fname] = dynamic_hits.get(fname, 0) + 1
            else:
                modern_hits[fname] = modern_hits.get(fname, 0) + 1

    findings: list[Finding] = []
    if dynamic_hits:
        detail = ", ".join(f"{k}×{v}" for k, v in sorted(dynamic_hits.items()))
        findings.append(Finding(
            feature_id="formula.dynamic_array",
            name_vi="Công thức mảng động / LAMBDA (_xlfn._xlws./_xlfn.)",
            compat_level=CompatLevel.C2,
            severity=Severity.MEDIUM,
            detail_vi=f"hàm: {detail}.",
            recommended_action_vi=(
                "Cần engine hỗ trợ 'spill' kết quả ra nhiều ô (FILTER/SORT/UNIQUE/SEQUENCE/"
                "RANDARRAY) hoặc LET/LAMBDA bậc cao. QUAN TRỌNG: nếu NaMiOffice chỉ hiển thị "
                "GIÁ TRỊ CACHE có sẵn trong tệp mà KHÔNG tự tính lại/spill đúng khi input "
                "đổi, thì KHÔNG được coi là 'đã hỗ trợ' — phải kiểm bằng tệp thật, sửa input "
                "và xem công thức tính lại đúng."
            ),
            evidence=[f"{k}:{v}" for k, v in sorted(dynamic_hits.items())],
        ))
    if modern_hits:
        detail = ", ".join(f"{k}×{v}" for k, v in sorted(modern_hits.items()))
        findings.append(Finding(
            feature_id="formula.modern_function",
            name_vi="Hàm hiện đại khác (_xlfn., không spill nhiều ô)",
            compat_level=CompatLevel.C1,
            severity=Severity.LOW,
            detail_vi=f"hàm: {detail}.",
            recommended_action_vi=(
                "LibreOffice Calc bản gần đây thường hỗ trợ các hàm này (XLOOKUP/IFS/"
                "TEXTJOIN/...), nhưng KHÔNG suy đoán — phải xác nhận theo phiên bản pin cụ "
                "thể trước khi khẳng định đã hỗ trợ."
            ),
            evidence=[f"{k}:{v}" for k, v in sorted(modern_hits.items())],
        ))
    return findings


def _check_pivot(names: list[str]) -> list[Finding]:
    pivot_tables = [n for n in names if n.lower().startswith("xl/pivottables/")]
    pivot_cache = [n for n in names if n.lower().startswith("xl/pivotcache/")]
    if not pivot_tables and not pivot_cache:
        return []
    return [Finding(
        feature_id="sheet.pivot_table",
        name_vi="PivotTable / PivotCache",
        compat_level=CompatLevel.C2,
        severity=Severity.MEDIUM,
        detail_vi=f"{len(pivot_tables)} PivotTable, {len(pivot_cache)} phần PivotCache.",
        recommended_action_vi=(
            "Có thể mở được dữ liệu SNAPSHOT (giá trị đã cache), nhưng 'Refresh' từ nguồn "
            "ngoài CHƯA được coi là hỗ trợ cho tới khi kiểm bằng tệp Pivot thật và so sánh "
            "với Microsoft Excel."
        ),
        evidence=pivot_tables + pivot_cache,
    )]


def _check_data_model_power_query(app: str, names: list[str]) -> list[Finding]:
    if app != "sheet":
        return []
    model = [n for n in names if n.lower().startswith("xl/model/")]
    connections = [n for n in names if n.lower() == "xl/connections.xml"]
    query_tables = [n for n in names if n.lower().startswith("xl/querytables/")]
    powerquery_like = [n for n in names if "powerquery" in n.lower()]
    custom_xml = [n for n in names if n.lower().startswith("customxml/")]

    hits = model + connections + query_tables + powerquery_like + custom_xml
    if not hits:
        return []
    return [Finding(
        feature_id="sheet.data_model_power_query",
        name_vi="Data Model / Power Query / Power Pivot / kết nối ngoài",
        compat_level=CompatLevel.C3,
        severity=Severity.HIGH,
        detail_vi=(
            f"xl/model: {len(model)}, xl/connections.xml: {len(connections)}, "
            f"queryTables: {len(query_tables)}, powerquery-like: {len(powerquery_like)}, "
            f"customXml: {len(custom_xml)}."
        ),
        recommended_action_vi=(
            "Power Query/Power Pivot/Data Model là HỆ RIÊNG biệt lập với bảng tính thường. "
            "NaMiOffice CHƯA hỗ trợ refresh/transform các nguồn này. Giữ nguyên phần dữ "
            "liệu hiện có, CẢNH BÁO rõ cho người dùng, KHÔNG tự xoá; ô/bảng đang hiển thị "
            "có thể chỉ là giá trị cache cũ, không phải kết quả mới nhất."
        ),
        evidence=hits,
    )]


def _check_charts(names: list[str]) -> list[Finding]:
    charts = [n for n in names if re.match(r"^(word|xl|ppt)/charts/chart\d+\.xml$", n, re.IGNORECASE)]
    if not charts:
        return []
    return [Finding(
        feature_id="media.charts",
        name_vi="Biểu đồ (chart parts)",
        compat_level=CompatLevel.C1,
        severity=Severity.LOW,
        detail_vi=f"{len(charts)} chart part: {', '.join(charts[:5])}"
                 + (" ..." if len(charts) > 5 else ""),
        recommended_action_vi=(
            "Kiểm lại layout/dữ liệu/trục/legend sau khi mở — biểu đồ phức tạp (3D, combo, "
            "trendline, dual-axis) dễ lệch khi render lại ở engine khác."
        ),
        evidence=charts,
    )]


def _check_media(names: list[str]) -> list[Finding]:
    media = [n for n in names if re.match(r"^(word|xl|ppt)/media/", n, re.IGNORECASE)]
    audio = [n for n in media if os.path.splitext(n)[1].lower() in _AUDIO_EXT]
    video = [n for n in media if os.path.splitext(n)[1].lower() in _VIDEO_EXT]
    if not audio and not video:
        return []
    return [Finding(
        feature_id="media.audio_video",
        name_vi="Media nhúng: audio/video",
        compat_level=CompatLevel.C1,
        severity=Severity.LOW,
        detail_vi=f"{len(video)} video, {len(audio)} audio: {', '.join((video + audio)[:5])}"
                 + (" ..." if (len(video) + len(audio)) > 5 else ""),
        recommended_action_vi=(
            "Kiểm tra codec/phát lại sau khi mở — codec độc quyền cũ (ví dụ WMV/WMA) ít "
            "được hỗ trợ ngoài Windows; không giả định phát được."
        ),
        evidence=video + audio,
    )]


def _check_ooxml_conformance(zf: zipfile.ZipFile, app: str | None, names: list[str],
                              notes: list[str]) -> tuple[str, list[Finding]]:
    if app is None or app not in _MAIN_PART:
        return "khong_ap_dung", []
    main_part = _MAIN_PART[app]
    if main_part not in names:
        notes.append(f"không tìm thấy part chính '{main_part}' — bỏ qua kiểm tra Transitional/Strict.")
        return "unknown", []
    data = _safe_read(zf, main_part, notes)
    if data is None:
        return "unknown", []
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        notes.append(f"không phân tích được '{main_part}': {exc}")
        return "unknown", []
    tag = root.tag
    ns = tag[1:tag.index("}")] if tag.startswith("{") and "}" in tag else ""
    if ns == _NS_STRICT.get(app):
        return "strict", [Finding(
            feature_id="format.ooxml_strict",
            name_vi="OOXML Strict (ISO/IEC 29500 Strict)",
            compat_level=CompatLevel.C2,
            severity=Severity.MEDIUM,
            detail_vi=f"part chính '{main_part}' dùng namespace Strict: {ns}",
            recommended_action_vi=(
                "OOXML Strict ít phổ biến; LibreOffice/Office hỗ trợ Transitional tốt hơn. "
                "Một số phần tử Strict cần ánh xạ tương đương — kiểm riêng trước khi coi là "
                "tương thích đầy đủ."
            ),
            evidence=[ns],
        )]
    if ns == _NS_TRANSITIONAL.get(app):
        return "transitional", []
    notes.append(f"namespace của part chính '{main_part}' không khớp Transitional/Strict đã biết: {ns!r}")
    return "unknown", []


# ---------------------------------------------------------------------------
# Hàm công khai chính.
# ---------------------------------------------------------------------------


def inspect_file(path: str) -> InspectionReport:
    """Kiểm tra TĨNH một tệp OOXML, KHÔNG mở bằng office app, KHÔNG thực thi
    nội dung. Trả về :class:`InspectionReport`.

    An toàn: chỉ đọc; không ném lỗi ra ngoài (lỗi được gom vào
    ``report.errors``/``report.notes`` để báo cáo vẫn trả về được)."""
    ext = os.path.splitext(path)[1].lower()
    app, _macro_ext = _EXT_INFO.get(ext, (None, False))
    file_kind = ext.lstrip(".") if ext else "(không có đuôi)"

    findings: list[Finding] = []
    notes: list[str] = []
    errors: list[str] = []

    try:
        with open(path, "rb") as fh:
            header = fh.read(8)
    except OSError as exc:
        return InspectionReport(
            path=path, file_kind=file_kind, app=app, is_zip=False,
            container_kind="unknown", ooxml_conformance="khong_ap_dung",
            findings=[], notes=[], errors=[f"không đọc được tệp: {exc}"],
        )

    is_zip = False
    try:
        is_zip = zipfile.is_zipfile(path)
    except OSError as exc:
        errors.append(f"lỗi khi kiểm tra ZIP: {exc}")

    if not is_zip:
        if header.startswith(_OLE_CFB_MAGIC):
            findings.append(Finding(
                feature_id="encryption.ole_cfb",
                name_vi="Mã hoá/IRM (gói OLE/Compound File Binary)",
                compat_level=CompatLevel.C3,
                severity=Severity.CRITICAL,
                detail_vi=(
                    "Tệp KHÔNG phải ZIP OOXML hợp lệ mà là Compound File Binary (OLE2) — "
                    "dấu hiệu điển hình của EncryptedPackage (Office mã hoá bằng mật khẩu "
                    "hoặc IRM/Azure Information Protection bọc gói OOXML bên trong)."
                ),
                recommended_action_vi=(
                    "Tệp được bảo vệ (mật khẩu hoặc IRM). KHÔNG cố vượt mật khẩu/IRM dưới "
                    "bất kỳ hình thức nào. Dừng xử lý; chỉ tiếp tục khi người dùng cung cấp "
                    "đúng mật khẩu qua hộp thoại chính thức của ứng dụng."
                ),
                evidence=[f"header_hex={header.hex()}"],
            ))
            container_kind = "ole_cfb"
        else:
            errors.append(
                "Không mở được dưới dạng ZIP OOXML và header không khớp chữ ký OLE/CFB — "
                "có thể là tệp hỏng, định dạng nhị phân Office cũ (.doc/.xls/.ppt thật), "
                "hoặc không phải tệp Office."
            )
            container_kind = "unknown"
        return InspectionReport(
            path=path, file_kind=file_kind, app=app, is_zip=False,
            container_kind=container_kind, ooxml_conformance="khong_ap_dung",
            findings=findings, notes=notes, errors=errors,
        )

    container_kind = "ooxml_zip"
    ooxml_conformance = "unknown"
    try:
        with zipfile.ZipFile(path) as zf:
            try:
                names = zf.namelist()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"không đọc được danh sách entry trong ZIP: {exc}")
                names = []

            # Mỗi bước được bọc riêng: một bucket lỗi không được làm hỏng cả báo cáo.
            steps = [
                ("macro", lambda: _check_macros(names, ext)),
                ("encryption_markers", lambda: _check_encryption_markers_inside_zip(names)),
                ("signature", lambda: _check_signatures(names)),
                ("external_workbook_links", lambda: _check_external_workbook_links(names)),
                ("external_relationships", lambda: _check_external_relationships(zf, names, notes)),
                ("embedded_ole", lambda: _check_embedded_ole_objects(names)),
                ("content_controls", lambda: _check_content_controls(zf, app or "", names, notes)),
                ("sheet_formulas", lambda: _check_sheet_formulas(zf, app or "", names, notes)),
                ("pivot", lambda: _check_pivot(names)),
                ("data_model_power_query", lambda: _check_data_model_power_query(app or "", names)),
                ("charts", lambda: _check_charts(names)),
                ("media", lambda: _check_media(names)),
            ]
            for step_name, step_fn in steps:
                try:
                    findings.extend(step_fn())
                except Exception as exc:  # noqa: BLE001 — cách ly lỗi theo bước
                    errors.append(f"lỗi ở bước '{step_name}': {exc!r}")

            try:
                ooxml_conformance, strict_findings = _check_ooxml_conformance(zf, app, names, notes)
                findings.extend(strict_findings)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"lỗi khi kiểm tra Transitional/Strict: {exc!r}")
                ooxml_conformance = "unknown"
    except zipfile.BadZipFile as exc:
        errors.append(f"ZIP báo hợp lệ ở is_zipfile() nhưng mở lỗi: {exc}")
        ooxml_conformance = "khong_ap_dung"

    return InspectionReport(
        path=path, file_kind=file_kind, app=app, is_zip=True,
        container_kind=container_kind, ooxml_conformance=ooxml_conformance,
        findings=findings, notes=notes, errors=errors,
    )
