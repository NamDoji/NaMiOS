"""Pytest cho namipdf_inspect — PDF Compatibility/Safety Inspector (NaMiPDF).

Mọi fixture là tệp PDF THẬT, sinh ra NGAY LÚC CHẠY TEST bằng reportlab (chỉ
dùng ở TEST, không phải runtime của tool) để có content stream/XObject hợp
lệ, rồi dùng pikepdf để GHÉP THÊM cấu trúc mà reportlab không có API bậc cao
để tạo (mã hoá, JavaScript/OpenAction/AA, chữ ký số giả lập cấu trúc,
AcroForm, XFA, tệp đính kèm) — đây là cách duy nhất để mô phỏng trung thực
các trường hợp mà một trình tạo PDF thật có thể sinh ra.

KHÔNG có bước nào trong file test này THỰC THI nội dung PDF (không chạy
JavaScript, không mở bằng trình xem PDF thật) — chỉ build & đọc lại bằng
pikepdf, giống đúng những gì namipdf_inspect làm ở runtime."""
from __future__ import annotations

import os
import subprocess
import sys

import pikepdf
import pytest
from namipdf_inspect.inspector import CompatLevel, DocumentStatus, Severity, inspect_file
from pikepdf import Array, Dictionary, Name, String
from reportlab.pdfgen import canvas

_CLI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "namipdf-inspect")


# ---------------------------------------------------------------------------
# Hạ tầng fixture chung.
# ---------------------------------------------------------------------------


def _text_pdf(tmp_path, name: str = "plain.pdf", text: str = "Hello NaMiPDF") -> str:
    path = os.path.join(tmp_path, name)
    c = canvas.Canvas(path, pagesize=(200, 200))
    c.drawString(10, 100, text)
    c.showPage()
    c.save()
    return path


def _scan_image_pdf(tmp_path, name: str = "scan.pdf") -> str:
    """Trang chỉ có một ảnh phủ toàn trang, KHÔNG operator Tj/TJ nào — mô
    phỏng một trang scan thật (đã xác minh bằng cách đọc lại content stream
    bằng pikepdf: ReportLab vẫn khai /Font trong Resources dù không vẽ chữ,
    nên inspector KHÔNG được dùng '/Font tồn tại' làm tín hiệu, chỉ dùng
    operator hiển thị chữ thật sự — test này canh đúng hành vi đó)."""
    from PIL import Image

    img_path = os.path.join(tmp_path, f"_src_{name}.png")
    Image.new("RGB", (40, 40), color=(180, 180, 180)).save(img_path)
    path = os.path.join(tmp_path, name)
    c = canvas.Canvas(path, pagesize=(200, 200))
    c.drawImage(img_path, 0, 0, width=200, height=200)
    c.showPage()
    c.save()
    return path


def _vector_only_pdf(tmp_path, name: str = "vector.pdf") -> str:
    """Trang chỉ có hình vẽ vector (không chữ, không ảnh) — KHÔNG phải scan
    (không có ảnh để OCR), cũng không phải 'Text PDF' theo nghĩa có nội dung
    chữ, nhưng công cụ phải xếp vào TEXT_PDF (không cần OCR) vì không có
    trang nào thuộc diện 'chỉ ảnh, không chữ'."""
    path = os.path.join(tmp_path, name)
    c = canvas.Canvas(path, pagesize=(200, 200))
    c.rect(10, 10, 100, 100, fill=1)
    c.showPage()
    c.save()
    return path


def _merge(tmp_path, srcs: list[str], name: str = "merged.pdf") -> str:
    out = pikepdf.new()
    for s in srcs:
        with pikepdf.open(s) as src:
            out.pages.extend(src.pages)
    path = os.path.join(tmp_path, name)
    out.save(path)
    out.close()
    return path


def _patch(src_path: str, dst_path: str, fn) -> str:
    """Mở lại ``src_path`` bằng pikepdf, gọi ``fn(pdf)`` để chỉnh cấu trúc,
    rồi lưu ra ``dst_path``. Dùng chung cho mọi fixture cần ghép cấu trúc mà
    reportlab không có API tạo trực tiếp."""
    with pikepdf.open(src_path) as pdf:
        fn(pdf)
        pdf.save(dst_path)
    return dst_path


# ---------------------------------------------------------------------------
# 1. Tệp sạch (Text PDF) — C0, an toàn ghi đè.
# ---------------------------------------------------------------------------


