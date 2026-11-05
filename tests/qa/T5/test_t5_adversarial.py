"""T5 — tester độc lập cụm Evidence/compat-gate/catalog (WP9 ``namios_evidence``,
WP4 ``namios_catalog``).

Map test-matrix: MAN-04 (gate "không task_verified khi thiếu evidence/QA
approval"), UX-03 (tìm kiếm tiếng Việt accent-insensitive, tên gốc giữ
nguyên, revocation).

Viết ĐỘC LẬP với ``tests/unit/evidence/*`` và ``tests/unit/catalog/*`` của
dev (không sao chép case, không sửa file dev). Trọng tâm KHÁC với dev:
  1. Gate không được TỰ TIN vào field ``decision`` tự khai báo trong report
     (chỉ tin tính toán từ ``tests``/``qa_reviewer`` thật) — dev chưa test
     combo "decision tự xưng task_verified nhưng tests chưa đủ".
  2. ``qa_reviewer`` RỖNG (``""``, không phải ``None``) — kiểm xem lớp gate
     (tier 2, ``compute_allowed_status``) có TỰ nó chặn hay dựa hoàn toàn
     vào schema tier 1 (``minLength: 1``) đã chặn trước — vi phạm chiều sâu
     phòng thủ "schema hợp lệ ≠ an toàn" nếu gate không tự chặn.
  3. Path traversal thật qua ``..`` khi KHÔNG có symlink nào tham gia (dev
     chỉ test symlink + path tương đối) — kiểm ``read_text_safe``/
     ``EvidenceValidatorImpl.load`` có đọc được file NGOÀI ý định hay không
     khi base thật (không qua symlink) nhưng chứa thành phần ``..``.
  4. Schema tier: unknown key ở các object LỒNG (``environment``,
     ``qa_approval``, phần tử ``tests[]``) — dev mới test unknown key ở
     top-level.
  5. Type confusion: ``required`` truyền dạng string "true"/"1" thay vì
     boolean thật.
  6. File evidence quá khổ (> giới hạn DoS) bị từ chối dù JSON hợp lệ.
  7. Catalog: tên/app_id phân biệt hoa-thường ở TẦNG IDENTITY (khác tầng
     fold tìm kiếm) — ``"ABC"`` và ``"abc"`` phải là 2 app khác nhau.
  8. Catalog: query có khoảng trắng kép (lỗi gõ phổ biến) — kiểm search có
     chuẩn hóa khoảng trắng hay không.
  9. Catalog: input NFC vs NFD (hai cách mã hoá Unicode khác nhau cho CÙNG
     một chữ có dấu) ở QUERY phải cùng khớp entry đã index (index luôn fold
     qua NFD rồi NFC lại — nhưng input query có thể đến dưới dạng NFD gốc từ
     OS/bàn phím khác).
  10. Revoked entry: xác nhận hành vi hiện tại (``list``/``search`` KHÔNG tự
      lọc revoked — caller phải tự gọi ``is_revoked``) — ghi nhận rõ đây là
      THIẾT KẾ đã công bố (không phải lỗi) để không bị hiểu nhầm khi đọc
      acceptance criteria WP4.
"""

from __future__ import annotations

import os
import sys
import unicodedata
from pathlib import Path

import pytest

