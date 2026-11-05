<!--
Cảm ơn PR của bạn! Điền ngắn gọn. PR đỏ cổng chất lượng sẽ không được merge.
Thank you for the PR! Keep it short. PRs that fail the quality gate will not be merged.
-->

## Tóm tắt / Summary

<!-- Thay đổi gì và vì sao. / What changed and why. -->

## Loại thay đổi / Type

- [ ] fix (sửa lỗi) · [ ] feat (tính năng) · [ ] docs · [ ] refactor · [ ] test · [ ] chore

## Cổng chất lượng / Quality gate (bắt buộc)

- [ ] `ruff check src` — xanh
- [ ] `black --check src` — xanh
- [ ] `mypy src/namios_core` — xanh
- [ ] `pytest` — 0 fail
- [ ] Có test cho hành vi mới / mỗi lần sửa lỗ hổng an toàn có test đối kháng (`tests/security/`).

## Bất biến trung thực / Honesty invariants (xem docs/ARCHITECTURE.md §2)

- [ ] Không nâng trạng thái bằng metadata/nhãn tự khai (gate chỉ HẠ).
- [ ] Không nhãn "đạt"/"verified" khi chưa có bằng chứng tool thật; thiếu → `blocked`.
- [ ] Chuỗi người đọc đi qua `namios_i18n` (VN + EN), không hard-code.
- [ ] I/O nhạy cảm đi qua `namios_security` (không shell/eval; redact secret/PII).

## Ghi chú review / Review notes

<!-- Bất biến nào liên quan và bạn giữ nó thế nào? Cần duyệt kiến trúc không? -->

> Thay đổi schema/DB/kiến trúc cần duyệt kiến trúc. Một người review độc lập (không phải tác giả)
> xác nhận trước khi merge.
