"""ECO-006 — ``ServiceEntry``: một mục trong danh bạ dịch vụ/phần mềm thiết
yếu. Ánh xạ 1-1 ``contracts/service-catalog.schema.json``.

Thiết kế CHỦ ĐÍCH không có trường thực thi/lệnh nào (không ``command``,
không ``argv``, không ``script``, không nội dung bộ cài nhị phân) — danh bạ
chỉ MÔ TẢ metadata để người dùng/CLI tự mở URL chính thức, KHÔNG BAO GIỜ điều
khiển hành vi máy (ECO-006: "không host lại bộ cài của cơ quan/nhà cung cấp
nếu chưa có quyền phân phối"; xem ``catalog_schema.py`` — schema
``additionalProperties: false`` chặn mọi trường lạ, gồm cả trường thực thi
nào đó có thể bị thêm nhầm sau này)."""

from __future__ import annotations

from dataclasses import dataclass

from namios_eco.status import PublishedStatus, WindowsMode

__all__ = ["ServiceEntry"]


@dataclass(frozen=True)
class ServiceEntry:
    """Một dịch vụ/phần mềm trong danh bạ (ECO-006).

    Trường tuple chứng nhận tối thiểu theo ECO-002 (tên, nhà cung cấp/cơ
    quan, URL chính thức, ngày kiểm, HĐH công bố, phiên bản) nằm rải trong
    các trường dưới; ``test_profile``/``evidence_source`` trỏ tới hồ sơ
    bằng chứng thật (có thể là ``report_id`` của ``namios_evidence``)."""

    #: ID ổn định — KHÔNG đổi sau khi phát hành (vd "thue.etax-ca-nhan").
    id: str
    #: Nhà cung cấp/nhà phát triển phần mềm.
    provider: str
    #: Cơ quan quản lý/ban hành thủ tục; ``None`` nếu không thuộc nhà nước.
    agency: str | None
    #: Mục đích/mô tả nghiệp vụ (vd "Lập và nộp tờ khai thuế hộ kinh doanh").
    purpose: str
    #: URL tải/đăng nhập CHÍNH THỨC — phải http(s), không scheme lạ (ECO-006).
    official_url: str
    #: Cách kiểm tra nguồn là chính thức (vd "khớp domain .gov.vn + ngày kiểm").
    source_check: str
    #: Phiên bản đã khảo sát; ``None`` nếu web không có version rõ ràng.
    version: str | None
    #: Giấy phép/điều khoản sử dụng.
    license: str
    #: HĐH nhà cung cấp CÔNG BỐ hỗ trợ (không phải HĐH đã tự kiểm — xem ECO-004).
    published_os: tuple[str, ...]
    #: Phụ thuộc đã biết (token, plugin, middleware, Java/.NET...).
    dependencies: tuple[str, ...]
    #: Điều kiện tài khoản (vd "cần CCCD gắn định danh mức 2 + SIM/USB ký số").
    account_condition: str
    #: Chi phí dịch vụ (vd "miễn phí", "theo gói năm", "theo giao dịch").
    service_cost: str
    #: Mức dữ liệu nhạy cảm xử lý qua dịch vụ (vd "ca_nhan", "tai_chinh", "cong_khai").
    data_sensitivity: str
    #: Tham chiếu hồ sơ test (vd ``report_id`` của một ``EvidenceReport``).
    test_profile: str
    #: Ngày kiểm nguồn gần nhất, ISO 8601 date "YYYY-MM-DD".
    last_updated: str
    #: Nguồn chứng cứ (URL văn bản/báo cáo tham chiếu cho published_status hiện tại).
    evidence_source: str
    #: Trạng thái công bố (ECO-003) — nên được suy ra bằng
    #: ``status.derive_published_status`` rồi gán, không tự đặt tay
    #: ``workflow_verified``/tuỳ ý (``validator.py`` thẩm định lại).
    published_status: PublishedStatus
    #: Chế độ Windows (ECO-015).
    windows_mode: WindowsMode
    #: NaMiOS tự kiểm và xác nhận chạy được (ECO-004) — ĐỘC LẬP với trường dưới.
    tested_by_namios: bool
    #: Nhà cung cấp/cơ quan CHÍNH THỨC xác nhận hỗ trợ (ECO-004) — ĐỘC LẬP với
    #: trường trên; KHÔNG được suy luận một chiều từ ``tested_by_namios``.
    officially_supported_by_vendor: bool
