"""Test System Inventory SmartAI M1 (SAI-006, Phụ lục 04).

Nghiệm thu: inventory CHỈ metadata — khai báo đúng những gì đã đọc qua
``read_fields`` (tiền tố ``declared.*``/``host.*`` duy nhất), KHÔNG BAO GIỜ
kéo theo thư mục cá nhân/nội dung file/dữ liệu kế toán (``out_of_scope``
luôn liệt kê các vùng đó), và thiết bị/máy in/token chỉ phản ánh đúng thứ
caller khai báo — không tự dò quét."""

from __future__ import annotations

from namios_smartai.inventory import collect_inventory, inventory_from_declared


def test_inventory_from_declared_dat_dung_truong_khai_bao() -> None:
    inv = inventory_from_declared(app_id="misa", app_version="2024")
    assert inv.app_id == "misa"
    assert inv.app_version == "2024"
    assert "declared.app_id" in inv.read_fields
    assert "declared.app_version" in inv.read_fields
    assert not any(f.startswith("host.") for f in inv.read_fields)
    assert inv.os == "unknown"


def test_collect_inventory_include_host_doc_metadata_host() -> None:
    inv = collect_inventory(app_id="misa", include_host=True)
    assert "host.os" in inv.read_fields
    assert "host.cpu_arch" in inv.read_fields
    assert "host.kernel" in inv.read_fields
    assert "declared.app_id" in inv.read_fields
    assert inv.os != ""
    assert inv.cpu_arch != ""
    assert inv.os != "unknown"
    assert inv.cpu_arch != "unknown"


def test_collect_inventory_khong_include_host_khong_doc_host() -> None:
    inv = collect_inventory(app_id="misa", include_host=False)
    assert not any(f.startswith("host.") for f in inv.read_fields)
    assert inv.os == "unknown"
    assert inv.cpu_arch == "unknown"
    assert inv.kernel is None


def test_out_of_scope_declared_khong_rong_va_chua_vung_ca_nhan() -> None:
    inv = inventory_from_declared(app_id="misa")
    assert inv.out_of_scope
    assert "home_documents" in inv.out_of_scope
    assert "file_contents" in inv.out_of_scope
    assert "accounting_data" in inv.out_of_scope


def test_out_of_scope_collect_host_khong_rong_va_chua_vung_ca_nhan() -> None:
    inv = collect_inventory(app_id="misa", include_host=True)
    assert inv.out_of_scope
    assert "home_documents" in inv.out_of_scope
    assert "file_contents" in inv.out_of_scope
    assert "accounting_data" in inv.out_of_scope


def test_read_fields_chi_chua_tien_to_declared_hoac_host_tu_declared() -> None:
    inv = inventory_from_declared(
        app_id="misa",
        app_version="2024",
        runtime=".NET",
        browser="chrome",
        devices=("HP-123",),
        printers=("Canon-1",),
        tokens=("tok-1",),
        network_ports=("8080",),
    )
    assert inv.read_fields
    for field_name in inv.read_fields:
        assert field_name.startswith("declared.") or field_name.startswith("host.")


def test_read_fields_chi_chua_tien_to_declared_hoac_host_tu_collect() -> None:
    inv = collect_inventory(
        app_id="misa",
        devices=("HP-123",),
        include_host=True,
    )
    assert inv.read_fields
    for field_name in inv.read_fields:
        assert field_name.startswith("declared.") or field_name.startswith("host.")


def test_devices_printers_tokens_chi_phan_anh_khai_bao_tu_declared() -> None:
    inv = inventory_from_declared(devices=("HP-123",))
    assert inv.devices == ("HP-123",)
    assert inv.printers == ()
    assert inv.tokens == ()


def test_devices_printers_tokens_chi_phan_anh_khai_bao_tu_collect() -> None:
    inv = collect_inventory(devices=("HP-123",), include_host=True)
    assert inv.devices == ("HP-123",)
    assert inv.printers == ()
    assert inv.tokens == ()


def test_devices_mac_dinh_rong() -> None:
    inv = inventory_from_declared()
    assert inv.devices == ()
    assert inv.printers == ()
    assert inv.tokens == ()
    assert inv.network_ports == ()
    assert inv.read_fields == ()
