# M1-INTERFACES — Hợp đồng dùng chung cho 10 gói dev

**Trạng thái:** DESIGN (chốt bởi pha M0, chưa phải kết quả chạy). Phiên bản 1.0 — 02/11/2026.
**Phạm vi:** chỉ M1 (lõi Python thuần chạy được trên host hiện tại: Debian 12, python 3.11, venv + pytest). KHÔNG đưa Wine/ISO/app thương mại vào đây (M2+ BLOCKED).
**Mục đích:** mọi dev M1 code SONG SONG dựa trên các hợp đồng dưới đây. Dev code theo *interface* (Protocol/dataclass/enum/hằng số do WP1 phát hành trong `namios_core`), KHÔNG import chéo vào implementation của module khác.

> Phân loại nhận định: **FACT** = dẫn từ đặc tả/contract; **DESIGN** = quyết định của pha M0 cho M1; **TARGET** = chỉ tiêu cần đo; **UNKNOWN** = chưa có bằng chứng.
> Namespace code hiện là `namios_*` (FACT, theo CLAUDE.md). Rebrand NaMiOS là pass cơ học sau, không ảnh hưởng hợp đồng.

Truy vết yêu cầu: CLI-001/002/003/004, TX-001, COMP-004/005, SEC-001/002/009, SUP-002, UX-006, §11.1/§11.2/§11.3, REPO-001/003.

---

## 0. Bản đồ package M1 và quyền sở hữu (DESIGN)

WP1 phát hành gói nền `namios_core` chứa TẤT CẢ interface (enum, dataclass, Protocol, hằng số đường dẫn). 9 WP còn lại import từ `namios_core` (chỉ đọc) và hiện thực trong thư mục riêng.

| Package `src/…` | WP sở hữu | Vai trò |
| --- | --- | --- |
| `namios_core/` | WP1 | Hợp đồng dùng chung: envelope, exit code, error code, state machine enum, compat enum, path constants, Protocol các API. KHÔNG chứa business logic. |
| `namios_security/` | WP8 | Safe path/FD, argv-only exec, redaction. Nền cho nhiều WP. |
| `namios_manifest/` | WP2 | Schema loader + semantic validator 2 tầng. |
| `namios_cli/` + `namios_doctor/` | WP3 | CLI framework, envelope writer, exit-code mapper, lệnh `doctor`. |
| `namios_catalog/` | WP4 | Catalog store, tìm kiếm tiếng Việt accent-insensitive, revocation. |
| `namios_txstate/` | WP5 | Transaction state store (SQLite) + journal + state machine + crash recovery. |
| `namios_planner/` | WP6 | Install planner: build plan, verify-at-apply, stale-reject. |
| `namios_helper/` (hiện thực của `namios_system_helper`) | WP7 | API typed (no RunCommand) + interface Polkit/D-Bus + policy allowlist. |
| `namios_evidence/` | WP9 | Evidence model + evidence-report validator + compat-state gate. |
| `namios_recipe/` | WP10 | Recipe engine declarative allowlist + dry-run fixtures. |

**Quy tắc chống giẫm chân (DESIGN):**
- Mỗi package có `__init__.py` RIÊNG do owner tạo. KHÔNG có `__init__.py` dùng chung nhiều chủ. `namios_core/__init__.py` chỉ WP1 sửa.
- `pyproject.toml` chỉ WP1 sở hữu; dùng `[tool.setuptools.packages.find] where = ["src"]` để tự nhận mọi package → thêm package mới KHÔNG cần sửa `pyproject.toml`.
- Test: mỗi WP ghi dưới `tests/unit/<module>/` và `tests/security/<module>/` của riêng mình. `tests/conftest.py` gốc do WP1 sở hữu.
- Phụ thuộc chỉ đi MỘT chiều qua `namios_core` (interface) hoặc các package nền đã khai báo (xem WP graph trong M1-WORK-PACKAGES.md). Cấm import vòng.

---

## 1. JSON envelope CLI (CLI-001) — FACT + DESIGN

Mọi lệnh có `--json` in **đúng MỘT** đối tượng JSON ra **stdout**. KHÔNG trộn log/tiến trình/cảnh báo người-đọc vào stdout JSON. Log kỹ thuật, dòng tiến trình, prompt → **stderr**. (FACT: CLI-001.)

