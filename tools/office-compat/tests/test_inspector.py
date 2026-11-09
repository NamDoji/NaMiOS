# -*- coding: utf-8 -*-
"""Pytest cho namioffice_inspect — Compatibility Inspector (NaMiOffice v2).

Mọi fixture là tệp OOXML THẬT, sinh ra NGAY LÚC CHẠY TEST bằng python-docx/
openpyxl/python-pptx (chỉ dùng ở TEST, không phải runtime của tool — tool
giao cho người dùng chỉ cần stdlib). Một số kịch bản (macro, chữ ký số, OLE
object ngoài, dynamic array đúng cú pháp Excel thật) không có API bậc cao
trong các thư viện trên, nên được dựng bằng cách VIẾT LẠI zip trực tiếp
(thêm/ghi đè entry) — đây là cách duy nhất để mô phỏng trung thực cấu trúc
mà Microsoft Office thật sự tạo ra (ví dụ: Excel LUÔN lưu hàm mới với tiền
tố ``_xlfn.``, điều mà openpyxl không tự làm).

KHÔNG có bước nào trong file test này THỰC THI nội dung OOXML (không mở
bằng LibreOffice/Office, không chạy macro) — chỉ build & đọc lại bằng
zipfile/ElementTree, giống đúng những gì namioffice_inspect làm.
"""
from __future__ import annotations

import os
import zipfile

import pytest
from openpyxl import Workbook

from namioffice_inspect.inspector import CompatLevel, Severity, inspect_file

# ---------------------------------------------------------------------------
# Hạ tầng fixture chung.
# ---------------------------------------------------------------------------


