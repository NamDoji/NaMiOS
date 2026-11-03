"""SEC-SWEEP — rà soát bảo mật adversarial ĐỘC LẬP (xem CLAUDE.md/threat-model.md).

Phạm vi: viết test TẤN CÔNG trên API công khai các module, theo từng lớp
SEC-001..SEC-012 + DATA-001/002 (xem ``docs/threat-model.md`` §4/§5 và
``docs/specs/DAC_TA_HE_DIEU_HANH.md`` §8/§10). KHÁC với ``tests/unit/**``
(dev viết để tự xác nhận) và ``tests/qa/**`` (QA theo WP cụ thể) — thư mục
này là một vai trò RIÊNG, tự dựng fixture, không import test helper của
dev/QA khác, mục tiêu là tìm lỗ hổng THẬT thay vì xác nhận lại thiết kế.

Quy ước: mọi test PHẢI khẳng định phòng thủ giữ (pass). Nếu một test lộ ra
lỗ hổng THẬT (phòng thủ thủng), test đó được giữ lại làm BẰNG CHỨNG bằng
``pytest.mark.xfail(strict=True, reason="SEC-SWEEP-NNN: ...")`` — KHÔNG tự
sửa code module khác để che giấu. Xem ``docs/SECURITY.md`` và
``qa/evidence-index/SEC-SWEEP/findings.md`` để biết danh sách finding ID
đang mở.
"""