Đối tượng envelope (DESIGN, `namios_core.envelope`):

```jsonc
{
  "api_version": "1.0",          // string cố định cho M1
  "operation_id": "b2c3…uuid4",  // string, 1 lần/lệnh, để truy vết journal
  "status": "ok",               // "ok" | "error"
  "data": { },                   // object | null — payload theo từng lệnh; null khi error
  "warnings": [                   // string[] tiếng Việt, không chặn thành công
    "Hồ sơ ở trạng thái untested; chưa thể cài."
  ],
  "error": null                   // null khi ok; object khi error (xem §3)
}
```

Khi `status="error"`: `data=null`, `error` là object; exit code != 0 theo §2.
Khi `status="ok"`: `error=null`; exit code 0; `warnings` có thể rỗng hoặc có phần tử.

Chữ ký writer (WP3 hiện thực; WP1 định kiểu):

```python
# namios_core/envelope.py (WP1 — kiểu + hằng số)
API_VERSION = "1.0"

@dataclass(frozen=True)
class Envelope:
    api_version: str
    operation_id: str
    status: Literal["ok", "error"]
    data: Mapping[str, Any] | None
    warnings: tuple[str, ...]
    error: "ErrorBody | None"

@dataclass(frozen=True)
class ErrorBody:
    code: str          # stable error code enum (§3), ví dụ "E_INPUT_SCHEMA"
    message_vi: str     # thông điệp tiếng Việt cho người dùng
    details: Mapping[str, Any] | None  # cấu trúc phụ, KHÔNG chứa secret/argv thô

# namios_cli (WP3 — hiện thực)
def emit_json(env: Envelope, stdout: TextIO) -> None: ...   # ghi 1 dòng JSON + '\n'
def new_operation_id() -> str: ...                            # uuid4 hex
```

Quy tắc `--` và argv (FACT CLI-001/COMP-004): `--` kết thúc options; đối số ứng dụng đi qua allowlist/argv, KHÔNG ghép thành shell. Xem `run_argv` §8.

---

## 2. Bảng exit code 0–9 (CLI-003) — FACT

| Code | Ý nghĩa (tiếng Việt) | Dùng khi |
| --- | --- | --- |
| 0 | Thành công | Thao tác hoàn tất, `status="ok"`. |
| 2 | Input/schema sai | Tham số, file hoặc JSON Schema không hợp lệ. |
| 3 | Thiếu dependency/quyền sử dụng | Thiếu phụ thuộc đã duyệt hoặc thiếu entitlement người dùng. |
| 4 | Mạng/xác thực nguồn | TLS/hash/redirect/nguồn không qua policy. |
| 5 | Không được cấp quyền | Polkit/helper từ chối; caller không hợp lệ. |
| 6 | Xung đột trạng thái/khóa | Mutex prefix bận; plan stale; mutation song song. |
| 7 | Bị hủy | Người dùng/flow hủy (CANCELLED). |
| 8 | Kiểm tra sau cài thất bại | VERIFYING fail; không được đánh dấu READY. |
| 9 | Lỗi nội bộ | Bug/ngoại lệ không lường; ghi log, không lộ secret. |

> Lưu ý: **1 không dùng** (dành cho lỗi runtime ngoài hợp đồng của interpreter). Mọi lệnh M1 PHẢI map lỗi về đúng một trong các code trên; có test CLI-01 kiểm nhất quán.

Hằng số (WP1): `namios_core.exitcodes.ExitCode(IntEnum)` với `OK=0, INPUT=2, DEPENDENCY=3, NETWORK=4, PERMISSION=5, CONFLICT=6, CANCELLED=7, VERIFY=8, INTERNAL=9`.

---

## 3. Mã lỗi ổn định (stable error codes) — DESIGN

Enum chuỗi, bất biến trên các phiên bản M1 (dùng trong `ErrorBody.code`). Map 1→nhiều tới exit code. (`namios_core.errors.ErrorCode(str, Enum)`.)