def test_plain_text_pdf_is_c0_text_status_and_safe_to_overwrite(tmp_path):
    path = _text_pdf(tmp_path)
    report = inspect_file(path)

    assert report.engine == "pikepdf"
    assert report.page_count == 1
    assert report.pdf_version in ("1.3", "1.4")
    assert report.producer and "ReportLab" in report.producer
    assert report.content_class == DocumentStatus.TEXT_PDF
    assert report.document_status == DocumentStatus.TEXT_PDF
    assert report.findings == []
    assert report.max_compat_level == CompatLevel.C0
    assert report.max_severity == Severity.INFO
    assert report.safe_to_overwrite is True
    assert report.requires_user_password is False
    assert report.errors == []


def test_vector_only_page_is_not_misclassified_as_scan(tmp_path):
    """Trang chỉ có hình vector (không chữ, không ảnh) KHÔNG được coi là
    'Scan image' — không có gì để OCR, không nên chặn sửa bằng nhãn sai."""
    path = _vector_only_pdf(tmp_path)
    report = inspect_file(path)
    assert report.content_class == DocumentStatus.TEXT_PDF
    assert report.find("content.scan_image") is None
    assert report.find("content.mixed_pages") is None


# ---------------------------------------------------------------------------
# 2. Scan image / Mixed — phân loại theo operator Tj/TJ thật, không theo
#    sự tồn tại của /Font trong Resources.
# ---------------------------------------------------------------------------


def test_scan_only_pdf_detected_as_scan_image_c2(tmp_path):
    path = _scan_image_pdf(tmp_path)
    report = inspect_file(path)

    assert report.content_class == DocumentStatus.SCAN_IMAGE
    assert report.document_status == DocumentStatus.SCAN_IMAGE
    finding = report.find("content.scan_image")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C2
    assert finding.severity == Severity.MEDIUM
    assert "trang 1" in finding.evidence
    assert report.safe_to_overwrite is False


def test_mixed_document_detected_when_text_and_scan_pages_combined(tmp_path):
    text_path = _text_pdf(tmp_path, "t.pdf")
    scan_path = _scan_image_pdf(tmp_path, "s.pdf")
    merged = _merge(tmp_path, [text_path, scan_path], "mixed.pdf")

    report = inspect_file(merged)
    assert report.page_count == 2
    assert report.content_class == DocumentStatus.MIXED
    assert report.document_status == DocumentStatus.MIXED
    finding = report.find("content.mixed_pages")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C2
    assert report.find("content.scan_image") is None  # bucket riêng, không trùng
    assert report.safe_to_overwrite is False


def test_text_nested_inside_form_xobject_still_counts_as_text_page(tmp_path):
    """Một số trình tạo PDF vẽ chữ bên trong Form XObject (gọi qua toán tử
    Do) thay vì trực tiếp trên content stream của trang — inspector PHẢI đệ
    quy vào Form XObject để không báo nhầm trang này là 'scan'."""
    base = _scan_image_pdf(tmp_path, "base.pdf")  # có sẵn 1 ảnh phủ trang

    def _wrap_text_in_form(pdf):
        page = pdf.pages[0]
        form_xobj = pdf.make_stream(b"BT /F1 12 Tf 10 10 Td (Chu nam trong Form XObject) Tj ET")
        form_xobj.Type = Name.XObject
        form_xobj.Subtype = Name.Form
        form_xobj.BBox = Array([0, 0, 200, 200])
        form_xobj.Resources = Dictionary(Font=Dictionary(F1=Dictionary(
            Type=Name.Font, Subtype=Name.Type1, BaseFont=Name.Helvetica,
        )))
        xobjects = page.Resources.get("/XObject")
        xobjects["/FxText"] = form_xobj
        extra = pdf.make_stream(b"q 1 0 0 1 0 0 cm /FxText Do Q")
        page.Contents = Array([page.Contents, extra])

    dst = os.path.join(tmp_path, "nested_text.pdf")
    _patch(base, dst, _wrap_text_in_form)

    report = inspect_file(dst)
    assert report.content_class == DocumentStatus.TEXT_PDF
    assert report.find("content.scan_image") is None


def test_large_page_count_truncates_scan_with_note(tmp_path, monkeypatch):
    """Giới hạn an toàn số trang quét (``_MAX_PAGES_SCANNED``) phải tạo note
    thay vì quét vô hạn trên tệp rất nhiều trang — kiểm bằng cách hạ giới hạn
    xuống rất thấp cho một tệp 3 trang."""
    import namipdf_inspect.inspector as inspector_mod

    monkeypatch.setattr(inspector_mod, "_MAX_PAGES_SCANNED", 1)
    text_path = _text_pdf(tmp_path, "t.pdf")
    merged = _merge(tmp_path, [text_path, text_path, text_path], "many.pdf")

    report = inspect_file(merged)
    assert report.page_count == 3
    assert any("chỉ phân loại nội dung 1 trang" in n for n in report.notes)


