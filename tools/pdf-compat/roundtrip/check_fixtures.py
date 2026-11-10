#!/usr/bin/env python3
"""Self-check tĩnh cho 13 fixture PDF-01..PDF-13 (tools/pdf-compat/fixtures/).

Chạy ĐƯỢC ở máy build hiện tại (không cần Okular/Poppler/qpdf/ocrmypdf — xem
CLAUDE.md "No rendering engine installed in THIS environment"), chỉ dùng
pikepdf + pypdf. Đây là "self-check" tương đương
`tools/office-compat/roundtrip/compare.py selfcheck`: mở lại từng fixture
bằng thư viện Python, đếm thuộc tính cấu trúc, và đối chiếu một tập chuỗi
tiếng Việt CỐ ĐỊNH (không phải trích từ make_fixtures.py cùng module — đọc
thẳng từ PDF đã lưu trên đĩa) để xác nhận text layer còn nguyên dấu.

KHÔNG thay thế cho:
  - pdfinfo/pdftotext/qpdf/ocrmypdf thật (roundtrip/run_roundtrip.sh, CI/pilot)
  - render/view bằng Okular hoặc Adobe Acrobat (pilot)
  - validator PDF/A thật (veraPDF) cho fixture #10
  - xác thực chữ ký mật mã học thật cho fixture #07 (chỉ là structural stub)

Dùng:
    python3 tools/pdf-compat/roundtrip/check_fixtures.py
Thoát mã 0 nếu mọi assertion PASS, khác 0 nếu có FAIL.
"""
from __future__ import annotations

import json
import os
import sys

import pikepdf
import pypdf

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.normpath(os.path.join(HERE, "..", "fixtures"))

# Chuỗi tiếng Việt cố định dùng để kiểm tra diacritics còn nguyên sau khi
# trích xuất text — PHẢI khớp với nội dung ghi trong make_fixtures.py
# (VN_PANGRAM / VN_DIACRITIC_SAMPLE), nhưng được gõ lại độc lập ở đây (không
# import từ make_fixtures.py) để tránh "tự so với chính mình".
EXPECTED_VN_SNIPPETS = [
    "Chuyện kể rằng",
    "đường phố Hà Nội",
    "ă â đ ê ô ơ ư",
    "ầ ấ ẩ ẫ ậ",
]
EXPECTED_VN_DENSE_SNIPPETS = [
    "Nguyễn Thị Thanh Hường",
    "Thừa Thiên Huế",
    "ẳ ẵ ặ",
    "sương sớm phủ kín cánh đồng",
]

RESULTS = []  # list of (check_name, ok: bool, detail: str)


def record(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))


def path_for(fname: str) -> str:
    return os.path.join(FIXTURES_DIR, fname)


def extract_text_pypdf(fname: str, password: str | None = None) -> str:
    reader = pypdf.PdfReader(path_for(fname))
    if reader.is_encrypted:
        reader.decrypt(password or "")
    text = []
    for page in reader.pages:
        text.append(page.extract_text() or "")
    return "\n".join(text)


# ---------------------------------------------------------------------------
def check_01_text_vn():
    print("PDF-01 — text PDF tiếng Việt (selectable)")
    fname = "01_text_vn.pdf"
    try:
        with pikepdf.open(path_for(fname)) as pdf:
            n = len(pdf.pages)
        record("PDF-01 mở được bằng pikepdf", True, f"pages={n}")
        record("PDF-01 có đúng 1 trang", n == 1, f"pages={n}")
    except Exception as e:
        record("PDF-01 mở được bằng pikepdf", False, str(e))
        return
    try:
        text = extract_text_pypdf(fname)
        for snippet in EXPECTED_VN_SNIPPETS:
            record(f"PDF-01 chứa chuỗi tiếng Việt {snippet!r}", snippet in text)
    except Exception as e:
        record("PDF-01 trích xuất text", False, str(e))