| ErrorCode | Exit | Ý nghĩa |
| --- | --- | --- |
| `E_INPUT_SCHEMA` | 2 | JSON Schema fail / tham số sai kiểu. |
| `E_INPUT_UNKNOWN_KEY` | 2 | Thuộc tính không biết (additionalProperties). |
| `E_SEMANTIC_TBD` | 2 | Hồ sơ còn TBD/null bắt buộc để cài (runner/hash/build). |
| `E_SEMANTIC_RECIPE` | 2 | Recipe chứa action/param ngoài allowlist hoặc có shell/eval/url-script. |
| `E_SEMANTIC_DEPENDENCY` | 3 | Dependency profile chưa duyệt. |
| `E_ENTITLEMENT_REQUIRED` | 3 | Thiếu quyền sử dụng của người dùng. |
| `E_HASH_MISMATCH` | 4 | Hash payload không khớp giá trị kỳ vọng. |
| `E_SOURCE_POLICY` | 4 | Host/redirect/scheme ngoài allowlist; TLS fail. |
| `E_PERMISSION_DENIED` | 5 | Polkit/helper từ chối; caller không hợp lệ. |
| `E_STATE_CONFLICT` | 6 | Mutex/khóa prefix bận; chuyển trạng thái bất hợp lệ. |
| `E_PLAN_STALE` | 6 | Plan hết hạn / nội dung đổi / sai user-host. |
| `E_CANCELLED` | 7 | Thao tác bị hủy. |
| `E_POSTCHECK_FAILED` | 8 | Kiểm tra sau cài thất bại. |
| `E_PATH_UNSAFE` | 2 | Đường dẫn vi phạm chính sách (traversal/symlink/mount/owner). |
| `E_REVOKED` | 2 | Manifest/profile ở trạng thái revoked. |
| `E_EVIDENCE_MISSING` | 2 | Chứng nhận task_verified nhưng thiếu evidence/QA approval. |
| `E_INTERNAL` | 9 | Lỗi nội bộ. |

Quy tắc: `message_vi` luôn tiếng Việt; chi tiết kỹ thuật ở `details` nhưng PHẢI qua redaction (§8) — không chứa mật khẩu/token/đường dẫn tài liệu người dùng/argv thô.

---

## 4. State machine giao dịch (TX-001) — FACT

Trạng thái (`namios_core.txstate.TxState(str, Enum)`):

```
NEW → VALIDATED → ACQUIRING → STAGING → INSTALLING → VERIFYING → READY
```

Nhánh phụ:
- Từ bất kỳ trạng thái "đang chạy" (`ACQUIRING, STAGING, INSTALLING, VERIFYING`): → `CANCELLING` → `CANCELLED`, hoặc → `FAILED`.
- Phục hồi: `FAILED | <dở sau crash>` → `RECOVERING` → `READY` (nếu kiểm tra thực tế OK) **hoặc** `NEEDS_ATTENTION` (khi không đảm bảo hoàn nguyên — TX-003).
- Gỡ app: `READY` → `REMOVING` → `REMOVED` (mặc định giữ dữ liệu — TX-005).

Bảng chuyển hợp lệ (DESIGN — WP5 là nguồn sự thật thi hành; các WP khác chỉ đọc enum):

| Từ | Được phép sang |
| --- | --- |
| NEW | VALIDATED, FAILED, CANCELLING |
| VALIDATED | ACQUIRING, FAILED, CANCELLING |
| ACQUIRING | STAGING, FAILED, CANCELLING |
| STAGING | INSTALLING, FAILED, CANCELLING |
| INSTALLING | VERIFYING, FAILED, CANCELLING |
| VERIFYING | READY, FAILED, CANCELLING |
| CANCELLING | CANCELLED, NEEDS_ATTENTION |
| FAILED | RECOVERING |
| RECOVERING | READY, NEEDS_ATTENTION |
| READY | REMOVING |
| REMOVING | REMOVED, NEEDS_ATTENTION |
| NEEDS_ATTENTION | RECOVERING, REMOVING |
| CANCELLED / REMOVED / READY(terminal cho tx) | — (terminal trong phạm vi giao dịch đó) |

Bất biến bắt buộc (FACT TX-001): **không đánh dấu READY chỉ vì installer exit 0** — chỉ sang READY sau VERIFYING pass. Mỗi bước ghi journal trước-và-sau với `operation_id`. SQLite chỉ bảo vệ metadata, KHÔNG biến thay đổi filesystem thành nguyên tử (FACT §13).

---

## 5. Enum compatibility status + "tuple chứng nhận" (§11.2) — FACT

`namios_core.compat.CompatStatus(str, Enum)`:

| Giá trị | Điều kiện |
| --- | --- |
| `untested` | Chưa có bộ test đủ cho tuple phiên bản. |
| `experimental` | Có bằng chứng chạy một phần; còn lỗi/thiếu phạm vi. |
| `task_verified` | TẤT CẢ tác vụ bắt buộc đạt trong cấu hình xác định + QA phê duyệt độc lập. |
| `blocked` | Tác vụ bắt buộc không đạt hoặc thiếu phụ thuộc ngoài. |
| `revoked` | Chứng nhận/profile bị thu hồi (bảo mật/mất dữ liệu/sai bằng chứng). |

**Tuple chứng nhận** (DESIGN dataclass `namios_core.compat.CertificationTuple`, FACT nội dung §11.2): `(os_build, kernel|null, graphics|null, desktop_session, runner_hash, profile_digest, app_build, app_hash, architecture, runtime_dependency_versions[], dataset_revision, test_suite_revision, hardware_or_vm_profile)`. Kết quả trên một tuple KHÔNG tự lan sang tuple khác. Đổi bất kỳ thành phần quan trọng ⇒ phải đánh giá lại (về `untested`/`experimental`).

Gate (FACT §11.2, WP9 thi hành): `task_verified` chỉ hợp lệ khi có evidence cho đúng tuple **và** `qa_approval.reviewer != null`. Nếu không → `E_EVIDENCE_MISSING`.

---

## 6. Layout thư mục dữ liệu + hằng số XDG (§11.3) — FACT + DESIGN

`namios_core.paths` cung cấp hàm trả path đã resolve theo XDG (KHÔNG hardcode `/home/<name>`; không nối chuỗi không kiểm tra — FACT §11.3/SEC-002).

| Hàm | Trả về (mặc định XDG) | Nội dung |
| --- | --- | --- |
| `config_dir()` | `$XDG_CONFIG_HOME/namios/` (≈ `~/.config/namios/`) | Tùy chọn + quyền người dùng chọn. |
| `prefixes_dir()` | `$XDG_DATA_HOME/namios/prefixes/<app-id>/<instance-id>/` | Prefix ứng dụng (M2 dùng). |
| `state_db_path()` | `$XDG_DATA_HOME/namios/state.sqlite3` | Transaction/launcher/state; KHÔNG chứa mật khẩu. |
| `cache_dir()` | `$XDG_CACHE_HOME/namios/` | Download/staging có TTL + hạn mức; xóa cache ≠ xóa tài liệu. |
| `logs_dir()` | `$XDG_STATE_HOME/namios/logs/` | Log đã lọc; mặc định ≤100 MB hoặc 14 ngày (cấu hình được). |
| `share_ro_dir()` | `/usr/share/namios/` | Tài nguyên package chỉ đọc. |
| `system_var_dir()` | `/var/lib/namios/` | Metadata hệ thống/cache root; ownership chặt; KHÔNG làm prefix user. |

Hằng số: `APP_NAME = "namios"`, `STATE_DB_FILENAME = "state.sqlite3"`, `LOG_MAX_BYTES_DEFAULT = 100*1024*1024`, `LOG_MAX_AGE_DAYS_DEFAULT = 14`.
Mọi path do caller cung cấp PHẢI qua `namios_security.resolve_within()` (§8) trước khi mở.

---

## 7. Chữ ký API Python then chốt giữa các module (Protocol) — DESIGN

WP1 khai báo các `Protocol`/dataclass dưới trong `namios_core`. Mỗi WP hiện thực lớp cụ thể và trả đối tượng khớp Protocol để ghép module. Kiểu dưới là **hợp đồng tối thiểu**; owner có thể thêm method nội bộ nhưng KHÔNG đổi chữ ký public.

### 7.1 Manifest + Validator API (WP2 — COMP-004, §11.1)