# ---------------------------------------------------------------------------
# 3. Mã hoá / mật khẩu / quyền — Protected, C3.
# ---------------------------------------------------------------------------


def test_owner_only_encryption_readable_is_protected_high(tmp_path):
    """Mã hoá CHỈ hạn chế quyền (mật khẩu người dùng rỗng) — mở được nội
    dung nhưng vẫn PHẢI gắn nhãn Protected theo đúng yêu cầu nhiệm vụ (mọi
    /Encrypt đều là Protected, không chỉ trường hợp cần mật khẩu)."""
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "owner_enc.pdf")

    def _encrypt(pdf):
        perms = pikepdf.Permissions(extract=False, print_highres=False)
        pdf.save(dst, encryption=pikepdf.Encryption(owner="owner-secret", user="", allow=perms, R=4))

    with pikepdf.open(src) as pdf:
        _encrypt(pdf)

    report = inspect_file(dst)
    assert report.document_status == DocumentStatus.PROTECTED
    assert report.requires_user_password is False
    finding = report.find("security.encryption")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C3
    assert finding.severity == Severity.HIGH
    assert "BỊ CHẶN" in finding.detail_vi
    assert report.safe_to_overwrite is False
    # Nội dung VẪN phân loại được (tham khảo) vì ta đọc được qua mật khẩu rỗng.
    assert report.content_class == DocumentStatus.TEXT_PDF


def test_user_password_required_without_password_blocks_as_critical(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "user_enc.pdf")
    with pikepdf.open(src) as pdf:
        pdf.save(dst, encryption=pikepdf.Encryption(owner="owner-secret", user="letmein", R=4))

    report = inspect_file(dst)
    assert report.requires_user_password is True
    assert report.document_status == DocumentStatus.PROTECTED
    assert report.content_class == DocumentStatus.UNKNOWN
    assert report.page_count is None
    finding = report.find("security.encryption")
    assert finding is not None
    assert finding.severity == Severity.CRITICAL
    assert report.max_severity == Severity.CRITICAL
    assert report.safe_to_overwrite is False


def test_wrong_password_supplied_still_blocks(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "user_enc2.pdf")
    with pikepdf.open(src) as pdf:
        pdf.save(dst, encryption=pikepdf.Encryption(owner="owner-secret", user="letmein", R=4))

    report = inspect_file(dst, password="wrong-guess")
    assert report.requires_user_password is True
    assert report.document_status == DocumentStatus.PROTECTED


def test_correct_user_password_supplied_allows_content_analysis(tmp_path):
    """Mật khẩu do NGƯỜI DÙNG chủ động cung cấp (không phải bẻ khoá) cho
    phép phân tích sâu hơn — nhưng document_status VẪN là Protected (tệp vẫn
    là tệp được bảo vệ, bất kể ta hiện có mật khẩu hay không)."""
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "user_enc3.pdf")
    with pikepdf.open(src) as pdf:
        pdf.save(dst, encryption=pikepdf.Encryption(owner="owner-secret", user="letmein", R=4))

    report = inspect_file(dst, password="letmein")
    assert report.requires_user_password is False
    assert report.document_status == DocumentStatus.PROTECTED
    assert report.page_count == 1
    assert report.content_class == DocumentStatus.TEXT_PDF


# ---------------------------------------------------------------------------
# 4. JavaScript / auto-actions — C3 HIGH (JS), C2 MEDIUM (auto_open).
# ---------------------------------------------------------------------------


def test_openaction_javascript_detected_and_flags_auto_open_too(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "js.pdf")

    def _add(pdf):
        action = pdf.make_indirect(Dictionary(S=Name.JavaScript, JS=String("app.alert('hi');")))
        pdf.Root.OpenAction = action

    _patch(src, dst, _add)
    report = inspect_file(dst)

    js = report.find("script.javascript")
    assert js is not None
    assert js.compat_level == CompatLevel.C3
    assert js.severity == Severity.HIGH
    assert any("catalog.OpenAction" in e for e in js.evidence)

    auto = report.find("action.auto_open")
    assert auto is not None
    assert auto.compat_level == CompatLevel.C2

    assert report.max_severity == Severity.HIGH
    assert report.safe_to_overwrite is False


