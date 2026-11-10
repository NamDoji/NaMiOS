# -*- coding: utf-8 -*-
"""Pytest cho namios_fileopen — PL20 vertical slice (MIME routing + archive
safety), triển khai bộ ca F20-01..F20-12.

ĐỌC TRƯỚC: ``docs/specs/namios-pl20/04_KIEN_TRUC_QA.md`` §4 (bảng gốc
F20-01..F20-12). Bảng gốc mô tả gate ở MỨC SẢN PHẨM/DESKTOP ĐẦY ĐỦ (có
Dolphin, codec thật, bàn phím Telex, mạng, onboarding người dùng...) —
công cụ này CHỈ LÀ LOGIC BACKEND (routing + archive safety), nên mỗi test
dưới đây ánh xạ tới MỘT SỐ ID F20-0X với ghi rõ:
  (a) phần THẬT được kiểm ở đây (chạy bằng pytest, không cần desktop), và
  (b) phần của hàng gốc KHÔNG nằm trong phạm vi toolkit này (UI/bàn phím/
      mạng/CAD font/codec thật/onboarding) — những phần đó là PILOT, xem
      ``README.md`` cùng thư mục để biết bảng đối chiếu đầy đủ.

Với F20-07/08/09 — ba hàng gốc (CAD/SVG font-xref, gõ Telex/VNI, mạng tắt/
web ghim) hoàn toàn KHÔNG thể kiểm bằng toolkit backend này (không có UI,
không gõ phím, không có app web) — ba SLOT này được DÙNG LẠI (repurposed)
cho ba việc nằm trong phạm vi toolkit mà nhiệm vụ PL20 yêu cầu rõ (corrupt/
truncated an toàn, PIL crop/convert round-trip, bất biến "không mất file
gốc"). Việc này được NÊU RÕ trong mỗi docstring + README — KHÔNG ngầm coi
là đã kiểm tra Telex/CAD/mạng.

Không có bước nào ở đây mở app NaMiOffice/NaMiPDF/NaMiArchive/NaMiImages/
NaMiMedia thật, không giải nén thật (``extractall``), không phát âm thanh/
video thật, không gọi mạng.
"""
from __future__ import annotations

import hashlib
import os
import tarfile
import wave
import zipfile

import pytest
from PIL import Image

from namios_fileopen import archive_safety, mime_router

# ---------------------------------------------------------------------------
# Fixture builders — mọi tệp sinh TẠI CHỖ lúc chạy test, không chứa dữ liệu
# người dùng thật.
# ---------------------------------------------------------------------------


def _sha256(path) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _make_docx(tmp_path, name="BaiHoc.docx") -> str:
    from docx import Document

    doc = Document()
    doc.add_heading("Tài liệu PL20", level=1)
    doc.add_paragraph("Nội dung kiểm tra mime_router — không phải dữ liệu thật.")
    path = os.path.join(tmp_path, name)
    doc.save(path)
    return path


def _make_xlsx(tmp_path, name="BangTinh.xlsx") -> str:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws["A1"] = "PL20"
    ws["A2"] = 42
    path = os.path.join(tmp_path, name)
    wb.save(path)
    return path


def _make_pptx(tmp_path, name="TrinhChieu.pptx") -> str:
    from pptx import Presentation

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "PL20"
    path = os.path.join(tmp_path, name)
    prs.save(path)
    return path


def _make_pdf(tmp_path, name="TaiLieu.pdf") -> str:
    import pikepdf

    pdf = pikepdf.new()
    path = os.path.join(tmp_path, name)
    pdf.save(path)
    pdf.close()
    return path


def _make_png(tmp_path, name="Anh.png", size=(8, 8), color=(10, 20, 30)) -> str:
    img = Image.new("RGB", size, color=color)
    path = os.path.join(tmp_path, name)
    img.save(path, format="PNG")
    return path


def _make_wav(tmp_path, name="Am.wav") -> str:
    path = os.path.join(tmp_path, name)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\x00\x00" * 8000)
    return path