def _rewrite_zip(src_path: str, dst_path: str, extra: dict[str, bytes] | None = None,
                  remove_prefixes: tuple[str, ...] = ()) -> None:
    """Sao chép toàn bộ entry của ``src_path`` sang ``dst_path``, bỏ các entry
    có tên bắt đầu bằng ``remove_prefixes``, rồi thêm/ghi đè các entry trong
    ``extra`` (name -> bytes). Dùng để mô phỏng cấu trúc gói OOXML mà các
    thư viện bậc cao (python-docx/openpyxl/python-pptx) không hỗ trợ tạo
    trực tiếp (vbaProject.bin, _xmlsignatures/, externalLinks, v.v.)."""
    extra = extra or {}
    with zipfile.ZipFile(src_path) as zin, zipfile.ZipFile(dst_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if any(item.filename.startswith(p) for p in remove_prefixes):
                continue
            if item.filename in extra:
                continue
            zout.writestr(item, zin.read(item.filename))
        for name, data in extra.items():
            zout.writestr(name, data)


def _plain_xlsx(tmp_path, name: str = "plain.xlsx") -> str:
    wb = Workbook()
    ws = wb.active
    ws.title = "Data"
    ws["A1"] = 1
    ws["A2"] = 2
    ws["A3"] = 3
    ws["B1"] = "=SUM(A1:A3)"
    path = os.path.join(tmp_path, name)
    wb.save(path)
    return path


def _plain_docx(tmp_path, name: str = "plain.docx") -> str:
    from docx import Document

    doc = Document()
    doc.add_heading("Tài liệu kiểm tra", level=1)
    doc.add_paragraph("Đoạn văn bản bình thường, không có tính năng rủi ro nào.")
    path = os.path.join(tmp_path, name)
    doc.save(path)
    return path


def _plain_pptx(tmp_path, name: str = "plain.pptx") -> str:
    from pptx import Presentation

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Slide kiểm tra"
    path = os.path.join(tmp_path, name)
    prs.save(path)
    return path


# ---------------------------------------------------------------------------
# 1. Tệp sạch — không có tính năng rủi ro nào.
# ---------------------------------------------------------------------------


def test_plain_xlsx_is_c0_and_safe_to_overwrite(tmp_path):
    path = _plain_xlsx(tmp_path)
    report = inspect_file(path)

    assert report.is_zip is True
    assert report.container_kind == "ooxml_zip"
    assert report.app == "sheet"
    assert report.ooxml_conformance == "transitional"
    assert report.findings == []
    assert report.max_compat_level == CompatLevel.C0
    assert report.max_severity == Severity.INFO
    assert report.safe_to_overwrite is True
    assert report.errors == []


def test_plain_docx_is_c0(tmp_path):
    path = _plain_docx(tmp_path)
    report = inspect_file(path)
    assert report.app == "writer"
    assert report.findings == []
    assert report.max_compat_level == CompatLevel.C0
    assert report.safe_to_overwrite is True


def test_plain_pptx_is_c0(tmp_path):
    path = _plain_pptx(tmp_path)
    report = inspect_file(path)
    assert report.app == "slides"
    assert report.findings == []
    assert report.max_compat_level == CompatLevel.C0


# ---------------------------------------------------------------------------
# 2. Macro VBA.
# ---------------------------------------------------------------------------


def test_docm_with_vba_project_bin_is_c3_high_blocks_overwrite(tmp_path):
    src = _plain_docx(tmp_path, "src.docx")
    dst = os.path.join(tmp_path, "withmacro.docm")
    _rewrite_zip(src, dst, extra={"word/vbaProject.bin": b"FAKE_VBA_PROJECT_STUB_NOT_REAL_OLE"})

    report = inspect_file(dst)
    finding = report.find("macro.vba")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C3
    assert finding.severity == Severity.HIGH
    assert "word/vbaProject.bin" in finding.evidence
    assert report.max_severity == Severity.HIGH
    assert report.safe_to_overwrite is False


def test_macro_extension_without_vba_project_still_flags_macro_risk(tmp_path):
    """Đuôi *.xlsm BẮT BUỘC phải bị coi là rủi ro macro ngay cả khi phần
    vbaProject.bin không còn trong gói (đuôi tệp là tín hiệu chính thức đủ
    để cảnh báo — spec 05_PROMPT bước 2: 'macro-enabled extension')."""
    src = _plain_xlsx(tmp_path, "src.xlsx")
    dst = os.path.join(tmp_path, "nobin.xlsm")
    _rewrite_zip(src, dst)  # copy y nguyên nội dung xlsx, chỉ đổi đuôi

    report = inspect_file(dst)
    finding = report.find("macro.vba")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C3
    assert finding.severity == Severity.HIGH
    assert "KHÔNG tìm thấy vbaProject.bin" in finding.detail_vi


def test_vba_project_without_macro_extension_is_abnormal_but_still_flagged(tmp_path):
    """vbaProject.bin lọt vào một tệp đuôi *.docx (không phải *m) là BẤT
    THƯỜNG (có thể đổi tên để né lọc) — vẫn phải coi là macro."""
    src = _plain_docx(tmp_path, "src.docx")
    dst = os.path.join(tmp_path, "sneaky.docx")
    _rewrite_zip(src, dst, extra={"word/vbaProject.bin": b"FAKE"})

    report = inspect_file(dst)
    finding = report.find("macro.vba")
    assert finding is not None
    assert "BẤT THƯỜNG" in finding.detail_vi


# ---------------------------------------------------------------------------
# 3. Chữ ký số.
# ---------------------------------------------------------------------------


def test_signed_part_flags_signature_not_macro(tmp_path):
    src = _plain_docx(tmp_path, "src.docx")
    dst = os.path.join(tmp_path, "signed.docx")
    _rewrite_zip(src, dst, extra={
        "_xmlsignatures/origin.sigs": b"<fake-origin/>",
        "_xmlsignatures/sig1.xml": b"<fake-signature/>",
    })

    report = inspect_file(dst)
    sig = report.find("signature.digital")
    assert sig is not None
    assert sig.compat_level == CompatLevel.C2
    assert sig.severity == Severity.HIGH
    assert report.find("macro.vba") is None
    # C2 vẫn đủ để chặn lưu-đè-trực-tiếp theo quy tắc atomic-save.
    assert report.safe_to_overwrite is False


# ---------------------------------------------------------------------------
# 4. Mã hoá / IRM (OLE CFB) — không phải ZIP.
# ---------------------------------------------------------------------------


def test_ole_cfb_header_blocks_as_encrypted_irm(tmp_path):
    path = os.path.join(tmp_path, "protected.xlsx")
    ole_magic = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    with open(path, "wb") as fh:
        fh.write(ole_magic + b"\x00" * 504)  # đệm cho đủ 512 byte sector đầu

    report = inspect_file(path)
    assert report.is_zip is False
    assert report.container_kind == "ole_cfb"
    finding = report.find("encryption.ole_cfb")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C3
    assert finding.severity == Severity.CRITICAL
    assert report.max_severity == Severity.CRITICAL
    assert report.safe_to_overwrite is False


def test_garbage_file_is_unknown_not_misclassified(tmp_path):
    path = os.path.join(tmp_path, "garbage.docx")
    with open(path, "wb") as fh:
        fh.write(b"khong phai zip, khong phai OLE, chi la rac thuan")

    report = inspect_file(path)
    assert report.is_zip is False
    assert report.container_kind == "unknown"
    assert report.findings == []
    assert report.errors  # phải có ghi chú lỗi, không được âm thầm im lặng


# ---------------------------------------------------------------------------
# 5. Công thức hiện đại / mảng động (Sheet).
# ---------------------------------------------------------------------------


def _xlsx_with_formula(tmp_path, name: str, formula_text: str) -> str:
    """Giả lập cách Excel THẬT lưu công thức hiện đại: tiền tố ``_xlfn.``
    (và ``_xlfn._xlws.`` cho một số hàm mảng động) ngay trong text của
    phần tử ``<f>`` — openpyxl không tự thêm tiền tố này, nên ta ghi literal
    string công thức để mô phỏng đúng bytes mà Excel thật tạo ra."""
    wb = Workbook()
    ws = wb.active
    ws["A1"] = formula_text
    path = os.path.join(tmp_path, name)
    wb.save(path)
    return path


def test_dynamic_array_function_detected_as_c2(tmp_path):
    path = _xlsx_with_formula(tmp_path, "dyn.xlsx", "=_xlfn._xlws.UNIQUE(B1:B5)")
    report = inspect_file(path)
    finding = report.find("formula.dynamic_array")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C2
    assert finding.severity == Severity.MEDIUM
    assert "UNIQUE" in finding.detail_vi
    assert report.max_compat_level == CompatLevel.C2
    assert report.safe_to_overwrite is False


def test_modern_scalar_function_detected_as_c1(tmp_path):
    path = _xlsx_with_formula(tmp_path, "modern.xlsx", "=_xlfn.XLOOKUP(C1,D1:D5,E1:E5)")
    report = inspect_file(path)
    finding = report.find("formula.modern_function")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C1
    assert finding.severity == Severity.LOW
    assert "XLOOKUP" in finding.detail_vi
    # KHÔNG có finding mảng động (XLOOKUP không spill nhiều ô).
    assert report.find("formula.dynamic_array") is None
    assert report.max_compat_level == CompatLevel.C1
    assert report.safe_to_overwrite is True


def test_lambda_and_dynamic_array_together_count_each_function(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws["A1"] = "=_xlfn.LET(x,1,x+1)"
    ws["A2"] = "=_xlfn._xlws.SORT(B1:B5)"
    ws["A3"] = "=_xlfn.XLOOKUP(C1,D1:D5,E1:E5)"
    path = os.path.join(tmp_path, "mix.xlsx")
    wb.save(path)

    report = inspect_file(path)
    dyn = report.find("formula.dynamic_array")
    modern = report.find("formula.modern_function")
    assert dyn is not None and "LET" in dyn.detail_vi and "SORT" in dyn.detail_vi
    assert modern is not None and "XLOOKUP" in modern.detail_vi


def test_bare_modern_function_without_xlfn_prefix_is_not_flagged(tmp_path):
    """Giới hạn trung thực đã ghi trong docstring module: công cụ CHỈ nhận
    diện qua tiền tố ``_xlfn.`` (đúng như Excel thật lưu). Công thức viết
    tay không có tiền tố này (vd do công cụ khác tạo ra) sẽ KHÔNG được báo
    — đây là hành vi có chủ ý, không phải lỗi."""
    path = _xlsx_with_formula(tmp_path, "bare.xlsx", "=XLOOKUP(C1,D1:D5,E1:E5)")
    report = inspect_file(path)
    assert report.find("formula.modern_function") is None
    assert report.find("formula.dynamic_array") is None


# ---------------------------------------------------------------------------
# 6. PivotTable / PivotCache.
# ---------------------------------------------------------------------------


def test_pivot_table_and_cache_detected_as_c2(tmp_path):
    src = _plain_xlsx(tmp_path, "src.xlsx")
    dst = os.path.join(tmp_path, "withpivot.xlsx")
    _rewrite_zip(src, dst, extra={
        "xl/pivotTables/pivotTable1.xml": b"<pivotTableDefinition/>",
        "xl/pivotCache/pivotCacheDefinition1.xml": b"<pivotCacheDefinition/>",
    })

    report = inspect_file(dst)
    finding = report.find("sheet.pivot_table")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C2
    assert "1 PivotTable" in finding.detail_vi


# ---------------------------------------------------------------------------
# 7. Data Model / Power Query (chỉ áp dụng cho Sheet).
# ---------------------------------------------------------------------------


def test_power_query_data_model_markers_detected_as_c3(tmp_path):
    src = _plain_xlsx(tmp_path, "src.xlsx")
    dst = os.path.join(tmp_path, "withpq.xlsx")
    _rewrite_zip(src, dst, extra={
        "xl/model/item1.data": b"\x00\x01binary-power-pivot-stub",
        "xl/connections.xml": b"<connections/>",
    })

    report = inspect_file(dst)
    finding = report.find("sheet.data_model_power_query")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C3
    assert finding.severity == Severity.HIGH
    assert report.safe_to_overwrite is False


def test_customxml_in_docx_does_not_trigger_power_query_false_positive(tmp_path):
    """customXml/ là chỗ Word dùng BÌNH THƯỜNG cho content-control data
    binding/thuộc tính tài liệu — KHÔNG phải dấu hiệu Power Query. Bucket
    'customXml/' trong spec chỉ áp dụng cho workbook (Sheet), không áp dụng
    cho Writer, để tránh báo giả tràn lan trên mọi file Word có customXml."""
    src = _plain_docx(tmp_path, "src.docx")
    dst = os.path.join(tmp_path, "withcustomxml.docx")
    _rewrite_zip(src, dst, extra={
        "customXml/item1.xml": b"<root/>",
        "customXml/itemProps1.xml": b"<datastoreItem/>",
    })

    report = inspect_file(dst)
    assert report.find("sheet.data_model_power_query") is None


# ---------------------------------------------------------------------------
# 8. Liên kết ngoài: workbook externalLinks, hyperlink mạng/UNC, OLE ngoài.
# ---------------------------------------------------------------------------


def test_external_workbook_links_detected_as_c2(tmp_path):
    src = _plain_xlsx(tmp_path, "src.xlsx")
    dst = os.path.join(tmp_path, "withextlink.xlsx")
    _rewrite_zip(src, dst, extra={"xl/externalLinks/externalLink1.xml": b"<externalLink/>"})

    report = inspect_file(dst)
    finding = report.find("external.workbook_links")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C2


def test_network_and_unc_hyperlinks_classified_separately(tmp_path):
    src = _plain_docx(tmp_path, "src.docx")
    dst = os.path.join(tmp_path, "withlinks.docx")
    rels = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        b'<Relationship Id="rIdNet" '
        b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
        b'Target="https://example.com/baivietgoc" TargetMode="External"/>'
        b'<Relationship Id="rIdUnc" '
        b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
        b'Target="\\\\fileserver\\share\\tailieu.docx" TargetMode="External"/>'
        b'</Relationships>'
    )
    _rewrite_zip(src, dst, extra={"word/_rels/document.xml.rels": rels})

    report = inspect_file(dst)
    net = report.find("link.hyperlink_network")
    unc = report.find("link.hyperlink_local_unc")
    assert net is not None and net.compat_level == CompatLevel.C1
    assert "example.com" in net.detail_vi
    assert unc is not None and unc.compat_level == CompatLevel.C2
    assert "fileserver" in unc.detail_vi


def test_external_ole_object_relationship_detected(tmp_path):
    src = _plain_docx(tmp_path, "src.docx")
    dst = os.path.join(tmp_path, "withole.docx")
    rels = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        b'<Relationship Id="rIdOle" '
        b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject" '
        b'Target="file:///C:/so_lieu_ngoai.xlsx" TargetMode="External"/>'
        b'</Relationships>'
    )
    _rewrite_zip(src, dst, extra={"word/_rels/document.xml.rels": rels})

    report = inspect_file(dst)
    finding = report.find("object.ole_external")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C2


