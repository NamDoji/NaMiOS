# -*- coding: utf-8 -*-
"""mime_router — dò MIME theo NỘI DUNG (không tin đuôi tệp) + chọn app NaMiOS.

Đọc TRƯỚC: ``docs/specs/namios-pl20/02_MO_TEP_VA_DINH_DANG.md`` §1/§2
("NaMiFiles dò MIME bằng nội dung và cấu trúc, đối chiếu đuôi tên, không mở
mã thực thi chỉ vì người dùng đổi đuôi") và
``docs/specs/namios-pl20/04_KIEN_TRUC_QA.md`` §1 ("nội dung được sniff trước
preview, đuôi chỉ là gợi ý. Registry có MIME, extension, magic, app id,
action view/edit/create/export...").

Module này hiện thực ĐÚNG lớp đó cho một tệp đơn: đọc vài nghìn byte đầu +
(với container ZIP) soi cấu trúc bên trong để phân loại OOXML/ODF/zip
thường, so với đuôi tệp khai báo, và trả về :class:`CapabilityReport` —
KHÔNG mở app thật, KHÔNG thực thi nội dung, KHÔNG gọi mạng.

Tái dùng có trích dẫn (không chép y nguyên — mở rộng cho nhiều định dạng
hơn, nhưng GIỮ NGUYÊN hai tập hợp gốc để không lệch chính sách giữa hai
công cụ):
  * ``EXECUTABLE_EXTENSIONS`` / ``DISGUISE_EXTENSIONS`` và chiến lược "đuôi
    kép" lấy nguyên từ ``tools/pl09-tests/t09_min_helpers.py``
    (``classify_usb_file``/``sniff_magic`` — T09-C, VN09-028).
  * Kiểu dữ liệu Finding/Report theo khuôn ``tools/office-compat/
    namioffice_inspect/inspector.py`` và ``tools/pdf-compat/
    namipdf_inspect/inspector.py`` (dataclass + ``to_dict``/``to_text_vi``).

Giới hạn trung thực:
  - Đây là sniff MAGIC BYTES + cấu trúc ZIP nông (tên entry/`mimetype`),
    KHÔNG phải một shared-mime-info engine đầy đủ (freedesktop thật có
    hàng nghìn rule XML theo thứ tự priority/glob; ở đây là một bảng tối
    thiểu đủ cho vertical slice PL20).
  - MP3/MP4/MKV/WAV ở đây CHỈ xác nhận MAGIC BYTES container/khung đầu —
    KHÔNG giải mã, KHÔNG xác nhận codec/track/DRM thật (đó là việc của
    NaMiMedia + audit giấy phép thật, xem 04_KIEN_TRUC_QA.md §3).
  - OLE/CFB (.doc/.xls/.ppt nhị phân cũ) không tự phân biệt được Writer/
    Sheet/Slides chỉ từ nội dung CFB không mở — dùng đuôi tệp làm phụ trợ
    CHỈ trong trường hợp này, có ghi chú rõ trong report (``notes_vi``).
  - KHÔNG phải virus scanner: chỉ chặn theo magic PE/ELF/shebang + đuôi kép
    đáng ngờ, không quét mã độc polymorphic/heuristic thật.
"""

from __future__ import annotations

import dataclasses
import os
import zipfile
from dataclasses import dataclass, field

__all__ = [
    "EXECUTABLE_EXTENSIONS",
    "DISGUISE_EXTENSIONS",
    "EXECUTABLE_CONTENT_KINDS",
    "AppInfo",
    "APP_CATALOG",
    "CONTENT_KIND_TO_APP",
    "CONTENT_KIND_TO_MIME",
    "CapabilityReport",
    "FileAssociationRegistry",
    "sniff_content_kind",
    "apps_for_content_kind",
    "route_file",
]


# ---------------------------------------------------------------------------
# Tập hợp lấy NGUYÊN từ tools/pl09-tests/t09_min_helpers.py (T09-C) — xem
# docstring module trên. Không đổi giá trị để hai công cụ không lệch chính
# sách "đuôi nào bị coi là thực thi / đuôi nào hay bị dùng làm lớp ngụy
# trang".
# ---------------------------------------------------------------------------