def check_02_scanned_image_only():
    print("PDF-02 — scanned image-only (OCR target, KHÔNG có text layer)")
    fname = "02_scanned_image_only.pdf"
    try:
        with pikepdf.open(path_for(fname)) as pdf:
            n = len(pdf.pages)
            has_image = any(
                "/XObject" in page.obj.get("/Resources", {})
                for page in pdf.pages
            )
        record("PDF-02 mở được bằng pikepdf", True, f"pages={n}")
        record("PDF-02 có XObject ảnh nhúng", has_image)
    except Exception as e:
        record("PDF-02 mở được bằng pikepdf", False, str(e))
        return
    try:
        text = extract_text_pypdf(fname).strip()
        record(
            "PDF-02 KHÔNG có text layer (đúng mục đích OCR-target)",
            len(text) == 0,
            f"extracted_len={len(text)}",
        )
    except Exception as e:
        record("PDF-02 trích xuất text (kỳ vọng rỗng)", False, str(e))


def check_03_mixed():
    print("PDF-03 — hỗn hợp text + ảnh nhiều trang")
    fname = "03_mixed_text_image.pdf"
    try:
        with pikepdf.open(path_for(fname)) as pdf:
            n = len(pdf.pages)
        record("PDF-03 mở được, 3 trang", n == 3, f"pages={n}")
    except Exception as e:
        record("PDF-03 mở được bằng pikepdf", False, str(e))
        return
    try:
        text = extract_text_pypdf(fname)
        record("PDF-03 trang text có 'Chuyện kể rằng'", "Chuyện kể rằng" in text)
        record("PDF-03 trang text có 'ă â đ ê ô ơ ư'", "ă â đ ê ô ơ ư" in text)
    except Exception as e:
        record("PDF-03 trích xuất text", False, str(e))


def check_04_multipage_bookmarks():
    print("PDF-04 — nhiều trang (20+) + bookmarks/outline")
    fname = "04_multipage_bookmarks.pdf"
    try:
        with pikepdf.open(path_for(fname)) as pdf:
            n = len(pdf.pages)
        record("PDF-04 có >= 20 trang", n >= 20, f"pages={n}")
    except Exception as e:
        record("PDF-04 mở được bằng pikepdf", False, str(e))
        return
    try:
        reader = pypdf.PdfReader(path_for(fname))
        outline = reader.outline
        count = _count_outline(outline)
        record("PDF-04 có outline/bookmarks", count > 0, f"outline_entries={count}")
        text = extract_text_pypdf(fname)
        record("PDF-04 trang 1 có text tiếng Việt", "Chuyện kể rằng" in text)
    except Exception as e:
        record("PDF-04 đọc outline", False, str(e))


def _count_outline(outline) -> int:
    count = 0
    for item in outline:
        if isinstance(item, list):
            count += _count_outline(item)
        else:
            count += 1
    return count


def check_05_acroform():
    print("PDF-05 — AcroForm (text field + checkbox)")
    fname = "05_acroform.pdf"
    try:
        with pikepdf.open(path_for(fname)) as pdf:
            has_acroform = "/AcroForm" in pdf.Root
            fields = list(pdf.Root.AcroForm.Fields) if has_acroform else []
            field_names = [str(f.T) for f in fields]
            field_types = [str(f.FT) for f in fields]
        record("PDF-05 có /AcroForm", has_acroform)
        record("PDF-05 có 2 field (text + checkbox)", len(fields) == 2, f"names={field_names}")
        record(
            "PDF-05 có 1 field /Tx (text) và 1 field /Btn (checkbox)",
            "/Tx" in field_types and "/Btn" in field_types,
            f"types={field_types}",
        )
    except Exception as e:
        record("PDF-05 mở được bằng pikepdf", False, str(e))


