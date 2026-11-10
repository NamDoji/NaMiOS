#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMi Data Pipeline — lắp nguồn + danh sách bước thành một pipeline tái lập.

Đây là lớp trung tâm của prototype "Get & Transform tương đương"
(`docs/specs/namioffice-v2/02_WRITER_SHEET_SLIDES.md` §B,
`docs/office/COMPAT-MATRIX.md` dòng SH-F2-01/02). Một `Pipeline`:

  1. Có MỘT nguồn chính (`source: SourceSpec`) + 0..n nguồn phụ đặt tên
     (`aux_sources`) dùng cho các bước merge/append.
  2. Có một DANH SÁCH BƯỚC có thứ tự (`steps`), mỗi bước THUẦN (xem
     `steps.py`), serialize được sang JSON và nạp lại được
     (`to_json`/`from_json`).
  3. `run()` đọc lại TOÀN BỘ nguồn từ đĩa + chạy lại TOÀN BỘ danh sách bước
     theo thứ tự — đây CHÍNH LÀ "refresh": không có khái niệm "refresh" khác
     với "run lần đầu", vì mọi bước thuần/deterministic nên refresh = đọc lại
     nguồn + replay. Mỗi lần `run()` ghi MỘT bản ghi vào `history` (thời
     điểm, số dòng kết quả, hash nội dung) — lịch sử chạy, KHÔNG phải lịch
     sử SỬA bước (đó là chính danh sách `steps`, đã có thứ tự + JSON hoá).

Trạng thái triển khai: prototype dev — chạy trong một tiến trình Python,
không có cache đĩa riêng (nguồn cục bộ đọc lại rất rẻ nên không cần), không
có secret vault (chưa có nguồn cần secret vì sql/web chưa nối client thật).
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from sources import SourceSpec, read_source
from steps import step_from_dict
from table import Table

SCHEMA_VERSION = 1


@dataclass
class Pipeline:
    name: str
    source: SourceSpec
    steps: List[Any] = field(default_factory=list)
    aux_sources: Dict[str, SourceSpec] = field(default_factory=dict)
    consent: bool = False
    history: List[dict] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Xây dựng pipeline (builder, trả về self để chain được)
    # ------------------------------------------------------------------ #
    def add_step(self, step: Any) -> "Pipeline":
        self.steps.append(step)
        return self

    def add_aux_source(self, name: str, spec: SourceSpec) -> "Pipeline":
        if name in self.aux_sources:
            raise ValueError(f"aux_source {name!r} đã tồn tại")
        self.aux_sources[name] = spec
        return self

    # ------------------------------------------------------------------ #
    # Chạy / refresh
    # ------------------------------------------------------------------ #
    def run(self) -> Table:
        """Đọc lại nguồn chính + mọi nguồn phụ TỪ ĐẦU, rồi chạy lại toàn bộ
        `steps` theo thứ tự. Đây cũng chính là hàm `refresh` — xem docstring
        module."""
        table = read_source(self.source, consent=self.consent)
        aux_tables: Dict[str, Table] = {
            n: read_source(spec, consent=self.consent) for n, spec in self.aux_sources.items()
        }
        for step in self.steps:
            table = step.apply(table, aux_tables)
        self.history.append(
            {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
                "step_count": len(self.steps),
                "row_count": len(table.rows),
                "output_hash": table.content_hash(),
            }
        )
        return table

    # `refresh` là alias có chủ đích của `run`: "refresh" trong Get & Transform
    # nghĩa là đọc lại nguồn + áp lại các bước đã ghi — ở đây KHÔNG có trạng
    # thái nào khác giữa "chạy lần đầu" và "refresh" vì mọi bước đều thuần.
    refresh = run

    # ------------------------------------------------------------------ #
    # Serialize / deserialize (để test "replay")
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "name": self.name,
            "source": self.source.to_dict(),
            "aux_sources": {n: s.to_dict() for n, s in self.aux_sources.items()},
            "steps": [s.to_dict() for s in self.steps],
            "consent": self.consent,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "Pipeline":
        if d.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(
                f"schema_version không khớp: nhận {d.get('schema_version')!r}, "
                f"cần {SCHEMA_VERSION!r}"
            )
        pipeline = cls(
            name=d["name"],
            source=SourceSpec.from_dict(d["source"]),
            consent=d.get("consent", False),
        )
        for n, s in d.get("aux_sources", {}).items():
            pipeline.add_aux_source(n, SourceSpec.from_dict(s))
        for step_dict in d.get("steps", []):
            pipeline.add_step(step_from_dict(step_dict))
        return pipeline

    @classmethod
    def from_json(cls, s: str) -> "Pipeline":
        return cls.from_dict(json.loads(s))


__all__ = ["Pipeline", "SCHEMA_VERSION"]