```python
# namios_core.manifest_types
@dataclass(frozen=True)
class Manifest:                      # ánh xạ 1-1 contracts/app-manifest.schema.json
    schema_version: str; id: str; name: str; publisher: str
    mode: Literal["native","web","wine","vm","remote"]
    application: "AppSection"; license: "LicenseSection"; source: "SourceSection"
    runtime: "RuntimeSection"; permissions: "PermissionsSection"
    recipe: tuple["RecipeStep", ...]; compatibility: "CompatSection"

@dataclass(frozen=True)
class SchemaResult:  ok: bool; errors: tuple["ValidationError", ...]
@dataclass(frozen=True)
class SemanticResult: ok: bool; errors: tuple["ValidationError", ...]; install_ready: bool
@dataclass(frozen=True)
class ValidationError: code: str; path: str; message_vi: str   # code ∈ ErrorCode (§3)

class ManifestValidator(Protocol):
    def load(self, path: str) -> Manifest: ...                    # dùng resolve_within + safe read
    def validate_schema(self, raw: Mapping[str, Any]) -> SchemaResult: ...
    def validate_semantic(self, m: Manifest, ctx: "SemanticContext") -> SemanticResult: ...

@dataclass(frozen=True)
class SemanticContext:                # dữ liệu để kiểm điều kiện ngữ nghĩa
    approved_dependency_ids: frozenset[str]
    pinned_runner_hashes: frozenset[str]
    revoked_ids: frozenset[str]        # từ catalog revocation (WP4)
```

Quy tắc semantic (FACT §11.1/COMP-004): chặn profile TBD/null bắt buộc để cài (`E_SEMANTIC_TBD`), runner chưa pin, dependency chưa duyệt (`E_SEMANTIC_DEPENDENCY`), recipe ngoài allowlist/có shell (`E_SEMANTIC_RECIPE`), trạng thái revoked (`E_REVOKED`), `task_verified` không evidence (`E_EVIDENCE_MISSING`). "Schema hợp lệ" ≠ "an toàn để chạy".

### 7.2 Catalog API (WP4 — compat-catalog, UX-006)

```python
@dataclass(frozen=True)
class CatalogEntry: manifest: Manifest; digest: str; channel: str  # dev/alpha/pilot/stable
@dataclass(frozen=True)
class RevocationRecord: target_id: str; reason: str; revoked_at: str  # ISO 8601

class CatalogStore(Protocol):
    def add(self, entry: CatalogEntry) -> None: ...
    def get(self, app_id: str) -> CatalogEntry | None: ...
    def list(self, channel: str | None = None) -> tuple[CatalogEntry, ...]: ...
    def search(self, query: str, limit: int = 50) -> tuple[CatalogEntry, ...]: ...  # accent-insensitive VN
    def is_revoked(self, app_id: str) -> bool: ...
    def revocations(self) -> tuple[RevocationRecord, ...]: ...
```

`search` (FACT UX-006): không phân biệt hoa/thường, khớp tên tiếng Việt CÓ DẤU và KHÔNG DẤU; KHÔNG đổi tên file thật để phục vụ tìm kiếm. Chuẩn hóa chỉ áp cho index tìm kiếm (fold dấu + casefold trên bản sao), giữ nguyên tên hiển thị.

### 7.3 Transaction State Store API (WP5 — TX-001, COMP-005)

```python
@dataclass(frozen=True)
class Transaction: tx_id: str; app_id: str; instance_id: str; state: TxState; updated_at: str
@dataclass(frozen=True)
class JournalEntry: tx_id: str; operation_id: str; phase: str; when: str; before: TxState; after: TxState; note_vi: str

class StateStore(Protocol):
    def open(self) -> None: ...                                  # tạo/migrate schema state.sqlite3
    def create_transaction(self, app_id: str, instance_id: str) -> Transaction: ...  # NEW
    def append_journal(self, e: JournalEntry) -> None: ...        # ghi TRƯỚC khi đổi state
    def advance(self, tx_id: str, to: TxState, operation_id: str, note_vi: str) -> Transaction: ...  # validate transition; E_STATE_CONFLICT nếu sai
    def get(self, tx_id: str) -> Transaction | None: ...
    def acquire_prefix_lock(self, app_id: str, instance_id: str) -> "PrefixLock": ...  # mutex; E_STATE_CONFLICT nếu bận
    def recover(self) -> tuple[Transaction, ...]: ...             # phát hiện tx dở sau crash; đưa về RECOVERING/NEEDS_ATTENTION
```

### 7.4 Install Planner API (WP6 — CLI-002)