def test_embedded_ole_object_part_detected(tmp_path):
    src = _plain_docx(tmp_path, "src.docx")
    dst = os.path.join(tmp_path, "withembed.docx")
    _rewrite_zip(src, dst, extra={"word/embeddings/oleObject1.bin": b"\x00fake-ole-bin"})

    report = inspect_file(dst)
    finding = report.find("object.embedded_ole")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C2


# ---------------------------------------------------------------------------
# 9. Content control (Writer w:sdt).
# ---------------------------------------------------------------------------


def test_content_control_sdt_detected(tmp_path):
    src = _plain_docx(tmp_path, "src.docx")
    dst = os.path.join(tmp_path, "withsdt.docx")
    with zipfile.ZipFile(src) as zin:
        doc_xml = zin.read("word/document.xml").decode("utf-8")
    assert "<w:body>" in doc_xml, "fixture python-docx đổi cấu trúc, cần cập nhật test"
    sdt_snippet = (
        '<w:sdt><w:sdtPr><w:alias w:val="Truong du lieu"/></w:sdtPr>'
        "<w:sdtContent><w:p/></w:sdtContent></w:sdt>"
    )
    patched = doc_xml.replace("<w:body>", "<w:body>" + sdt_snippet, 1)
    _rewrite_zip(src, dst, extra={"word/document.xml": patched.encode("utf-8")})

    report = inspect_file(dst)
    finding = report.find("writer.content_controls")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C1
    assert "1 content control" in finding.detail_vi