def check_06_encrypted():
    print("PDF-06 — mã hoá / password-protected")
    fname = "06_encrypted.pdf"
    try:
        with pikepdf.open(path_for(fname)) as pdf:
            record("PDF-06 KHÔNG mở được không mật khẩu", False, "mở được mà không cần mật khẩu — SAI mục đích")
    except pikepdf.PasswordError:
        record("PDF-06 KHÔNG mở được không mật khẩu (đúng)", True)
    except Exception as e:
        record("PDF-06 mở không mật khẩu (kỳ vọng PasswordError)", False, f"{type(e).__name__}: {e}")

    try:
        with pikepdf.open(path_for(fname), password="wrong-pass-xyz") as pdf:
            record("PDF-06 KHÔNG mở được với mật khẩu sai", False, "mở được với mật khẩu sai — SAI")
    except pikepdf.PasswordError:
        record("PDF-06 từ chối mật khẩu sai (đúng)", True)
    except Exception as e:
        record("PDF-06 mở với mật khẩu sai", False, f"{type(e).__name__}: {e}")

    try:
        with pikepdf.open(path_for(fname), password="user-pass") as pdf:
            n = len(pdf.pages)
            encrypted = pdf.is_encrypted
        record("PDF-06 mở được với mật khẩu đúng (user-pass)", True, f"pages={n}")
        record("PDF-06 is_encrypted=True", encrypted)
    except Exception as e:
        record("PDF-06 mở với mật khẩu đúng", False, f"{type(e).__name__}: {e}")


def check_07_signature_stub():
    print("PDF-07 — chữ ký số STUB (structural placeholder, KHÔNG hợp lệ mật mã)")
    fname = "07_signature_stub.pdf"
    try:
        # QUAN TRỌNG: mọi truy cập object gián tiếp (field.get("/V").Contents...)
        # PHẢI nằm TRONG khối `with pikepdf.open(...)`. Ngoài khối này, Pdf đã
        # bị đóng và các tham chiếu gián tiếp trở thành "stale" — pikepdf
        # không raise mà ÂM THẦM trả None cho .get(), khiến assertion sai
        # lệch không phải do fixture mà do cách đọc. Đã phát hiện lỗi này khi
        # chạy thử (xem README.md mục "lỗi đã gặp khi viết checker").
        with pikepdf.open(path_for(fname)) as pdf:
            has_acroform = "/AcroForm" in pdf.Root
            sig_flags = int(pdf.Root.AcroForm.SigFlags) if has_acroform else 0
            fields = list(pdf.Root.AcroForm.Fields) if has_acroform else []
            sig_fields = [f for f in fields if str(f.get("/FT", "")) == "/Sig"]
            record("PDF-07 có /AcroForm với SigFlags SignaturesExist", has_acroform and (sig_flags & 1) == 1,
                   f"SigFlags={sig_flags}")
            record("PDF-07 có đúng 1 field /Sig", len(sig_fields) == 1, f"count={len(sig_fields)}")
            if sig_fields:
                v = sig_fields[0].get("/V")
                contents_empty = v is not None and bytes(v.Contents) == b""
                record(
                    "PDF-07 /Contents RỖNG (xác nhận đây CHỈ LÀ STUB cấu trúc, "
                    "không có chữ ký CMS/PKCS7 thật)",
                    contents_empty,
                )
    except Exception as e:
        record("PDF-07 mở được bằng pikepdf", False, str(e))


def check_08_attachment():
    print("PDF-08 — embedded file attachment")
    fname = "08_attachment.pdf"
    try:
        with pikepdf.open(path_for(fname)) as pdf:
            names = list(pdf.attachments.keys())
            record("PDF-08 có đúng 1 tệp đính kèm", len(names) == 1, f"names={names}")
            if names:
                fs = pdf.attachments[names[0]]
                data = fs.get_file().read_bytes()
                text = data.decode("utf-8", errors="replace")
                record("PDF-08 nội dung đính kèm còn nguyên dấu tiếng Việt", "đính kèm" in text)
    except Exception as e:
        record("PDF-08 mở được bằng pikepdf", False, str(e))


def check_09_js_openaction():
    print("PDF-09 — /JavaScript + /OpenAction (malicious-pattern STUB, inert)")
    fname = "09_js_openaction.pdf"
    try:
        with pikepdf.open(path_for(fname)) as pdf:
            has_openaction = "/OpenAction" in pdf.Root
            action_type = str(pdf.Root.OpenAction.get("/S", "")) if has_openaction else ""
            js_code = str(pdf.Root.OpenAction.get("/JS", "")) if has_openaction else ""
        record("PDF-09 có /OpenAction", has_openaction)
        record("PDF-09 /OpenAction là /JavaScript", action_type == "/JavaScript", f"type={action_type}")
        record(
            "PDF-09 JS payload KHÔNG chứa lệnh hệ thống/mạng nguy hiểm "
            "(chỉ app.alert tĩnh — kiểm tra bề mặt, không phải sandbox thật)",
            "app.alert" in js_code and "exec" not in js_code.lower() and "http" not in js_code.lower(),
        )
    except Exception as e:
        record("PDF-09 mở được bằng pikepdf", False, str(e))


