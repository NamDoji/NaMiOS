"""Test HỢP ĐỒNG (contract/schema) cho error-catalog.json ↔ error-codes.md ↔
EVENT-ERROR-CONTRACT.md — KHÔNG cần máy thật, KHÔNG mô phỏng sự kiện (xem
sim_network.py/sim_printer.py/sim_bluetooth.py cho phần đó).

Theo EVENT-ERROR-CONTRACT.md §7 "Unit/contract (không cần máy thật)":
  - catalog ↔ error-codes.md parity
  - schema catalog (trường bắt buộc, kind hợp lệ, command là argv tĩnh,
    privileged:true ⇒ pkexec)
  - localization (l10n_key duy nhất, message_vi không rỗng)
  - phong bì sự kiện (result=unknown ⇔ cause_code kết thúc -000)
  - redaction (test riêng trong smartai_tests.sh vì cần gọi code thật)

Chạy: python3 -m pytest tools/reliability-tests/error_catalog_tests.py -v
"""

from __future__ import annotations

import re

import pytest

pytestmark = pytest.mark.filterwarnings("ignore")

# Ký tự shell nguy hiểm mà EVENT-ERROR-CONTRACT.md §7 cấm trong `command`
# (argv tĩnh, không phải chuỗi do người dùng điền rồi exec qua shell).
_DANGEROUS_SHELL_CHARS = re.compile(r"[;|&$`<>]")

_NM_CODE_RE = re.compile(r"\bNM-[A-Z]+-\d{3}\b")

# Domain -> vocab phase hợp lệ. mang/may_in/bluetooth đọc TỪ catalog["phases"]
# (không hard-code lại — tự thân catalog là nguồn sự thật, test chỉ xác nhận
# entry khớp với CHÍNH vocab catalog công bố). phan_cung/quyen/ung_dung không
# có trong catalog["phases"] (đó là 3 họ GIỮ NGUYÊN từ 8-mã-cũ, không thuộc
# phạm vi phase-mịn của hợp đồng) — vocab của 3 họ này lấy từ
# EVENT-ERROR-CONTRACT.md §3.4 / error-codes.md §6.4 (chỉ 1 phase cố định mỗi
# mã, trích dẫn tường minh ở đây vì catalog không tự liệt kê vocab cho chúng).
_LEGACY_DOMAIN_PHASES = {
    "phan_cung": {"firmware", "driver", "disk"},
    "quyen": {"permission"},
    "ung_dung": {"app-crash"},
}


# ---------------------------------------------------------------------------
# Schema cơ bản
# ---------------------------------------------------------------------------


def test_catalog_has_expected_top_level_shape(catalog_data: dict) -> None:
    for key in ("schema", "entries", "phases", "action_kinds", "confidence_levels"):
        assert key in catalog_data, f"Catalog thiếu khoá top-level '{key}'"
    assert catalog_data["entries"], "Catalog không có entry nào"


def test_every_entry_key_matches_its_own_cause_code_and_nm_code(catalog_data: dict) -> None:
    for key, entry in catalog_data["entries"].items():
        assert entry.get("cause_code") == key, f"{key}: cause_code lệch với khoá dict"
        assert entry.get("nm_code") == key, f"{key}: nm_code lệch với khoá dict"
        assert _NM_CODE_RE.fullmatch(key), f"{key}: không đúng dạng NM-<NHÓM>-<3 số>"


REQUIRED_FIELDS = (
    "domain",
    "phase",
    "cause_code",
    "nm_code",
    "l10n_key",
    "message_vi",
    "needs_evidence",
    "safe_actions",
    "default_confidence",
    "detector",
)


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_every_entry_has_required_field(catalog_data: dict, field: str) -> None:
    missing = [k for k, e in catalog_data["entries"].items() if field not in e]
    assert not missing, f"Các mã thiếu trường '{field}': {missing}"


# ---------------------------------------------------------------------------
# phase ∈ domain vocab (đọc vocab từ catalog, không hard-code cho mang/may_in/
# bluetooth; dùng bảng trích dẫn tài liệu cho 3 domain cũ).
# ---------------------------------------------------------------------------


def test_phase_belongs_to_domain_vocab(catalog_data: dict) -> None:
    phases_vocab = catalog_data["phases"]
    bad = []
    for code, entry in catalog_data["entries"].items():
        domain = entry["domain"]
        phase = entry["phase"]
        if phase == "unknown":
            # Sentinel *-000: luôn hợp lệ bất kể domain (CHƯA XÁC ĐỊNH).
            continue
        if domain in phases_vocab:
            vocab = set(phases_vocab[domain])
        elif domain in _LEGACY_DOMAIN_PHASES:
            vocab = _LEGACY_DOMAIN_PHASES[domain]
        else:
            bad.append(f"{code}: domain '{domain}' không có vocab nào biết tới")
            continue
        if phase not in vocab:
            bad.append(f"{code}: phase '{phase}' không thuộc vocab của domain '{domain}' ({sorted(vocab)})")
    assert not bad, "\n".join(bad)