# ---------------------------------------------------------------------------
# 10. OOXML Transitional vs Strict.
# ---------------------------------------------------------------------------


def test_ooxml_strict_namespace_detected(tmp_path):
    path = os.path.join(tmp_path, "strict.docx")
    content_types = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        b'<Default Extension="xml" ContentType="application/xml"/>'
        b'<Override PartName="/word/document.xml" '
        b'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        b"</Types>"
    )
    root_rels = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        b'<Relationship Id="rId1" '
        b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        b'Target="word/document.xml"/></Relationships>'
    )
    document_xml = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<w:document xmlns:w="http://purl.oclc.org/ooxml/wordprocessingml/main">'
        b"<w:body><w:p/></w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("word/document.xml", document_xml)

    report = inspect_file(path)
    assert report.ooxml_conformance == "strict"
    finding = report.find("format.ooxml_strict")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C2


# ---------------------------------------------------------------------------
# 11. Biểu đồ + media (audio/video) — PPTX.
# ---------------------------------------------------------------------------


def test_chart_detected_in_pptx(tmp_path):
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.util import Inches

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    chart_data = CategoryChartData()
    chart_data.categories = ["A", "B", "C"]
    chart_data.add_series("Series 1", (1, 2, 3))
    slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(1), Inches(1), Inches(4), Inches(3), chart_data,
    )
    path = os.path.join(tmp_path, "withchart.pptx")
    prs.save(path)

    report = inspect_file(path)
    finding = report.find("media.charts")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C1
    assert len(finding.evidence) == 1


