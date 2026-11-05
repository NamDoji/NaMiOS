"""Doc drift-guard: tài liệu cộng đồng phải khớp repo thật (không để mục rữa).

Không phụ thuộc thư viện ngoài (chỉ stdlib) — giữ đúng ràng buộc lõi không deps.
"""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]


def _read(rel: str) -> str:
    return (_REPO / rel).read_text(encoding="utf-8")


def test_architecture_lists_every_src_package() -> None:
    """docs/ARCHITECTURE.md phải nhắc tới MỌI package `src/namios_*` — nếu thêm
    package mà quên cập nhật bản đồ, test này đỏ."""
    arch = _read("docs/ARCHITECTURE.md")
    packages = sorted(p.name for p in (_REPO / "src").iterdir() if p.name.startswith("namios_"))
    assert packages, "không thấy package namios_* nào trong src/"
    missing = [p for p in packages if p not in arch]
    assert not missing, f"docs/ARCHITECTURE.md thiếu các package: {missing}"


def test_contributing_cites_the_real_gate() -> None:
    """CONTRIBUTING phải nêu đúng 4 lệnh cổng chất lượng (khớp CI/pyproject)."""
    doc = _read("CONTRIBUTING.md")
    for cmd in ("ruff check src", "black --check src", "mypy src/namios_core", "pytest"):
        assert cmd in doc, f"CONTRIBUTING.md thiếu lệnh cổng: {cmd}"


def test_core_community_docs_present_and_nonempty() -> None:
    for rel in (
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "docs/ARCHITECTURE.md",
        "docs/community/COMPATIBILITY-CONTRIBUTION.md",
        "docs/SECURITY.md",
    ):
        assert (_REPO / rel).is_file(), f"thiếu tài liệu: {rel}"
        assert len(_read(rel).strip()) > 200, f"tài liệu quá ngắn/rỗng: {rel}"


def test_issue_templates_present() -> None:
    tmpl = _REPO / ".github" / "ISSUE_TEMPLATE"
    for name in ("bug_report.yml", "compatibility_report.yml", "feature_request.yml", "config.yml"):
        f = tmpl / name
        assert f.is_file(), f"thiếu issue template: {name}"
        assert "name:" in f.read_text(encoding="utf-8") or name == "config.yml"
    assert (_REPO / ".github" / "PULL_REQUEST_TEMPLATE.md").is_file()


def test_honest_status_rule_is_stated() -> None:
    """Nguyên tắc số 1 (không nhãn 'đạt' khi chưa có bằng chứng) PHẢI xuất hiện
    trong bản đồ kiến trúc — đây là bất biến văn hoá + kỹ thuật của dự án."""
    arch = _read("docs/ARCHITECTURE.md")
    assert "blocked" in arch.lower()
    assert "bằng chứng" in arch or "evidence" in arch.lower()


def test_ci_workflow_enforces_the_gate() -> None:
    """Cổng chất lượng phải được CI THỰC THI (không chỉ ghi trong tài liệu): CI
    tồn tại và chạy đúng 4 lệnh cổng trên cả src lẫn tests."""
    ci = _REPO / ".github" / "workflows" / "ci.yml"
    assert ci.is_file(), "thiếu .github/workflows/ci.yml — cổng không được thực thi"
    text = ci.read_text(encoding="utf-8")
    for cmd in (
        "ruff check src tests",
        "black --check src tests",
        "mypy src/namios_core",
        "pytest",
    ):
        assert cmd in text, f"ci.yml thiếu lệnh cổng: {cmd}"