EXECUTABLE_EXTENSIONS: frozenset[str] = frozenset(
    {"exe", "scr", "com", "bat", "cmd", "msi", "pif", "jar", "vbs", "js", "ps1", "wsf"}
)
DISGUISE_EXTENSIONS: frozenset[str] = frozenset(
    {"pdf", "docx", "doc", "xlsx", "xls", "jpg", "jpeg", "png", "txt", "zip", "mp3", "mp4"}
)

#: content_kind coi là "mã thực thi/script" theo MAGIC BYTES thật (không
#: phải theo đuôi) — luôn bị chặn route, bất kể đuôi khai báo là gì.
EXECUTABLE_CONTENT_KINDS: frozenset[str] = frozenset(
    {"pe_executable", "elf_executable", "script_shebang"}
)

#: Hai đuôi ghép ("tar.gz"...) được coi là một đơn vị khi so khớp bảng gợi ý
#: đuôi — tránh báo nhầm "mismatch" cho .tar.gz vì .gz đơn lẻ không giống
#: .tar.gz về app/engine cần dùng.
_COMPOUND_EXTENSIONS: frozenset[str] = frozenset({"tar.gz", "tar.bz2", "tar.xz", "tar.xz2"})

_HEAD_BYTES = 4096  # đủ cho mọi magic header đã biết ở dưới; không đọc cả tệp.


# ---------------------------------------------------------------------------
# Catalog app NaMiOS (02_MO_TEP_VA_DINH_DANG.md bảng mục 1).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AppInfo:
    app_id: str
    name_vi: str
    can_view: bool
    can_edit: bool
    caveat_vi: str = ""

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


APP_CATALOG: dict[str, AppInfo] = {
    "namioffice_writer": AppInfo(
        "namioffice_writer", "NaMiWriter (NaMiOffice)", True, True,
        "DOCX phức tạp/macro/chữ ký/font theo corpus — dùng "
        "tools/office-compat/namioffice_inspect để chấm C0–C3 chi tiết TRƯỚC khi lưu đè.",
    ),
    "namioffice_sheet": AppInfo(
        "namioffice_sheet", "NaMiSheet (NaMiOffice)", True, True,
        "Công thức/Pivot/chart/XLSM/Power Query theo phiên bản/ma trận — "
        "dùng tools/office-compat/namioffice_inspect.",
    ),
    "namioffice_slides": AppInfo(
        "namioffice_slides", "NaMiSlides (NaMiOffice)", True, True,
        "Animation/video/font/object nhúng có thể khác — dùng tools/office-compat/namioffice_inspect.",
    ),
    "namipdf": AppInfo(
        "namipdf", "NaMiPDF", True, False,
        "Xem P0; sửa nội dung/OCR/ký/redact qua cổng riêng, KHÔNG coi là 'sửa' mặc định — "
        "dùng tools/pdf-compat/namipdf_inspect để biết Signed/Protected/Scan TRƯỚC khi cho sửa.",
    ),
    "namiarchive": AppInfo(
        "namiarchive", "NaMiArchive", True, True,
        "Giải nén PHẢI qua archive_safety (module cùng cấp) trước — không tự giải nén khi báo không an toàn.",
    ),
    "namiimages": AppInfo(
        "namiimages", "NaMiImages", True, True,
        "Crop/rotate/resize cơ bản; EXIF orientation/ICC/animation/alpha/JPEG mất dữ liệu "
        "theo 02_MO_TEP_VA_DINH_DANG.md §4.",
    ),
    "namimedia": AppInfo(
        "namimedia", "NaMiMedia", True, False,
        "Phát/playlist; converter/editor là P1 riêng. Codec/container/DRM thật cần audit "
        "giấy phép theo thị trường — xem 04_KIEN_TRUC_QA.md §3; KHÔNG tự tìm codec lạ trên mạng.",
    ),
    "namibrowser": AppInfo(
        "namibrowser", "NaMiBrowser (xem nhanh)", True, False,
        "Chỉ xem nhanh trong sandbox trình duyệt (preview, không ghi được quyền) — "
        "KHÔNG dùng thay NaMiPDF/NaMiImages cho chỉnh sửa; không phải app mặc định chính thức.",
    ),
}