def test_embedded_video_in_pptx_media_detected(tmp_path):
    src = _plain_pptx(tmp_path, "src.pptx")
    dst = os.path.join(tmp_path, "withvideo.pptx")
    _rewrite_zip(src, dst, extra={"ppt/media/media1.mp4": b"\x00fake-mp4-bytes"})

    report = inspect_file(dst)
    finding = report.find("media.audio_video")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C1
    assert "1 video" in finding.detail_vi


def test_image_only_media_is_not_flagged(tmp_path):
    """Ảnh tĩnh KHÔNG được coi là rủi ro — chỉ audio/video mới báo, để báo
    cáo tập trung vào tính năng thật sự rủi ro (ảnh hầu như luôn hiển thị
    đúng, không cần cảnh báo)."""
    src = _plain_pptx(tmp_path, "src.pptx")
    dst = os.path.join(tmp_path, "withimage.pptx")
    _rewrite_zip(src, dst, extra={"ppt/media/image1.png": b"\x89PNG\r\n\x1a\nfake"})

    report = inspect_file(dst)
    assert report.find("media.audio_video") is None


# ---------------------------------------------------------------------------
# 12. Tổng hợp mức nghiêm trọng + verdict trên nhiều lỗi cùng lúc.
# ---------------------------------------------------------------------------


