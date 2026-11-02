"""ECO-006/ECO-003 — kiểm TRỰC TIẾP mọi file ``catalog/services/*.json``
đóng gói trong repo (đọc JSON thô bằng ``json.loads`` + thẩm định bằng
``namios_eco`` — ĐỘC LẬP với ``namios_cli.service_catalog_loader`` đã có
integration test riêng, để không phụ thuộc vào cùng một đường load có thể
có bug chung):

  - KHÔNG entry nào được gán ``workflow_verified``.
  - MỌI entry có ``official_url`` http(s), ``last_updated`` hợp lệ, và
    ``evidence_source`` không rỗng.
  - MỌI entry qua được tầng 1 (structure) + tầng 2 tối thiểu (URL chính
    thức + không có khoá thực thi lạ) của ``namios_eco``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from namios_eco.catalog_schema import build_entry, validate_raw
from namios_eco.status import PublishedStatus
from namios_eco.validator import validate_no_executable_keys, validate_official_url

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CATALOG_DIR = _REPO_ROOT / "catalog" / "services"


def _catalog_files() -> list[Path]:
    files = sorted(_CATALOG_DIR.glob("*.json"))
    assert files, f"Không tìm thấy file catalog nào ở {_CATALOG_DIR} — test này cần dữ liệu thật."
    return files


def test_catalog_services_directory_is_not_empty() -> None:
    assert len(_catalog_files()) >= 6  # tối thiểu 1 đại diện / 6 nhóm ECO §2


@pytest.mark.parametrize("path", _catalog_files(), ids=lambda p: p.name)
def test_each_real_catalog_file_passes_schema_and_semantic_layers(path: Path) -> None:
    raw = json.loads(path.read_text(encoding="utf-8"))
    schema_errors = validate_raw(raw)
    assert schema_errors == [], f"{path.name}: lỗi tầng 1: {schema_errors}"

    semantic_errors = [
        *validate_official_url(raw["official_url"]),
        *validate_no_executable_keys(raw),
    ]
    assert semantic_errors == [], f"{path.name}: lỗi tầng 2: {semantic_errors}"


@pytest.mark.parametrize("path", _catalog_files(), ids=lambda p: p.name)
def test_each_real_catalog_entry_is_not_claimed_workflow_verified(path: Path) -> None:
    """GATE trung thực cấp cao nhất cho danh bạ khảo sát ban đầu: chưa có
    entry nào từng chạy thử 7 nấc thật với evidence nộp/nhận — TUYỆT ĐỐI
    không được có file nào tự nhận ``workflow_verified``."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    entry = build_entry(raw)
    assert entry.published_status != PublishedStatus.WORKFLOW_VERIFIED, (
        f"{path.name}: catalog khảo sát ban đầu nhưng đã tự nhận "
        "'workflow_verified' — chưa có bằng chứng nộp/nhận thật nào (ECO-003)."
    )


@pytest.mark.parametrize("path", _catalog_files(), ids=lambda p: p.name)
def test_each_real_catalog_entry_has_official_http_url_last_updated_and_evidence_source(
    path: Path,
) -> None:
    raw = json.loads(path.read_text(encoding="utf-8"))
    entry = build_entry(raw)

    assert entry.official_url.startswith(("http://", "https://")), (
        f"{path.name}: official_url không phải http(s): {entry.official_url!r}"
    )
    assert len(entry.last_updated) == 10 and entry.last_updated[4] == "-" and entry.last_updated[7] == "-", (
        f"{path.name}: last_updated không đúng dạng YYYY-MM-DD: {entry.last_updated!r}"
    )
    assert entry.evidence_source.strip() != "", f"{path.name}: evidence_source rỗng."


def test_no_real_catalog_entry_id_is_duplicated_across_files() -> None:
    """ID ổn định (ECO-006) phải DUY NHẤT trên toàn danh bạ — trùng ID giữa
    2 file khác nhau là một lỗi dữ liệu nghiêm trọng (một trong hai sẽ bị
    "mất" khi load theo ``id``)."""

    seen: dict[str, str] = {}
    for path in _catalog_files():
        raw = json.loads(path.read_text(encoding="utf-8"))
        entry_id = raw["id"]
        if entry_id in seen:
            pytest.fail(f"ID '{entry_id}' trùng giữa '{seen[entry_id]}' và '{path.name}'")
        seen[entry_id] = path.name


def test_no_real_catalog_file_contains_a_fabricated_receipt_or_pin_collection_field() -> None:
    """ECO-016/ECO-008 — phòng vệ cấp dữ liệu: không file catalog nào được
    chứa trường mang hình dạng "đã có biên nhận/mã hồ sơ thật" (bịa bằng
    chứng) hay thu PIN/token thật (vốn ngoài phạm vi field cho phép của
    schema — ``additionalProperties: false`` đã chặn ở tầng 1, nhưng tester
    kiểm lại thủ công trên JSON THÔ, trước khi qua schema, để không phụ
    thuộc một lớp duy nhất)."""

    forbidden_raw_keys = {"receipt_number", "ma_ho_so", "pin", "token_pin", "otp", "mat_khau", "password"}
    for path in _catalog_files():
        raw = json.loads(path.read_text(encoding="utf-8"))
        present = forbidden_raw_keys & set(raw.keys())
        assert not present, f"{path.name}: chứa khoá bị cấm {present}"