def test_document_level_javascript_name_tree_detected(tmp_path):
    """Script gắn trong ``/Names/JavaScript`` chạy tự động khi mở tài liệu
    (cơ chế 'document-level JavaScript' chuẩn của Acrobat) — PHẢI bị phát
    hiện dù không nằm trong OpenAction/AA."""
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "doclevel_js.pdf")

    def _add(pdf):
        js_entry = pdf.make_indirect(Dictionary(S=Name.JavaScript, JS=String("this.print();")))
        names_tree = Dictionary(Names=Array([String("Script1"), js_entry]))
        pdf.Root.Names = Dictionary(JavaScript=names_tree)

    _patch(src, dst, _add)
    report = inspect_file(dst)
    js = report.find("script.javascript")
    assert js is not None
    assert any("names.JavaScript" in e for e in js.evidence)


def test_launch_action_is_critical_and_distinct_from_javascript(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "launch.pdf")

    def _add(pdf):
        action = pdf.make_indirect(Dictionary(
            S=Name.Launch, F=Dictionary(Type=Name.Filespec, F=String("calc.exe")),
        ))
        pdf.Root.OpenAction = action

    _patch(src, dst, _add)
    report = inspect_file(dst)

    launch = report.find("action.launch_external")
    assert launch is not None
    assert launch.compat_level == CompatLevel.C3
    assert launch.severity == Severity.CRITICAL
    assert report.find("script.javascript") is None
    assert report.max_severity == Severity.CRITICAL


def test_submitform_and_gotor_detected_as_external_reference(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "submit.pdf")

    def _add(pdf):
        action = pdf.make_indirect(Dictionary(
            S=Name("/SubmitForm"), F=Dictionary(FS=Name("/URL"), F=String("https://example.com/submit")),
        ))
        pdf.Root.OpenAction = action

    _patch(src, dst, _add)
    report = inspect_file(dst)
    finding = report.find("action.external_reference")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C2
    assert "SubmitForm" in finding.detail_vi


def test_uri_link_action_is_low_risk_and_safe_to_overwrite(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "uri.pdf")

    def _add(pdf):
        page = pdf.pages[0]
        uri_action = Dictionary(S=Name.URI, URI=String("https://example.com/baivietgoc"))
        link = pdf.make_indirect(Dictionary(
            Type=Name.Annot, Subtype=Name.Link, Rect=Array([0, 0, 50, 50]), A=uri_action,
        ))
        page.Annots = Array([link])

    _patch(src, dst, _add)
    report = inspect_file(dst)

    finding = report.find("link.external_uri")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C1
    assert finding.severity == Severity.LOW
    assert "example.com" in finding.detail_vi
    # Annotation /A (click-to-navigate) KHÔNG phải auto-action.
    assert report.find("action.auto_open") is None
    assert report.max_compat_level == CompatLevel.C1
    assert report.safe_to_overwrite is True


# ---------------------------------------------------------------------------
# 5. Tệp đính kèm/nhúng — C2 MEDIUM, qua 3 đường phát hiện khác nhau.
# ---------------------------------------------------------------------------


def test_embedded_file_via_names_tree_detected(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "attach.pdf")

    def _add(pdf):
        afs = pikepdf.AttachedFileSpec(pdf, b"hello world attachment", description="ghi chu", filename="note.txt")
        pdf.attachments["note.txt"] = afs

    with pikepdf.open(src) as pdf:
        _add(pdf)
        pdf.save(dst)

    report = inspect_file(dst)
    finding = report.find("attachment.embedded_file")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C2
    assert finding.severity == Severity.MEDIUM
    assert report.safe_to_overwrite is False


def test_file_attachment_annotation_detected(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "attach_annot.pdf")

    def _add(pdf):
        page = pdf.pages[0]
        ef_stream = pdf.make_stream(b"attached via annotation")
        ef_stream.Type = Name.EmbeddedFile
        fs = Dictionary(Type=Name.Filespec, F=String("via_annot.bin"), EF=Dictionary(F=ef_stream))
        annot = pdf.make_indirect(Dictionary(
            Type=Name.Annot, Subtype=Name("/FileAttachment"), Rect=Array([0, 0, 20, 20]), FS=fs,
        ))
        page.Annots = Array([annot])

    _patch(src, dst, _add)
    report = inspect_file(dst)
    assert report.find("attachment.embedded_file") is not None


def test_loose_filespec_object_not_registered_anywhere_still_caught(tmp_path):
    """Filespec/EmbeddedFile KHÔNG đăng ký qua Names/EmbeddedFiles hay bất kỳ
    annotation nào (chỉ là một object rời trong xref) vẫn PHẢI bị phát hiện
    qua bước quét toàn cục dự phòng — phòng tệp cố tình giấu đính kèm theo
    cách bất thường."""
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "loose.pdf")

    def _add(pdf):
        ef_stream = pdf.make_stream(b"loose attachment bytes")
        ef_stream.Type = Name.EmbeddedFile
        fs = pdf.make_indirect(Dictionary(Type=Name.Filespec, F=String("loose.bin"), EF=Dictionary(F=ef_stream)))
        pdf.Root.SomeVendorExt = fs

    _patch(src, dst, _add)
    report = inspect_file(dst)
    assert report.find("attachment.embedded_file") is not None