#: Ánh xạ content_kind (đã sniff) -> app MẶC ĐỊNH (02_MO_TEP_VA_DINH_DANG.md bảng mục 1).
CONTENT_KIND_TO_APP: dict[str, str] = {
    "ooxml_docx": "namioffice_writer",
    "ooxml_xlsx": "namioffice_sheet",
    "ooxml_pptx": "namioffice_slides",
    "odf_odt": "namioffice_writer",
    "odf_ods": "namioffice_sheet",
    "odf_odp": "namioffice_slides",
    "rtf": "namioffice_writer",
    "text_plain": "namioffice_writer",  # có thể bị override sang sheet cho .csv/.tsv, xem route_file
    "pdf": "namipdf",
    "zip_archive": "namiarchive",
    "jar_archive": "namiarchive",
    "tar_archive": "namiarchive",
    "gzip_file": "namiarchive",
    "bzip2_file": "namiarchive",
    "xz_file": "namiarchive",
    "sevenzip_file": "namiarchive",
    "rar_file": "namiarchive",
    "png": "namiimages",
    "jpeg": "namiimages",
    "gif": "namiimages",
    "bmp": "namiimages",
    "webp": "namiimages",
    "tiff": "namiimages",
    "mp3": "namimedia",
    "wav": "namimedia",
    "flac": "namimedia",
    "ogg": "namimedia",
    "aac_adts": "namimedia",
    "mp4_or_mov": "namimedia",
    "ebml_matroska": "namimedia",
    "avi": "namimedia",
}

#: App "xem nhanh" thêm ngoài app mặc định (cho "Mở bằng..."/Open-With và
#: cho bài test đổi app mặc định — 02_MO_TEP_VA_DINH_DANG.md §2).
_EXTRA_ALTERNATE_APPS: dict[str, tuple[str, ...]] = {
    "pdf": ("namibrowser",),
    "png": ("namibrowser",),
    "jpeg": ("namibrowser",),
    "gif": ("namibrowser",),
    "bmp": ("namibrowser",),
    "webp": ("namibrowser",),
}

#: ext (OLE/CFB cũ) -> sub-app NaMiOffice khi KHÔNG đoán được từ nội dung
#: CFB không mở (word/xl/ppt binary cũ dùng chung 1 magic header).
_OLE_LEGACY_EXT_TO_APP: dict[str, str] = {
    "doc": "namioffice_writer", "dot": "namioffice_writer",
    "xls": "namioffice_sheet", "xlt": "namioffice_sheet", "xla": "namioffice_sheet",
    "ppt": "namioffice_slides", "pps": "namioffice_slides", "pot": "namioffice_slides",
}

#: Mô tả mime "kiểu freedesktop" cho mỗi content_kind — chỉ để hiển thị,
#: KHÔNG phải import thật từ shared-mime-info (xem giới hạn ở đầu file).
CONTENT_KIND_TO_MIME: dict[str, str] = {
    "ooxml_docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "ooxml_xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "ooxml_pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "ooxml_unknown": "application/zip",
    "odf_odt": "application/vnd.oasis.opendocument.text",
    "odf_ods": "application/vnd.oasis.opendocument.spreadsheet",
    "odf_odp": "application/vnd.oasis.opendocument.presentation",
    "odf_unknown": "application/zip",
    "pdf": "application/pdf",
    "zip_archive": "application/zip",
    "zip_archive_corrupt": "application/zip",
    "jar_archive": "application/java-archive",
    "tar_archive": "application/x-tar",
    "gzip_file": "application/gzip",
    "bzip2_file": "application/x-bzip2",
    "xz_file": "application/x-xz",
    "sevenzip_file": "application/x-7z-compressed",
    "rar_file": "application/vnd.rar",
    "png": "image/png",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "webp": "image/webp",
    "tiff": "image/tiff",
    "mp3": "audio/mpeg",
    "wav": "audio/vnd.wave",
    "flac": "audio/flac",
    "ogg": "audio/ogg",
    "aac_adts": "audio/aac",
    "mp4_or_mov": "video/mp4",
    "ebml_matroska": "video/x-matroska",
    "avi": "video/x-msvideo",
    "ole_cfb_legacy_office": "application/x-ole-storage",
    "rtf": "application/rtf",
    "text_plain": "text/plain",
    "pe_executable": "application/x-msdownload",
    "elf_executable": "application/x-executable",
    "script_shebang": "text/x-shellscript",
    "unknown_binary": "application/octet-stream",
    "unreadable": "application/octet-stream",
}