```python
@dataclass(frozen=True)
class InstallPlan:
    plan_id: str; app_id: str; user: str; host: str
    profile_digest: str; artifact_digests: tuple[tuple[str, str], ...]  # (path_label, sha256)
    changes: tuple[str, ...]; required_space_bytes: int
    permissions: "PermissionsSection"; expires_at: str                  # ISO 8601 UTC
@dataclass(frozen=True)
class ApplyCheck: ok: bool; code: str | None; message_vi: str | None    # code ∈ ErrorCode

class InstallPlanner(Protocol):
    def build_plan(self, m: Manifest, installer_path: str | None, ctx: SemanticContext) -> InstallPlan: ...
    def verify_at_apply(self, plan: InstallPlan, current_user: str, current_host: str) -> ApplyCheck: ...
```

Quy tắc (FACT CLI-002): `verify_at_apply` PHẢI xác minh lại artifact digest + user/host + hạn dùng; reject plan sai user, hết hạn, hoặc nội dung đổi → `E_PLAN_STALE`.

### 7.5 System-helper typed API + D-Bus signatures (WP7 — SEC-001, CLI-004)

KHÔNG có `RunCommand`. KHÔNG cho caller truyền repository/key/package tùy ý ngoài allowlist đã phát hành (FACT CLI-004). Thao tác phân vùng KHÔNG qua helper này.

```python
# Interface mức Python (helper service + proxy phía client)
@dataclass(frozen=True)
class SystemCapabilities: os_build: str; kernel: str; session_type: str; sandbox_mode: str; has_kvm: bool
@dataclass(frozen=True)
class PackagePlanRequest: allowlist_key: str                      # KHÓA trỏ tới plan đã duyệt, KHÔNG phải tên package tự do
@dataclass(frozen=True)
class ApprovedPackagePlan: plan_id: str; signed_digest: str
@dataclass(frozen=True)
class UpdateStatus: pending: tuple[str, ...]; reboot_required: bool

class SystemHelper(Protocol):
    def GetSystemCapabilities(self) -> SystemCapabilities: ...
    def PlanPackageInstall(self, req: PackagePlanRequest) -> ApprovedPackagePlan: ...
    def ApplyApprovedPackagePlan(self, plan: ApprovedPackagePlan) -> UpdateStatus: ...
    def GetUpdateStatus(self) -> UpdateStatus: ...
```

Ánh xạ D-Bus (DESIGN; M1 hiện thực interface + policy, chưa cần bus thật để test logic):
- Bus name: `org.namios.SystemHelper1` (system bus). Object path: `/org/namios/SystemHelper1`. Interface: `org.namios.SystemHelper1`.
- Method typed signatures (chỉ scalar/struct có kiểu, KHÔNG nhận mảng lệnh):
  - `GetSystemCapabilities() → (ssssb)` → `(os_build, kernel, session_type, sandbox_mode, has_kvm)`.
  - `PlanPackageInstall(s allowlist_key) → (ss)` → `(plan_id, signed_digest)`.
  - `ApplyApprovedPackagePlan(ss plan) → (asb)` → `(pending[], reboot_required)`.
  - `GetUpdateStatus() → (asb)`.
- Mỗi method gắn một action Polkit riêng (SEC-001): `org.namios.systemhelper.get-capabilities` (allow-active, no-auth read), `…plan-package`, `…apply-package` (auth_admin_keep). Helper xác thực: danh tính caller (uid qua D-Bus, không tin PID thô), Polkit, kiểu tham số, allowlist_key hợp lệ, trạng thái hệ thống. Từ chối → `E_PERMISSION_DENIED` (exit 5).

### 7.6 Recipe action types + engine (WP10 — COMP-004)

6 action khai báo (FACT contract recipe.enum). Params typed; KHÔNG `shell`/`eval`/url-script/template nội suy; dùng argv array (FACT COMP-004).

```python
@dataclass(frozen=True)
class CreatePrefix:      prefix_architecture: Literal["win32","win64"]
@dataclass(frozen=True)
class InstallDependency: dependency_profile_id: str               # phải ∈ approved_dependency_ids
@dataclass(frozen=True)
class SetRegistryValue:  key: str; value_name: str; value_type: Literal["REG_SZ","REG_DWORD"]; value: str
@dataclass(frozen=True)
class RunInstaller:      installer_ref: str; argv: tuple[str, ...] # installer do người dùng cấp; argv-only
@dataclass(frozen=True)
class VerifyFile:        path_label: str; sha256: str
@dataclass(frozen=True)
class CreateLauncher:    app_id: str; profile_id: str             # KHÔNG nhúng mật khẩu/URL-1-lần/lệnh (COMP-006)

RecipeStep = CreatePrefix | InstallDependency | SetRegistryValue | RunInstaller | VerifyFile | CreateLauncher

@dataclass(frozen=True)
class DryRunResult: ok: bool; planned_actions: tuple[str, ...]; rejected: tuple[ValidationError, ...]

class RecipeEngine(Protocol):
    def parse(self, raw_steps: Sequence[Mapping[str, Any]]) -> tuple[RecipeStep, ...]: ...   # reject action/param lạ
    def dry_run(self, steps: Sequence[RecipeStep], ctx: SemanticContext) -> DryRunResult: ... # KHÔNG thực thi gì
```