# ---------------------------------------------------------------------------
# 6. Biểu mẫu — AcroForm C1 (C2 nếu NeedAppearances), XFA C3.
# ---------------------------------------------------------------------------


def test_acroform_with_fields_is_c1_low_and_safe(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "acroform.pdf")

    def _add(pdf):
        page = pdf.pages[0]
        field = pdf.make_indirect(Dictionary(
            FT=Name.Tx, T=String("Field1"), Rect=Array([0, 0, 100, 20]),
            Type=Name.Annot, Subtype=Name.Widget,
        ))
        page.Annots = Array([field])
        pdf.Root.AcroForm = pdf.make_indirect(Dictionary(Fields=Array([field])))

    _patch(src, dst, _add)
    report = inspect_file(dst)

    finding = report.find("form.acroform")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C1
    assert finding.severity == Severity.LOW
    assert report.find("form.xfa") is None
    assert report.safe_to_overwrite is True


def test_acroform_needs_appearances_bumps_to_c2(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "acroform_na.pdf")

    def _add(pdf):
        page = pdf.pages[0]
        field = pdf.make_indirect(Dictionary(
            FT=Name.Tx, T=String("Field1"), Rect=Array([0, 0, 100, 20]),
            Type=Name.Annot, Subtype=Name.Widget,
        ))
        page.Annots = Array([field])
        pdf.Root.AcroForm = pdf.make_indirect(Dictionary(Fields=Array([field]), NeedAppearances=True))

    _patch(src, dst, _add)
    report = inspect_file(dst)
    finding = report.find("form.acroform")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C2
    assert finding.severity == Severity.MEDIUM
    assert "NeedAppearances" in finding.detail_vi
    assert report.safe_to_overwrite is False


def test_xfa_form_is_c3_high_and_blocks_overwrite(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "xfa.pdf")

    def _add(pdf):
        xfa_stream = pdf.make_stream(b"<xdp:xdp xmlns:xdp='http://ns.adobe.com/xdp/'></xdp:xdp>")
        pdf.Root.AcroForm = pdf.make_indirect(Dictionary(Fields=Array([]), XFA=xfa_stream))

    _patch(src, dst, _add)
    report = inspect_file(dst)

    finding = report.find("form.xfa")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C3
    assert finding.severity == Severity.HIGH
    assert report.safe_to_overwrite is False


# ---------------------------------------------------------------------------
# 7. Chữ ký số — Signed, C3 HIGH, status ưu tiên hơn content_class.
# ---------------------------------------------------------------------------


def test_signature_with_docmdp_sets_signed_status(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "signed.pdf")

    def _add(pdf):
        page = pdf.pages[0]
        sig_value = pdf.make_indirect(Dictionary(
            Type=Name.Sig, Filter=Name("/Adobe.PPKLite"), SubFilter=Name("/adbe.pkcs7.detached"),
            ByteRange=Array([0, 100, 200, 300]), Contents=pikepdf.String(bytes(16)),
        ))
        sig_field = pdf.make_indirect(Dictionary(
            FT=Name.Sig, T=String("Signature1"), Rect=Array([0, 0, 0, 0]),
            Type=Name.Annot, Subtype=Name.Widget, V=sig_value,
        ))
        page.Annots = Array([sig_field])
        pdf.Root.AcroForm = pdf.make_indirect(Dictionary(Fields=Array([sig_field]), SigFlags=3))
        pdf.Root.Perms = pdf.make_indirect(Dictionary(DocMDP=sig_value))

    _patch(src, dst, _add)
    report = inspect_file(dst)

    assert report.document_status == DocumentStatus.SIGNED
    assert report.content_class == DocumentStatus.TEXT_PDF  # vẫn tính được, nhưng không dùng làm status
    sig = report.find("signature.digital")
    assert sig is not None
    assert sig.compat_level == CompatLevel.C3
    assert sig.severity == Severity.HIGH
    assert "DocMDP" in sig.detail_vi
    assert "ByteRange" in sig.detail_vi
    assert report.safe_to_overwrite is False


