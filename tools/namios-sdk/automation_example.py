#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMiOS Extension SDK — ví dụ automation THẬT, chạy được KHÔNG CẦN app Office
(ADR-0022 §"Ví dụ automation an toàn").

Minh hoạ cụ thể khái niệm "automation trong phạm vi được review" của manifest
`examples/word-count-vi.manifest.json` (scope `office:document-only`, entrypoint
`nami_script_api`, sandbox `python_subprocess_restricted`): đếm từ tiếng Việt
trong MỘT file .docx được truyền vào theo đường dẫn tham số rõ ràng (không tự
dò toàn ổ đĩa, không mở file khác, không ra mạng).

Dùng `python-docx` (đã cài trong môi trường này) để đọc text của .docx thật —
đây KHÔNG phải mô phỏng UNO/LibreOffice: nó đọc/ghi file .docx trên đĩa trực
tiếp qua thư viện, không cần LibreOffice/UNO đang chạy. Khi chạy thật trong
NaMiOffice qua `nami_script_api`, lớp gọi tương đương sẽ lấy text từ API tài
liệu ĐANG MỞ thay vì mở lại file — ranh giới này nêu rõ trong ADR-0022 §Phạm
vi trung thực.

Hai hàm minh hoạ:
  * `count_vietnamese_words(path)` — đọc .docx, đếm từ tiếng Việt (tách theo
    khoảng trắng/dấu câu, giữ nguyên ký tự có dấu), trả báo cáo có cấu trúc.
    Chỉ ĐỌC — khớp `dry_run_supported: true` + `rollback.supported: true`
    ("read-only, không có trạng thái cần hoàn tác") của manifest mẫu.
  * `add_word_count_footer(path, out_path, dry_run=True)` — biến thể CÓ GHI,
    minh hoạ dry-run + rollback: `dry_run=True` (mặc định) chỉ TRẢ VỀ nội dung
    sẽ ghi, KHÔNG đụng file; `dry_run=False` ghi ra `out_path` (một file MỚI,
    không đè file gốc) — hoàn tác = xoá `out_path`, tài liệu gốc không đổi.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

import docx

#: Khớp một "từ" gồm chữ cái Unicode (bao gồm chữ Việt có dấu) hoặc số.
#: \w trong Python re với cờ UNICODE (mặc định ở Python 3) đã bao phủ các
#: ký tự có dấu tiếng Việt (vd 'đ', 'ư', 'ờ'), nên không cần bảng ký tự riêng.
_WORD_RE = re.compile(r"[^\W\d_]+|\d+", re.UNICODE)


@dataclass(frozen=True)
class WordCountReport:
    source_path: str
    paragraph_count: int
    word_count: int
    unique_word_count: int
    sample_words: List[str]

    def to_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "paragraph_count": self.paragraph_count,
            "word_count": self.word_count,
            "unique_word_count": self.unique_word_count,
            "sample_words": self.sample_words,
        }


def _extract_paragraph_texts(document: "docx.document.Document") -> List[str]:
    """Lấy text của mọi đoạn văn trong THÂN tài liệu (không gồm header/footer/
    textbox — giới hạn đã nêu rõ, tránh ngộ nhận 'đếm hết tài liệu')."""
    return [p.text for p in document.paragraphs]


def tokenize_vietnamese(text: str) -> List[str]:
    """Tách từ đơn giản: theo khoảng trắng + dấu câu, giữ ký tự có dấu."""
    return _WORD_RE.findall(text)


def count_vietnamese_words(path: str | Path) -> WordCountReport:
    """Đọc MỘT file .docx tại `path` (tham số rõ ràng, không tự dò) và đếm từ.

    Chỉ đọc (`office:document-only`, read-only) — không ghi, không gọi mạng,
    không đọc file nào khác ngoài `path`.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"không tìm thấy file .docx: {path}")
    if path.suffix.lower() != ".docx":
        raise ValueError(f"chỉ hỗ trợ .docx trong ví dụ này, nhận: {path.suffix!r}")

    document = docx.Document(str(path))
    texts = _extract_paragraph_texts(document)

    words: List[str] = []
    for text in texts:
        words.extend(tokenize_vietnamese(text))

    seen = []
    seen_set = set()
    for w in words:
        key = w.casefold()
        if key not in seen_set:
            seen_set.add(key)
            seen.append(w)

    return WordCountReport(
        source_path=str(path),
        paragraph_count=len(texts),
        word_count=len(words),
        unique_word_count=len(seen_set),
        sample_words=seen[:20],
    )


def add_word_count_footer(
    path: str | Path, out_path: str | Path, dry_run: bool = True
) -> dict:
    """Thêm MỘT đoạn cuối tài liệu ghi số từ đã đếm — minh hoạ dry-run + rollback.

    - `dry_run=True` (mặc định, an toàn): KHÔNG đụng đĩa. Trả về nội dung
      đoạn sẽ-được-thêm để người dùng xem trước khi đồng ý ghi thật
      (khớp `dry_run_supported: true` trong manifest).
    - `dry_run=False`: ghi ra `out_path` — một file MỚI khác `path`, tài liệu
      gốc giữ nguyên. Rollback = xoá `out_path`.
    """
    report = count_vietnamese_words(path)
    footer_text = f"[NaMiOffice SDK demo] Số từ tiếng Việt: {report.word_count}"

    if dry_run:
        return {
            "dry_run": True,
            "would_write_to": str(out_path),
            "footer_text": footer_text,
            "source_path": str(path),
            "rollback": "dry_run=true không ghi gì — không cần hoàn tác.",
        }

    out_path = Path(out_path)
    if out_path.resolve() == Path(path).resolve():
        raise ValueError(
            "out_path phải khác source path — không được đè tài liệu gốc "
            "(hard rule: ghi ra file mới để giữ rollback đơn giản)"
        )

    document = docx.Document(str(path))
    document.add_paragraph(footer_text)
    document.save(str(out_path))

    return {
        "dry_run": False,
        "written_to": str(out_path),
        "footer_text": footer_text,
        "source_path": str(path),
        "rollback": f"xoá file '{out_path}' để hoàn tác; tài liệu gốc '{path}' không đổi.",
    }


def _cli() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="NaMiOS Extension SDK — đếm từ tiếng Việt trong .docx (ví dụ ADR-0022)"
    )
    parser.add_argument("docx_path", type=Path)
    args = parser.parse_args()

    report = count_vietnamese_words(args.docx_path)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