def _make_mp3_magic(tmp_path, name="Nhac.mp3") -> str:
    """Chỉ đúng MAGIC BYTES (ID3v2 header) — KHÔNG phải MP3 giải mã được
    thật (xem giới hạn trung thực ở README: codec/playback thật là pilot)."""
    path = os.path.join(tmp_path, name)
    with open(path, "wb") as fh:
        fh.write(b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\x00" * 64)
    return path


def _make_mp4_ftyp(tmp_path, name="Clip.mp4") -> str:
    """Box ``ftyp`` ISO-BMFF tối giản — chỉ đủ để sniff là container MP4/
    MOV, KHÔNG phải MP4 phát được thật (codec/track/playback là pilot)."""
    path = os.path.join(tmp_path, name)
    ftyp_body = b"isom" + (0).to_bytes(4, "big") + b"isomiso2mp41"
    box = (8 + len(ftyp_body)).to_bytes(4, "big") + b"ftyp" + ftyp_body
    with open(path, "wb") as fh:
        fh.write(box)
    return path


def _make_pe_disguised_as_pdf(tmp_path, name="Hoa_don.pdf.exe") -> str:
    """Mô phỏng đúng ví dụ nhiệm vụ: tệp có magic PE thật (``MZ``) nhưng
    tên giả dạng hóa đơn PDF rồi mới tới đuôi thực thi thật."""
    path = os.path.join(tmp_path, name)
    with open(path, "wb") as fh:
        fh.write(b"MZ" + b"\x90" * 62 + b"\x00" * 64)
    return path


def _write_zip(path, entries: dict) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry_name, data in entries.items():
            zf.writestr(entry_name, data)


def _make_plain_zip(tmp_path, name="TepNen.zip") -> str:
    path = os.path.join(tmp_path, name)
    _write_zip(path, {"doc.txt": "xin chào PL20".encode("utf-8"), "ghi_chu.txt": b"note"})
    return path


def _make_zip_bomb(tmp_path, name="bomb.zip", size_bytes=20 * 1024 * 1024) -> str:
    """Zip-bomb cổ điển: một entry dữ liệu rất đều (toàn byte 0) nén được
    với tỉ lệ cực cao bằng DEFLATE thường — kích thước TRÊN ĐĨA vẫn nhỏ."""
    path = os.path.join(tmp_path, name)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bomb.bin", b"\x00" * size_bytes)
    return path


def _make_zip_traversal(tmp_path, name="traversal.zip") -> str:
    path = os.path.join(tmp_path, name)
    _write_zip(
        path,
        {
            "../../../etc/passwd": b"evil",
            "/etc/shadow": b"evil-abs",
            "normal_entry.txt": b"ok, khong co gi la",
        },
    )
    return path


def _make_tar_symlink_escape(tmp_path, name="evil_symlink.tar") -> str:
    path = os.path.join(tmp_path, name)
    with tarfile.open(path, "w") as tf:
        ti = tarfile.TarInfo(name="innocuous_link")
        ti.type = tarfile.SYMTYPE
        ti.linkname = "../../../etc/passwd"
        ti.size = 0
        tf.addfile(ti)
        normal = tarfile.TarInfo(name="normal.txt")
        data = b"ok"
        normal.size = len(data)
        import io

        tf.addfile(normal, io.BytesIO(data))
    return path


# ---------------------------------------------------------------------------
# F20-01 — DOCX/XLSX/PPTX route đúng app NaMiOffice theo NỘI DUNG thật.
#   Phạm vi kiểm ở đây: CHỈ phần ROUTING (app nào mở). Phần "báo tính năng
#   rủi ro + round-trip" của hàng gốc do tools/office-compat/namioffice_inspect
#   đảm nhiệm (đã có bộ test riêng) — KHÔNG lặp lại ở đây.
# ---------------------------------------------------------------------------


def test_f20_01_docx_xlsx_pptx_route_to_namioffice(tmp_path):
    docx_report = mime_router.route_file(_make_docx(tmp_path))
    xlsx_report = mime_router.route_file(_make_xlsx(tmp_path))
    pptx_report = mime_router.route_file(_make_pptx(tmp_path))

    assert docx_report.detected_content_kind == "ooxml_docx"
    assert docx_report.app == "namioffice_writer"
    assert docx_report.can_view and docx_report.can_edit
    assert not docx_report.blocked and not docx_report.extension_content_mismatch

    assert xlsx_report.detected_content_kind == "ooxml_xlsx"
    assert xlsx_report.app == "namioffice_sheet"

    assert pptx_report.detected_content_kind == "ooxml_pptx"
    assert pptx_report.app == "namioffice_slides"

    # Đổi đuôi .docx thành .zip (vẫn là ZIP OOXML thật) -> vẫn route ĐÚNG
    # theo NỘI DUNG, không bị đuôi "zip" đánh lạc hướng.
    docx_path = _make_docx(tmp_path, name="DoiDuoi.zip")
    renamed_report = mime_router.route_file(docx_path)
    assert renamed_report.detected_content_kind == "ooxml_docx"
    assert renamed_report.app == "namioffice_writer"


# ---------------------------------------------------------------------------
# F20-02 — PDF route đúng NaMiPDF + không chạm vào bản gốc khi kiểm tra.
#   Phạm vi: routing + bất biến "không sửa file khi inspect". Trạng thái
#   Signed/Scan/Protected là việc của tools/pdf-compat/namipdf_inspect.
# ---------------------------------------------------------------------------


def test_f20_02_pdf_routes_to_namipdf_and_file_untouched(tmp_path):
    pdf_path = _make_pdf(tmp_path)
    before = _sha256(pdf_path)

    report = mime_router.route_file(pdf_path)

    assert report.detected_content_kind == "pdf"
    assert report.app == "namipdf"
    assert report.can_view is True and report.can_edit is False
    assert not report.blocked

    after = _sha256(pdf_path)
    assert before == after, "route_file() KHÔNG được sửa nội dung tệp gốc"


# ---------------------------------------------------------------------------
# F20-03 — ZIP route đúng NaMiArchive; zip-bomb bị archive_safety CHẶN.
# ---------------------------------------------------------------------------


def test_f20_03_zip_routes_to_namiarchive_and_bomb_is_blocked(tmp_path):
    plain_zip = _make_plain_zip(tmp_path)
    plain_report = mime_router.route_file(plain_zip)
    assert plain_report.detected_content_kind == "zip_archive"
    assert plain_report.app == "namiarchive"
    assert not plain_report.blocked

    plain_safety = archive_safety.assess_zip(plain_zip)
    assert plain_safety.safe is True
    assert plain_safety.blocked_reasons == []

    bomb_path = _make_zip_bomb(tmp_path)
    bomb_safety = archive_safety.assess_zip(bomb_path)
    assert bomb_safety.safe is False
    assert bomb_safety.compression_ratio > archive_safety.DEFAULT_MAX_COMPRESSION_RATIO
    assert any("compression_ratio_exceeded" in r for r in bomb_safety.blocked_reasons)
    # Kích thước TRÊN ĐĨA của bomb phải nhỏ hơn hẳn dữ liệu giải nén khai báo
    # — đúng đặc trưng zip-bomb (nén cực tốt từ dữ liệu rất đều).
    assert os.path.getsize(bomb_path) < bomb_safety.total_uncompressed_bytes / 50


# ---------------------------------------------------------------------------
# F20-04 — Đuôi giả (Hoa_don.pdf.exe) bị CHẶN, không route như PDF; tên tệp
# tiếng Việt có dấu vẫn sniff/route đúng bình thường.
# ---------------------------------------------------------------------------


def test_f20_04_fake_extension_blocked_and_vietnamese_filename_ok(tmp_path):
    fake_path = _make_pe_disguised_as_pdf(tmp_path)
    fake_report = mime_router.route_file(fake_path)

    assert fake_report.detected_content_kind == "pe_executable"
    assert fake_report.blocked is True
    assert fake_report.app is None
    assert "executable_content" in fake_report.risk_flags
    assert "double_extension_disguise" in fake_report.risk_flags
    assert fake_report.warnings_vi, "tệp bị chặn phải có cảnh báo rõ, không chặn âm thầm"

    vn_pdf = _make_pdf(tmp_path, name="Hóa_đơn_tháng_Mười_Một_Ngày_10.pdf")
    vn_report = mime_router.route_file(vn_pdf)
    assert vn_report.detected_content_kind == "pdf"
    assert vn_report.app == "namipdf"
    assert vn_report.blocked is False


# ---------------------------------------------------------------------------
# F20-05 — Ảnh raster (PNG/JPEG/GIF/BMP/WEBP/TIFF) route đúng NaMiImages.
#   EXIF/ICC/animation là tính năng NaMiImages sâu hơn, không kiểm ở đây.
# ---------------------------------------------------------------------------


def test_f20_05_image_formats_route_to_namiimages(tmp_path):
    cases = [
        ("PNG", "anh.png", "png"),
        ("JPEG", "anh.jpg", "jpeg"),
        ("GIF", "anh.gif", "gif"),
        ("BMP", "anh.bmp", "bmp"),
        ("WEBP", "anh.webp", "webp"),
        ("TIFF", "anh.tiff", "tiff"),
    ]
    for fmt, filename, expected_kind in cases:
        path = os.path.join(tmp_path, filename)
        Image.new("RGB", (8, 8), color=(1, 2, 3)).save(path, format=fmt)
        report = mime_router.route_file(path)
        assert report.detected_content_kind == expected_kind, f"{filename}: {report.detected_content_kind}"
        assert report.app == "namiimages", f"{filename}: app={report.app}"
        assert report.blocked is False
        assert report.extension_content_mismatch is False


# ---------------------------------------------------------------------------
# F20-06 — Audio/Video (WAV thật + MP3/MP4 ở MỨC MAGIC BYTES) route đúng
# NaMiMedia. Codec/playback thật là PILOT (xem README).
# ---------------------------------------------------------------------------


def test_f20_06_audio_video_route_to_namimedia(tmp_path):
    wav_report = mime_router.route_file(_make_wav(tmp_path))
    assert wav_report.detected_content_kind == "wav"
    assert wav_report.app == "namimedia"
    assert wav_report.can_view is True and wav_report.can_edit is False

    mp3_report = mime_router.route_file(_make_mp3_magic(tmp_path))
    assert mp3_report.detected_content_kind == "mp3"
    assert mp3_report.app == "namimedia"

    mp4_report = mime_router.route_file(_make_mp4_ftyp(tmp_path))
    assert mp4_report.detected_content_kind == "mp4_or_mov"
    assert mp4_report.app == "namimedia"


# ---------------------------------------------------------------------------
# F20-07 (SLOT DÙNG LẠI — hàng gốc là CAD/SVG font/xref, ngoài phạm vi
# toolkit này hoàn toàn) — tệp hỏng/cắt cụt/rỗng được XỬ LÝ AN TOÀN, không
# crash, không âm thầm coi là hợp lệ.
# ---------------------------------------------------------------------------


def test_f20_07_corrupt_or_truncated_files_handled_gracefully(tmp_path):
    # (a) Tệp rỗng mang đuôi .docx — mime_router KHÔNG được crash, KHÔNG
    # được âm thầm route như docx thật khi không có tín hiệu nội dung nào.
    empty_path = os.path.join(tmp_path, "rong.docx")
    open(empty_path, "wb").close()
    empty_report = mime_router.route_file(empty_path)
    assert empty_report.detected_content_kind == "unknown_binary"
    assert empty_report.app is None
    assert empty_report.blocked is False  # rỗng không phải mã độc, chỉ là "không nhận diện được"
    assert any("Không nhận diện được định dạng" in n for n in empty_report.notes_vi)

    # (b) ZIP thật bị cắt cụt giữa file — archive_safety không được crash,
    # phải trả về safe=False kèm lỗi rõ (không phải ngoại lệ ném ra ngoài).
    real_zip = _make_plain_zip(tmp_path, name="goc.zip")
    with open(real_zip, "rb") as fh:
        full_bytes = fh.read()
    truncated_path = os.path.join(tmp_path, "cat_cut.zip")
    with open(truncated_path, "wb") as fh:
        fh.write(full_bytes[: len(full_bytes) // 2])
    truncated_report = archive_safety.assess_zip(truncated_path)
    assert truncated_report.safe is False
    assert truncated_report.errors or truncated_report.blocked_reasons

    # (c) Bytes ngẫu nhiên mang đuôi .zip (không phải ZIP thật) — cũng phải
    # báo rõ, không crash.
    garbage_path = os.path.join(tmp_path, "rac.zip")
    with open(garbage_path, "wb") as fh:
        fh.write(bytes(range(0, 200)) * 3)
    garbage_report = archive_safety.assess_zip(garbage_path)
    assert garbage_report.safe is False
    assert garbage_report.errors or garbage_report.blocked_reasons


# ---------------------------------------------------------------------------
# F20-08 (SLOT DÙNG LẠI — hàng gốc là gõ Telex/VNI, ngoài phạm vi toolkit
# này hoàn toàn — không có bàn phím/ô nhập liệu ở đây) — crop/convert ảnh
# qua PIL round-trip đúng, LƯU BẢN SAO, không đụng bản gốc.
# ---------------------------------------------------------------------------


def test_f20_08_image_crop_convert_roundtrip_via_pil(tmp_path):
    png_path = _make_png(tmp_path, size=(16, 16), color=(100, 150, 200))
    original_hash = _sha256(png_path)

    with Image.open(png_path) as img:
        img.load()
        cropped = img.crop((0, 0, 8, 8)).convert("RGB")
        jpeg_copy_path = os.path.join(tmp_path, "da_cat_va_doi.jpg")
        cropped.save(jpeg_copy_path, format="JPEG", quality=95)

    # Bản gốc PNG KHÔNG bị sửa (chỉ tạo BẢN SAO JPEG mới).
    assert _sha256(png_path) == original_hash

    with Image.open(jpeg_copy_path) as out:
        out.load()
        assert out.size == (8, 8)
        assert out.mode == "RGB"
        r, g, b = out.getpixel((4, 4))
        # JPEG là lossy — chấp nhận sai số nhỏ, không yêu cầu khớp tuyệt đối.
        assert abs(r - 100) <= 12 and abs(g - 150) <= 12 and abs(b - 200) <= 12

    jpeg_report = mime_router.route_file(jpeg_copy_path)
    assert jpeg_report.detected_content_kind == "jpeg"
    assert jpeg_report.app == "namiimages"


# ---------------------------------------------------------------------------
# F20-09 (SLOT DÙNG LẠI — hàng gốc là mạng tắt/web ghim, công cụ này không
# gọi mạng nên không áp dụng) — quét BẤT KỲ bằng mime_router/archive_safety
# KHÔNG BAO GIỜ sửa đổi tệp gốc, trên mọi loại fixture.
# ---------------------------------------------------------------------------


def test_f20_09_original_file_never_modified_by_any_inspection(tmp_path):
    paths = [
        _make_docx(tmp_path),
        _make_pdf(tmp_path),
        _make_plain_zip(tmp_path),
        _make_png(tmp_path),
        _make_wav(tmp_path),
    ]
    before = {p: _sha256(p) for p in paths}

    for p in paths:
        mime_router.route_file(p)
    archive_safety.assess_archive(paths[2])  # zip fixture

    for p in paths:
        assert os.path.exists(p), f"tệp gốc biến mất sau khi inspect: {p}"
        assert _sha256(p) == before[p], f"tệp gốc BỊ SỬA sau khi inspect: {p}"


# ---------------------------------------------------------------------------
# F20-10 — Đổi app mặc định ("Luôn dùng ứng dụng này cho loại tệp") resolve
# đúng; không cho đặt app không khai hỗ trợ; KHÔNG BAO GIỜ áp override cho
# report đã bị chặn (an toàn > tùy chọn người dùng).
# ---------------------------------------------------------------------------


def test_f20_10_change_default_app_resolves(tmp_path):
    registry = mime_router.FileAssociationRegistry()
    png_report = mime_router.route_file(_make_png(tmp_path))
    assert png_report.app == "namiimages"

    registry.set_default("png", "namibrowser")
    resolved = registry.resolve(png_report)
    assert resolved.app == "namibrowser"
    assert resolved.can_edit is False
    assert resolved is not png_report  # report gốc không bị sửa tại chỗ
    assert png_report.app == "namiimages"

    registry.reset_default("png")
    assert registry.resolve(png_report).app == "namiimages"

    # Không cho đặt một app KHÔNG khai hỗ trợ content_kind làm mặc định.
    with pytest.raises(ValueError):
        registry.set_default("png", "namimedia")

    # Bất biến an toàn: dù override dict có bị "ép" chứa entry cho nội dung
    # thực thi (mô phỏng lỗi/giả định xấu nhất), resolve() vẫn PHẢI bỏ qua
    # vì report.blocked=True — override không được dùng để lách chặn.
    fake_report = mime_router.route_file(_make_pe_disguised_as_pdf(tmp_path))
    assert fake_report.blocked is True
    registry._overrides["pe_executable"] = "namioffice_writer"  # type: ignore[attr-defined]  # noqa: SLF001
    still_blocked = registry.resolve(fake_report)
    assert still_blocked.app is None
    assert still_blocked.blocked is True


# ---------------------------------------------------------------------------
# F20-11 — Archive traversal (zip-slip + absolute path) và symlink escape
# (tar) bị CHẶN; không có bước nào thực sự giải nén/đụng file ngoài đích.
# ---------------------------------------------------------------------------


def test_f20_11_archive_path_traversal_and_symlink_escape_blocked(tmp_path):
    traversal_zip = _make_zip_traversal(tmp_path)
    zip_report = archive_safety.assess_zip(traversal_zip)
    assert zip_report.safe is False
    assert any(s.startswith("path_traversal:") for s in zip_report.suspicious_entries)
    assert any("../../../etc/passwd" in s or "/etc/shadow" in s for s in zip_report.suspicious_entries)

    symlink_tar = _make_tar_symlink_escape(tmp_path)
    tar_report = archive_safety.assess_tar(symlink_tar)
    assert tar_report.safe is False
    assert any(s.startswith("symlink_escape:") for s in tar_report.suspicious_entries)

    # Không có bước quét nào được phép GIẢI NÉN thật — xác nhận không file
    # nào tên "passwd"/"shadow" xuất hiện trên đĩa sau khi quét.
    for root, _dirs, files in os.walk(tmp_path):
        assert "passwd" not in files and "shadow" not in files, (
            f"archive_safety có vẻ đã GIẢI NÉN thật vào {root} — vi phạm bất biến chỉ-đọc"
        )


# ---------------------------------------------------------------------------
# F20-12 (PHẦN LỚN hàng gốc là onboarding/UI/bàn phím — pilot) — phần kiểm
# được ở backend: định dạng không nhận diện được có fallback AN TOÀN theo
# đúng câu chữ 02_MO_TEP_VA_DINH_DANG.md §1, và MỌI report bị chặn/không an
# toàn đều có lý do cụ thể (không có "lỗi câm", tức luôn có "next action"
# ở dạng thông tin máy đọc được).
# ---------------------------------------------------------------------------


def test_f20_12_unknown_format_has_safe_fallback_and_reasons_are_never_silent(tmp_path):
    mystery_path = os.path.join(tmp_path, "bi_an.xyz123")
    with open(mystery_path, "wb") as fh:
        fh.write(bytes(range(200, 256)) * 8)  # không khớp magic nào, không phải UTF-8 hợp lệ
    mystery_report = mime_router.route_file(mystery_path)
    assert mystery_report.app is None
    assert mystery_report.blocked is False
    assert any("Không nhận diện được định dạng" in n for n in mystery_report.notes_vi)

    fake_report = mime_router.route_file(_make_pe_disguised_as_pdf(tmp_path))
    assert fake_report.blocked is True
    assert fake_report.warnings_vi, "report bị chặn phải luôn có cảnh báo cụ thể"

    bomb_safety = archive_safety.assess_zip(_make_zip_bomb(tmp_path))
    assert bomb_safety.safe is False
    assert bomb_safety.blocked_reasons, "report archive không an toàn phải luôn có lý do cụ thể"

    traversal_safety = archive_safety.assess_zip(_make_zip_traversal(tmp_path))
    assert traversal_safety.safe is False
    assert traversal_safety.suspicious_entries, "report archive không an toàn phải luôn có lý do cụ thể"