def test_signature_without_docmdp_still_detected_as_signed(tmp_path):
    """Chữ ký phê duyệt (approval signature, không phải certification/DocMDP)
    vẫn PHẢI đặt status Signed — không chỉ chữ ký chứng thực."""
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "signed_approval.pdf")

    def _add(pdf):
        page = pdf.pages[0]
        sig_value = pdf.make_indirect(Dictionary(
            Type=Name.Sig, Filter=Name("/Adobe.PPKLite"), SubFilter=Name("/adbe.pkcs7.detached"),
            ByteRange=Array([0, 50, 100, 150]), Contents=pikepdf.String(bytes(16)),
        ))
        sig_field = pdf.make_indirect(Dictionary(
            FT=Name.Sig, T=String("Signature1"), Rect=Array([0, 0, 0, 0]),
            Type=Name.Annot, Subtype=Name.Widget, V=sig_value,
        ))
        page.Annots = Array([sig_field])
        pdf.Root.AcroForm = pdf.make_indirect(Dictionary(Fields=Array([sig_field]), SigFlags=1))

    _patch(src, dst, _add)
    report = inspect_file(dst)
    assert report.document_status == DocumentStatus.SIGNED
    sig = report.find("signature.digital")
    assert sig is not None
    assert "DocMDP" not in sig.detail_vi


def test_signed_and_scanned_together_status_is_signed_not_scan(tmp_path):
    """Ưu tiên trạng thái: Signed đứng TRƯỚC phân loại nội dung — một tài
    liệu scan ĐÃ KÝ vẫn phải hiển thị 'Signed' (chặn sửa), không phải 'Scan
    image' (gợi ý có thể chạy OCR rồi sửa, điều này SAI vì sẽ phá chữ ký)."""
    scan_src = _scan_image_pdf(tmp_path)
    dst = os.path.join(tmp_path, "signed_scan.pdf")

    def _add(pdf):
        page = pdf.pages[0]
        sig_value = pdf.make_indirect(Dictionary(
            Type=Name.Sig, Filter=Name("/Adobe.PPKLite"), SubFilter=Name("/adbe.pkcs7.detached"),
            ByteRange=Array([0, 50, 100, 150]), Contents=pikepdf.String(bytes(16)),
        ))
        sig_field = pdf.make_indirect(Dictionary(
            FT=Name.Sig, T=String("Signature1"), Rect=Array([0, 0, 0, 0]),
            Type=Name.Annot, Subtype=Name.Widget, V=sig_value,
        ))
        page.Annots = Array([sig_field])
        pdf.Root.AcroForm = pdf.make_indirect(Dictionary(Fields=Array([sig_field]), SigFlags=1))

    _patch(scan_src, dst, _add)
    report = inspect_file(dst)
    assert report.content_class == DocumentStatus.SCAN_IMAGE
    assert report.document_status == DocumentStatus.SIGNED


# ---------------------------------------------------------------------------
# 8. PDF/A hint + phiên bản PDF 2.0 — thông tin tham khảo, không chặn.
# ---------------------------------------------------------------------------


def test_pdfa_hint_detected_as_info_does_not_block_overwrite(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "pdfa.pdf")

    with pikepdf.open(src) as pdf:
        oi = pdf.make_indirect(Dictionary(
            Type=Name.OutputIntent, S=Name("/GTS_PDFA1"), OutputConditionIdentifier=String("sRGB IEC61966-2.1"),
        ))
        pdf.Root.OutputIntents = Array([oi])
        with pdf.open_metadata() as meta:
            meta["pdfaid:part"] = "1"
            meta["pdfaid:conformance"] = "B"
        pdf.save(dst)

    report = inspect_file(dst)
    finding = report.find("format.pdfa_hint")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C1
    assert finding.severity == Severity.INFO
    assert "KHÔNG phải xác nhận tuân thủ thật" in finding.recommended_action_vi
    assert report.safe_to_overwrite is True


def test_pdf20_version_flagged_as_low_info(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "v20.pdf")
    with pikepdf.open(src) as pdf:
        pdf.save(dst, force_version="2.0")

    report = inspect_file(dst)
    assert report.pdf_version == "2.0"
    finding = report.find("format.pdf20")
    assert finding is not None
    assert finding.compat_level == CompatLevel.C1
    assert finding.severity == Severity.LOW
    assert report.safe_to_overwrite is True


# ---------------------------------------------------------------------------
# 9. Tệp hỏng/không phải PDF — không sập, báo lỗi rõ.
# ---------------------------------------------------------------------------


def test_garbage_file_does_not_crash_and_reports_errors(tmp_path):
    path = os.path.join(tmp_path, "garbage.pdf")
    with open(path, "wb") as fh:
        fh.write(b"khong phai PDF, chi la rac thuan tuy khong co magic header gi ca")

    report = inspect_file(path)
    assert report.document_status == DocumentStatus.UNKNOWN
    assert report.errors  # phải có lỗi ghi lại, không được im lặng
    assert report.page_count is None


