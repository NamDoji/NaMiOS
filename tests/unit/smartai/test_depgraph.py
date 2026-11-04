"""SAI-007 — Dependency Graph: required node chưa observed/có blocker → chặn execute."""

from __future__ import annotations

from namios_smartai._types import DepKind, DepNode, NodeStatus
from namios_smartai.depgraph import build_graph, execute_blockers, is_execute_blocked


def test_app_opens_but_db_missing_blocks_execute() -> None:
    g = build_graph(
        "vn.accounting.sme_books",
        (
            DepNode("misa.exe", DepKind.INSTALLER, NodeStatus.OBSERVED, required=True),
            DepNode("runtime", DepKind.RUNTIME, NodeStatus.OBSERVED, required=True),
            DepNode("sqlserver", DepKind.DATABASE, NodeStatus.UNKNOWN, required=True),
        ),
    )
    assert is_execute_blocked(g)
    assert any("sqlserver" in b for b in execute_blockers(g))


def test_all_observed_not_blocked() -> None:
    g = build_graph(
        "w",
        (
            DepNode("a", DepKind.RUNTIME, NodeStatus.OBSERVED, required=True),
            DepNode("b", DepKind.BROWSER, NodeStatus.OBSERVED, required=True),
        ),
    )
    assert not is_execute_blocked(g)
    assert execute_blockers(g) == ()


def test_explicit_blocker_blocks_even_if_observed() -> None:
    g = build_graph(
        "w",
        (
            DepNode(
                "tok",
                DepKind.TOKEN,
                NodeStatus.OBSERVED,
                required=True,
                blocker="middleware Windows-only",
            ),
        ),
    )
    assert is_execute_blocked(g)


def test_optional_unknown_node_does_not_block() -> None:
    g = build_graph(
        "w",
        (DepNode("doc", DepKind.DOCUMENT, NodeStatus.UNKNOWN, required=False),),
    )
    assert not is_execute_blocked(g)