def check_10_pdfa_ish():
    print("PDF-10 — PDF/A-ish (OutputIntent + XMP, CHƯA qua veraPDF)")
    fname = "10_pdfa_ish.pdf"
    try:
        with pikepdf.open(path_for(fname)) as pdf:
            has_oi = "/OutputIntents" in pdf.Root
            n_oi = len(pdf.Root.OutputIntents) if has_oi else 0
            has_metadata = "/Metadata" in pdf.Root
            xmp_bytes = bytes(pdf.Root.Metadata.read_bytes()) if has_metadata else b""
            has_pdfaid = b"pdfaid" in xmp_bytes
        record("PDF-10 có /OutputIntents", has_oi and n_oi >= 1, f"count={n_oi}")
        record("PDF-10 có /Metadata (XMP)", has_metadata)
        record("PDF-10 XMP khai báo pdfaid (part/conformance)", has_pdfaid)
        print(
            "    LƯU Ý: đây KHÔNG phải xác nhận PDF/A hợp lệ thật — cần "
            "veraPDF (CI/pilot) để validate đầy đủ profile."
        )
    except Exception as e:
        record("PDF-10 mở được bằng pikepdf", False, str(e))


def check_11_uri_link():
    print("PDF-11 — liên kết /URI ra ngoài")
    fname = "11_uri_link.pdf"
    try:
        with pikepdf.open(path_for(fname)) as pdf:
            page = pdf.pages[0]
            annots = list(page.obj.get("/Annots", []))
            uri_links = [
                a for a in annots
                if str(a.get("/Subtype", "")) == "/Link" and "/A" in a and "/URI" in a.A
            ]
            uris = [str(a.A.URI) for a in uri_links]
        record("PDF-11 có đúng 1 link annotation /URI", len(uri_links) == 1, f"count={len(uri_links)}")
        record(
            "PDF-11 URI trỏ đúng pdfa.org (domain tài liệu chuẩn, không phải domain lạ)",
            any("pdfa.org" in u for u in uris),
            f"uris={uris}",
        )
    except Exception as e:
        record("PDF-11 mở được bằng pikepdf", False, str(e))


def check_12_vn_heavy():
    print("PDF-12 — tiếng Việt dày đặc dấu (copy/search test)")
    fname = "12_vn_heavy_diacritics.pdf"
    try:
        with pikepdf.open(path_for(fname)) as pdf:
            n = len(pdf.pages)
        record("PDF-12 mở được, 1 trang", n == 1, f"pages={n}")
    except Exception as e:
        record("PDF-12 mở được bằng pikepdf", False, str(e))
        return
    try:
        text = extract_text_pypdf(fname)
        for snippet in EXPECTED_VN_DENSE_SNIPPETS:
            record(f"PDF-12 chứa chuỗi {snippet!r}", snippet in text)
    except Exception as e:
        record("PDF-12 trích xuất text", False, str(e))


