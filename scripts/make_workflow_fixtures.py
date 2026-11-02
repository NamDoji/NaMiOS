"""Sinh fixture 3 workflow mẫu cho Gói 1 (M0, P0 — GIAO-VIEC-M0-M2.md):

  A_docx  — viết DOCX tiếng Việt có dấu -> gửi tệp -> (mô phỏng) in.
  B_xlsx  — mở XLSX -> tính bằng công thức thật -> lưu -> đối chiếu giá trị.
  C_misa  — KHÔNG có MISA thật: mock dataset kế toán (danh mục + chứng từ)
            + báo cáo tổng hợp/chi tiết tự tính bằng Python/Decimal.

NGUYÊN TẮC (bắt buộc, xem CLAUDE.md + docs/specs/GIAO-VIEC-M0-M2.md Gói 1):
  - Toàn bộ nội dung văn bản/số liệu trong file này là TỰ SOẠN cho mục đích
    test kỹ thuật (rights-clean) — KHÔNG copy tài liệu có bản quyền, KHÔNG
    chứa dữ liệu thật/bí mật/secret.
  - Mọi "expected value" đều được TÍNH LẠI BẰNG PYTHON ngay trong script này
    (không nhớ/chép từ Excel hay MISA thật) — giám khảo đọc code là đọc được
    cách suy ra, và có thể re-run để kiểm tra lại.
  - Workflow B dùng Decimal cho mọi phép tính tiền tệ + khai báo rõ quy tắc
    làm tròn (ROUND half-away-from-zero kiểu Excel ROUND(), KHÁC round()
    mặc định của Python là round-half-to-even/banker's rounding).
  - Workflow C không có MISA/SQL Server thật => README.md trong C_misa ghi
    rõ "test MISA thật = BLOCKED" (theo CLAUDE.md: không giả lập để báo đạt).
  - File DOCX/XLSX được đọc lại ngay sau khi sinh (python-docx / openpyxl)
    để xác nhận mở lại được — KHÔNG tuyên bố "đã test trên Office/Excel/Word
    thật" vì môi trường build này không có Office thật.

Chạy:
    /home/node/.openclaw/workspace/code_projects/namios/.venv/bin/python \
        scripts/make_workflow_fixtures.py

Phụ thuộc (cài trong .venv riêng của agent fixtures, KHÔNG phải dependency
production của package `namios`): python-docx, openpyxl.
"""

from __future__ import annotations

import csv
import json
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from docx import Document
import openpyxl
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = ROOT / "fixtures" / "workflows"


def _nfc(text: str) -> str:
    """Trả về `text` sau khi khẳng định nó đã ở dạng NFC (giữ dấu tiếng
    Việt nguyên vẹn khi round-trip DOCX/CSV). Raise nếu không phải NFC —
    tức có lỗi soạn nội dung (decomposed Unicode lẫn vào)."""
    normalized = unicodedata.normalize("NFC", text)
    if normalized != text:
        raise ValueError(f"Chuỗi không ở dạng NFC: {text!r}")
    return text


def _vn_thousands(value: Decimal) -> str:
    """Định dạng số nguyên VND theo kiểu người Việt: dấu chấm phân nghìn,
    không có phần lẻ (VND không có hào/xu trong các fixture này)."""
    q = value.quantize(Decimal("1"))
    sign = "-" if q < 0 else ""
    digits = str(abs(int(q)))
    groups = []
    while digits:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    return sign + ".".join(groups)


def _vn_decimal_two(value: Decimal) -> str:
    """Định dạng số có 2 chữ số lẻ theo locale vi-VN: chấm phân nghìn,
    phẩy phân thập phân — dùng cho case CSV-locale (B_xlsx)."""
    q = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    sign = "-" if q < 0 else ""
    q = abs(q)
    int_part = int(q)
    frac_part = int((q - int_part) * 100)
    return f"{sign}{_vn_thousands(Decimal(int_part))},{frac_part:02d}"


