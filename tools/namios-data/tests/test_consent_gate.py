# -*- coding: utf-8 -*-
"""consent-gate blocks a network source (bullet riêng trong yêu cầu task).

Theo docs/specs/namioffice-v2/02_WRITER_SHEET_SLIDES.md §B + COMPAT-MATRIX
SH-F2-03 (Gate P0): nguồn mạng (sql/web) phải bị CHẶN theo mặc định, và
thông báo consent phải nói rõ dữ liệu sẽ gửi/nhận — không được mơ hồ."""
import csv

import pytest

from consent import ConsentNotice, ConsentRequiredError, check_consent, describe
from pipeline import Pipeline
from sources import SourceSpec, read_source


def test_local_sources_never_require_consent():
    # csv/json cục bộ: không bao giờ cần consent, không ném lỗi ở cổng này.
    check_consent("csv", "/tmp/anything.csv", consent=False)
    check_consent("json", "/tmp/anything.json", consent=False)


def test_network_source_blocked_without_consent():
    with pytest.raises(ConsentRequiredError) as exc_info:
        check_consent("sql", "postgresql://db.example.com/sales", consent=False)
    msg = str(exc_info.value)
    assert "db.example.com" in msg  # thông báo phải nêu đích thật, không mơ hồ
    assert "đồng ý" in msg.lower() or "consent" in msg.lower()


def test_web_source_blocked_without_consent():
    with pytest.raises(ConsentRequiredError):
        check_consent("web", "https://api.example.com/export.json", consent=False)


def test_consent_notice_names_exact_data_sent_and_received():
    notice = describe("sql", "postgresql://db.example.com/sales", query="SELECT * FROM orders")
    assert isinstance(notice, ConsentNotice)
    rendered = notice.render_vi()
    assert "db.example.com" in rendered
    assert "SELECT * FROM orders" in rendered
    assert "Sẽ GỬI" in rendered and "Sẽ NHẬN" in rendered

    local_notice = describe("csv", "/home/user/data.csv")
    assert "không có gì" in local_notice.will_send.lower() or "không ra mạng" in local_notice.will_send.lower()


def test_read_source_sql_blocked_end_to_end_without_consent():
    spec = SourceSpec(kind="sql", uri="postgresql://db.example.com/sales", options={"query": "SELECT 1"})
    with pytest.raises(ConsentRequiredError):
        read_source(spec, consent=False)


def test_read_source_sql_with_consent_is_still_not_wired_to_a_real_client():
    """Ngay cả khi người dùng ĐỒNG Ý, prototype này KHÔNG được âm thầm giả vờ
    đọc được dữ liệu mạng không tồn tại — phải báo NotImplementedError rõ
    ràng, KHÔNG trả về Table rỗng/giả như thể đã nối thành công."""
    spec = SourceSpec(kind="sql", uri="postgresql://db.example.com/sales", options={"query": "SELECT 1"})
    with pytest.raises(NotImplementedError):
        read_source(spec, consent=True)


def test_pipeline_run_propagates_consent_gate_for_aux_network_source(tmp_path):
    """Một pipeline đọc CSV cục bộ làm nguồn chính nhưng có một nguồn PHỤ là
    web — nếu pipeline.consent=False (mặc định AN TOÀN), chạy pipeline phải
    chặn ngay tại nguồn phụ đó, không chạy lọt bước nào."""
    csv_path = tmp_path / "local.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["A"])
        w.writerow(["1"])

    p = Pipeline(name="mixed", source=SourceSpec(kind="csv", uri=str(csv_path)))
    p.add_aux_source("remote", SourceSpec(kind="web", uri="https://api.example.com/data"))

    assert p.consent is False  # mặc định phải an toàn (chặn mạng)
    with pytest.raises(ConsentRequiredError):
        p.run()