def test_nonexistent_file_does_not_raise(tmp_path):
    path = os.path.join(tmp_path, "khong_ton_tai.pdf")
    report = inspect_file(path)
    assert report.errors
    assert report.document_status == DocumentStatus.UNKNOWN


# ---------------------------------------------------------------------------
# 10. Tổng hợp nhiều findings cùng lúc — mức nghiêm trọng cao nhất thắng.
# ---------------------------------------------------------------------------


def test_multiple_findings_aggregate_to_worst_severity_and_status(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "combo.pdf")

    def _add(pdf):
        page = pdf.pages[0]
        js_action = pdf.make_indirect(Dictionary(S=Name.JavaScript, JS=String("app.alert('x')")))
        pdf.Root.OpenAction = js_action
        afs = pikepdf.AttachedFileSpec(pdf, b"data", filename="a.txt")
        pdf.attachments["a.txt"] = afs
        uri_action = Dictionary(S=Name.URI, URI=String("https://example.com"))
        link = pdf.make_indirect(Dictionary(
            Type=Name.Annot, Subtype=Name.Link, Rect=Array([0, 0, 10, 10]), A=uri_action,
        ))
        page.Annots = Array([link])

    _patch(src, dst, _add)
    report = inspect_file(dst)

    assert report.find("script.javascript") is not None
    assert report.find("attachment.embedded_file") is not None
    assert report.find("link.external_uri") is not None
    assert report.max_compat_level == CompatLevel.C3
    assert report.max_severity == Severity.HIGH
    assert report.safe_to_overwrite is False
    assert len(report.findings) >= 3


# ---------------------------------------------------------------------------
# 11. Serialization (JSON + text) không ném lỗi và chứa trường bắt buộc.
# ---------------------------------------------------------------------------


def test_to_dict_and_to_text_vi_do_not_raise_and_contain_verdict(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "launch_report.pdf")

    def _add(pdf):
        pdf.Root.OpenAction = pdf.make_indirect(Dictionary(S=Name.Launch, F=String("evil.exe")))

    _patch(src, dst, _add)
    report = inspect_file(dst)

    d = report.to_dict()
    assert d["max_compat_level"] == "C3"
    assert d["max_severity"] == "critical"
    assert d["safe_to_overwrite"] is False
    assert d["document_status"] == "text_pdf"
    assert any(f["feature_id"] == "action.launch_external" for f in d["findings"])

    text = report.to_text_vi()
    assert "AN TOÀN GHI ĐÈ BẢN GỐC? KHÔNG" in text
    assert "action.launch_external" in text


# ---------------------------------------------------------------------------
# 12. CLI — exit code theo severity, --json hợp lệ, --password hoạt động.
# ---------------------------------------------------------------------------


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, _CLI, *args],
        capture_output=True, text=True, timeout=30,
    )


def test_cli_exit_code_zero_for_clean_pdf(tmp_path):
    path = _text_pdf(tmp_path)
    result = _run_cli(path)
    assert result.returncode == 0
    assert "Text PDF" in result.stdout


def test_cli_exit_code_three_for_launch_action(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "launch_cli.pdf")

    def _add(pdf):
        pdf.Root.OpenAction = pdf.make_indirect(Dictionary(S=Name.Launch, F=String("evil.exe")))

    _patch(src, dst, _add)
    result = _run_cli(dst)
    assert result.returncode == 3


def test_cli_exit_code_three_for_password_required(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "pw_cli.pdf")
    with pikepdf.open(src) as pdf:
        pdf.save(dst, encryption=pikepdf.Encryption(owner="o", user="u", R=4))

    result = _run_cli(dst)
    assert result.returncode == 3
    assert "Protected" in result.stdout


def test_cli_json_output_is_valid_json_with_expected_keys(tmp_path):
    path = _text_pdf(tmp_path)
    result = _run_cli("--json", path)
    assert result.returncode == 0
    import json
    payload = json.loads(result.stdout)
    assert payload["document_status"] == "text_pdf"
    assert payload["safe_to_overwrite"] is True


def test_cli_password_flag_unlocks_content_analysis(tmp_path):
    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "pw_cli2.pdf")
    with pikepdf.open(src) as pdf:
        pdf.save(dst, encryption=pikepdf.Encryption(owner="o", user="letmein", R=4))

    result_no_pw = _run_cli("--json", dst)
    result_with_pw = _run_cli("--json", "--password", "letmein", dst)
    import json
    no_pw = json.loads(result_no_pw.stdout)
    with_pw = json.loads(result_with_pw.stdout)
    assert no_pw["requires_user_password"] is True
    assert no_pw["page_count"] is None
    assert with_pw["requires_user_password"] is False
    assert with_pw["page_count"] == 1