def _build_app_capable_kinds() -> dict[str, frozenset[str]]:
    result: dict[str, set[str]] = {}
    for kind, app_id in CONTENT_KIND_TO_APP.items():
        result.setdefault(app_id, set()).add(kind)
    for app_id in _OLE_LEGACY_EXT_TO_APP.values():
        result.setdefault(app_id, set()).add("ole_cfb_legacy_office")
    for kind, extra_apps in _EXTRA_ALTERNATE_APPS.items():
        for app_id in extra_apps:
            result.setdefault(app_id, set()).add(kind)
    return {app_id: frozenset(kinds) for app_id, kinds in result.items()}


#: app_id -> tập content_kind app đó TỰ KHAI hỗ trợ — dùng để (a) liệt kê
#: "Mở bằng..." và (b) chặn người dùng đặt một app KHÔNG khai hỗ trợ loại
#: tệp làm mặc định (02_MO_TEP_VA_DINH_DANG.md §2: "Không để một chương
#: trình 'chiếm' mặc định hàng trăm MIME không xử lý tốt").
APP_CAPABLE_KINDS: dict[str, frozenset[str]] = _build_app_capable_kinds()


def apps_for_content_kind(content_kind: str) -> tuple[str, ...]:
    """Danh sách app (đã sắp xếp) tự khai hỗ trợ ``content_kind`` — dùng cho
    menu "Mở bằng..."."""
    return tuple(sorted(app_id for app_id, kinds in APP_CAPABLE_KINDS.items() if content_kind in kinds))


#: ext (đuôi cuối, hoặc đuôi ghép trong ``_COMPOUND_EXTENSIONS``) -> tập
#: content_kind coi là "khớp đuôi" — dùng để phát hiện lệch đuôi/nội dung.
EXTENSION_HINT_TABLE: dict[str, frozenset[str]] = {
    "docx": frozenset({"ooxml_docx"}), "docm": frozenset({"ooxml_docx"}),
    "dotx": frozenset({"ooxml_docx"}),
    "xlsx": frozenset({"ooxml_xlsx"}), "xlsm": frozenset({"ooxml_xlsx"}),
    "xltx": frozenset({"ooxml_xlsx"}),
    "pptx": frozenset({"ooxml_pptx"}), "pptm": frozenset({"ooxml_pptx"}),
    "potx": frozenset({"ooxml_pptx"}),
    "odt": frozenset({"odf_odt"}), "ods": frozenset({"odf_ods"}), "odp": frozenset({"odf_odp"}),
    "doc": frozenset({"ole_cfb_legacy_office", "ooxml_docx"}),
    "dot": frozenset({"ole_cfb_legacy_office"}),
    "xls": frozenset({"ole_cfb_legacy_office", "ooxml_xlsx"}),
    "xlt": frozenset({"ole_cfb_legacy_office"}),
    "ppt": frozenset({"ole_cfb_legacy_office", "ooxml_pptx"}),
    "pps": frozenset({"ole_cfb_legacy_office"}),
    "pot": frozenset({"ole_cfb_legacy_office"}),
    "rtf": frozenset({"rtf"}),
    "txt": frozenset({"text_plain"}),
    "csv": frozenset({"text_plain"}), "tsv": frozenset({"text_plain"}),
    "md": frozenset({"text_plain"}), "json": frozenset({"text_plain"}),
    "pdf": frozenset({"pdf"}),
    "zip": frozenset({"zip_archive", "jar_archive", "ooxml_unknown", "odf_unknown"}),
    "jar": frozenset({"jar_archive"}),
    "7z": frozenset({"sevenzip_file"}),
    "tar": frozenset({"tar_archive"}),
    "tar.gz": frozenset({"tar_archive"}), "tgz": frozenset({"tar_archive"}),
    "tar.bz2": frozenset({"tar_archive"}), "tbz2": frozenset({"tar_archive"}),
    "tar.xz": frozenset({"tar_archive"}),
    "gz": frozenset({"gzip_file", "tar_archive"}),
    "bz2": frozenset({"bzip2_file", "tar_archive"}),
    "xz": frozenset({"xz_file", "tar_archive"}),
    "rar": frozenset({"rar_file"}),
    "png": frozenset({"png"}),
    "jpg": frozenset({"jpeg"}), "jpeg": frozenset({"jpeg"}),
    "gif": frozenset({"gif"}),
    "bmp": frozenset({"bmp"}),
    "webp": frozenset({"webp"}),
    "tif": frozenset({"tiff"}), "tiff": frozenset({"tiff"}),
    "mp3": frozenset({"mp3"}),
    "wav": frozenset({"wav"}),
    "flac": frozenset({"flac"}),
    "ogg": frozenset({"ogg"}), "oga": frozenset({"ogg"}),
    "aac": frozenset({"aac_adts"}),
    "m4a": frozenset({"mp4_or_mov"}),
    "mp4": frozenset({"mp4_or_mov"}), "m4v": frozenset({"mp4_or_mov"}),
    "mov": frozenset({"mp4_or_mov"}),
    "mkv": frozenset({"ebml_matroska"}), "webm": frozenset({"ebml_matroska"}),
    "avi": frozenset({"avi"}),
}