M1: chỉ `dry_run` (không cài thật — FACT M1 gate). Thực thi thật là M2 (BLOCKED).

### 7.7 Evidence API (WP9 — §11.2)

```python
@dataclass(frozen=True)
class EvidenceReport:   # ánh xạ contracts/evidence-report.schema.json
    report_id: str; manifest_id: str; tests: tuple["EvidenceTest", ...]
    decision: Literal["pending","experimental","task_verified","blocked","revoked"]
    qa_reviewer: str | None; environment: Mapping[str, Any]
@dataclass(frozen=True)
class EvidenceTest: test_id: str; required: bool; result: Literal["pass","fail","not_run","skipped","blocked_external_dependency"]
@dataclass(frozen=True)
class GateResult: allowed_status: CompatStatus; reasons_vi: tuple[str, ...]

class EvidenceValidator(Protocol):
    def load(self, path: str) -> EvidenceReport: ...
    def validate_schema(self, raw: Mapping[str, Any]) -> SchemaResult: ...
    def compute_allowed_status(self, rep: EvidenceReport) -> GateResult: ...  # gate "no task_verified w/o evidence"
```

Gate (FACT §11.2/§18.3): `task_verified` chỉ khi mọi test `required=true` có `result="pass"` **và** `qa_reviewer != null`. Nếu có `required` test là `not_run`/`skipped`/`blocked_external_dependency` → KHÔNG được `task_verified` (tối đa `experimental`/`blocked`). `skipped` KHÔNG được đổi thành pass (FACT §18.1).

### 7.8 Security primitives (WP8 — SEC-002/009, SUP-002)

```python
class SafePath(Protocol):
    def resolve_within(self, base: str, candidate: str) -> str: ...   # FD-based; chặn symlink/hardlink/traversal/TOCTOU; E_PATH_UNSAFE
    def open_within(self, base: str, candidate: str, mode: str) -> "IO[bytes]": ...  # O_NOFOLLOW + openat-style
class SafeExec(Protocol):
    def run_argv(self, argv: Sequence[str], *, timeout: float, env: Mapping[str,str] | None = None) -> "CompletedProc": ...
    # KHÔNG shell=True, KHÔNG nối chuỗi; argv[0] phải là path tuyệt đối đã allowlist
class Redactor(Protocol):
    def redact_text(self, s: str) -> str: ...        # mật khẩu/token/OTP/QR/đường dẫn tài liệu/IP nội bộ/username
    def redact_obj(self, o: Mapping[str, Any]) -> Mapping[str, Any]: ...
```

FACT: redaction KHÔNG chỉ regex — WP8 cung cấp cả cơ chế allowlist field + test dữ liệu nhạy cảm (SUP-002). Mọi `ErrorBody.details`, log, diagnostics export phải đi qua `Redactor`.

---

## 8. Quy ước chung bắt buộc (tổng hợp từ CLAUDE.md) — FACT

- KHÔNG `shell=True`, `eval`, `curl|bash`; mọi exec dùng `run_argv` (§7.8).
- KHÔNG đọc/ghi path ngoài policy; mọi path qua `resolve_within` (FD-based, không chỉ check chuỗi `..`).
- KHÔNG ghi secret vào source/log/stdout JSON/argv; dùng `Redactor` + (khi cần lưu thật) secret service/KWallet (SEC-009) — ngoài phạm vi logic M1, chỉ để interface.
- Validation 2 tầng luôn chạy đủ: schema rồi semantic; "schema pass" không mở cài.
- JSON output đúng envelope §1; exit code đúng §2; mã lỗi ổn định §3.
- Không ghi ngoài workspace được phép; không giả lập để báo đạt; test blocked giữ lý do, không đổi skipped→pass.