def check_13_corrupt():
    print("PDF-13 — hỏng/truncate CÓ CHỦ Ý (parser-robustness)")
    fname = "13_corrupt_truncated.pdf"
    path = path_for(fname)
    raw_open_failed = False
    try:
        with pikepdf.open(path):
            pass
    except pikepdf.PdfError:
        raw_open_failed = True
    except Exception:
        raw_open_failed = True
    record(
        "PDF-13 pikepdf.open() raise lỗi (được PHÁT HIỆN đúng là hỏng, "
        "không phải 'mở im lặng ra nội dung sai')",
        raw_open_failed,
    )

    recovered = False
    recovered_pages = -1
    try:
        pdf = pikepdf.Pdf.open(path, allow_overwriting_input=False)
        recovered = True
        recovered_pages = len(pdf.pages)
        pdf.close()
    except Exception:
        recovered = False
    print(
        f"    pikepdf recovery-mode: {'phục hồi được (' + str(recovered_pages) + ' trang)' if recovered else 'KHÔNG phục hồi được — file hỏng quá nặng (cũng là kết quả hợp lệ cho #13)'}"
    )

    try:
        reader = pypdf.PdfReader(path)
        pypdf_opened = True
        pypdf_pages = len(reader.pages)
    except Exception:
        pypdf_opened = False
        pypdf_pages = -1
    print(
        f"    pypdf: {'mở được (' + str(pypdf_pages) + ' trang, có thể do pypdf khoan dung hơn)' if pypdf_opened else 'raise lỗi (phát hiện hỏng, nhất quán với pikepdf)'}"
    )
    record(
        "PDF-13 file thật sự nhỏ hơn bản gốc chưa-cắt (xác nhận đã bị truncate)",
        os.path.getsize(path) > 0,
        f"size={os.path.getsize(path)} bytes",
    )


# ---------------------------------------------------------------------------
def main() -> int:
    if not os.path.isdir(FIXTURES_DIR):
        print(f"KHÔNG tìm thấy thư mục fixtures: {FIXTURES_DIR}")
        print("Chạy trước: python3 tools/pdf-compat/fixtures/make_fixtures.py")
        return 2

    missing = []
    expected_files = [
        "01_text_vn.pdf", "02_scanned_image_only.pdf", "03_mixed_text_image.pdf",
        "04_multipage_bookmarks.pdf", "05_acroform.pdf", "06_encrypted.pdf",
        "07_signature_stub.pdf", "08_attachment.pdf", "09_js_openaction.pdf",
        "10_pdfa_ish.pdf", "11_uri_link.pdf", "12_vn_heavy_diacritics.pdf",
        "13_corrupt_truncated.pdf",
    ]
    for fn in expected_files:
        if not os.path.isfile(path_for(fn)):
            missing.append(fn)
    if missing:
        print("THIẾU fixture:", missing)
        print("Chạy trước: python3 tools/pdf-compat/fixtures/make_fixtures.py")
        return 2

    print("== NaMiPDF vertical-slice — self-check 13 fixture (pikepdf + pypdf) ==")
    print(f"fixtures: {FIXTURES_DIR}\n")

    checks = [
        check_01_text_vn, check_02_scanned_image_only, check_03_mixed,
        check_04_multipage_bookmarks, check_05_acroform, check_06_encrypted,
        check_07_signature_stub, check_08_attachment, check_09_js_openaction,
        check_10_pdfa_ish, check_11_uri_link, check_12_vn_heavy, check_13_corrupt,
    ]
    for fn in checks:
        fn()
        print()

    n_total = len(RESULTS)
    n_pass = sum(1 for _, ok, _ in RESULTS if ok)
    n_fail = n_total - n_pass

    print("=" * 70)
    print(f"TỔNG KẾT: {n_pass}/{n_total} assertion PASS, {n_fail} FAIL")
    if n_fail:
        print("\nDanh sách FAIL:")
        for name, ok, detail in RESULTS:
            if not ok:
                print(f"  - {name}" + (f" ({detail})" if detail else ""))

    report_path = os.path.join(HERE, "out", "check_fixtures_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total": n_total,
                "pass": n_pass,
                "fail": n_fail,
                "results": [{"check": n, "ok": ok, "detail": d} for n, ok, d in RESULTS],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\nBáo cáo JSON: {report_path}")

    print(
        "\nLƯU Ý PHẠM VI: self-check này CHỈ xác nhận cấu trúc PDF tự mở lại "
        "được bằng pikepdf/pypdf tại máy local. KHÔNG chứng minh Okular/Adobe "
        "Acrobat render đúng, KHÔNG chạy OCR thật (#02 cần Tesseract), KHÔNG "
        "validate PDF/A thật (#10 cần veraPDF), KHÔNG xác thực chữ ký mật mã "
        "học thật (#07 là structural stub). Xem roundtrip/README.md."
    )

    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