def test_message_vi_non_empty(catalog_data: dict) -> None:
    empty = [k for k, e in catalog_data["entries"].items() if not e.get("message_vi", "").strip()]
    assert not empty, f"Các mã có message_vi rỗng: {empty}"


def test_needs_evidence_non_empty_list(catalog_data: dict) -> None:
    bad = [
        k
        for k, e in catalog_data["entries"].items()
        if not isinstance(e.get("needs_evidence"), list) or len(e["needs_evidence"]) == 0
    ]
    assert not bad, f"Các mã thiếu needs_evidence (phải là list non-empty): {bad}"


def test_l10n_key_unique_and_well_formed(catalog_data: dict) -> None:
    keys = {}
    bad_format = []
    for code, entry in catalog_data["entries"].items():
        key = entry.get("l10n_key", "")
        if not re.fullmatch(r"err\.[a-z0-9]+\.[a-z0-9_-]+", key):
            bad_format.append(f"{code}: l10n_key '{key}' sai dạng err.<domain>.<phase>")
        keys.setdefault(key, []).append(code)
    dup = {k: v for k, v in keys.items() if len(v) > 1}
    assert not bad_format, "\n".join(bad_format)
    assert not dup, f"l10n_key bị trùng giữa các mã: {dup}"


def test_default_confidence_in_declared_vocab(catalog_data: dict) -> None:
    vocab = set(catalog_data["confidence_levels"])
    bad = [
        f"{k}: default_confidence='{e.get('default_confidence')}'"
        for k, e in catalog_data["entries"].items()
        if e.get("default_confidence") not in vocab
    ]
    assert not bad, "\n".join(bad)


# ---------------------------------------------------------------------------
# Quy tắc "CHƯA XÁC ĐỊNH" (§4): mọi mã *-000 PHẢI là sentinel unknown + nói rõ
# "CHƯA XÁC ĐỊNH" trong message_vi + default_confidence=thấp (§4.1 "mỗi họ có
# một mã sentinel ... với phase=unknown, default_confidence=thấp").
# ---------------------------------------------------------------------------


def test_every_000_code_is_unknown_sentinel(catalog_data: dict) -> None:
    bad = []
    sentinel_codes = [c for c in catalog_data["entries"] if c.endswith("-000")]
    for code in sentinel_codes:
        entry = catalog_data["entries"][code]
        if entry["phase"] != "unknown":
            bad.append(f"{code}: *-000 nhưng phase='{entry['phase']}' (phải 'unknown')")
        if entry["default_confidence"] != "thấp":
            bad.append(
                f"{code}: *-000 nhưng default_confidence='{entry['default_confidence']}' (phải 'thấp')"
            )
        if "CHƯA XÁC ĐỊNH" not in entry["message_vi"]:
            bad.append(f"{code}: message_vi không nói rõ 'CHƯA XÁC ĐỊNH'")
    assert sentinel_codes, "Không tìm thấy mã *-000 nào để kiểm — danh sách rỗng là bất thường"
    assert not bad, "\n".join(bad)


def test_unknown_phase_only_used_by_000_codes(catalog_data: dict) -> None:
    """Bất biến ngược: phase=unknown CHỈ xuất hiện ở mã *-000 (không một mã cụ
    thể nào được phép mập mờ 'unknown' mà không phải sentinel)."""
    bad = [
        k
        for k, e in catalog_data["entries"].items()
        if e["phase"] == "unknown" and not k.endswith("-000")
    ]
    assert not bad, f"Các mã phase=unknown nhưng KHÔNG phải *-000: {bad}"


# ---------------------------------------------------------------------------
# safe_actions hợp lệ + "bypass not allowed": kind hợp lệ, privileged=>pkexec,
# không sudo/su trực tiếp (chỉ pkexec/polkit mới được cấp quyền), command là
# argv tĩnh (không ký tự shell nguy hiểm để tránh injection nếu lỡ nối chuỗi).
# ---------------------------------------------------------------------------

_VALID_KINDS = {"read-only", "state-change", "launch", "manual"}