def _ext_lookup_key(ext_parts: list[str]) -> str:
    if len(ext_parts) >= 2:
        compound = f"{ext_parts[-2]}.{ext_parts[-1]}"
        if compound in _COMPOUND_EXTENSIONS:
            return compound
    return ext_parts[-1] if ext_parts else ""


# ---------------------------------------------------------------------------
# Sniff nội dung — magic bytes + soi cấu trúc ZIP nông.
# ---------------------------------------------------------------------------


def _sniff_zip_subtype(path: str) -> str:
    """Soi NÔNG cấu trúc một container ZIP (chỉ đọc tên entry + nội dung
    entry ``mimetype`` nếu có — KHÔNG đọc toàn bộ nội dung từng part, tránh
    trùng việc mà ``archive_safety``/``namioffice_inspect`` đã làm kỹ hơn)."""
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            lnames = set(names)
            if "[Content_Types].xml" in lnames:
                if any(n.startswith("word/") for n in lnames):
                    return "ooxml_docx"
                if any(n.startswith("xl/") for n in lnames):
                    return "ooxml_xlsx"
                if any(n.startswith("ppt/") for n in lnames):
                    return "ooxml_pptx"
                return "ooxml_unknown"
            if "mimetype" in lnames:
                try:
                    mt = zf.read("mimetype").decode("ascii", errors="replace").strip()
                except Exception:  # noqa: BLE001
                    mt = ""
                odf_map = {
                    "application/vnd.oasis.opendocument.text": "odf_odt",
                    "application/vnd.oasis.opendocument.spreadsheet": "odf_ods",
                    "application/vnd.oasis.opendocument.presentation": "odf_odp",
                }
                return odf_map.get(mt, "odf_unknown")
            if "META-INF/MANIFEST.MF" in lnames:
                return "jar_archive"
            return "zip_archive"
    except Exception:  # noqa: BLE001 — zip hỏng/đóng gói lạ, không ném lỗi ra ngoài sniff
        return "zip_archive_corrupt"