def test_multiple_findings_aggregate_to_worst_severity(tmp_path):
    src = _plain_docx(tmp_path, "src.docx")
    dst = os.path.join(tmp_path, "combo.docm")
    _rewrite_zip(src, dst, extra={
        "word/vbaProject.bin": b"FAKE",                 # C3 HIGH
        "_xmlsignatures/sig1.xml": b"<fake/>",           # C2 HIGH
        "word/embeddings/oleObject1.bin": b"\x00fake",   # C2 MEDIUM
    })

    report = inspect_file(dst)
    assert report.find("macro.vba") is not None
    assert report.find("signature.digital") is not None
    assert report.find("object.embedded_ole") is not None
    assert report.max_compat_level == CompatLevel.C3
    assert report.max_severity == Severity.HIGH
    assert report.safe_to_overwrite is False
    assert len(report.findings) == 3


# ---------------------------------------------------------------------------
# 13. Fixture THẬT có sẵn trong kit (vertical slice 05_PROMPT bước 3).
# ---------------------------------------------------------------------------


def test_real_longdoc_fixture_from_vertical_slice_if_present():
    """tools/office-compat/fixtures/LongDoc.docx (sinh bởi fixtures/make_doc.py
    cho vertical-slice Writer của kit) có 1 hyperlink http thật, media chỉ
    có ảnh, không macro/không chữ ký/không content control — nên kỳ vọng
    đúng 1 finding (hyperlink mạng, C1) và an toàn lưu đè."""
    here = os.path.dirname(os.path.abspath(__file__))
    fixture = os.path.join(os.path.dirname(here), "fixtures", "LongDoc.docx")
    if not os.path.exists(fixture):
        pytest.skip("fixtures/LongDoc.docx chưa được sinh (chạy fixtures/make_doc.py trước)")

    report = inspect_file(fixture)
    assert report.app == "writer"
    assert report.ooxml_conformance == "transitional"
    assert report.find("macro.vba") is None
    assert report.find("signature.digital") is None
    assert report.find("encryption.ole_cfb") is None
    net = report.find("link.hyperlink_network")
    assert net is not None
    assert "libreoffice.org" in net.detail_vi
    assert report.max_compat_level == CompatLevel.C1
    assert report.safe_to_overwrite is True


# ---------------------------------------------------------------------------
# 14. Serialization (JSON + text) không ném lỗi và chứa trường bắt buộc.
# ---------------------------------------------------------------------------


def test_to_dict_and_to_text_vi_do_not_raise_and_contain_verdict(tmp_path):
    src = _plain_docx(tmp_path, "src.docx")
    dst = os.path.join(tmp_path, "withmacro.docm")
    _rewrite_zip(src, dst, extra={"word/vbaProject.bin": b"FAKE"})
    report = inspect_file(dst)

    d = report.to_dict()
    assert d["max_compat_level"] == "C3"
    assert d["max_severity"] == "high"
    assert d["safe_to_overwrite"] is False
    assert any(f["feature_id"] == "macro.vba" for f in d["findings"])

    text = report.to_text_vi()
    assert "AN TOÀN ĐỂ LƯU ĐÈ? KHÔNG" in text
    assert "macro.vba" in text
