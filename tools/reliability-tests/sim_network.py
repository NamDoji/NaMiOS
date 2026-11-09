"""SỰ KIỆN MẠNG MÔ PHỎNG (simulated) — KHÔNG đụng Wi-Fi/Ethernet thật.

Hai lớp test tách bạch rõ ràng (đọc kỹ trước khi thêm test mới):

  A) REAL TOOL — gọi THẬT `namios-chan-doan` (subprocess, PATH trỏ vào lệnh
     `ip`/`nmcli` GIẢ do FakeBin dựng) để kiểm 2 mã THÔ đã có detector thật
     (NM-NET-001 mất mạng, NM-NET-002 portal/limited) + đường xuống cấp khi
     thiếu `ip`/`nmcli`. Đây là test tích hợp THẬT trên script thật.

  B) ORACLE THAM CHIẾU (reference oracle, `classify_network_phase` dưới) —
     hiện thực THUẦN PYTHON của bảng quyết định radio→ssid→auth→ip→dns→portal
     ở EVENT-ERROR-CONTRACT.md §3.1. KHÔNG CÓ detector thật nào trong
     `namios-chan-doan` làm việc này — catalog tự khai `detector: "specified
     (... — chưa thêm vào namios-chan-doan)"` cho mọi mã NM-NET-003..007.
     Oracle ở đây tồn tại để: (1) chứng minh bảng quyết định của hợp đồng là
     tất định/khả thi, (2) khoá lại hành vi mong đợi bằng test trước khi code
     thật được viết, (3) khi namios-chan-doan thêm detector thật cho các mã
     này (bước tiếp theo U13-08), bảng quyết định NÊN COPY từ đây và test
     NÊN ĐỔI sang gọi hàm thật — tránh lệch "hai cách hiểu" giữa test và
     code. Mọi test ở lớp B được đánh dấu rõ bằng tiền tố `test_oracle_*`.

Chạy: python3 -m pytest tools/reliability-tests/sim_network.py -v
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from conftest import FakeBin

# ===========================================================================
# A) REAL TOOL — namios-chan-doan, màn hình 1 (Mạng)
# ===========================================================================


def _net_fake_bin(
    fake_bin: FakeBin,
    *,
    up_iface: bool,
    has_default_route: bool,
    connectivity: str | None,
    has_ip_cmd: bool = True,
    has_nmcli_cmd: bool = True,
) -> FakeBin:
    """Dựng `ip`/`nmcli` giả mô phỏng CHÍNH XÁC dạng output thật mà
    net_report() của namios-chan-doan phân tích (xem awk -F': ' trên dòng
    `ip -o link show up`)."""
    if has_ip_cmd:
        up_line = (
            "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP"
            if up_iface
            else ""
        )
        route_line = "default via 192.0.2.1 dev eth0" if has_default_route else ""
        fake_bin.add(
            "ip",
            f"""
case "$*" in
  "-o link show up") printf '%s\\n' "{up_line}" ;;
  "route show default") printf '%s\\n' "{route_line}" ;;
esac
exit 0
""",
        )
    else:
        fake_bin.missing("ip")

    if has_nmcli_cmd:
        conn_out = connectivity or ""
        fake_bin.add(
            "nmcli",
            f"""
case "$*" in
  "networking connectivity") printf '%s\\n' "{conn_out}" ;;