def test_safe_actions_schema_and_kind_vocab(catalog_data: dict) -> None:
    bad = []
    for code, entry in catalog_data["entries"].items():
        actions = entry.get("safe_actions", [])
        assert isinstance(actions, list) and len(actions) >= 1, f"{code}: safe_actions rỗng"
        for a in actions:
            for f in ("id", "label_vi", "kind", "privileged", "command", "undo", "playbook"):
                if f not in a:
                    bad.append(f"{code}/{a.get('id', '?')}: thiếu trường '{f}'")
            if a.get("kind") not in _VALID_KINDS:
                bad.append(f"{code}/{a.get('id', '?')}: kind='{a.get('kind')}' không hợp lệ")
            if not isinstance(a.get("privileged"), bool):
                bad.append(f"{code}/{a.get('id', '?')}: privileged phải là boolean")
    assert not bad, "\n".join(bad)


def test_privileged_actions_only_via_pkexec_no_bypass(catalog_data: dict) -> None:
    """'privileged:true' PHẢI đi qua pkexec (polkit hỏi mật khẩu) — không có
    đường vòng (§5 'không có đường vòng'). Đồng thời: KHÔNG mã nào dùng
    `sudo`/`su -c` trực tiếp ở bất kỳ action nào (mọi nâng quyền phải qua
    polkit, không phải qua sudoers tĩnh — đây là 'bypass not allowed')."""
    bad = []
    for code, entry in catalog_data["entries"].items():
        for a in entry.get("safe_actions", []):
            cmd = a.get("command", "") or ""
            if a.get("privileged") is True:
                if not cmd.startswith("pkexec "):
                    bad.append(
                        f"{code}/{a['id']}: privileged=true nhưng command không bắt đầu bằng 'pkexec ': {cmd!r}"
                    )
            if re.search(r"\bsudo\b|\bsu\s+-c\b", cmd):
                bad.append(f"{code}/{a['id']}: dùng sudo/su trực tiếp (bypass polkit): {cmd!r}")
    assert not bad, "\n".join(bad)


def test_command_is_static_argv_no_shell_metacharacters(catalog_data: dict) -> None:
    bad = []
    for code, entry in catalog_data["entries"].items():
        for a in entry.get("safe_actions", []):
            cmd = a.get("command", "") or ""
            if cmd and _DANGEROUS_SHELL_CHARS.search(cmd):
                bad.append(f"{code}/{a['id']}: command chứa ký tự shell nguy hiểm: {cmd!r}")
    assert not bad, "\n".join(bad)


def test_manual_and_read_only_actions_do_not_require_privilege(catalog_data: dict) -> None:
    """manual/read-only là hành động không đổi gì hoặc người dùng tự làm tay —
    không có lý do gì cần pkexec; nếu có nghĩa là catalog gán nhầm kind."""
    bad = [
        f"{code}/{a['id']}: kind='{a['kind']}' nhưng privileged=true"
        for code, entry in catalog_data["entries"].items()
        for a in entry.get("safe_actions", [])
        if a["kind"] in {"manual", "read-only"} and a.get("privileged") is True
    ]
    assert not bad, "\n".join(bad)


# ---------------------------------------------------------------------------
# refines_to (NM-NET-001 mã thô) phải trỏ tới các phase thật có trong catalog.
# ---------------------------------------------------------------------------


def test_coarse_refines_to_points_at_real_phases_in_same_domain(catalog_data: dict) -> None:
    entries = catalog_data["entries"]
    checked_any = False
    for code, entry in entries.items():
        if not entry.get("coarse"):
            continue
        checked_any = True
        domain = entry["domain"]
        refines_to = entry.get("refines_to", [])
        assert refines_to, f"{code}: coarse=true nhưng refines_to rỗng"
        phases_of_domain = {
            e["phase"]
            for e in entries.values()
            if e["domain"] == domain and e["phase"] != "unknown"
        }
        for phase in refines_to:
            assert phase in phases_of_domain, (
                f"{code}: refines_to liệt kê phase '{phase}' nhưng không có mã nào trong "
                f"domain '{domain}' thực sự dùng phase đó (phases có thật: {sorted(phases_of_domain)})"
            )
    assert checked_any, "Không có mã coarse nào để kiểm — bất thường (NM-NET-001 phải coarse=true)"


# ---------------------------------------------------------------------------
# Parity catalog ↔ error-codes.md (EVENT-ERROR-CONTRACT.md §5 "Tính nhất quán
# bắt buộc").
# ---------------------------------------------------------------------------


