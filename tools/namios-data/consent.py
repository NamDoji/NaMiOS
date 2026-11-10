#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMi Data Pipeline — cổng đồng ý nguồn dữ liệu (consent gate).

Theo `docs/specs/namioffice-v2/02_WRITER_SHEET_SLIDES.md` §B: "Chặn truy vấn
ngoài mạng khi mở tệp, yêu cầu consent nguồn và chỉ rõ dữ liệu sẽ gửi" và
`docs/office/COMPAT-MATRIX.md` dòng `SH-F2-03` (Gate P0: "không mở kết nối
ngoài ngoài ý muốn").

Quy tắc của module này:
  * Nguồn CỤC BỘ (csv/json đọc từ đĩa) — KHÔNG BAO GIỜ cần consent, không bao
    giờ tự ra mạng.
  * Nguồn MẠNG (sql/web) — bị CHẶN theo mặc định. Chỉ chạy nếu caller truyền
    `consent=True` MỘT CÁCH TƯỜNG MINH cho đúng pipeline/run đó (không có cờ
    toàn cục "luôn đồng ý"). Trước khi chặn/cho phép, `describe()` phải trả
    về một câu mô tả CHÍNH XÁC những gì sẽ được gửi/đọc, để hiển thị cho
    người dùng xác nhận.

Trạng thái triển khai: cổng chặn là THẬT (test được) — nhưng ở prototype này
CHƯA có client HTTP/SQL thật nào được nối sau cổng (`sources.py` ném
`NotImplementedError` ngay cả khi `consent=True`). Do đó: "có consent-gate"
≠ "có kết nối mạng/SQL hoạt động". Xem docs/office/NAMI-DATA-PIPELINE.md
mục "KHÔNG phải".
"""
from __future__ import annotations

from dataclasses import dataclass

#: Các loại nguồn được xem là "cục bộ, không ra mạng".
LOCAL_SOURCE_KINDS = frozenset({"csv", "json"})

#: Các loại nguồn được xem là "ra mạng" — luôn cần consent tường minh.
NETWORK_SOURCE_KINDS = frozenset({"sql", "web"})

ALL_SOURCE_KINDS = LOCAL_SOURCE_KINDS | NETWORK_SOURCE_KINDS


class ConsentRequiredError(PermissionError):
    """Nguồn mạng bị chặn vì thiếu `consent=True` tường minh."""


@dataclass(frozen=True)
class ConsentNotice:
    """Mô tả CHÍNH XÁC dữ liệu sẽ gửi/đọc, hiển thị cho người dùng trước khi
    họ bấm đồng ý. `will_send` nêu rõ những gì RỜI khỏi máy (ví dụ: tham số
    truy vấn, chuỗi kết nối) — KHÔNG mơ hồ "sẽ kết nối Internet"."""

    source_kind: str
    uri: str
    will_send: str
    will_receive: str

    def render_vi(self) -> str:
        return (
            f"Nguồn '{self.source_kind}' tại {self.uri!r}.\n"
            f"  Sẽ GỬI ra ngoài: {self.will_send}\n"
            f"  Sẽ NHẬN về: {self.will_receive}\n"
            f"  Đây là nguồn MẠNG — cần bạn đồng ý tường minh (consent=True) mỗi lần dùng."
        )


def describe(source_kind: str, uri: str, *, query: str = "") -> ConsentNotice:
    """Dựng thông báo consent cho một nguồn. Với nguồn cục bộ, thông báo nói
    rõ KHÔNG có gì rời máy."""
    if source_kind in LOCAL_SOURCE_KINDS:
        return ConsentNotice(
            source_kind=source_kind,
            uri=uri,
            will_send="(không có gì — nguồn cục bộ, không ra mạng)",
            will_receive=f"nội dung file {uri!r} đọc từ đĩa cục bộ",
        )
    if source_kind in NETWORK_SOURCE_KINDS:
        sent = f"địa chỉ/chuỗi kết nối {uri!r}" + (f" + câu truy vấn: {query!r}" if query else "")
        return ConsentNotice(
            source_kind=source_kind,
            uri=uri,
            will_send=sent,
            will_receive="dữ liệu trả về từ nguồn mạng đó (không kiểm soát được nội dung)",
        )
    raise ValueError(f"source_kind không hợp lệ: {source_kind!r} (hợp lệ: {sorted(ALL_SOURCE_KINDS)!r})")


def check_consent(source_kind: str, uri: str, *, consent: bool, query: str = "") -> None:
    """Cổng chặn. Gọi TRƯỚC khi mở bất kỳ nguồn nào trong `sources.py`.

    * Nguồn cục bộ: luôn qua (no-op).
    * Nguồn mạng + consent=False: ném `ConsentRequiredError` kèm nguyên văn
      thông báo consent (để log/hiển thị lại được).
    * Nguồn mạng + consent=True: qua cổng này (không có nghĩa là có client
      mạng thật — xem docstring module)."""
    if source_kind in LOCAL_SOURCE_KINDS:
        return
    if source_kind not in NETWORK_SOURCE_KINDS:
        raise ValueError(f"source_kind không hợp lệ: {source_kind!r}")
    notice = describe(source_kind, uri, query=query)
    if not consent:
        raise ConsentRequiredError(
            "Nguồn mạng bị CHẶN vì thiếu đồng ý tường minh (consent=True).\n"
            + notice.render_vi()
        )


__all__ = [
    "LOCAL_SOURCE_KINDS",
    "NETWORK_SOURCE_KINDS",
    "ALL_SOURCE_KINDS",
    "ConsentRequiredError",
    "ConsentNotice",
    "describe",
    "check_consent",
]
