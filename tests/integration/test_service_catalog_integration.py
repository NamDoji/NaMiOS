"""Integration — ``namios service list|search|inspect`` end-to-end qua
``main()`` THẬT (``deps=None`` ⇒ không cần ``CliDependencies`` — danh bạ
ECO-006 là dữ liệu tĩnh đọc trực tiếp từ ``catalog/services/`` bởi
``namios_cli.service_catalog_loader``, KHÔNG qua Protocol liên-WP).

Phần 1 chạy trên danh bạ THẬT đã đóng gói trong repo (``catalog/services/``):
khẳng định không entry nào tự nhận ``workflow_verified`` (đúng chủ đích khảo
sát ban đầu — ECO-003 §3), và trạng thái hiển thị khớp đúng dữ liệu trên đĩa.

Phần 2 dùng fixture CÔ LẬP (``tests/integration/fixtures/service/**``, qua
``monkeypatch`` trên ``CATALOG_SERVICES_DIR`` — biến module-level, đọc lại
mỗi lần gọi ``load_service_catalog()`` nên monkeypatch có hiệu lực ngay) để
test ADVERSARIAL GATE ECO-003 ("downloadable_only"/"launches_only" TUYỆT ĐỐI
không được hiển thị là dùng được) và test lỗi catalog hỏng không làm crash
CLI.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from namios_cli.main import main
from namios_core.exitcodes import ExitCode

_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "service"


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    rc = main(argv, stdout=out, stderr=err)  # deps=None ⇒ chạy thật, không fake
    return rc, out.getvalue(), err.getvalue()


def _patch_catalog_dir(monkeypatch: pytest.MonkeyPatch, fixture_subdir: str) -> None:
    monkeypatch.setattr(
        "namios_cli.service_catalog_loader.CATALOG_SERVICES_DIR",
        _FIXTURES_DIR / fixture_subdir,
    )


# ---------------------------------------------------------------------------
# Phần 1 — danh bạ THẬT đóng gói cùng repo (catalog/services/)
# ---------------------------------------------------------------------------


def test_service_list_real_catalog_json_envelope_ok() -> None:
    rc, out, err = _run(["service", "list", "--json"])
    assert rc == ExitCode.OK
    assert err == ""
    lines = out.splitlines()
    assert len(lines) == 1  # CLI-001: đúng một dòng JSON, không log lẫn vào
    parsed = json.loads(lines[0])
    assert parsed["status"] == "ok"
    assert parsed["error"] is None


def test_service_list_real_catalog_has_at_least_twelve_entries_across_groups() -> None:
    """ECO §2/§5 giao việc: 6 nhóm (thuế/kế toán-hoá đơn/BHXH/hành chính
    công/giáo dục/ngành dọc) — kiểm tra có đủ đại diện, không chỉ 1-2 mục."""

    rc, out, _err = _run(["service", "list", "--json"])
    assert rc == ExitCode.OK
    data = json.loads(out)["data"]
    ids = {e["id"] for e in data["entries"]}
    assert len(ids) >= 12
    assert data["listed"] == len(ids)
    prefixes = {i.split(".", 1)[0] for i in ids}
    assert {"thue", "ketoan", "bhxh", "hanhchinh", "giaoduc", "nganhdoc"} <= prefixes


def test_service_list_real_catalog_never_claims_workflow_verified() -> None:
    """FACT giao việc: danh bạ khảo sát ban đầu CHỈ dùng
    ``not_inventoried``/``launches_only`` — TUYỆT ĐỐI không
    ``workflow_verified`` (chưa có bằng chứng nộp/nhận thật nào)."""

    rc, out, _err = _run(["service", "list", "--json"])
    assert rc == ExitCode.OK
    data = json.loads(out)["data"]
    assert data["workflow_verified"] == 0
    for entry in data["entries"]:
        assert entry["published_status"] != "workflow_verified"
        # Hệ quả trực tiếp của GATE ECO-003: không claim workflow_verified
        # ⇒ cũng không được hiển thị usable=True cho bất kỳ entry nào trong
        # danh bạ khảo sát ban đầu này.
        assert entry["usable"] is False


def test_service_list_real_catalog_warns_about_listed_vs_working_eco_022() -> None:
    rc, out, _err = _run(["service", "list", "--json"])
    assert rc == ExitCode.OK
    parsed = json.loads(out)
    joined = " ".join(parsed["warnings"])
    assert "0" in joined  # workflow_verified=0
    assert "liệt kê" in joined


def test_service_inspect_known_real_entry_returns_full_fields_and_usable_false() -> None:
    rc, out, _err = _run(["service", "inspect", "thue.htkk", "--json"])
    assert rc == ExitCode.OK
    data = json.loads(out)["data"]
    assert data["id"] == "thue.htkk"
    assert data["published_status"] == "not_inventoried"
    assert data["usable"] is False
    assert data["official_url"].startswith("https://")
    assert data["tested_by_namios"] is False
    assert data["officially_supported_by_vendor"] is False


def test_service_inspect_unknown_id_is_input_schema_error_not_crash() -> None:
    rc, out, err = _run(["service", "inspect", "khong-ton-tai.abc", "--json"])
    assert rc == ExitCode.INPUT
    assert err == ""
    parsed = json.loads(out)
    assert parsed["status"] == "error"
    assert parsed["data"] is None
    assert parsed["error"]["code"] == "E_INPUT_SCHEMA"


def test_service_search_real_catalog_accent_insensitive_matches_same_hits() -> None:
    rc1, out1, _err1 = _run(["service", "search", "khai thuế", "--json"])
    rc2, out2, _err2 = _run(["service", "search", "khai thue", "--json"])
    assert rc1 == ExitCode.OK
    assert rc2 == ExitCode.OK
    ids1 = {h["id"] for h in json.loads(out1)["data"]["hits"]}
    ids2 = {h["id"] for h in json.loads(out2)["data"]["hits"]}
    assert ids1 == ids2
    assert "thue.htkk" in ids1


def test_service_search_real_catalog_case_insensitive() -> None:
    rc, out, _err = _run(["service", "search", "KHAI THUẾ", "--json"])
    assert rc == ExitCode.OK
    ids = {h["id"] for h in json.loads(out)["data"]["hits"]}
    assert "thue.htkk" in ids


def test_service_search_real_catalog_no_match_returns_empty_hits_not_error() -> None:
    rc, out, _err = _run(["service", "search", "khong-khop-gi-ca-xyz123", "--json"])
    assert rc == ExitCode.OK
    data = json.loads(out)["data"]
    assert data["hits"] == []


def test_service_search_negative_limit_is_input_schema_error() -> None:
    rc, out, err = _run(["service", "search", "thue", "--limit", "0", "--json"])
    assert rc == ExitCode.INPUT
    assert err == ""
    parsed = json.loads(out)
    assert parsed["error"]["code"] == "E_INPUT_SCHEMA"


def test_service_list_without_json_prints_human_text_not_json() -> None:
    rc, out, _err = _run(["service", "list"])
    assert rc == ExitCode.OK
    with pytest.raises(json.JSONDecodeError):
        json.loads(out)
    assert "OK" in out


# ---------------------------------------------------------------------------
# Phần 2 — fixtures cô lập (monkeypatch CATALOG_SERVICES_DIR) — adversarial
# ---------------------------------------------------------------------------


def test_service_list_launches_only_fixture_is_never_shown_usable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GATE ECO-003 tuyệt đối: dù dữ liệu claim ``launches_only`` (mở được
    nhưng chưa thử đăng nhập/tác vụ kế), CLI PHẢI báo ``usable: false`` và có
    warning rõ ràng — không có cách nào qua CLI khiến nó thành "dùng được"."""

    _patch_catalog_dir(monkeypatch, "single_launches_only")
    rc, out, _err = _run(["service", "list", "--json"])
    assert rc == ExitCode.OK
    parsed = json.loads(out)
    entries = parsed["data"]["entries"]
    assert len(entries) == 1
    assert entries[0]["published_status"] == "launches_only"
    assert entries[0]["usable"] is False
    joined_warnings = " ".join(parsed["warnings"])
    assert "launches_only" in joined_warnings
    assert "KHÔNG đồng nghĩa dùng được" in joined_warnings