def sniff_content_kind(path: str) -> str:
    """Dò loại NỘI DUNG thật của ``path`` từ magic bytes (+ cấu trúc ZIP
    nông khi cần) — KHÔNG tin đuôi tệp. Luôn trả về một chuỗi (không ném
    lỗi trừ khi tệp không đọc được, lúc đó trả ``"unreadable"``)."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(_HEAD_BYTES)
    except OSError:
        return "unreadable"

    if head.startswith(b"MZ"):
        return "pe_executable"
    if head.startswith(b"\x7fELF"):
        return "elf_executable"
    if head.startswith(b"#!"):
        return "script_shebang"
    if b"%PDF-" in head[:1024]:
        return "pdf"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if head[:2] == b"BM":
        return "bmp"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "wav"
    if head[:4] == b"RIFF" and head[8:12] == b"AVI ":
        return "avi"
    if head[:4] == b"fLaC":
        return "flac"
    if head[:4] == b"OggS":
        return "ogg"
    if head[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    if head.startswith(b"ID3") or (len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0):
        return "mp3"
    if len(head) >= 2 and head[0] == 0xFF and head[1] in (0xF1, 0xF9):
        return "aac_adts"
    if len(head) >= 12 and head[4:8] == b"ftyp":
        return "mp4_or_mov"
    if head[:4] == b"\x1a\x45\xdf\xa3":
        return "ebml_matroska"
    if head[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return "ole_cfb_legacy_office"
    if head[:4] == b"Rar!":
        return "rar_file"
    if head[:6] == b"7z\xbc\xaf\x27\x1c":
        return "sevenzip_file"
    if head[:2] == b"\x1f\x8b":
        return "gzip_file"
    if head[:3] == b"BZh":
        return "bzip2_file"
    if head[:6] == b"\xfd7zXZ\x00":
        return "xz_file"
    if head.startswith(b"{\\rtf"):
        return "rtf"

    try:
        import tarfile
        if tarfile.is_tarfile(path):
            return "tar_archive"
    except Exception:  # noqa: BLE001
        pass

    try:
        if zipfile.is_zipfile(path):
            return _sniff_zip_subtype(path)
    except Exception:  # noqa: BLE001
        pass

    if not head:
        return "unknown_binary"
    try:
        head.decode("utf-8")
        return "text_plain"
    except UnicodeDecodeError:
        return "unknown_binary"


# ---------------------------------------------------------------------------
# CapabilityReport.
# ---------------------------------------------------------------------------


@dataclass
class CapabilityReport:
    """Kết quả route MỘT tệp — trả cho NaMiFiles/CLI trước khi mở app thật."""

    path: str
    ext: str  # đuôi cuối khai báo (không dấu '.'), "" nếu không có
    detected_content_kind: str
    detected_mime: str
    app: str | None
    app_name_vi: str | None
    can_view: bool
    can_edit: bool
    blocked: bool
    extension_content_mismatch: bool
    double_extension_disguise: bool
    risk_flags: list[str] = field(default_factory=list)
    warnings_vi: list[str] = field(default_factory=list)
    notes_vi: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "ext": self.ext,
            "detected_content_kind": self.detected_content_kind,
            "detected_mime": self.detected_mime,
            "app": self.app,
            "app_name_vi": self.app_name_vi,
            "can_view": self.can_view,
            "can_edit": self.can_edit,
            "blocked": self.blocked,
            "extension_content_mismatch": self.extension_content_mismatch,
            "double_extension_disguise": self.double_extension_disguise,
            "risk_flags": list(self.risk_flags),
            "warnings_vi": list(self.warnings_vi),
            "notes_vi": list(self.notes_vi),
        }

    def to_text_vi(self) -> str:
        lines = [
            "=== BÁO CÁO MIME ROUTER (NaMiOS, PL20) ===",
            f"Tệp: {self.path}",
            f"Đuôi khai báo: .{self.ext}" if self.ext else "Đuôi khai báo: (không có)",
            f"Nội dung dò được: {self.detected_content_kind} ({self.detected_mime})",
        ]
        if self.blocked:
            lines.append("KẾT QUẢ: BỊ CHẶN — không mở bằng app nào, không tự thực thi.")
        elif self.app:
            info = APP_CATALOG.get(self.app)
            lines.append(
                f"KẾT QUẢ: mở bằng {self.app_name_vi or self.app} "
                f"(xem: {self.can_view}, sửa: {self.can_edit})"
            )
            if info and info.caveat_vi:
                lines.append(f"  Lưu ý: {info.caveat_vi}")
        else:
            lines.append(
                "KẾT QUẢ: Không nhận diện được định dạng — hiển thị tùy chọn an toàn "
                "(xem/quét/lưu nguyên vẹn), không tự mở bằng app nào."
            )
        if self.risk_flags:
            lines.append(f"Cờ rủi ro: {', '.join(self.risk_flags)}")
        for w in self.warnings_vi:
            lines.append(f"  CẢNH BÁO: {w}")
        for n in self.notes_vi:
            lines.append(f"  * {n}")
        return "\n".join(lines)


def _basename_ext_parts(path: str) -> list[str]:
    basename = os.path.basename(path)
    parts = basename.split(".")
    if len(parts) <= 1:
        return []
    return [p.lower() for p in parts[1:]]


def route_file(path: str) -> CapabilityReport:
    """Route MỘT tệp theo NỘI DUNG thật (đuôi chỉ là gợi ý/tín hiệu phụ) —
    KHÔNG mở app thật, KHÔNG thực thi, KHÔNG sửa/ghi gì vào ``path``.

    Trả về :class:`CapabilityReport`; không ném lỗi ra ngoài kể cả khi tệp
    không đọc được (``detected_content_kind == "unreadable"``, ``blocked``
    sẽ là ``True`` vì không có gì an toàn để mở)."""
    ext_parts = _basename_ext_parts(path)
    last_ext = ext_parts[-1] if ext_parts else ""
    disguise_ext = ext_parts[-2] if len(ext_parts) >= 2 else ""
    lookup_ext = _ext_lookup_key(ext_parts)

    double_extension_disguise = bool(
        disguise_ext in DISGUISE_EXTENSIONS and last_ext in EXECUTABLE_EXTENSIONS
    )

    content_kind = sniff_content_kind(path)

    risk_flags: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    if content_kind == "unreadable":
        return CapabilityReport(
            path=path, ext=last_ext, detected_content_kind=content_kind,
            detected_mime=CONTENT_KIND_TO_MIME.get(content_kind, "application/octet-stream"),
            app=None, app_name_vi=None, can_view=False, can_edit=False, blocked=True,
            extension_content_mismatch=False, double_extension_disguise=double_extension_disguise,
            risk_flags=["file_unreadable"],
            warnings_vi=[f"Không đọc được tệp '{path}' để kiểm tra — KHÔNG mở, không giả định an toàn."],
            notes_vi=[],
        )

    is_executable_content = content_kind in EXECUTABLE_CONTENT_KINDS

    expected_kinds = EXTENSION_HINT_TABLE.get(lookup_ext, frozenset())
    extension_content_mismatch = bool(
        expected_kinds and content_kind not in expected_kinds
        and content_kind not in ("zip_archive_corrupt", "unknown_binary")
    )

    if double_extension_disguise:
        risk_flags.append("double_extension_disguise")
        warnings.append(
            f"Tên tệp có ĐUÔI KÉP đáng ngờ: .{disguise_ext}.{last_ext} — có thể là tệp thực thi "
            "ngụy trang (xem T09-C, tools/pl09-tests/t09_min_helpers.py)."
        )
    if is_executable_content:
        risk_flags.append("executable_content")
        warnings.append(
            f"Nội dung tệp là mã thực thi/script thật ({content_kind}) — đuôi khai báo "
            f"'.{last_ext or '(không có)'}' không quan trọng, KHÔNG được mở/chạy."
        )
    if extension_content_mismatch:
        risk_flags.append("extension_content_mismatch")
        warnings.append(
            f"Đuôi tệp '.{last_ext}' không khớp nội dung thật đã dò được ({content_kind})."
        )

    blocked = is_executable_content or double_extension_disguise

    app: str | None = None
    app_name_vi: str | None = None
    can_view = False
    can_edit = False

    if not blocked:
        resolved_app_id = CONTENT_KIND_TO_APP.get(content_kind)

        if resolved_app_id is None and content_kind == "ole_cfb_legacy_office":
            resolved_app_id = _OLE_LEGACY_EXT_TO_APP.get(last_ext, "namioffice_writer")
            notes.append(
                "Định dạng OLE/CFB nhị phân cũ (.doc/.xls/.ppt) không tự phân biệt Writer/"
                "Sheet/Slides chỉ từ nội dung CFB chưa mở — dùng ĐUÔI TỆP làm phụ trợ để chọn "
                f"sub-app ('.{last_ext}' -> {resolved_app_id}); nếu đuôi sai, sub-app này có "
                "thể sai."
            )

        if resolved_app_id == "namioffice_writer" and content_kind == "text_plain" and last_ext in ("csv", "tsv"):
            resolved_app_id = "namioffice_sheet"
            notes.append(f"Nội dung text thuần không tự phân biệt CSV/TXT — dùng đuôi '.{last_ext}' để mở bằng NaMiSheet.")

        # CHỦ Ý không suy đoán theo đuôi khi nội dung THỰC SỰ không có tín hiệu
        # (unknown_binary/zip_archive_corrupt) — 02_MO_TEP_VA_DINH_DANG.md §1:
        # "tệp lạ hiển thị 'Không nhận diện được định dạng' cùng tùy chọn an
        # toàn", KHÔNG lặng lẽ mở bằng app đoán theo đuôi khi không có gì
        # trong nội dung xác nhận điều đó.
        if (
            resolved_app_id is None
            and expected_kinds
            and content_kind not in ("unknown_binary", "zip_archive_corrupt")
        ):
            fallback_kind = next(iter(expected_kinds))
            resolved_app_id = CONTENT_KIND_TO_APP.get(fallback_kind)
            if resolved_app_id is not None:
                risk_flags.append("routed_by_extension_fallback")
                notes.append(
                    "Không dò được app theo NỘI DUNG; dùng SUY ĐOÁN theo đuôi tệp "
                    f"('.{last_ext}') — CHƯA xác nhận bằng nội dung thật, cần xem lại."
                )

        if resolved_app_id is not None:
            info = APP_CATALOG[resolved_app_id]
            app, app_name_vi, can_view, can_edit = info.app_id, info.name_vi, info.can_view, info.can_edit
        else:
            notes.append(
                "Không nhận diện được định dạng (content_kind="
                f"{content_kind!r}, ext='.{last_ext}' nếu có) — hiển thị 'Không nhận diện được "
                "định dạng' cùng tùy chọn an toàn theo 02_MO_TEP_VA_DINH_DANG.md §1, KHÔNG tự mở."
            )

    return CapabilityReport(
        path=path, ext=last_ext, detected_content_kind=content_kind,
        detected_mime=CONTENT_KIND_TO_MIME.get(content_kind, "application/octet-stream"),
        app=app, app_name_vi=app_name_vi, can_view=can_view, can_edit=can_edit, blocked=blocked,
        extension_content_mismatch=extension_content_mismatch,
        double_extension_disguise=double_extension_disguise,
        risk_flags=risk_flags, warnings_vi=warnings, notes_vi=notes,
    )


# ---------------------------------------------------------------------------
# "Luôn dùng ứng dụng này cho loại tệp" — đổi app mặc định theo content_kind.
# ---------------------------------------------------------------------------


class FileAssociationRegistry:
    """Mô hình tối giản phần "đổi app mặc định" của NaMiFiles
    (02_MO_TEP_VA_DINH_DANG.md §2: "Hỗ trợ thay mặc định trong Settings và
    reset mà không làm hỏng hệ thống... Không để một chương trình 'chiếm'
    mặc định hàng trăm MIME không xử lý tốt").

    Bất biến an toàn: ``resolve()`` KHÔNG BAO GIỜ áp override cho một
    :class:`CapabilityReport` đã ``blocked=True`` — đổi app mặc định không
    được dùng để lách việc chặn mã thực thi/đuôi giả."""

    def __init__(self) -> None:
        self._overrides: dict[str, str] = {}

    def set_default(self, content_kind: str, app_id: str) -> None:
        if app_id not in APP_CATALOG:
            raise ValueError(f"app_id không tồn tại trong APP_CATALOG: {app_id!r}")
        if content_kind not in APP_CAPABLE_KINDS.get(app_id, frozenset()):
            raise ValueError(
                f"App '{app_id}' không tự khai hỗ trợ content_kind={content_kind!r} — không thể "
                "đặt làm mặc định (tránh một app 'chiếm' MIME nó không xử lý tốt, "
                "02_MO_TEP_VA_DINH_DANG.md §2)."
            )
        self._overrides[content_kind] = app_id

    def reset_default(self, content_kind: str) -> None:
        self._overrides.pop(content_kind, None)

    def get_default(self, content_kind: str) -> str | None:
        return self._overrides.get(content_kind)

    def resolve(self, report: CapabilityReport) -> CapabilityReport:
        """Trả về report mới có ``app`` đổi theo override người dùng đã đặt
        (nếu có và report không bị chặn); report gốc không bị sửa."""
        if report.blocked:
            return report
        override_app_id = self._overrides.get(report.detected_content_kind)
        if not override_app_id or override_app_id == report.app:
            return report
        info = APP_CATALOG[override_app_id]
        return dataclasses.replace(
            report,
            app=info.app_id,
            app_name_vi=info.name_vi,
            can_view=info.can_view,
            can_edit=info.can_edit,
            notes_vi=[
                *report.notes_vi,
                f"Đã áp dụng app MẶC ĐỊNH do người dùng chọn cho loại '{report.detected_content_kind}': "
                f"{info.app_id} (thay cho mặc định hệ thống).",
            ],
        )