def test_multiple_files_cli_exit_code_is_worst_of_all(tmp_path):
    clean = _text_pdf(tmp_path, "clean.pdf")
    launch_dst = os.path.join(tmp_path, "launch_multi.pdf")

    def _add(pdf):
        pdf.Root.OpenAction = pdf.make_indirect(Dictionary(S=Name.Launch, F=String("evil.exe")))

    _patch(clean, launch_dst, _add)
    result = _run_cli(clean, launch_dst)
    assert result.returncode == 3


# ---------------------------------------------------------------------------
# 13. Nhánh dự phòng pypdf (degrade khi pikepdf không cài được).
# ---------------------------------------------------------------------------


def test_pypdf_fallback_path_used_when_pikepdf_unavailable_plain_pdf(tmp_path, monkeypatch):
    import namipdf_inspect.inspector as inspector_mod

    monkeypatch.setattr(inspector_mod, "_HAVE_PIKEPDF", False)
    path = _text_pdf(tmp_path)
    report = inspector_mod.inspect_file(path)

    assert report.engine == "pypdf-fallback"
    assert report.page_count == 1
    assert report.content_class == DocumentStatus.TEXT_PDF
    assert any("KHÔNG kiểm tra chữ ký số" in n for n in report.notes)


def test_pypdf_fallback_path_detects_encryption_and_js(tmp_path, monkeypatch):
    import namipdf_inspect.inspector as inspector_mod

    src = _text_pdf(tmp_path)
    js_dst = os.path.join(tmp_path, "fallback_js.pdf")

    def _add(pdf):
        action = pdf.make_indirect(Dictionary(S=Name.JavaScript, JS=String("app.alert('x')")))
        pdf.Root.OpenAction = action

    _patch(src, js_dst, _add)

    monkeypatch.setattr(inspector_mod, "_HAVE_PIKEPDF", False)
    report = inspector_mod.inspect_file(js_dst)
    assert report.engine == "pypdf-fallback"
    assert report.find("script.javascript") is not None
    assert report.find("action.auto_open") is not None


def test_pypdf_fallback_path_handles_user_password_required(tmp_path, monkeypatch):
    import namipdf_inspect.inspector as inspector_mod

    src = _text_pdf(tmp_path)
    dst = os.path.join(tmp_path, "fallback_pw.pdf")
    with pikepdf.open(src) as pdf:
        pdf.save(dst, encryption=pikepdf.Encryption(owner="o", user="secret", R=4))

    monkeypatch.setattr(inspector_mod, "_HAVE_PIKEPDF", False)
    report = inspector_mod.inspect_file(dst)
    assert report.engine == "pypdf-fallback"
    assert report.requires_user_password is True
    assert report.document_status == DocumentStatus.PROTECTED


def test_both_engines_unavailable_returns_error_report_without_raising(tmp_path, monkeypatch):
    import namipdf_inspect.inspector as inspector_mod

    monkeypatch.setattr(inspector_mod, "_HAVE_PIKEPDF", False)
    monkeypatch.setattr(inspector_mod, "_HAVE_PYPDF", False)
    path = _text_pdf(tmp_path)
    report = inspector_mod.inspect_file(path)
    assert report.engine == "none"
    assert report.errors
    assert report.document_status == DocumentStatus.UNKNOWN


# ---------------------------------------------------------------------------
# 14. Ordering/an toàn mặc định của CompatLevel/Severity (hợp đồng dữ liệu).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("status", [DocumentStatus.SIGNED, DocumentStatus.PROTECTED])
def test_safe_to_overwrite_always_false_for_signed_or_protected_even_with_no_findings(status):
    """Phòng thủ kép: dù (giả định) không có Finding nào (không nên xảy ra
    trong thực tế vì luôn có ít nhất 1 Finding kèm theo), document_status
    Signed/Protected vẫn PHẢI tự nó chặn ghi đè — test trực tiếp property
    bằng cách dựng InspectionReport tối giản."""
    from namipdf_inspect.inspector import InspectionReport

    report = InspectionReport(
        path="x.pdf", engine="pikepdf", pdf_version="1.7", page_count=1,
        producer=None, creator=None, is_linearized=False, requires_user_password=False,
        content_class=DocumentStatus.TEXT_PDF, document_status=status,
        findings=[], notes=[], errors=[],
    )
    assert report.safe_to_overwrite is False
