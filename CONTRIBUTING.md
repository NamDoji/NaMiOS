# Đóng góp cho NaMiOS

Cảm ơn bạn muốn góp sức cho **NaMiOS** — hệ điều hành miễn phí, mã nguồn mở cho người Việt.
Dự án này đặt **tính cộng đồng** và **sự trung thực** lên hàng đầu: một bản phân phối chỉ
mạnh khi có người thật đóng góp hồ sơ tương thích thật, và chỉ đáng tin khi không ai tô hồng.

> English version below (§EN).

## 1. Trước khi bắt đầu

Đọc hai tài liệu này — chúng quyết định PR của bạn được nhận hay không:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — bản đồ module + **6 bất biến** không được phá.
- [`CLAUDE.md`](CLAUDE.md) — quy tắc kỹ thuật & non-negotiables.

Nguyên tắc số 1 của dự án: **không nhãn "đạt" khi chưa có bằng chứng thật**. Thiếu môi
trường → ghi `blocked`, không bịa.

## 2. Dựng môi trường

Cần Python ≥ 3.11 (xem `pyproject.toml`). Lõi phần mềm **không có dependency runtime** —
chỉ dùng thư viện chuẩn; dependency chỉ dành cho dev (test/lint).

```bash
git clone https://github.com/NamDoji/NaMiOS.git
cd NaMiOS
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"          # cài namios + pytest/ruff/black/mypy
```

Thử CLI thật:

```bash
namios doctor --json            # báo cáo capability host (không secret)
namios compat workflows         # danh sách workflow tương thích
namios smartai plan "cài MISA"  # lập kế hoạch (CHƯA thực thi)
```

## 3. Cổng chất lượng (phải xanh TRƯỚC khi gửi PR)

Chạy đúng 4 lệnh này — chúng được **CI tự chạy** trên mọi push/PR
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)); PR đỏ cổng sẽ không được merge:

```bash
ruff check src tests     # lint (line-length 100; rule E,F,I,UP,B,S) — cả src lẫn test
black --check src tests  # format — cả src lẫn test
mypy src/namios_core     # type-check hợp đồng dùng chung (strict)
pytest                   # toàn bộ test suite — phải 0 fail
```

Mẹo: `black src tests && ruff check --fix src tests` để tự sửa format/import trước khi check.

## 4. Quy tắc viết code (giữ dự án đồng nhất)

- **Tiếng Việt chỉn chu** cho mọi chuỗi người đọc — và đi qua `namios_i18n` (`t(key, lang)`),
  **không hard-code**. Thêm key vào catalog VN **và** EN (có test parity).
- **I/O nhạy cảm** (đọc file người dùng, ghi log, export) đi qua `namios_security`
  (`open_within`, redaction). Không `os.system`/`subprocess` shell, không `eval`.
- **Không nâng trạng thái bằng metadata.** Nếu bạn chạm gate (`namios_eco`, `namios_compat`,
  `namios_smartai.promotion`), nhớ: chỉ bằng chứng tool + người duyệt + nghiệp vụ mới nâng.
- **Frozen dataclass + str-Enum** cho hợp đồng dữ liệu; `from __future__ import annotations`.
- Mỗi hành vi mới **phải có test**; sửa lỗ hổng an toàn **phải kèm test đối kháng** trong
  `tests/security/` để khóa (regression guard).

## 5. Quy trình Pull Request

1. Tạo nhánh từ `main`: `git checkout -b feat/<mô-tả-ngắn>`.
2. Commit nhỏ, rõ; message dạng `type(scope): mô tả` (vd `fix(compat): ...`).
3. Chạy đủ 4 cổng chất lượng ở §3 → xanh hết.
4. Mở PR theo mẫu ([`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md)) —
   nêu rõ bất biến nào liên quan + bạn đã giữ nó thế nào.
5. Một người review độc lập (không phải tác giả) xác nhận trước khi merge. Thay đổi
   schema/DB/kiến trúc cần duyệt kiến trúc.

## 6. Đóng góp hồ sơ tương thích (phần quan trọng nhất của cộng đồng)

Giá trị lớn nhất bạn có thể đóng góp là **kết quả chạy app Windows thật trên NaMiOS**. Nhưng:

- Báo "máy mình chạy ngon" là **phản hồi cộng đồng CHƯA kiểm** — nó **không** tự thành
  "đã chứng nhận". Nó gợi ý một test case để đội kiểm lại.
- Chứng nhận "chạy được" chỉ đến từ **lab NaMiOS** với bằng chứng tool + đúng (app, mode,
  version) + người duyệt nghiệp vụ.

Cách gửi báo cáo đúng chuẩn: xem [`docs/community/COMPATIBILITY-CONTRIBUTION.md`](docs/community/COMPATIBILITY-CONTRIBUTION.md).

## 7. Báo lỗ hổng bảo mật

**Không** mở issue công khai cho lỗ hổng. Quy trình báo riêng: [`docs/SECURITY.md`](docs/SECURITY.md).

## 8. Giấy phép & ứng xử

Đóng góp theo giấy phép **Apache-2.0** (xem `pyproject.toml`). Tham gia tức là bạn đồng ý
[Quy tắc ứng xử](CODE_OF_CONDUCT.md).

---

## EN — Contributing to NaMiOS

NaMiOS is a free, open-source operating system for Vietnamese users. The project puts
**community** and **honesty** first: a distro is only strong with real contributed compatibility
data, and only trustworthy if nobody sugar-coats results.

**Read first:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (module map + the 6 invariants you
must not break) and [`CLAUDE.md`](CLAUDE.md). Rule #1: **no "pass" label without real evidence** —
missing infra means `blocked`, never fabricated.

**Setup** (Python ≥ 3.11, no runtime deps — stdlib only):

```bash
git clone https://github.com/NamDoji/NaMiOS.git && cd NaMiOS
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

**Quality gate (CI-enforced on every push/PR via `.github/workflows/ci.yml`; must be green before a PR):**

```bash
ruff check src tests   &&   black --check src tests   &&   mypy src/namios_core   &&   pytest
```

**Code rules:** user-facing strings go through `namios_i18n` (`t(key, lang)`, add VN **and** EN);
sensitive I/O goes through `namios_security` (no shell, no eval); metadata never promotes a gate;
frozen dataclasses + str-Enums; every new behavior needs a test, every security fix needs an
adversarial regression test in `tests/security/`.

**PRs:** branch from `main`, small commits (`type(scope): ...`), pass all four gates, fill the PR
template, get one independent reviewer. **Compatibility reports** are the most valuable community
contribution — but a community "works for me" is unverified feedback, **not** a certification; see
[`docs/community/COMPATIBILITY-CONTRIBUTION.md`](docs/community/COMPATIBILITY-CONTRIBUTION.md).
**Security issues:** private disclosure only — [`docs/SECURITY.md`](docs/SECURITY.md). License:
**Apache-2.0**; by contributing you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
