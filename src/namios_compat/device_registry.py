"""Danh bạ năng lực thiết bị (COMP-032, kèm COMP-036 nhóm thiết bị chuyên
ngành — Phụ lục 03).

NGUYÊN TẮC CỐT LÕI (COMP-032): KHÔNG có khái niệm "hỗ trợ máy in" chung
chung. Mỗi ``DeviceEntry`` khai báo CHỨC NĂNG đã test riêng cho ĐÚNG model
(``tested_functions``) qua ĐÚNG giao thức (``protocol``). Thiết bị cùng hãng
nhưng khác model KHÔNG BAO GIỜ được tự suy ra là dùng được — đây là lý do
``capability_by_model`` có nhánh "no-carryover" riêng, từ chối cả khi vendor
đã có model khác đã test.

Ba câu hỏi registry trả lời:
  - ``capability_for(device_id, function)``: model NÀY (theo ID đã đăng ký)
    có dùng được chức năng này chưa — chỉ ``True`` khi đã test VÀ status
    ``verified``.
  - ``capability_by_model(vendor, model, function)``: biến thể tra theo
    vendor+model thô (chưa biết device_id) — SAME nguyên tắc, cộng thêm
    chặn suy diễn chéo model cùng hãng.
  - ``lookup_vid_pid``: tra nhanh theo VID/PID USB (có thể trả nhiều kết quả
    nếu nhiều entry khai cùng VID/PID — KHÔNG tự chọn, để caller tự quyết).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar

from namios_compat import _i18n as _i18n  # noqa: F401
from namios_compat._types import DeviceClass, DeviceEntry, DeviceProtocol, TechnicalStatus
from namios_i18n import Lang, t

__all__ = ["DeviceRegistry", "load_devices"]

_EnumT = TypeVar("_EnumT", bound=Enum)


class DeviceRegistry:
    """Bộ nhớ trong của các ``DeviceEntry`` đã đăng ký, tra theo ``device_id``,
    ``device_class``, hoặc VID/PID USB."""

    def __init__(self) -> None:
        self._by_id: dict[str, DeviceEntry] = {}

    def register(self, entry: DeviceEntry) -> None:
        """Lưu ``entry`` theo ``device_id``. Trùng ID đã đăng ký → ``ValueError``
        (mỗi ID chỉ ứng với MỘT hồ sơ thiết bị, không âm thầm ghi đè)."""

        if entry.device_id in self._by_id:
            raise ValueError(
                f"Thiết bị '{entry.device_id}' đã được đăng ký trước đó — không ghi đè."
            )
        self._by_id[entry.device_id] = entry

    def get(self, device_id: str) -> DeviceEntry | None:
        """Tra một entry theo ``device_id``; ``None`` nếu chưa đăng ký."""

        return self._by_id.get(device_id)

    def list(self, device_class: DeviceClass | None = None) -> tuple[DeviceEntry, ...]:
        """Danh sách entry, lọc theo ``device_class`` nếu có, thứ tự ỔN ĐỊNH
        (sort theo ``device_id``) để caller/test không phụ thuộc thứ tự insert."""

        values = tuple(self._by_id.values())
        if device_class is not None:
            values = tuple(e for e in values if e.device_class == device_class)
        return tuple(sorted(values, key=lambda e: e.device_id))

    def lookup_vid_pid(self, vid: str, pid: str) -> tuple[DeviceEntry, ...]:
        """Tra theo VID/PID USB chính xác (so sánh hex không phân biệt hoa/
        thường/khoảng trắng). Có thể trả nhiều entry — không tự chọn một."""

        vid_norm = vid.strip().lower()
        pid_norm = pid.strip().lower()
        matches = [
            entry
            for entry in self._by_id.values()
            if entry.vid is not None
            and entry.pid is not None
            and entry.vid.strip().lower() == vid_norm
            and entry.pid.strip().lower() == pid_norm
        ]
        return tuple(sorted(matches, key=lambda e: e.device_id))

    def capability_for(self, device_id: str, function: str) -> tuple[bool, str]:
        """COMP-032: thiết bị ``device_id`` dùng được ``function`` chưa?

        ``True`` CHỈ khi đã đăng ký, ``function`` nằm trong ``tested_functions``
        VÀ ``status == TechnicalStatus.VERIFIED`` — partial/blocked/failed/
        not_inventoried đều bị từ chối dù chức năng có trong danh sách test."""

        entry = self._by_id.get(device_id)
        if entry is None:
            # Chưa có hồ sơ nào cho ID này — coi như chưa test gì (từ chối).
            return False, t(
                "compat.device.refuse_untested_function",
                lang=Lang.VI,
                function=function,
                model=device_id,
            )

        if function in entry.tested_functions and entry.status == TechnicalStatus.VERIFIED:
            return True, t(
                "compat.device.ok_tested",
                lang=Lang.VI,
                model=entry.model,
                function=function,
                protocol=entry.protocol.value,
            )

        return False, t(
            "compat.device.refuse_untested_function",
            lang=Lang.VI,
            function=function,
            model=entry.model,
        )

    def capability_by_model(self, vendor: str, model: str, function: str) -> tuple[bool, str]:
        """COMP-032 NO-CARRYOVER: tra theo vendor+model thô (chưa biết
        device_id).

        - Có entry khớp ĐÚNG vendor+model → delegate sang ``capability_for``.
        - Không khớp đúng model nhưng vendor có model KHÁC đã đăng ký → từ
          chối rõ ràng (không suy diễn chéo model cùng hãng).
        - Vendor hoàn toàn chưa biết → cũng từ chối (vẫn không có gì để suy)."""

        vendor_norm = vendor.strip().lower()
        model_norm = model.strip().lower()

        exact: DeviceEntry | None = None
        for entry in self._by_id.values():
            if entry.vendor.strip().lower() != vendor_norm:
                continue
            if entry.model.strip().lower() == model_norm:
                exact = entry
                break

        if exact is not None:
            return self.capability_for(exact.device_id, function)

        return False, t(
            "compat.device.refuse_carryover",
            lang=Lang.VI,
            model=model,
            vendor=vendor,
        )


def _parse_enum(
    enum_cls: type[_EnumT],
    value: Any,
    *,
    field: str,
    context: str,
    default: _EnumT | None = None,
) -> _EnumT:
    """Chuyển ``value`` thô (chuỗi JSON) sang enum ``enum_cls``; ``None`` dùng
    ``default`` nếu có, ngược lại là thiếu trường bắt buộc. Giá trị không
    khớp enum nào → ``ValueError`` rõ ràng (không âm thầm rơi về mặc định)."""

    if value is None:
        if default is not None:
            return default
        raise ValueError(f"Thiết bị '{context}' thiếu trường bắt buộc '{field}'.")
    try:
        return enum_cls(value)
    except ValueError as exc:
        raise ValueError(
            f"Giá trị '{value}' không hợp lệ cho trường '{field}' của thiết bị '{context}'."
        ) from exc


def _build_entry(raw: Any, *, index: int, path: str) -> DeviceEntry:
    if not isinstance(raw, Mapping):
        raise ValueError(f"Mục thiết bị #{index} trong '{path}' phải là object JSON.")

    try:
        device_id = str(raw["device_id"])
        vendor = str(raw["vendor"])
        model = str(raw["model"])
        linux_mechanism = str(raw["linux_mechanism"])
    except KeyError as exc:
        raise ValueError(f"Thiết bị #{index} trong '{path}' thiếu trường bắt buộc {exc}.") from exc

    device_class = _parse_enum(
        DeviceClass, raw.get("device_class"), field="device_class", context=device_id
    )
    protocol = _parse_enum(DeviceProtocol, raw.get("protocol"), field="protocol", context=device_id)
    status = _parse_enum(
        TechnicalStatus,
        raw.get("status"),
        field="status",
        context=device_id,
        default=TechnicalStatus.NOT_INVENTORIED,
    )

    tested_functions = tuple(str(f) for f in raw.get("tested_functions", ()))
    evidence_ids = tuple(str(e) for e in raw.get("evidence_ids", ()))

    return DeviceEntry(
        device_id=device_id,
        device_class=device_class,
        vendor=vendor,
        model=model,
        protocol=protocol,
        linux_mechanism=linux_mechanism,
        tested_functions=tested_functions,
        vid=raw.get("vid"),
        pid=raw.get("pid"),
        firmware=raw.get("firmware"),
        version=raw.get("version"),
        permission_condition=str(raw.get("permission_condition", "")),
        status=status,
        evidence_ids=evidence_ids,
        notes_vi=str(raw.get("notes_vi", "")),
    )


def load_devices(path: str) -> tuple[DeviceEntry, ...]:
    """Đọc một file JSON (array các object thiết bị) và dựng ``DeviceEntry``.

    Khoan dung trường tuỳ chọn thiếu (dùng default của ``DeviceEntry``);
    giá trị enum sai → ``ValueError`` rõ ràng, KHÔNG âm thầm bỏ qua record."""

    with Path(path).open("r", encoding="utf-8") as fh:
        raw: Any = json.load(fh)

    if not isinstance(raw, list):
        raise ValueError(f"File thiết bị '{path}' phải là JSON array ở cấp cao nhất.")

    return tuple(_build_entry(item, index=i, path=path) for i, item in enumerate(raw))