_SRC_DIR = str(Path(__file__).resolve().parents[3] / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from namios_core.catalog_types import CatalogEntry, RevocationRecord
from namios_core.evidence_types import EvidenceReport, EvidenceTest
from namios_core.manifest_types import (
    AppSection,
    CompatSection,
    LicenseSection,
    Manifest,
    PermissionsSection,
    RuntimeSection,
    SourceSection,
)
from namios_evidence._errors import EvidenceLoadError
from namios_evidence._gate import compute_allowed_status
from namios_evidence._safe_io import PathUnsafeError, read_text_safe
from namios_evidence.validator import EvidenceValidatorImpl

_CONTRACTS_DIR = Path(__file__).resolve().parents[3] / "contracts"
_EVIDENCE_FIXTURES_DIR = Path(__file__).resolve().parents[3] / "fixtures" / "evidence"


def _validator() -> EvidenceValidatorImpl:
    return EvidenceValidatorImpl()


def _load_raw(path: Path) -> dict:
    import json

    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Manifest/CatalogEntry builder TỰ VIẾT (độc lập ``tests/unit/catalog/
# _fixtures.py`` của dev — không import file test của dev).
# ---------------------------------------------------------------------------


def _t5_manifest(app_id: str, name: str, publisher: str = "T5 Publisher") -> Manifest:
    return Manifest(
        schema_version="1.0",
        id=app_id,
        name=name,
        publisher=publisher,
        mode="native",
        application=AppSection(
            version="1.0.0", build="b1", architecture="x86_64", installer_sha256="f" * 64
        ),
        license=LicenseSection(
            kind="open_source",
            spdx_expression="MIT",
            user_entitlement_required=False,
            redistribution="allowed_with_conditions",
            terms_url=None,
        ),
        source=SourceSection(
            acquisition="distribution_repository",
            official_url=None,
            allowed_hosts=(),
            automatic_download=False,
        ),
        runtime=RuntimeSection(
            runner_id=None,
            runner_sha256=None,
            prefix_architecture="not_applicable",
            wow64_strategy="not_applicable",
            dependency_profile_ids=(),
        ),
        permissions=PermissionsSection(
            filesystem=(),
            network="deny",
            audio=False,
            microphone=False,
            camera=False,
            printing=False,
            clipboard="deny",
            display="wayland",
            isolation="not_applicable",
            exceptions=(),
        ),
        recipe=(),
        compatibility=CompatSection(
            status="untested",
            vendor_support="unknown",
            required_task_ids=(),
            limitations=(),
            last_tested=None,
            evidence_id=None,
        ),
    )


def _t5_entry(
    app_id: str, name: str, publisher: str = "T5 Publisher", channel: str = "stable"
) -> CatalogEntry:
    return CatalogEntry(
        manifest=_t5_manifest(app_id, name, publisher), digest="a" * 64, channel=channel
    )


# ===========================================================================
# 1) Gate KHÔNG được tin field "decision" tự khai báo trong report
# ===========================================================================


def test_gate_ignores_self_declared_decision_task_verified_when_required_not_run() -> None:
    """Report tự khai ``decision="task_verified"`` (kẻ tấn công/báo lỗi giả
    mạo giá trị này) NHƯNG test bắt buộc vẫn ``not_run`` và có qa_reviewer —
    gate PHẢI tự tính lại từ ``tests``, KHÔNG được tin ``decision`` tự
    xưng."""

    rep = EvidenceReport(
        report_id="attack-1",
        manifest_id="app-attack",
        tests=(EvidenceTest(test_id="T1", required=True, result="not_run"),),
        decision="task_verified",  # tự xưng — KHÔNG phải sự thật
        qa_reviewer="qa.someone",
        environment={},
    )
    gate = compute_allowed_status(rep)
    assert gate.allowed_status != gate.allowed_status.TASK_VERIFIED
    assert gate.reasons_vi


def test_gate_ignores_self_declared_decision_task_verified_when_all_skipped() -> None:
    rep = EvidenceReport(
        report_id="attack-2",
        manifest_id="app-attack",
        tests=(
            EvidenceTest(test_id="T1", required=True, result="skipped"),
            EvidenceTest(test_id="T2", required=True, result="skipped"),
        ),
        decision="task_verified",
        qa_reviewer="qa.someone",
        environment={},
    )
    gate = compute_allowed_status(rep)
    assert gate.allowed_status.value != "task_verified"


def test_gate_empty_tests_tuple_is_untested_not_task_verified() -> None:
    """Report hoàn toàn không có test nào (tuple rỗng, không chỉ "không có
    required") — vẫn phải ``untested``, không được coi ngầm là đã đủ."""

    rep = EvidenceReport(
        report_id="attack-3",
        manifest_id="app-attack",
        tests=(),
        decision="task_verified",
        qa_reviewer="qa.someone",
        environment={},
    )
    gate = compute_allowed_status(rep)
    assert gate.allowed_status.value == "untested"


# ===========================================================================
# 2) qa_reviewer RỖNG ("") — gate tier-2 có tự chặn hay chỉ nhờ schema?
# ===========================================================================


def test_gate_treats_empty_string_reviewer_as_no_reviewer() -> None:
    """``EvidenceReport`` là dataclass thuần, CÓ THỂ được tạo trực tiếp
    (không qua ``EvidenceValidatorImpl.load``) bởi WP khác/CLI tương lai.
    Gate (hàm có trách nhiệm chứng nhận cuối cùng) KHÔNG được chỉ dựa vào
    schema tier-1 (``minLength:1`` trên ``qa_approval.reviewer``) đã chặn
    reviewer rỗng — chính gate PHẢI tự coi ``""`` (rỗng, không phải nhận
    diện thật) tương đương KHÔNG có reviewer, theo đúng tinh thần phòng thủ
    nhiều tầng "schema hợp lệ ≠ an toàn" áp dụng ngược lại cho chính gate.
    """

    rep = EvidenceReport(
        report_id="attack-4",
        manifest_id="app-attack",
        tests=(EvidenceTest(test_id="T1", required=True, result="pass"),),
        decision="task_verified",
        qa_reviewer="",  # rỗng — KHÔNG phải None nhưng cũng KHÔNG phải danh tính thật
        environment={},
    )
    gate = compute_allowed_status(rep)
    assert gate.allowed_status.value != "task_verified", (
        "Gate cấp task_verified cho qa_reviewer='' (rỗng) — chỉ an toàn vì "
        "tầng schema (minLength:1) chặn trước khi tới gate; bản thân gate "
        "không tự phòng thủ, vi phạm nguyên tắc nhiều tầng của §11.2."
    )


def test_gate_treats_whitespace_only_reviewer_as_no_reviewer() -> None:
    """Chuỗi chỉ gồm khoảng trắng (``"   "``) vượt qua ``minLength:1`` ở
    schema (không rỗng theo độ dài) nhưng KHÔNG phải một danh tính QA thật —
    PHẢI không được coi là có reviewer."""

    rep = EvidenceReport(
        report_id="attack-5",
        manifest_id="app-attack",
        tests=(EvidenceTest(test_id="T1", required=True, result="pass"),),
        decision="task_verified",
        qa_reviewer="   ",
        environment={},
    )
    gate = compute_allowed_status(rep)
    assert gate.allowed_status.value != "task_verified"


# ===========================================================================
# 3) Path traversal qua ".." KHÔNG có symlink — base thật, không bị chặn bởi
#    kiểm tra realpath(base) == abspath(base) vì không có symlink nào.
# ===========================================================================


def test_path_traversal_via_dotdot_without_symlink_must_be_rejected(tmp_path: Path) -> None:
    """Dựng cây thư mục THẬT (không symlink): ``<tmp>/intended/evidence/``.
    Người gọi lẽ ra chỉ đọc file trong đó, nhưng truyền một path tuyệt đối
    có ``../../`` trỏ ra ``<tmp>/secret/out-of-scope.json`` (file KHÁC,
    cùng hệ thống file, không phải symlink). Nếu hàm chỉ kiểm
    ``realpath(dirname) == abspath(dirname)`` (đều đúng vì không symlink)
    mà không có BẤT KỲ ràng buộc "nằm trong phạm vi cho phép" nào khác, file
    bí mật SẼ bị đọc được — đây là vi phạm trực tiếp CLAUDE.md: "chống
    traversal ... không chỉ check '..'"."""

    intended_dir = tmp_path / "intended" / "evidence"
    intended_dir.mkdir(parents=True)

    secret_dir = tmp_path / "secret"
    secret_dir.mkdir(parents=True)
    secret_file = secret_dir / "out-of-scope.json"
    secret_file.write_text('{"marker": "T5-SECRET-SHOULD-NOT-BE-READABLE"}', encoding="utf-8")

    # Path tuyệt đối, có '..', KHÔNG đi qua symlink nào — chỉ đi bộ bằng
    # thành phần thư mục thật.
    traversal_path = str(intended_dir / ".." / ".." / "secret" / "out-of-scope.json")
    assert os.path.realpath(traversal_path) == str(secret_file.resolve())

    with pytest.raises(PathUnsafeError):
        read_text_safe(traversal_path)


def test_evidence_validator_load_rejects_dotdot_traversal_to_outside_file(tmp_path: Path) -> None:
    """Cùng kịch bản nhưng qua API công khai ``EvidenceValidatorImpl.load``
    (đường thật mà CLI/WP khác sẽ gọi) — nội dung file ngoài phạm vi là JSON
    hợp lệ nhưng KHÔNG đúng schema evidence-report; nếu hàm đọc được nội
    dung (dù sau đó fail ở schema) tức là traversal ĐÃ XUYÊN QUA — phải bị
    chặn ở tầng path-safety TRƯỚC KHI đọc, không phải để lộ nội dung rồi mới
    fail ở schema."""

    intended_dir = tmp_path / "intended" / "evidence"
    intended_dir.mkdir(parents=True)

    secret_dir = tmp_path / "secret"
    secret_dir.mkdir(parents=True)
    secret_file = secret_dir / "out-of-scope.json"
    secret_file.write_text('{"marker": "T5-SECRET"}', encoding="utf-8")

    traversal_path = str(intended_dir / ".." / ".." / "secret" / "out-of-scope.json")

    with pytest.raises((PathUnsafeError, EvidenceLoadError)) as exc_info:
        _validator().load(traversal_path)

    # Nếu lỗi là EvidenceLoadError (schema fail) thay vì PathUnsafeError,
    # nghĩa là file BÍ MẬT đã bị ĐỌC THÀNH CÔNG trước khi bị schema chặn —
    # đây chính là bằng chứng traversal thật đã xảy ra (chặn muộn, sai
    # tầng). Gắn assertion tường minh để không bị bỏ sót khi review.
    if isinstance(exc_info.value, EvidenceLoadError):
        pytest.fail(
            "Traversal '..' đã ĐỌC ĐƯỢC nội dung file ngoài phạm vi trước "
            "khi bị chặn (chặn ở tầng schema, không phải tầng path-safety) "
            f"— chi tiết lỗi thật: {exc_info.value.errors}"
        )


def test_path_traversal_landing_back_inside_allowed_tree_is_the_control_case(
    tmp_path: Path,
) -> None:
    """Case đối chứng (KHÔNG phải tấn công): ``..`` rồi lại đi vào đúng
    ngay trong cây cho phép (không thoát ra ngoài thật) — phải ĐƯỢC đọc
    bình thường, để xác nhận test traversal ở trên là do thoát ra NGOÀI,
    không phải do hàm chặn mọi ``..`` một cách quá tay (false positive)."""

    base = tmp_path / "intended"
    base.mkdir()
    f = base / "report.json"
    f.write_text("hello", encoding="utf-8")

    roundtrip_path = str(base / ".." / "intended" / "report.json")
    assert os.path.realpath(roundtrip_path) == str(f.resolve())

    content = read_text_safe(roundtrip_path)
    assert content == "hello"


# ===========================================================================
# 4) Schema tier: unknown key ở object LỒNG (environment / qa_approval /
#    tests[]) — dev chỉ test unknown key ở top-level.
# ===========================================================================


def _base_valid_raw() -> dict:
    return _load_raw(_EVIDENCE_FIXTURES_DIR / "sample-task-verified.json")


def test_unknown_key_inside_environment_object_rejected() -> None:
    raw = _base_valid_raw()
    raw["environment"]["trusted_vendor_flag"] = True
    result = _validator().validate_schema(raw)
    assert result.ok is False


def test_unknown_key_inside_qa_approval_object_rejected() -> None:
    raw = _base_valid_raw()
    raw["qa_approval"]["signed_off_by_ceo"] = True
    result = _validator().validate_schema(raw)
    assert result.ok is False


def test_unknown_key_inside_tests_array_item_rejected() -> None:
    raw = _base_valid_raw()
    raw["tests"][0]["bypass_required_check"] = True
    result = _validator().validate_schema(raw)
    assert result.ok is False


# ===========================================================================
# 5) Type confusion: "required" dạng string không phải bool thật
# ===========================================================================


def test_required_field_as_string_true_is_rejected_not_coerced() -> None:
    """JSON Schema ``type: boolean`` không được tự ý coerce chuỗi "true"
    thành ``True`` — nếu bộ nạp coi nhầm là hợp lệ, một report có thể khai
    ``"required": "false"`` (chuỗi non-empty, truthy trong Python) và vô
    tình bị tính như required=True ở nơi khác, hoặc ngược lại."""

    raw = _base_valid_raw()
    raw["tests"][0]["required"] = "true"
    result = _validator().validate_schema(raw)
    assert result.ok is False


def test_result_field_as_integer_is_rejected() -> None:
    raw = _base_valid_raw()
    raw["tests"][0]["result"] = 1
    result = _validator().validate_schema(raw)
    assert result.ok is False


# ===========================================================================
# 6) DoS: file evidence quá khổ bị từ chối dù JSON hợp lệ bên trong
# ===========================================================================


def test_oversized_evidence_file_rejected_even_if_valid_json(tmp_path: Path) -> None:
    import json

    raw = _base_valid_raw()
    # Nhồi known_issues (field hợp lệ theo schema, chấp nhận array string)
    # tới khi vượt giới hạn 2 MiB của read_text_safe — vẫn là JSON tuyệt
    # đối hợp lệ và SCHEMA-hợp lệ về cấu trúc issue array, chỉ khổ lớn.
    big_padding = "x" * 500
    raw["known_issues"] = [f"{big_padding}-{i}" for i in range(4200)]
    text = json.dumps(raw)
    assert len(text.encode("utf-8")) > 2 * 1024 * 1024, "payload phải thật sự vượt 2 MiB"

    big_path = tmp_path / "huge-evidence.json"
    big_path.write_text(text, encoding="utf-8")

    with pytest.raises(PathUnsafeError):
        read_text_safe(str(big_path))


# ===========================================================================
# 7) Catalog: identity (app_id) phân biệt hoa/thường — khác tầng fold search
# ===========================================================================


def test_catalog_app_id_identity_is_case_sensitive_distinct_entries() -> None:
    from namios_catalog.store import InMemoryCatalogStore

    store = InMemoryCatalogStore()
    store.add(_t5_entry("App-ABC", "Ứng dụng ABC hoa"))
    store.add(_t5_entry("app-abc", "Ứng dụng abc thường"))

    assert store.get("App-ABC") is not None
    assert store.get("app-abc") is not None
    assert store.get("App-ABC").manifest.name != store.get("app-abc").manifest.name
    assert len(store.list()) == 2, "hai app_id khác hoa/thường PHẢI là 2 entry riêng, không đè nhau"


def test_catalog_revoke_one_case_variant_does_not_affect_the_other() -> None:
    from namios_catalog.store import InMemoryCatalogStore

    store = InMemoryCatalogStore()
    store.add(_t5_entry("App-ABC", "A"))
    store.add(_t5_entry("app-abc", "B"))
    store.revoke(
        RevocationRecord(target_id="App-ABC", reason="r", revoked_at="2026-11-02T00:00:00Z")
    )

    assert store.is_revoked("App-ABC") is True
    assert store.is_revoked("app-abc") is False


# ===========================================================================
# 8) Catalog: khoảng trắng kép trong query — lỗi gõ phổ biến
# ===========================================================================


def test_search_query_with_double_internal_space_still_matches() -> None:
    """``fold_vn`` chỉ fold dấu+hoa/thường, KHÔNG chuẩn hoá khoảng trắng.
    Haystack được ``store.add`` nối bằng ĐÚNG MỘT khoảng trắng
    (``" ".join(...)``) — nếu người dùng gõ 2 khoảng trắng liên tiếp (lỗi
    gõ rất phổ biến, đặc biệt gõ tiếng Việt có dấu qua bộ gõ), substring
    match sẽ KHÔNG khớp dù về ngữ nghĩa là cùng một câu tìm kiếm."""

    from namios_catalog.store import InMemoryCatalogStore

    store = InMemoryCatalogStore()
    store.add(_t5_entry("vn-demo", "Đỗ Chí Cường Studio", "NaMiOS"))

    normal = store.search("Đỗ Chí Cường")
    double_space = store.search("Đỗ  Chí   Cường")  # 2-3 khoảng trắng liên tiếp

    assert normal != (), "sanity: query chuẩn phải khớp"
    assert double_space == normal, (
        "Query có khoảng trắng kép (lỗi gõ phổ biến) KHÔNG khớp được entry "
        f"mà query 1-khoảng-trắng khớp được. normal={normal!r} "
        f"double_space={double_space!r}"
    )


# ===========================================================================
# 9) Catalog: query Unicode NFD (decomposed) phải khớp entry đã index dù
#    index được xây từ chuỗi NFC (precomposed, dạng phổ biến khi lưu file).
# ===========================================================================


def test_search_query_in_nfd_unicode_form_matches_nfc_indexed_entry() -> None:
    from namios_catalog.store import InMemoryCatalogStore

    name_nfc = unicodedata.normalize("NFC", "Đỗ Chí Cường Studio")
    store = InMemoryCatalogStore()
    store.add(_t5_entry("vn-demo-nfc", name_nfc, "NaMiOS"))

    # Query do người dùng gõ tới dưới dạng NFD (decomposed) — xảy ra thật
    # khi dữ liệu đến từ một số bàn phím/IME hoặc hệ điều hành macOS (vốn
    # thường chuẩn hoá tên file theo NFD).
    query_nfd = unicodedata.normalize("NFD", "Đỗ Chí Cường")
    assert query_nfd != "Đỗ Chí Cường", "sanity: NFD phải khác biểu diễn byte so với NFC gốc"

    results = store.search(query_nfd)
    assert [r.manifest.id for r in results] == ["vn-demo-nfc"], (
        "Query Unicode NFD không khớp được entry đã index ở dạng NFC — " f"results={results!r}"
    )


# ===========================================================================
# 10) Revoked entry: xác nhận hành vi hiện tại (không tự lọc ở store) — ghi
#     nhận là THIẾT KẾ, không phải regression, để không hiểu nhầm UX-03.
# ===========================================================================


def test_revoked_entry_still_returned_by_list_and_search_caller_must_filter() -> None:
    """Ghi nhận HÀNH VI HIỆN TẠI (không phải lỗi mới phát hiện — khớp
    docstring có sẵn của ``InMemoryCatalogStore.revoke``): entry bị revoke
    vẫn xuất hiện trong ``list()``/``search()``; caller (CLI/semantic layer)
    PHẢI tự gọi ``is_revoked()`` trước khi hiển thị "cài được". Nếu hành vi
    này thay đổi (ví dụ dev tự thêm filter ẩn), test này sẽ FAIL và cần
    xem lại thiết kế, không phải ngược lại."""

    from namios_catalog.store import InMemoryCatalogStore

    store = InMemoryCatalogStore()
    store.add(_t5_entry("demo-app", "Demo App"))
    store.revoke(
        RevocationRecord(target_id="demo-app", reason="r", revoked_at="2026-11-02T00:00:00Z")
    )

    assert "demo-app" in {e.manifest.id for e in store.list()}
    assert "demo-app" in {e.manifest.id for e in store.search("demo")}
    assert store.is_revoked("demo-app") is True