def round_vnd_to_thousand(raw: Decimal) -> Decimal:
    """Quy tắc làm tròn tiền VNĐ dùng trong workflow B: làm tròn đến NGHÌN
    đồng gần nhất, theo kiểu Excel ROUND(x, -3) = round-half-AWAY-FROM-ZERO
    (0.5 nghìn luôn làm tròn LÊN theo giá trị tuyệt đối), KHÔNG phải
    round-half-to-even (banker's rounding) là mặc định của hàm round() hay
    Decimal quantize mặc định của Python."""
    return (raw / Decimal(1000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal(1000)


# ---------------------------------------------------------------------------
# Workflow A — DOCX tiếng Việt có dấu
# ---------------------------------------------------------------------------


def build_workflow_a() -> dict[str, Any]:
    out_dir = WORKFLOWS_DIR / "A_docx"
    out_dir.mkdir(parents=True, exist_ok=True)
    docx_path = out_dir / "baocao-tieng-viet.docx"

    heading_text = _nfc("Báo cáo công việc tuần — Dự án NaMiOS")
    intro_text = _nfc(
        "Báo cáo này tổng hợp công việc đã hoàn thành trong tuần, dùng để "
        "kiểm tra khả năng đọc lại văn bản tiếng Việt có dấu, danh sách và "
        "bảng biểu khi mở bằng các công cụ xử lý văn bản khác nhau."
    )
    list_items = [
        _nfc(
            "Khảo sát ứng dụng Word, Excel, Zalo PC và MISA SME theo yêu "
            "cầu khảo sát ưu tiên của Gói 1."
        ),
        _nfc(
            "Soạn fixture DOCX, XLSX và dữ liệu kế toán mẫu để kiểm tra "
            "round-trip đọc/ghi."
        ),
        _nfc(
            "Đối chiếu giá trị công thức tính bằng Python/Decimal cho phần "
            "liên quan tiền tệ."
        ),
        _nfc(
            "Ghi nhận trạng thái chưa khảo sát (unknown) cho các ứng dụng "
            "chưa có dữ liệu thật từ chủ dự án."
        ),
    ]
    pre_table_text = _nfc("Bảng theo dõi tiến độ công việc trong tuần:")
    table_header = [_nfc(h) for h in ["STT", "Công việc", "Người thực hiện", "Trạng thái"]]
    table_rows = [
        [_nfc(v) for v in row]
        for row in [
            ["1", "Khảo sát ứng dụng ưu tiên", "Đội khảo sát", "Đã ghi nhận"],
            ["2", "Soạn fixture DOCX/XLSX", "Đội kỹ thuật", "Hoàn thành"],
            ["3", "Đối chiếu công thức bằng Python", "Đội kỹ thuật", "Hoàn thành"],
        ]
    ]
    closing_text = _nfc(
        "Người lập báo cáo: Đội kỹ thuật NaMiOS — Ngày 02/11/2026."
    )

    doc = Document()
    doc.add_heading(heading_text, level=1)
    doc.add_paragraph(intro_text)
    for item in list_items:
        doc.add_paragraph(item, style="List Bullet")
    doc.add_paragraph(pre_table_text)
    table = doc.add_table(rows=1 + len(table_rows), cols=len(table_header))
    table.style = "Table Grid"
    for col_idx, header_text in enumerate(table_header):
        table.cell(0, col_idx).text = header_text
    for row_idx, row_values in enumerate(table_rows, start=1):
        for col_idx, cell_value in enumerate(row_values):
            table.cell(row_idx, col_idx).text = cell_value
    doc.add_paragraph(closing_text)

    # Đếm từ đối tượng Document trước khi save — số này là "expected" dùng
    # để đối chiếu sau khi mở lại file đã lưu.
    paragraph_texts = [p.text for p in doc.paragraphs]
    heading_count = sum(1 for p in doc.paragraphs if p.style.name.startswith("Heading"))
    list_item_count = sum(1 for p in doc.paragraphs if p.style.name.startswith("List"))
    table_count = len(doc.tables)
    table_dims = [(len(t.rows), len(t.columns)) for t in doc.tables]

    doc.save(docx_path)

    # Round-trip verify ngay (python-docx, KHÔNG phải Office/Word thật).
    reopened = Document(docx_path)
    reopened_texts = [p.text for p in reopened.paragraphs]
    reopened_heading_count = sum(
        1 for p in reopened.paragraphs if p.style.name.startswith("Heading")
    )
    reopened_list_count = sum(
        1 for p in reopened.paragraphs if p.style.name.startswith("List")
    )
    reopened_table_dims = [(len(t.rows), len(t.columns)) for t in reopened.tables]
    reopened_table_cells = [
        [[cell.text for cell in row.cells] for row in t.rows] for t in reopened.tables
    ]

    assert reopened_texts == paragraph_texts, "Paragraph text lệch sau round-trip DOCX"
    assert reopened_heading_count == heading_count == 1
    assert reopened_list_count == list_item_count == len(list_items)
    assert reopened_table_dims == table_dims == [(1 + len(table_rows), len(table_header))]
    for text in paragraph_texts:
        _nfc(text)  # raise nếu lệch NFC sau round-trip
    expected_table_cells = [table_header] + table_rows
    assert reopened_table_cells == [expected_table_cells]

    expected_md_lines = [
        "# Expected round-trip — A_docx/baocao-tieng-viet.docx",
        "",
        "Tự sinh bởi `scripts/make_workflow_fixtures.py` — các số dưới đây "
        "được **tính từ chính đối tượng `docx.Document` trước khi lưu file**, "
        "sau đó script đã mở lại file vừa lưu (python-docx) và so khớp "
        "(assert) — KHÔNG phải test trên Microsoft Word thật (không có "
        "trong môi trường build này).",
        "",
        f"- Tổng số paragraph cấp đỉnh (`doc.paragraphs`, không tính cell trong bảng): **{len(paragraph_texts)}**",
        f"- Số heading (style bắt đầu bằng `Heading`): **{heading_count}**",
        f"- Số đoạn danh sách (style bắt đầu bằng `List`): **{list_item_count}**",
        f"- Số bảng: **{table_count}**",
        f"- Kích thước bảng (rows x cols): **{table_dims[0][0]} x {table_dims[0][1]}** "
        f"({1} header row + {len(table_rows)} data rows)",
        "- Toàn bộ text tiếng Việt đã được khẳng định ở dạng NFC "
        "(`unicodedata.normalize('NFC', text) == text`) cả trước khi lưu và "
        "sau khi mở lại — không bị tách dấu (decomposed) qua round-trip.",
        "",
        "## Nội dung từng paragraph cấp đỉnh (theo thứ tự)",
        "",
    ]
    for idx, text in enumerate(paragraph_texts, start=1):
        expected_md_lines.append(f"{idx}. {text}")
    expected_md_lines += [
        "",
        "## Nội dung bảng (expected, bao gồm header)",
        "",
        "| " + " | ".join(table_header) + " |",
        "| " + " | ".join("---" for _ in table_header) + " |",
    ]
    for row in table_rows:
        expected_md_lines.append("| " + " | ".join(row) + " |")
    expected_md_lines += [
        "",
        "## Giới hạn",
        "",
        "- Chỉ xác minh round-trip bằng `python-docx`. KHÔNG có Microsoft "
        "Word/LibreOffice thật trong môi trường build này nên KHÔNG tuyên "
        "bố đã test mở/in bằng Word/LibreOffice thật hay máy in thật "
        "(DEV-002). Bước \"in\" của workflow A vẫn `not_run`/`unknown` cho "
        "tới khi có máy in + driver + người xác nhận theo DEV-001/002.",
    ]
    (out_dir / "expected.md").write_text("\n".join(expected_md_lines) + "\n", encoding="utf-8")

    return {
        "docx_path": str(docx_path.relative_to(ROOT)),
        "paragraph_count": len(paragraph_texts),
        "heading_count": heading_count,
        "list_item_count": list_item_count,
        "table_count": table_count,
        "table_dims": table_dims,
    }


# ---------------------------------------------------------------------------
# Workflow B — XLSX với công thức thật + expected tự tính bằng Python
# ---------------------------------------------------------------------------


@dataclass
class _Item:
    stt: int
    ma_hang: str
    ten_hang: str
    so_luong: int
    don_gia_vnd: Decimal
    ngay_mua: date


def build_workflow_b() -> dict[str, Any]:
    out_dir = WORKFLOWS_DIR / "B_xlsx"
    out_dir.mkdir(parents=True, exist_ok=True)
    xlsx_path = out_dir / "bangtinh.xlsx"
    csv_path = out_dir / "bangtinh-vi-VN.csv"
    expected_path = out_dir / "expected.json"

    items = [
        _Item(1, "MH01", _nfc("Bàn làm việc gỗ công nghiệp"), 5, Decimal("1250000"), date(2026, 1, 15)),
        _Item(2, "MH02", _nfc("Ghế xoay văn phòng"), 10, Decimal("1020625"), date(2026, 2, 20)),
        _Item(3, "MH03", _nfc("Màn hình 24 inch"), 8, Decimal("3200000"), date(2026, 3, 5)),
        _Item(4, "MH04", _nfc("Bàn phím cơ"), 15, Decimal("620000"), date(2026, 4, 18)),
        _Item(5, "MH05", _nfc("Ổ cứng SSD 500GB"), 20, Decimal("950000"), date(2026, 5, 22)),
    ]
    warranty_days = 365
    vat_rate = Decimal("0.08")

    wb = openpyxl.Workbook()
    ws_price = wb.active
    ws_price.title = "BangGia"
    ws_price.append(["MaHang", "GiaThamKhao"])
    for it in items:
        # Giá tham khảo đặt bằng đúng DonGiaVND để VLOOKUP/XLOOKUP dùng làm
        # đối chiếu chéo giá bán (nếu chủ dự án sau này đổi giá tham khảo
        # khác DonGiaVND, expected.json phải tính lại theo giá trị MỚI).
        ws_price.append([it.ma_hang, int(it.don_gia_vnd)])
    price_last_row = 1 + len(items)

    ws = wb.create_sheet("BangTinh")
    header = [
        "STT", "MaHang", "TenHang", "SoLuong", "DonGiaVND", "ThanhTien",
        "VAT8Pct", "TongThanhToan", "NgayMua", "NgayHetBaoHanh", "XepLoai",
        "GiaTraCuuVLOOKUP", "GiaTraCuuXLOOKUP",
    ]
    ws.append(header)
    col = {name: get_column_letter(i + 1) for i, name in enumerate(header)}

    for it in items:
        r = it.stt + 1  # header ở row 1
        ws.append([
            it.stt,
            it.ma_hang,
            it.ten_hang,
            it.so_luong,
            int(it.don_gia_vnd),
            f"={col['SoLuong']}{r}*{col['DonGiaVND']}{r}",
            f"=ROUND({col['ThanhTien']}{r}*{float(vat_rate)},-3)",
            f"={col['ThanhTien']}{r}+{col['VAT8Pct']}{r}",
            it.ngay_mua,
            f"={col['NgayMua']}{r}+{warranty_days}",
            f'=IF({col["SoLuong"]}{r}>=10,"Số lượng lớn","Số lượng nhỏ")',
            f"=VLOOKUP({col['MaHang']}{r},BangGia!$A$2:$B${price_last_row},2,FALSE)",
            f"=XLOOKUP({col['MaHang']}{r},BangGia!$A$2:$A${price_last_row},BangGia!$B$2:$B${price_last_row})",
        ])

    last_data_row = 1 + len(items)
    summary_row = last_data_row + 1
    avg_row = summary_row + 1
    ws.cell(row=summary_row, column=1, value=_nfc("Tổng cộng"))
    ws[f"{col['ThanhTien']}{summary_row}"] = f"=SUM({col['ThanhTien']}2:{col['ThanhTien']}{last_data_row})"
    ws[f"{col['VAT8Pct']}{summary_row}"] = f"=SUM({col['VAT8Pct']}2:{col['VAT8Pct']}{last_data_row})"
    ws[f"{col['TongThanhToan']}{summary_row}"] = f"=SUM({col['TongThanhToan']}2:{col['TongThanhToan']}{last_data_row})"
    ws.cell(row=avg_row, column=1, value=_nfc("Đơn giá trung bình"))
    ws[f"{col['DonGiaVND']}{avg_row}"] = f"=AVERAGE({col['DonGiaVND']}2:{col['DonGiaVND']}{last_data_row})"

    for sheet in (ws_price, ws):
        for column_cells in sheet.columns:
            width = max(len(str(c.value)) if c.value is not None else 0 for c in column_cells)
            sheet.column_dimensions[get_column_letter(column_cells[0].column)].width = min(max(width + 2, 10), 32)

    wb.save(xlsx_path)

    # Round-trip verify ngay: đọc lại formula text (openpyxl, KHÔNG có
    # Excel thật ở môi trường build này nên KHÔNG có giá trị cached).
    reopened = openpyxl.load_workbook(xlsx_path, data_only=False)
    rws = reopened["BangTinh"]
    formulas_by_cell: dict[str, str] = {}
    for it in items:
        r = it.stt + 1
        for field in ("ThanhTien", "VAT8Pct", "TongThanhToan", "NgayHetBaoHanh", "XepLoai", "GiaTraCuuVLOOKUP", "GiaTraCuuXLOOKUP"):
            cell_ref = f"{col[field]}{r}"
            written = ws[cell_ref].value
            read_back = rws[cell_ref].value
            assert read_back == written, f"Formula lệch sau round-trip tại {cell_ref}: {read_back!r} != {written!r}"
            formulas_by_cell[cell_ref] = read_back
    for cell_ref in (
        f"{col['ThanhTien']}{summary_row}", f"{col['VAT8Pct']}{summary_row}",
        f"{col['TongThanhToan']}{summary_row}", f"{col['DonGiaVND']}{avg_row}",
    ):
        formulas_by_cell[cell_ref] = rws[cell_ref].value

    # ---- Expected values tự tính bằng Python/Decimal (KHÔNG từ Excel) ----
    rows_expected = []
    thanh_tien_list: list[Decimal] = []
    vat_list: list[Decimal] = []
    tong_list: list[Decimal] = []
    for it in items:
        r = it.stt + 1
        thanh_tien = Decimal(it.so_luong) * it.don_gia_vnd
        vat_raw = thanh_tien * vat_rate
        vat_rounded = round_vnd_to_thousand(vat_raw)
        tong = thanh_tien + vat_rounded
        ngay_het = it.ngay_mua + timedelta(days=warranty_days)
        xep_loai = _nfc("Số lượng lớn") if it.so_luong >= 10 else _nfc("Số lượng nhỏ")
        gia_tra_cuu = it.don_gia_vnd  # BangGia.GiaThamKhao == DonGiaVND theo thiết kế fixture

        thanh_tien_list.append(thanh_tien)
        vat_list.append(vat_rounded)
        tong_list.append(tong)

        rows_expected.append({
            "stt": it.stt,
            "ma_hang": it.ma_hang,
            "so_luong": it.so_luong,
            "don_gia_vnd": str(it.don_gia_vnd),
            "cells": {
                f"{col['ThanhTien']}{r}": {
                    "formula": formulas_by_cell[f"{col['ThanhTien']}{r}"],
                    "expected_value": str(thanh_tien),
                    "calc": "SoLuong * DonGiaVND",
                },
                f"{col['VAT8Pct']}{r}": {
                    "formula": formulas_by_cell[f"{col['VAT8Pct']}{r}"],
                    "expected_value": str(vat_rounded),
                    "calc": "ROUND(ThanhTien * 8%, -3) — làm tròn đến nghìn VNĐ, "
                    "round-half-away-from-zero kiểu Excel ROUND() "
                    f"(giá trị chưa làm tròn: {vat_raw})",
                },
                f"{col['TongThanhToan']}{r}": {
                    "formula": formulas_by_cell[f"{col['TongThanhToan']}{r}"],
                    "expected_value": str(tong),
                    "calc": "ThanhTien + VAT8Pct",
                },
                f"{col['NgayHetBaoHanh']}{r}": {
                    "formula": formulas_by_cell[f"{col['NgayHetBaoHanh']}{r}"],
                    "expected_value": ngay_het.isoformat(),
                    "calc": f"NgayMua + {warranty_days} ngày (tính bằng datetime.date + timedelta trong Python)",
                },
                f"{col['XepLoai']}{r}": {
                    "formula": formulas_by_cell[f"{col['XepLoai']}{r}"],
                    "expected_value": xep_loai,
                    "calc": "IF(SoLuong >= 10, \"Số lượng lớn\", \"Số lượng nhỏ\")",
                },
                f"{col['GiaTraCuuVLOOKUP']}{r}": {
                    "formula": formulas_by_cell[f"{col['GiaTraCuuVLOOKUP']}{r}"],
                    "expected_value": str(gia_tra_cuu),
                    "calc": "VLOOKUP(MaHang, BangGia!A:B, 2, FALSE) — tra GiaThamKhao, "
                    "fixture đặt GiaThamKhao = DonGiaVND nên expected = DonGiaVND",
                },
                f"{col['GiaTraCuuXLOOKUP']}{r}": {
                    "formula": formulas_by_cell[f"{col['GiaTraCuuXLOOKUP']}{r}"],
                    "expected_value": str(gia_tra_cuu),
                    "calc": "XLOOKUP tương đương VLOOKUP ở trên",
                },
            },
        })

    sum_thanh_tien = sum(thanh_tien_list, Decimal(0))
    sum_vat = sum(vat_list, Decimal(0))
    sum_tong = sum(tong_list, Decimal(0))
    avg_don_gia = sum((it.don_gia_vnd for it in items), Decimal(0)) / Decimal(len(items))

    assert sum_thanh_tien + sum_vat == sum_tong

    summary_expected = {
        f"{col['ThanhTien']}{summary_row}": {
            "formula": formulas_by_cell[f"{col['ThanhTien']}{summary_row}"],
            "expected_value": str(sum_thanh_tien),
            "calc": "SUM(ThanhTien của 5 dòng)",
        },
        f"{col['VAT8Pct']}{summary_row}": {
            "formula": formulas_by_cell[f"{col['VAT8Pct']}{summary_row}"],
            "expected_value": str(sum_vat),
            "calc": "SUM(VAT8Pct đã làm tròn của 5 dòng)",
        },
        f"{col['TongThanhToan']}{summary_row}": {
            "formula": formulas_by_cell[f"{col['TongThanhToan']}{summary_row}"],
            "expected_value": str(sum_tong),
            "calc": "SUM(TongThanhToan của 5 dòng) == ThanhTien tổng + VAT tổng",
        },
        f"{col['DonGiaVND']}{avg_row}": {
            "formula": formulas_by_cell[f"{col['DonGiaVND']}{avg_row}"],
            "expected_value": str(avg_don_gia),
            "expected_value_float": float(avg_don_gia),
            "calc": "AVERAGE(DonGiaVND của 5 dòng) = tổng / 5 — so khớp với "
            "tolerance float vì AVERAGE trong Excel trả về số thực IEEE-754",
        },
    }

    # ---- CSV-locale case: xuất lại ThanhTien theo locale vi-VN ----
    # Mô phỏng CSV xuất từ Excel với locale vi-VN: dấu phẩy chấm phẩy làm
    # delimiter, dấu chấm phân nghìn, dấu phẩy phân thập phân — khác hẳn
    # CSV locale en-US (dấu phẩy delimiter, dấu chấm phân thập phân).
    csv_rows = []
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        header_csv = ["STT", "MaHang", "TenHang", "SoLuong", "DonGiaVND", "ThanhTien"]
        writer.writerow(header_csv)
        for it, thanh_tien in zip(items, thanh_tien_list):
            row = [
                str(it.stt), it.ma_hang, it.ten_hang, str(it.so_luong),
                _vn_decimal_two(it.don_gia_vnd), _vn_decimal_two(thanh_tien),
            ]
            writer.writerow(row)
            csv_rows.append(row)
        total_row = ["", "", _nfc("Tổng cộng"), "", "", _vn_decimal_two(sum_thanh_tien)]
        writer.writerow(total_row)
        csv_rows.append(total_row)

    def _parse_vn_decimal(text: str) -> Decimal:
        """Parser tham chiếu cho case CSV-locale vi-VN: bỏ dấu chấm phân
        nghìn, đổi dấu phẩy phân thập phân thành dấu chấm, rồi parse
        Decimal. Dùng để kiểm tra giám khảo đọc lại đúng giá trị."""
        cleaned = text.replace(".", "").replace(",", ".")
        return Decimal(cleaned)

    locale_check = []
    for it, thanh_tien in zip(items, thanh_tien_list):
        formatted = _vn_decimal_two(thanh_tien)
        parsed_back = _parse_vn_decimal(formatted)
        assert parsed_back == thanh_tien.quantize(Decimal("0.01")), (
            f"CSV-locale round-trip lệch cho {it.ma_hang}: {parsed_back} != {thanh_tien}"
        )
        locale_check.append({
            "ma_hang": it.ma_hang,
            "csv_text_vi_VN": formatted,
            "expected_parsed_decimal": str(thanh_tien.quantize(Decimal("0.01"))),
        })

    expected_payload = {
        "schema_note": "Mọi expected_value trong file này được TÍNH BẰNG PYTHON "
        "(Decimal/datetime) trong scripts/make_workflow_fixtures.py — KHÔNG lấy "
        "từ cache công thức Excel (môi trường build không có Excel thật nên "
        "openpyxl không có giá trị cached; chỉ formula text được ghi/đọc lại).",
        "workbook": "bangtinh.xlsx",
        "lookup_sheet": "BangGia",
        "rounding_rule": {
            "currency": "ROUND(x, -3) kiểu Excel = làm tròn đến nghìn VNĐ gần "
            "nhất, round-half-AWAY-FROM-ZERO (Decimal ROUND_HALF_UP trong "
            "Python) — KHÁC round-half-to-even (banker's rounding) là mặc "
            "định của round()/Decimal.quantize mặc định.",
            "example": "816500 (nửa nghìn) -> 817000, KHÔNG phải 816000.",
        },
        "tolerance": {
            "integer_vnd_fields": "So khớp CHÍNH XÁC (Decimal, không sai 1 đồng).",
            "float_fields": "AVERAGE trả số thực IEEE-754 — tolerance tuyệt đối 1e-6.",
            "date_fields": "So khớp CHÍNH XÁC chuỗi ISO 8601 (YYYY-MM-DD).",
        },
        "rows": rows_expected,
        "summary": summary_expected,
        "csv_locale_case": {
            "file": "bangtinh-vi-VN.csv",
            "delimiter": ";",
            "decimal_separator": ",",
            "thousands_separator": ".",
            "note": "Mô phỏng CSV Excel xuất ra dưới locale vi-VN — khác CSV "
            "en-US (delimiter ',', decimal '.'). Parser tham chiếu: bỏ '.' rồi "
            "đổi ',' thành '.'.",
            "rows": locale_check,
        },
    }
    expected_path.write_text(
        json.dumps(expected_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    return {
        "xlsx_path": str(xlsx_path.relative_to(ROOT)),
        "csv_path": str(csv_path.relative_to(ROOT)),
        "expected_path": str(expected_path.relative_to(ROOT)),
        "formula_cells_verified": len(formulas_by_cell),
        "sum_thanh_tien": str(sum_thanh_tien),
        "sum_vat": str(sum_vat),
        "sum_tong_thanh_toan": str(sum_tong),
    }


# ---------------------------------------------------------------------------
# Workflow C — mock dataset kế toán (KHÔNG có MISA thật)
# ---------------------------------------------------------------------------


@dataclass
class _Voucher:
    so_ct: str
    ngay_ct: date
    dien_giai: str
    tk_no: str
    tk_co: str
    so_tien: Decimal


def build_workflow_c() -> dict[str, Any]:
    out_dir = WORKFLOWS_DIR / "C_misa"
    out_dir.mkdir(parents=True, exist_ok=True)
    accounts_path = out_dir / "danhmuc-taikhoan.csv"
    vouchers_path = out_dir / "chungtu.csv"
    report_path = out_dir / "expected-report.md"
    readme_path = out_dir / "README.md"

    accounts = [
        ("111", _nfc("Tiền mặt")),
        ("112", _nfc("Tiền gửi ngân hàng")),
        ("131", _nfc("Phải thu của khách hàng")),
        ("156", _nfc("Hàng hóa")),
        ("331", _nfc("Phải trả cho người bán")),
        ("511", _nfc("Doanh thu bán hàng và cung cấp dịch vụ")),
        ("632", _nfc("Giá vốn hàng bán")),
        ("642", _nfc("Chi phí quản lý kinh doanh")),
    ]

    vouchers = [
        _Voucher("PC001", date(2026, 10, 1), _nfc("Rút tiền gửi ngân hàng về quỹ tiền mặt"), "111", "112", Decimal("20000000")),
        _Voucher("PT001", date(2026, 10, 3), _nfc("Thu tiền khách hàng A thanh toán công nợ"), "112", "131", Decimal("15000000")),
        _Voucher("HD001", date(2026, 10, 5), _nfc("Bán hàng hóa cho khách hàng B, chưa thu tiền"), "131", "511", Decimal("25000000")),
        _Voucher("GV001", date(2026, 10, 5), _nfc("Ghi nhận giá vốn hàng bán theo hóa đơn HD001"), "632", "156", Decimal("18000000")),
        _Voucher("PNK001", date(2026, 10, 8), _nfc("Nhập hàng hóa từ nhà cung cấp C, chưa trả tiền"), "156", "331", Decimal("22000000")),
        _Voucher("PC002", date(2026, 10, 12), _nfc("Trả tiền cho nhà cung cấp C"), "331", "111", Decimal("10000000")),
        _Voucher("PC003", date(2026, 10, 20), _nfc("Chi phí quản lý văn phòng tháng 10"), "642", "111", Decimal("4500000")),
        _Voucher("PT002", date(2026, 10, 25), _nfc("Thu tiền khách hàng B thanh toán một phần"), "111", "131", Decimal("12000000")),
    ]

    with accounts_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["MaTaiKhoan", "TenTaiKhoan"])
        for code, name in accounts:
            writer.writerow([code, name])

    with vouchers_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["SoCT", "NgayCT", "DienGiai", "TKNo", "TKCo", "SoTien"])
        for v in vouchers:
            writer.writerow([v.so_ct, v.ngay_ct.isoformat(), v.dien_giai, v.tk_no, v.tk_co, str(v.so_tien)])

    account_names = dict(accounts)
    account_codes = [c for c, _ in accounts]

    # ---- Tổng hợp (trial balance) theo Nợ/Có từng tài khoản — Decimal ----
    no_sum: dict[str, Decimal] = {c: Decimal(0) for c in account_codes}
    co_sum: dict[str, Decimal] = {c: Decimal(0) for c in account_codes}
    for v in vouchers:
        no_sum[v.tk_no] += v.so_tien
        co_sum[v.tk_co] += v.so_tien

    total_no = sum(no_sum.values(), Decimal(0))
    total_co = sum(co_sum.values(), Decimal(0))
    total_vouchers = sum((v.so_tien for v in vouchers), Decimal(0))
    assert total_no == total_co == total_vouchers, (
        "Bảng cân đối không khớp — mỗi chứng từ phải xuất hiện đúng 1 lần ở "
        f"cột Nợ và 1 lần ở cột Có: {total_no=} {total_co=} {total_vouchers=}"
    )

    # ---- Chi tiết theo tài khoản (sổ cái rút gọn) ----
    detail_by_account: dict[str, list[dict[str, str]]] = {c: [] for c in account_codes}
    for v in vouchers:
        detail_by_account[v.tk_no].append({
            "so_ct": v.so_ct, "ngay_ct": v.ngay_ct.isoformat(), "dien_giai": v.dien_giai,
            "vai_tro": "Nợ", "doi_ung": v.tk_co, "so_tien": str(v.so_tien),
        })
        detail_by_account[v.tk_co].append({
            "so_ct": v.so_ct, "ngay_ct": v.ngay_ct.isoformat(), "dien_giai": v.dien_giai,
            "vai_tro": "Có", "doi_ung": v.tk_no, "so_tien": str(v.so_tien),
        })

    lines = [
        "# Expected report — C_misa (mock dataset, KHÔNG phải MISA thật)",
        "",
        "Tự sinh bởi `scripts/make_workflow_fixtures.py`. Toàn bộ số liệu dưới "
        "đây được TÍNH TRONG PYTHON bằng `Decimal` từ dữ liệu chứng từ tự soạn "
        "ở `chungtu.csv` — KHÔNG lấy từ phần mềm MISA/SQL Server thật (không "
        "có trong môi trường build này — xem `README.md` cùng thư mục).",
        "",
        "## Danh mục tài khoản",
        "",
        "| Mã TK | Tên tài khoản |",
        "| --- | --- |",
    ]
    for code, name in accounts:
        lines.append(f"| {code} | {name} |")

    lines += [
        "",
        "## Danh sách chứng từ (`chungtu.csv`)",
        "",
        "| Số CT | Ngày CT | Diễn giải | TK Nợ | TK Có | Số tiền (VNĐ) |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for v in vouchers:
        lines.append(
            f"| {v.so_ct} | {v.ngay_ct.isoformat()} | {v.dien_giai} | {v.tk_no} | "
            f"{v.tk_co} | {_vn_thousands(v.so_tien)} |"
        )

    lines += [
        "",
        "## Bảng tổng hợp (trial balance) theo tài khoản — expected",
        "",
        "Công thức: với mỗi tài khoản, `Nợ` = tổng `SoTien` các chứng từ có "
        "`TKNo` = tài khoản đó; `Có` = tổng `SoTien` các chứng từ có `TKCo` = "
        "tài khoản đó.",
        "",
        "| Mã TK | Tên tài khoản | Tổng Nợ (VNĐ) | Tổng Có (VNĐ) |",
        "| --- | --- | --- | --- |",
    ]
    for code, name in accounts:
        lines.append(f"| {code} | {name} | {_vn_thousands(no_sum[code])} | {_vn_thousands(co_sum[code])} |")
    lines += [
        f"| **Tổng** |  | **{_vn_thousands(total_no)}** | **{_vn_thousands(total_co)}** |",
        "",
        f"Kiểm tra bất biến: Tổng Nợ = Tổng Có = Tổng số tiền tất cả chứng từ "
        f"= **{_vn_thousands(total_vouchers)}** VNĐ (mỗi chứng từ ghi đúng 1 lần ở "
        "cột Nợ và 1 lần ở cột Có trên hai tài khoản khác nhau — bất biến "
        "của hạch toán kép, được `assert` trong script sinh fixture).",
        "",
        "## Bảng chi tiết (sổ cái rút gọn) theo từng tài khoản — expected",
        "",
    ]
    for code, name in accounts:
        lines.append(f"### TK {code} — {name}")
        lines.append("")
        lines.append("| Số CT | Ngày CT | Diễn giải | Vai trò | Đối ứng | Số tiền (VNĐ) |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for d in detail_by_account[code]:
            lines.append(
                f"| {d['so_ct']} | {d['ngay_ct']} | {d['dien_giai']} | {d['vai_tro']} | "
                f"{d['doi_ung']} | {_vn_thousands(Decimal(d['so_tien']))} |"
            )
        lines.append("")

    lines += [
        "## Ghi chú số liệu",
        "",
        "- Tất cả số tiền là VNĐ nguyên (không có phần lẻ hào/xu) nên không "
        "cần quy tắc làm tròn khi tổng hợp — phép `+` Decimal chính xác tuyệt "
        "đối, không có sai số float.",
        "- Dataset chỉ có 8 chứng từ, tự soạn cho mục đích test kỹ thuật — "
        "KHÔNG phải số liệu doanh nghiệp thật.",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    readme_text = f"""# C_misa — mock dataset kế toán (KHÔNG có MISA thật)

**Trạng thái: test MISA SME thật = BLOCKED** tại môi trường build này (xem
`CLAUDE.md`, `docs/specs/GIAO-VIEC-M0-M2.md` Gói 1/Gói 3). Thư mục này KHÔNG
chứa và KHÔNG mô phỏng MISA SME/AMIS. Lý do blocked:

- Không có bản MISA SME có quyền dùng (license) để cài/kích hoạt.
- Không có SQL Server + máy Windows lab hợp lệ (MISA SME chọn SQL Server
  theo phiên bản Windows — xem đặc tả §4.1/§6.4 và nguồn [3] trong
  `docs/specs/GIAO-VIEC-M0-M2.md`).
- Không có kế toán viên QA để đối chiếu kết quả theo quy trình thật
  (OWNERSHIP-AND-SURVEY.md Phần C, MIG-001).

## Thay vào đó, thư mục này chứa gì

Một **dataset kế toán giả tự soạn** (danh mục tài khoản + chứng từ), đủ để
luyện/kiểm tra logic **tổng hợp (trial balance) và chi tiết (sổ cái rút
gọn)** bằng Python/Decimal — KHÔNG đụng tới phần mềm MISA:

- `danhmuc-taikhoan.csv` — 8 tài khoản mẫu (111, 112, 131, 156, 331, 511,
  632, 642), tên tự soạn theo hệ thống tài khoản kế toán Việt Nam phổ biến
  (không copy từ tài liệu MISA có bản quyền).
- `chungtu.csv` — 8 chứng từ hạch toán kép tự soạn (rút tiền, thu/chi,
  bán hàng, giá vốn, nhập hàng, trả nợ, chi phí).
- `expected-report.md` — báo cáo tổng hợp + chi tiết **tự tính bằng
  Python/Decimal** từ đúng 8 chứng từ trên, kèm bất biến kiểm tra chéo
  (Tổng Nợ = Tổng Có = Tổng số tiền chứng từ).

## Khi có MISA thật để test (M2/M4, sau khi được cấp quyền)

Theo Gói 3 (GIAO-VIEC-M0-M2.md): cần đúng build MISA SME theo năm, SQL
Server trên máy Windows lab hợp lệ, dữ liệu kế toán giả (có thể dùng lại
dataset ở đây làm input nhập tay/import), và kế toán viên đối chiếu kết quả
xuất ra từ MISA với `expected-report.md` này. Bộ test MISA thật tối thiểu
gồm: kết nối DB, nhập chứng từ, xuất báo cáo tổng hợp/chi tiết, in, backup
và restore — KHÔNG được báo `task_verified` nếu thiếu QA kế toán ký.
"""
    readme_path.write_text(readme_text, encoding="utf-8")

    return {
        "accounts_path": str(accounts_path.relative_to(ROOT)),
        "vouchers_path": str(vouchers_path.relative_to(ROOT)),
        "report_path": str(report_path.relative_to(ROOT)),
        "readme_path": str(readme_path.relative_to(ROOT)),
        "voucher_count": len(vouchers),
        "total_no": str(total_no),
        "total_co": str(total_co),
    }


# ---------------------------------------------------------------------------
# README tổng (fixtures/workflows/README.md)
# ---------------------------------------------------------------------------


def build_top_level_readme(summary: dict[str, Any]) -> None:
    text = f"""# fixtures/workflows — 3 workflow mẫu cho Gói 1 (M0, P0)

Sinh bởi `scripts/make_workflow_fixtures.py` (chạy lại được, idempotent —
overwrite đúng các file trong thư mục này). Mục đích: chứng minh công cụ
đo workflow trọn vẹn (viết tài liệu → tính toán → đối chiếu) chạy được tại
môi trường build hiện tại (Debian 12, không Office/MISA/Wine/máy in thật —
xem `CLAUDE.md`), TRƯỚC khi có dữ liệu khảo sát/license thật từ chủ dự án.

## Tái tạo

```
/home/node/.openclaw/workspace/code_projects/namios/.venv/bin/pip install -q python-docx openpyxl
/home/node/.openclaw/workspace/code_projects/namios/.venv/bin/python scripts/make_workflow_fixtures.py
```

Script tự verify ngay sau khi sinh (round-trip đọc lại bằng `python-docx` /
`openpyxl`, assert số liệu khớp) — thoát lỗi (`AssertionError`) nếu có sai
lệch, không im lặng bỏ qua.

## Nguồn gốc nội dung (rights-clean)

Toàn bộ văn bản, bảng biểu, số liệu, tên hàng hóa, tên tài khoản và chứng
từ trong ba workflow là **tự soạn** cho mục đích test kỹ thuật. KHÔNG copy
nội dung từ tài liệu có bản quyền (Microsoft, MISA, hay bất kỳ nguồn nào
khác). Không chứa secret, dữ liệu thật hoặc thông tin cá nhân.

## Nguyên tắc "expected tự tính"

Mọi giá trị `expected` (DOCX: số đoạn/heading/bảng; XLSX: kết quả công
thức; MISA mock: báo cáo tổng hợp/chi tiết) đều được **tính lại bằng
Python ngay trong `scripts/make_workflow_fixtures.py`** — không chép tay,
không dựa vào cache công thức Excel hay phần mềm MISA thật. Giám khảo có
thể đọc hàm tính tương ứng hoặc chạy lại script để kiểm tra độc lập.

## A_docx — viết DOCX tiếng Việt → gửi tệp → (mô phỏng) in

- `A_docx/baocao-tieng-viet.docx` — văn bản tiếng Việt có dấu (heading +
  đoạn văn + danh sách + 1 bảng {summary['a']['table_dims'][0][0]}x{summary['a']['table_dims'][0][1]}).
  Tổng {summary['a']['paragraph_count']} paragraph cấp đỉnh, {summary['a']['heading_count']} heading,
  {summary['a']['list_item_count']} đoạn danh sách.
- `A_docx/expected.md` — mô tả round-trip kỳ vọng (số đoạn, text NFC giữ
  nguyên, kích thước bảng) + giới hạn (chưa test Word/LibreOffice/máy in
  thật).

## B_xlsx — mở XLSX → tính bằng công thức thật → lưu → đối chiếu giá trị

- `B_xlsx/bangtinh.xlsx` — 2 sheet (`BangGia` tra cứu, `BangTinh` 5 dòng dữ
  liệu) với công thức thật: phép nhân, `SUM`, `AVERAGE`, `IF`, `VLOOKUP`,
  `XLOOKUP`, cộng ngày (`NgayMua + 365`), và `ROUND(x,-3)` làm tròn tiền
  VNĐ đến nghìn đồng gần nhất (round-half-away-from-zero).
- `B_xlsx/bangtinh-vi-VN.csv` — case CSV-locale vi-VN (delimiter `;`, dấu
  chấm phân nghìn, dấu phẩy phân thập phân), khác locale en-US.
- `B_xlsx/expected.json` — giá trị kỳ vọng từng ô công thức (tính bằng
  Python/Decimal/`datetime`), kèm tolerance cho field float (`AVERAGE`) và
  quy tắc làm tròn Decimal cho field tiền tệ, cộng case parse CSV-locale.

## C_misa — KHÔNG có MISA thật: mock dataset kế toán

- `C_misa/danhmuc-taikhoan.csv`, `C_misa/chungtu.csv` — dataset kế toán giả
  tự soạn ({summary['c']['voucher_count']} chứng từ, 8 tài khoản).
- `C_misa/expected-report.md` — báo cáo tổng hợp (trial balance Nợ/Có theo
  tài khoản) + chi tiết (sổ cái rút gọn), tính bằng Python/Decimal, có bất
  biến kiểm tra chéo Tổng Nợ = Tổng Có = Tổng số tiền chứng từ
  ({_vn_thousands(Decimal(summary['c']['total_no']))} VNĐ).
- `C_misa/README.md` — ghi rõ **test MISA SME thật = BLOCKED** (cần license
  MISA + SQL Server + máy Windows lab + kế toán viên QA), không giả lập để
  báo đạt.

## Giới hạn chung (áp dụng cả 3 workflow)

- Không có Microsoft Word/Excel/MISA thật trong môi trường build này —
  mọi round-trip chỉ xác minh qua `python-docx`/`openpyxl`/Python thuần,
  KHÔNG phải Office/MISA thật.
- Không có máy in/scanner thật — bước "in" trong workflow A và "in chứng
  từ" trong workflow C giữ trạng thái `unknown`/`not_run`, KHÔNG được tính
  là đã khảo sát hay đã pass (theo Gate của Gói 1).
- Dữ liệu 100% tự tạo, không đại diện cho khảo sát người dùng thật —
  không được dùng các số liệu này để kết luận "ứng dụng X khảo sát xong".
"""
    (WORKFLOWS_DIR / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    result_a = build_workflow_a()
    result_b = build_workflow_b()
    result_c = build_workflow_c()
    build_top_level_readme({"a": result_a, "b": result_b, "c": result_c})

    print(json.dumps({
        "status": "ok",
        "workflow_a": result_a,
        "workflow_b": result_b,
        "workflow_c": result_c,
    }, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