esac
exit 0
""",
        )
    else:
        fake_bin.missing("nmcli")
    return fake_bin


def _run_net_screen(run_cli, chan_doan_bin: Path, fake_bin: FakeBin, home: Path) -> str:
    """Điều hướng namios-chan-doan (TTY fallback, không kdialog) tới màn hình
    1 (Mạng) rồi thoát ngay — trả toàn bộ stdout."""
    proc = run_cli(
        ["bash", str(chan_doan_bin)],
        path_env=fake_bin.path_env(),
        stdin_text="1\n\n0\n",
        home=home,
    )
    assert proc.returncode == 0, f"chan-doan phải luôn exit 0; stderr={proc.stderr!r}"
    return proc.stdout


def test_real_net_down_no_interface(run_cli, chan_doan_bin, fake_bin, tmp_path):
    _net_fake_bin(fake_bin, up_iface=False, has_default_route=False, connectivity=None)
    out = _run_net_screen(run_cli, chan_doan_bin, fake_bin, tmp_path)
    assert "[NM-NET-001]" in out
    assert "MẤT MẠNG" in out


def test_real_net_down_route_missing_even_if_iface_up(run_cli, chan_doan_bin, fake_bin, tmp_path):
    """up_iface=True nhưng KHÔNG có default route — net_report() vẫn báo
    NM-NET-001 ('or' logic: thiếu MỘT trong hai là đủ)."""
    _net_fake_bin(fake_bin, up_iface=True, has_default_route=False, connectivity=None)
    out = _run_net_screen(run_cli, chan_doan_bin, fake_bin, tmp_path)
    assert "[NM-NET-001]" in out


@pytest.mark.parametrize("bad_connectivity", ["limited", "portal", "none"])
def test_real_net_portal_or_limited(run_cli, chan_doan_bin, fake_bin, tmp_path, bad_connectivity):
    _net_fake_bin(fake_bin, up_iface=True, has_default_route=True, connectivity=bad_connectivity)
    out = _run_net_screen(run_cli, chan_doan_bin, fake_bin, tmp_path)
    assert "[NM-NET-002]" in out
    assert "[NM-NET-001]" not in out


def test_real_net_ok_when_full_connectivity(run_cli, chan_doan_bin, fake_bin, tmp_path):
    _net_fake_bin(fake_bin, up_iface=True, has_default_route=True, connectivity="full")
    out = _run_net_screen(run_cli, chan_doan_bin, fake_bin, tmp_path)
    assert "[OK]" in out
    assert "NM-NET-001" not in out
    assert "NM-NET-002" not in out


def test_real_net_degrades_without_nmcli_does_not_fabricate_ok(run_cli, chan_doan_bin, fake_bin, tmp_path):
    """Thiếu nmcli: có giao diện + route nhưng KHÔNG biết connectivity thật —
    tool PHẢI báo '[--]' (không xác định), KHÔNG được suy diễn thành [OK]
    (nguyên tắc 'false negative nguy hiểm hơn im lặng', error-codes.md §3)."""
    _net_fake_bin(fake_bin, up_iface=True, has_default_route=True, connectivity=None, has_nmcli_cmd=False)
    out = _run_net_screen(run_cli, chan_doan_bin, fake_bin, tmp_path)
    assert "[--]" in out
    assert "[OK]" not in out
    assert "NM-NET-001" not in out
    assert "NM-NET-002" not in out


def test_real_net_degrades_without_ip_command(run_cli, chan_doan_bin, fake_bin, tmp_path):
    """Thiếu lệnh `ip` (iproute2) hoàn toàn — tool phải báo rõ 'không xác
    định được' và KHÔNG được in bất kỳ mã NM-NET-* nào (không có dữ liệu để
    phân loại), vẫn exit 0."""
    fake_bin.missing("ip")
    fake_bin.add("nmcli", "exit 0")  # không được gọi tới nếu ip thiếu (return sớm)
    out = _run_net_screen(run_cli, chan_doan_bin, fake_bin, tmp_path)
    assert "Không có lệnh 'ip'" in out
    assert "NM-NET-001" not in out
    assert "NM-NET-002" not in out
    assert not fake_bin.called("nmcli"), "net_report() return sớm khi thiếu ip — không được gọi nmcli"


# ===========================================================================
# B) ORACLE THAM CHIẾU — bảng quyết định radio→ssid→auth→ip→dns→portal
# ===========================================================================


@dataclass
class NetEvidence:
    """Tín hiệu read-only y hệt cột 'Bằng chứng' ở EVENT-ERROR-CONTRACT.md
    §3.1 / error-codes.md §6.1. `None` = chưa quan sát được / không áp dụng."""

    radio_wifi_disabled: bool | None = None
    rfkill_blocked: bool | None = None
    desired_ssid_requested: str | None = None
    desired_ssid_seen_in_scan: bool | None = None
    nm_need_auth_repeated: bool | None = None
    ip_link_local_only: bool | None = None
    has_default_route: bool | None = None
    dns_resolution_failed: bool | None = None
    connectivity: str | None = None  # "full" | "limited" | "portal" | "none"


def classify_network_phase(ev: NetEvidence) -> tuple[str, str]:
    """Oracle THAM CHIẾU (test-only, xem docstring đầu file). Trả
    (phase, cause_code); phase='ok' nếu không có lỗi; phase='unknown' +
    NM-NET-000 nếu bằng chứng không đủ để quy về một bước cụ thể.

    Thứ tự kiểm ĐÚNG pipeline §3.1: radio → ssid → auth → ip → dns → portal —
    dừng ở bước ĐẦU TIÊN có bằng chứng thất bại (không bịa nguyên nhân khi
    thiếu bằng chứng)."""
    if ev.radio_wifi_disabled or ev.rfkill_blocked:
        return ("radio", "NM-NET-003")
    if ev.desired_ssid_requested and ev.desired_ssid_seen_in_scan is False:
        return ("ssid", "NM-NET-004")
    if ev.nm_need_auth_repeated:
        return ("auth", "NM-NET-005")
    if ev.ip_link_local_only or ev.has_default_route is False:
        return ("ip", "NM-NET-006")
    if ev.dns_resolution_failed and ev.has_default_route:
        return ("dns", "NM-NET-007")
    if ev.connectivity in {"limited", "portal", "none"}:
        return ("portal", "NM-NET-002")
    if ev.connectivity == "full":
        return ("ok", "")
    return ("unknown", "NM-NET-000")


@pytest.mark.parametrize(
    "evidence,expected_phase,expected_code",
    [
        (NetEvidence(radio_wifi_disabled=True), "radio", "NM-NET-003"),
        (NetEvidence(rfkill_blocked=True), "radio", "NM-NET-003"),
        (
            NetEvidence(desired_ssid_requested="VanPhong_5G", desired_ssid_seen_in_scan=False),
            "ssid",
            "NM-NET-004",
        ),
        (NetEvidence(nm_need_auth_repeated=True), "auth", "NM-NET-005"),
        (NetEvidence(ip_link_local_only=True), "ip", "NM-NET-006"),
        (NetEvidence(has_default_route=False), "ip", "NM-NET-006"),
        (
            NetEvidence(has_default_route=True, dns_resolution_failed=True),
            "dns",
            "NM-NET-007",
        ),
        (NetEvidence(connectivity="portal"), "portal", "NM-NET-002"),
        (NetEvidence(connectivity="limited"), "portal", "NM-NET-002"),
        (NetEvidence(connectivity="none"), "portal", "NM-NET-002"),
        (NetEvidence(connectivity="full"), "ok", ""),
    ],
)
def test_oracle_phase_detection(evidence, expected_phase, expected_code):
    phase, code = classify_network_phase(evidence)
    assert (phase, code) == (expected_phase, expected_code)


def test_oracle_insufficient_evidence_is_unknown_never_fabricated():
    phase, code = classify_network_phase(NetEvidence())
    assert (phase, code) == ("unknown", "NM-NET-000")


def test_oracle_ssid_evidence_without_knowing_desired_name_is_unknown():
    """Nếu không biết TÊN mạng mong muốn, 'không thấy SSID' không thể quy kết
    — catalog NM-NET-004 ghi rõ 'nếu không biết tên mạng mong muốn thì bằng
    chứng chưa đủ → CHƯA XÁC ĐỊNH' (error-codes.md §6.1 cột Ý nghĩa)."""
    ev = NetEvidence(desired_ssid_seen_in_scan=False)  # không có desired_ssid_requested
    phase, code = classify_network_phase(ev)
    assert (phase, code) == ("unknown", "NM-NET-000")