def test_service_inspect_launches_only_fixture_never_usable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_catalog_dir(monkeypatch, "single_launches_only")
    rc, out, _err = _run(["service", "inspect", "test.fixture-launches-only", "--json"])
    assert rc == ExitCode.OK
    parsed = json.loads(out)
    assert parsed["data"]["usable"] is False
    assert any("KHÔNG đồng nghĩa dùng được" in w for w in parsed["warnings"])


def test_service_list_workflow_verified_fixture_is_the_only_usable_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Đối chứng dương: GATE không phải "luôn luôn false" một cách ngẫu
    nhiên — ``workflow_verified`` (khi dữ liệu thật sự claim vậy) PHẢI hiển
    thị ``usable: true`` và KHÔNG kèm cảnh báo "không đồng nghĩa dùng được"
    (cảnh báo đó CHỈ gắn với downloadable_only/launches_only)."""

    _patch_catalog_dir(monkeypatch, "single_workflow_verified")
    rc, out, _err = _run(["service", "list", "--json"])
    assert rc == ExitCode.OK
    parsed = json.loads(out)
    entries = parsed["data"]["entries"]
    assert entries[0]["published_status"] == "workflow_verified"
    assert entries[0]["usable"] is True
    assert parsed["data"]["workflow_verified"] == 1
    assert not any("KHÔNG đồng nghĩa dùng được" in w for w in parsed["warnings"])


def test_service_search_fixture_isolates_unrelated_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_catalog_dir(monkeypatch, "two_search_entries")
    # "hồ sơ khai" chỉ nằm trong purpose của entry A — cả hai id đều chứa
    # chuỗi con "thue" (vì id cũng nằm trong haystack tìm kiếm), nên dùng
    # cụm từ chỉ khớp purpose của A để thật sự kiểm được tính loại trừ.
    rc, out, _err = _run(["service", "search", "hồ sơ khai", "--json"])
    assert rc == ExitCode.OK
    ids = {h["id"] for h in json.loads(out)["data"]["hits"]}
    assert ids == {"test.fixture-khai-thue-a"}


def test_service_search_fixture_hit_has_requires_account_or_token_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_catalog_dir(monkeypatch, "two_search_entries")
    rc, out, _err = _run(["service", "search", "fixture", "--json"])
    assert rc == ExitCode.OK
    hits = json.loads(out)["data"]["hits"]
    assert len(hits) == 2
    for hit in hits:
        assert isinstance(hit["requires_account_or_token"], bool)


def test_service_list_broken_catalog_missing_field_is_internal_error_not_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """File catalog hỏng (thiếu trường bắt buộc tầng 1) — CLI PHẢI trả
    envelope lỗi ``E_INTERNAL`` rõ ràng, KHÔNG crash tiến trình, KHÔNG giả
    ``ok`` bỏ qua entry hỏng."""

    _patch_catalog_dir(monkeypatch, "broken_missing_field")
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main(["service", "list", "--json"], stdout=out, stderr=err)
    except Exception as exc:  # noqa: BLE001 — chính là điều đang kiểm tra
        pytest.fail(
            "DEFECT: catalog hỏng (thiếu field) làm main() crash bằng "
            f"{type(exc).__name__}({exc!r}) thay vì trả envelope lỗi."
        )
    assert rc == ExitCode.INTERNAL
    parsed = json.loads(out.getvalue())
    assert parsed["status"] == "error"
    assert parsed["data"] is None
    assert parsed["error"]["code"] == "E_INTERNAL"


def test_service_list_broken_catalog_executable_key_is_internal_error_not_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Phòng vệ nhiều lớp (ECO-006): file catalog có khóa thực thi bị cấm
    (``shell``) PHẢI bị chặn ở tầng loader (tầng 2), không lọt qua CLI dưới
    bất kỳ hình thức nào, và tuyệt đối không lộ nội dung độc hại ra envelope."""

    _patch_catalog_dir(monkeypatch, "broken_executable_key")
    rc, out, err = _run(["service", "list", "--json"])
    assert rc == ExitCode.INTERNAL
    assert err == ""
    parsed = json.loads(out)
    assert parsed["error"]["code"] == "E_INTERNAL"
    full_payload = json.dumps(parsed, ensure_ascii=False)
    assert "rm -rf" not in full_payload
