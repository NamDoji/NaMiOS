"""SEC-002 FINDING — ``namios_manifest._safe_io.read_text_safe`` có cua so
TOCTOU giua buoc kiem ``realpath`` va buoc ``os.open`` cuoi, vi module nay
KHONG dung FD-based walk (``dir_fd`` + ``O_NOFOLLOW`` tung buoc) nhu
``namios_security.safe_path`` — no tu che mot ban "interim" (xem docstring
module: "chua co namios_security (WP8)... TODO chuyen sang goi no").

``ManifestValidatorImpl.load()`` (API cong khai WP2, M1-INTERFACES §7.1) goi
thang ham nay de doc file manifest TU NGUON KHONG TIN CAY (catalog/profile
cua actor TA-01) — day la API tan cong thuc, khong phai code noi bo.

Repro (mo phong attacker thang race): ngay truoc loi goi ``os.open(path,
O_NOFOLLOW, ...)`` o cuoi ham, doi MOT THANH PHAN TRUNG GIAN cua duong dan
(da duoc kiem ``realpath`` la thu muc thuong truoc do) thanh symlink tro ra
ngoai. ``O_NOFOLLOW`` chi chan symlink o THANH PHAN CUOI cua duong dan khi
goi ``os.open`` voi mot chuoi path day -- KHONG chan duoc symlink o thanh
phan TRUNG GIAN (kernel van resolve binh thuong cac thanh phan truoc do).
Ket qua: ham doc duoc noi dung mot file NGOAI thu muc du dinh, bo qua toan
bo bat bien "khong symlink trung gian" ma docstring tuyen bo.

KHONG tu sua ``namios_manifest/_safe_io.py`` (ngoai pham vi vai tro nay) —
giu test nay lam bang chung cho SEC-SWEEP-002."""

from __future__ import annotations

import os
import shutil


def test_read_text_safe_toctou_intermediate_dir_swap_leaks_outside_file(tmp_path) -> None:
    import namios_manifest._safe_io as safe_io_mod

    real_subdir = tmp_path / "profiles"
    real_subdir.mkdir()
    manifest_path = real_subdir / "app.manifest.json"
    manifest_path.write_text('{"id": "khong-doc-duoc-cai-nay"}')

    attacker_dir = tmp_path / "attacker_dir"
    attacker_dir.mkdir()
    (attacker_dir / "app.manifest.json").write_text(
        '{"id": "DA BI DOC TU NGOAI thu muc profiles du dinh"}'
    )

    path_to_read = str(manifest_path)
    orig_open = os.open
    swapped = {"done": False}

    def evil_open(path, flags, *a, **kw):
        if path == path_to_read and not swapped["done"]:
            swapped["done"] = True
            # Attacker thang race NGAY TRUOC khi os.open() thuc su chay:
            # doi thu muc trung gian "profiles" thanh symlink -> attacker_dir.
            shutil.rmtree(real_subdir)
            os.symlink(str(attacker_dir), real_subdir)
        return orig_open(path, flags, *a, **kw)

    os.open = evil_open
    try:
        content = safe_io_mod.read_text_safe(path_to_read)
    finally:
        os.open = orig_open

    # Ky vong AN TOAN (nhung se KHONG xay ra — day la bang chung lo hong):
    # phai raise PathUnsafeError, KHONG tra ve noi dung tu ngoai pham vi.
    assert "DA BI DOC TU NGOAI" not in content, (
        "VULNERABLE: read_text_safe() da doc xuyen symlink trung gian bi "
        f"doi giua luc kiem va luc mo (TOCTOU) -- noi dung ro: {content!r}"
    )