def test_oracle_earliest_pipeline_stage_wins_on_contradictory_evidence():
    """Bằng chứng mâu thuẫn/không thực tế (radio tắt NHƯNG lại có dấu hiệu DNS
    lỗi) — pipeline vẫn phải dừng ở bước SỚM NHẤT (radio), đúng nguyên tắc
    'lỗi được định vị ở bước ĐẦU TIÊN thất bại' (§3)."""
    ev = NetEvidence(
        radio_wifi_disabled=True,
        has_default_route=True,
        dns_resolution_failed=True,
        connectivity="portal",
    )
    phase, code = classify_network_phase(ev)
    assert (phase, code) == ("radio", "NM-NET-003")


def test_oracle_outputs_always_match_catalog_phase_and_domain(catalog_data):
    """Catalog ↔ oracle: với MỌI (phase, cause_code) oracle có thể trả ra
    (trừ 'ok' không có mã), catalog PHẢI có entry đó với đúng phase + domain
    'mang' — khoá hành vi oracle luôn khớp nguồn sự thật máy-đọc."""
    sample_evidences = [
        NetEvidence(radio_wifi_disabled=True),
        NetEvidence(rfkill_blocked=True),
        NetEvidence(desired_ssid_requested="x", desired_ssid_seen_in_scan=False),
        NetEvidence(nm_need_auth_repeated=True),
        NetEvidence(ip_link_local_only=True),
        NetEvidence(has_default_route=True, dns_resolution_failed=True),
        NetEvidence(connectivity="portal"),
        NetEvidence(),
    ]
    for ev in sample_evidences:
        phase, code = classify_network_phase(ev)
        if phase == "ok":
            continue
        assert code in catalog_data["entries"], f"{code} (phase={phase}) không có trong catalog"
        entry = catalog_data["entries"][code]
        assert entry["phase"] == phase, f"{code}: oracle phase={phase} != catalog phase={entry['phase']}"
        assert entry["domain"] == "mang"