def _codes_mentioned_in(text: str) -> set[str]:
    """Trích mọi mã NM-<NHÓM>-<3 số> LITERAL xuất hiện trong văn bản (bỏ qua
    placeholder dạng 'NM-<NHÓM>-000' hoặc 'NM-*-000' không phải mã thật), VÀ
    nở các dạng viết tắt gộp (vd 'NM-PERM-001/002') thành mã đầy đủ."""
    codes = set(_NM_CODE_RE.findall(text))
    for m in re.finditer(r"\bNM-([A-Z]+)-(\d{3})((?:/\d{3})+)\b", text):
        group, first, rest = m.group(1), m.group(2), m.group(3)
        codes.add(f"NM-{group}-{first}")
        for suffix in rest.split("/")[1:]:
            codes.add(f"NM-{group}-{suffix}")
    return codes


def test_catalog_codes_all_appear_in_error_codes_md(catalog_data: dict, error_codes_md_text: str) -> None:
    doc_codes = _codes_mentioned_in(error_codes_md_text)
    catalog_codes = set(catalog_data["entries"].keys())
    missing_in_doc = catalog_codes - doc_codes
    assert not missing_in_doc, (
        f"Các mã có trong catalog nhưng KHÔNG được nhắc trong error-codes.md: {sorted(missing_in_doc)}"
    )


def test_error_codes_md_codes_all_appear_in_catalog(catalog_data: dict, error_codes_md_text: str) -> None:
    doc_codes = _codes_mentioned_in(error_codes_md_text)
    catalog_codes = set(catalog_data["entries"].keys())
    missing_in_catalog = doc_codes - catalog_codes
    assert not missing_in_catalog, (
        f"Các mã được nhắc trong error-codes.md nhưng KHÔNG có trong catalog: {sorted(missing_in_catalog)}"
    )


def test_catalog_codes_all_appear_in_contract_md(catalog_data: dict, contract_md_text: str) -> None:
    """EVENT-ERROR-CONTRACT.md §3/§5 là nguồn mô tả phase; mọi mã cụ thể (trừ
    sentinel *-000, vốn được nói chung bằng mẫu 'NM-<NHÓM>-000') nên được
    nhắc tới đâu đó trong hợp đồng — tránh catalog có mã 'mồ côi' không được
    đặc tả ở văn bản hợp đồng."""
    doc_codes = _codes_mentioned_in(contract_md_text)
    catalog_codes = {c for c in catalog_data["entries"] if not c.endswith("-000")}
    missing = catalog_codes - doc_codes
    assert not missing, f"Mã có trong catalog nhưng không được hợp đồng {CONTRACT_MD_NAME} nhắc tới: {sorted(missing)}"


CONTRACT_MD_NAME = "EVENT-ERROR-CONTRACT.md"


# ---------------------------------------------------------------------------
# detector field trung thực: chỉ 2 giá trị dạng được phép (có .../specified ...)
# — tránh một mã tự xưng "có" (đã code thật) sai sự thật so với §5 ghi chú.
# ---------------------------------------------------------------------------


def test_detector_field_is_honest_vocab(catalog_data: dict) -> None:
    bad = [
        f"{k}: detector='{e['detector']}'"
        for k, e in catalog_data["entries"].items()
        if not (e["detector"].startswith("có") or e["detector"].startswith("specified"))
    ]
    assert not bad, "\n".join(bad)


def test_detector_has_vs_specified_matches_known_set_of_implemented_codes(catalog_data: dict) -> None:
    """8 mã CŨ (đã có detector thật trong namios-chan-doan, theo
    error-codes.md §3) phải detector='có'; mọi mã KHÁC (phase mịn mới của
    hợp đồng) phải detector bắt đầu bằng 'specified' — ghi thật tình trạng,
    tránh quảng cáo quá năng lực hiện tại (đúng nguyên tắc nêu ở catalog
    §5 cột detector)."""
    implemented = {
        "NM-NET-001",
        "NM-NET-002",
        "NM-DRV-001",
        "NM-DRV-002",
        "NM-DSK-001",
        "NM-PERM-001",
        "NM-PERM-002",
        "NM-APP-001",
        "NM-APP-002",
    }
    # Các mã sentinel *-000 có detector='có (mặc định khi nhánh dưới không
    # khớp)' — đây CŨNG là một detector thật (nhánh else), tính là implemented.
    sentinels = {k for k in catalog_data["entries"] if k.endswith("-000")}
    implemented |= sentinels

    bad = []
    for code, entry in catalog_data["entries"].items():
        is_co = entry["detector"].startswith("có")
        should_be_co = code in implemented
        if is_co != should_be_co:
            bad.append(
                f"{code}: detector bắt đầu bằng "
                f"{'có' if is_co else 'specified'} nhưng theo tập mã đã-triển-khai "
                f"thì phải {'có' if should_be_co else 'specified'}"
            )
    assert not bad, "\n".join(bad)


