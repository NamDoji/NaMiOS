# -*- coding: utf-8 -*-
"""Test ví dụ automation THẬT (ADR-0022): đếm từ tiếng Việt trong .docx +
dry-run/rollback — xem tools/namios-sdk/automation_example.py.
"""
from __future__ import annotations

import docx
import pytest

import automation_example as ax


@pytest.fixture()
def sample_docx(tmp_path):
    """Tạo một file .docx thật với văn bản tiếng Việt có dấu, trả đường dẫn."""
    document = docx.Document()
    document.add_paragraph("Hôm nay trời đẹp, học sinh đi học rất vui vẻ.")
    document.add_paragraph("Toán học và tiếng Việt đều quan trọng như nhau.")
    document.add_paragraph("")  # đoạn trống — phải không góp từ nào
    path = tmp_path / "bai-van.docx"
    document.save(str(path))
    return path


def test_tokenize_vietnamese_keeps_diacritics():
    words = ax.tokenize_vietnamese("Trường học tiếng Việt rất đẹp")
    assert words == ["Trường", "học", "tiếng", "Việt", "rất", "đẹp"]


def test_count_vietnamese_words_on_real_docx(sample_docx):
    report = ax.count_vietnamese_words(sample_docx)

    assert report.source_path == str(sample_docx)
    assert report.paragraph_count == 3  # gồm đoạn trống
    assert report.word_count > 0
    # Câu 1 có 11 từ, câu 2 có 10 từ (kiểm bằng tokenize_vietnamese, không đếm tay).
    assert report.word_count == 21
    assert "Hôm" in report.sample_words
    assert "tiếng" in report.sample_words or "Việt" in report.sample_words
    # casefold dedupe: "tiếng"/"Việt" xuất hiện lặp giữa 2 câu vẫn tính unique đúng.
    assert report.unique_word_count <= report.word_count


def test_count_vietnamese_words_rejects_missing_file(tmp_path):
    missing = tmp_path / "khong-ton-tai.docx"
    with pytest.raises(FileNotFoundError):
        ax.count_vietnamese_words(missing)


def test_count_vietnamese_words_rejects_non_docx(tmp_path):
    txt_path = tmp_path / "ghi-chu.txt"
    txt_path.write_text("không phải docx", encoding="utf-8")
    with pytest.raises(ValueError):
        ax.count_vietnamese_words(txt_path)


def test_add_word_count_footer_dry_run_does_not_touch_disk(sample_docx, tmp_path):
    out_path = tmp_path / "bai-van-co-footer.docx"
    result = ax.add_word_count_footer(sample_docx, out_path, dry_run=True)

    assert result["dry_run"] is True
    assert "Số từ tiếng Việt" in result["footer_text"]
    assert not out_path.exists(), "dry_run=True TUYỆT ĐỐI không được ghi file"

    # Tài liệu gốc cũng không đổi số đoạn.
    original = docx.Document(str(sample_docx))
    assert len(original.paragraphs) == 3


def test_add_word_count_footer_real_write_creates_new_file_only(sample_docx, tmp_path):
    out_path = tmp_path / "bai-van-co-footer.docx"
    result = ax.add_word_count_footer(sample_docx, out_path, dry_run=False)

    assert result["dry_run"] is False
    assert out_path.exists(), "dry_run=False phải tạo file mới"

    # File gốc giữ nguyên 3 đoạn (không bị ghi đè).
    original = docx.Document(str(sample_docx))
    assert len(original.paragraphs) == 3

    # File mới có thêm đúng 1 đoạn footer, nội dung gốc vẫn còn.
    updated = docx.Document(str(out_path))
    assert len(updated.paragraphs) == 4
    assert "Số từ tiếng Việt" in updated.paragraphs[-1].text

    # Rollback = xoá out_path, tài liệu gốc không đổi (bằng chứng: xoá rồi gốc còn đọc được).
    out_path.unlink()
    assert sample_docx.exists()
    assert docx.Document(str(sample_docx)).paragraphs[0].text.startswith("Hôm nay")


def test_add_word_count_footer_rejects_overwriting_source(sample_docx):
    with pytest.raises(ValueError):
        ax.add_word_count_footer(sample_docx, sample_docx, dry_run=False)
