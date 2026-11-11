"""Áp lựa chọn lần đầu (UI-005) — ghi file config trong ``$HOME`` KHÔNG cần
root, **VÀ** áp lựa chọn đó lên desktop session hiện tại bằng cơ chế an toàn
đã có sẵn (``namios_security.run_argv`` — argv-only, KHÔNG shell=True).

``ConfigApplier`` ghi/đọc một file JSON duy nhất (``welcome.json``) trong
thư mục config do caller truyền vào (mặc định caller dùng
``namios_core.paths.config_dir()``; module này KHÔNG tự hardcode
``~/.config``). Mọi lần ``apply()`` đều giữ lại giá trị TRƯỚC đó trong một
file backup (``welcome.json.bak``) để ``revert()`` khôi phục được — "hoàn
tác" ở đây nghĩa là lấy lại đúng nội dung lần áp dụng trước, không phải một
Undo tổng quát cho toàn hệ thống.

``apply_runtime_desktop_settings`` (thêm 10/11/2026, sửa lỗ hổng "chỉ ghi
``welcome.json``, KHÔNG áp dụng gì thật") là lớp CHẠY THẬT bên cạnh
``ConfigApplier.apply``: ghi config fcitx5-unikey (``~/.config/fcitx5/conf/
unikey.conf``), đặt ``kdeglobals [KScreen] ScaleFactor`` qua ``kwriteconfig6``,
đặt MIME mặc định qua ``xdg-mime``, đặt máy in mặc định qua ``lpoptions`` —
TOÀN BỘ qua ``namios_security.run_argv`` (argv tuyệt đối, đã allowlist theo
``shutil.which``, KHÔNG tự chế subprocess riêng, đúng quy ước WP8 "mọi WP
khác chỉ import từ ``namios_security``"). Nguyên tắc tối thượng: **"áp được
gì thì áp, áp sai/áp thiếu còn hơn làm sập phiên đăng nhập lần đầu"** — mỗi
khía cạnh (``_apply_*``) tự cô lập lỗi của riêng nó bằng try/except RIÊNG,
không khía cạnh nào chặn khía cạnh khác, và hàm tổng
``apply_runtime_desktop_settings`` không bao giờ ``raise`` ra ngoài. KHÔNG
có cơ chế nào ở đây ghi đè ``etc/skel/.config/{kwinrc,kdeglobals,plasmarc,
appletsrc}`` tĩnh — mọi thay đổi đều qua lệnh hệ thống (``kwriteconfig6``/
``xdg-mime``/``lpoptions``) ghi vào file THẬT của user hiện tại lúc runtime,
không đụng file skel đóng gói (xem ``docs/specs/UX-WINDOWS-FAMILIAR.md``).

``verified_on_host: NO`` cho mọi cơ chế áp dụng thật dưới đây (tên khoá
``kdeglobals``/giá trị enum ``fcitx5-unikey`` đã đối chiếu mã nguồn upstream
công khai — xem ghi chú ở từng hàm — nhưng CHƯA chạy qua một desktop KDE
Plasma 6 thật trên Debian 13 trixie, container dựng hiện tại headless)."""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from namios_i18n import Lang, t
from namios_security import ExecPolicyError, redact_text, run_argv

# NOTE (i18n, 03/11/2026): ``reason_vi``/``FirstRunValidationError.reason_vi``
# đi qua ``namios_i18n.t`` (nhóm key ``welcome.firstrun.error.*``, VI/EN đã
# seed) nhưng LUÔN ép ``lang=Lang.VI`` — field đặt tên theo quy ước ``_vi``
# (giống ``ValidationError.message_vi`` ở namios_eco/namios_core), một
# nguồn sự thật chung, KHÔNG đổi theo ngôn ngữ hiển thị wizard (``ui.py``
# dịch phần LABEL hiển thị riêng, độc lập với exception này).

__all__ = [
    "ImeMethod",
    "UiScalePercent",
    "FirstRunChoices",
    "AppliedConfigReport",
    "FirstRunValidationError",
    "ConfigApplier",
    "WelcomeDoneMarker",
    "RuntimeApplyStatus",
    "RuntimeApplyOutcome",
    "RuntimeApplyReport",
    "apply_runtime_desktop_settings",
]

ImeMethod = Literal["telex", "vni"]
UiScalePercent = Literal[100, 125, 150]

_VALID_IME_METHODS: frozenset[str] = frozenset({"telex", "vni"})
_VALID_UI_SCALES: frozenset[int] = frozenset({100, 125, 150})

_CONFIG_FILENAME = "welcome.json"
_BACKUP_SUFFIX = ".bak"
_SCHEMA_VERSION = 1
_DONE_MARKER_FILENAME = "welcome-done"
_APPLY_REPORT_FILENAME = "welcome-apply-report.json"

#: Timeout 1 lệnh hệ thống được gọi lúc apply (kwriteconfig6/xdg-mime/
#: lpstat/lpoptions/fcitx5-remote) — đủ rộng cho máy chậm, đủ hẹp để không
#: treo cả wizard nếu 1 lệnh bị kẹt (vd daemon không phản hồi dbus).
_APPLY_COMMAND_TIMEOUT_SECONDS = 10.0

#: fcitx5-unikey (`src/unikey-config.h` upstream, `FCITX_CONFIG_ENUM_NAME_WITH_I18N
#: (UkInputMethod, N_("Telex"), N_("VNI"), ...)`) nhận giá trị khoá
#: ``InputMethod`` đúng NGUYÊN VĂN các chuỗi này trong
#: ``~/.config/fcitx5/conf/unikey.conf`` — đã đối chiếu mã nguồn upstream
#: công khai (xem docstring module), CHƯA chạy thật trên Fcitx5 đóng gói
#: Debian 13 trixie (verified_on_host: NO, cùng mức độ chắc chắn như hook
#: `0200-fcitx5-default-im.hook.chroot` đã ghi rõ cho chính file profile).
_FCITX5_UNIKEY_INPUT_METHOD_VALUE: dict[str, str] = {"telex": "Telex", "vni": "VNI"}

#: Hệ số scale KDE Plasma đọc từ ``kdeglobals`` nhóm ``[KScreen]`` khoá
#: ``ScaleFactor`` (kiểu double) — khoá CHUẨN do `kcmshell6 kcm_kscreen`/
#: `kwriteconfig6 --group KScreen --key ScaleFactor` ghi, cộng đồng KDE dùng
#: rộng rãi cho scale toàn cục. Có hiệu lực đầy đủ sau khi đăng xuất/đăng
#: nhập lại (khởi động lại `plasmashell` giữa phiên là rủi ro "làm sập
#: phiên đăng nhập lần đầu" — KHÔNG làm ở đây).
_UI_SCALE_FACTOR: dict[int, str] = {100: "1.0", 125: "1.25", 150: "1.5"}

_MIME_TYPE_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_MIME_TYPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_MIME_TYPE_PDF = "application/pdf"

#: Alias tên app người dùng gõ (giá trị mặc định của 3 ô nhập ở
#: ``ui._DefaultAppsPage``) -> desktop-entry-id THẬT theo đúng tên gói trong
#: ``docs/specs/PL09-DEFAULT-APPS.md`` §3. App không có trong bảng này vẫn
#: được thử (xem ``_resolve_desktop_id``) — bảng chỉ là phím tắt cho các ca
#: phổ biến nhất, KHÔNG phải allowlist chặn giá trị khác.
_DEFAULT_APP_DESKTOP_ID_ALIASES: dict[str, str] = {
    "libreoffice-writer": "libreoffice-writer.desktop",
    "libreoffice-calc": "libreoffice-calc.desktop",
    "libreoffice-impress": "libreoffice-impress.desktop",
    "okular": "org.kde.okular.desktop",
    "firefox": "firefox-esr.desktop",
    "firefox-esr": "firefox-esr.desktop",
}

RuntimeApplyStatus = Literal["applied", "skipped", "failed"]


@dataclass(frozen=True)
class FirstRunChoices:
    """Các lựa chọn luồng đầu tiên (UI-005). ``default_printer=None`` nghĩa
    là người dùng chưa chọn máy in mặc định (bỏ qua bước này)."""

    ime_method: ImeMethod
    ui_scale_percent: UiScalePercent
    default_app_docx: str
    default_app_xlsx: str
    default_app_pdf: str
    default_printer: str | None = None

    def validate(self) -> None:
        if self.ime_method not in _VALID_IME_METHODS:
            raise FirstRunValidationError(
                field="ime_method",
                reason_vi=t(
                    "welcome.firstrun.error.ime_method_invalid",
                    lang=Lang.VI,
                    value=self.ime_method,
                ),
            )
        if self.ui_scale_percent not in _VALID_UI_SCALES:
            raise FirstRunValidationError(
                field="ui_scale_percent",
                reason_vi=t(
                    "welcome.firstrun.error.ui_scale_invalid",
                    lang=Lang.VI,
                    value=self.ui_scale_percent,
                ),
            )
        for field_name, value in (
            ("default_app_docx", self.default_app_docx),
            ("default_app_xlsx", self.default_app_xlsx),
            ("default_app_pdf", self.default_app_pdf),
        ):
            if not value or not value.strip():
                raise FirstRunValidationError(
                    field=field_name,
                    reason_vi=t("welcome.firstrun.error.field_blank", lang=Lang.VI),
                )


@dataclass(frozen=True)
class AppliedConfigReport:
    """Kết quả một lần ``apply()`` — ``previous`` là giá trị trước đó
    (``None`` nếu đây là lần áp dụng đầu tiên)."""

    config_path: str
    backup_path: str | None
    previous: FirstRunChoices | None
    current: FirstRunChoices


@dataclass
class FirstRunValidationError(Exception):
    """Lựa chọn lần đầu không hợp lệ (field cụ thể)."""

    field: str
    reason_vi: str

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return t(
            "welcome.firstrun.error.validation_prefix",
            lang=Lang.VI,
            field=self.field,
            reason=self.reason_vi,
        )


@dataclass(frozen=True)
class RuntimeApplyOutcome:
    """Kết quả áp dụng THẬT một khía cạnh (``aspect``, ví dụ
    ``"ime_method"``/``"ui_scale_percent"``/``"default_app_pdf"``/
    ``"default_printer"``) lên desktop session hiện tại.

    ``status``: ``"applied"`` (đã ghi/gọi lệnh thành công), ``"skipped"``
    (cố ý KHÔNG áp — thiếu công cụ hệ thống, chưa chọn, hoặc app/máy in
    không khớp cái gì có thật trên máy — tránh ghi default trỏ vào chỗ
    không tồn tại), ``"failed"`` (có thử nhưng lệnh/IO báo lỗi). KHÔNG khía
    cạnh nào raise ra khỏi hàm tạo outcome của nó — xem từng ``_apply_*``."""

    aspect: str
    status: RuntimeApplyStatus
    detail: str


@dataclass(frozen=True)
class RuntimeApplyReport:
    """Tổng hợp mọi ``RuntimeApplyOutcome`` của một lần
    ``apply_runtime_desktop_settings`` — ``ConfigApplier.write_apply_report``
    ghi report này cạnh ``welcome.json`` để chẩn đoán sau (vd
    ``namios-chan-doan``) biết khía cạnh nào áp được/bị bỏ qua/lỗi."""

    outcomes: tuple[RuntimeApplyOutcome, ...]
    applied_at: str

    @property
    def has_failure(self) -> bool:
        """``True`` nếu ÍT NHẤT một khía cạnh ``"failed"`` (KHÔNG tính
        ``"skipped"`` — bỏ qua có chủ đích không phải lỗi)."""

        return any(outcome.status == "failed" for outcome in self.outcomes)


def _choices_to_payload(choices: FirstRunChoices, applied_at: str) -> dict[str, Any]:
    payload = asdict(choices)
    payload["schema_version"] = _SCHEMA_VERSION
    payload["applied_at"] = applied_at
    return payload


def _payload_to_choices(payload: dict[str, Any]) -> FirstRunChoices:
    return FirstRunChoices(
        ime_method=payload["ime_method"],
        ui_scale_percent=payload["ui_scale_percent"],
        default_app_docx=payload["default_app_docx"],
        default_app_xlsx=payload["default_app_xlsx"],
        default_app_pdf=payload["default_app_pdf"],
        default_printer=payload.get("default_printer"),
    )


def _default_clock() -> datetime:
    return datetime.now(tz=UTC)


class ConfigApplier:
    """Ghi/đọc/hoàn tác lựa chọn luồng đầu tiên trong một file config JSON
    dưới ``config_dir`` (do caller truyền vào — KHÔNG hardcode ``$HOME``)."""

    def __init__(
        self,
        config_dir: Path | str,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._config_dir = Path(config_dir)
        self._clock = clock if clock is not None else _default_clock

    @property
    def config_path(self) -> Path:
        return self._config_dir / _CONFIG_FILENAME

    @property
    def backup_path(self) -> Path:
        return self._config_dir / f"{_CONFIG_FILENAME}{_BACKUP_SUFFIX}"

    def read_current(self) -> FirstRunChoices | None:
        """Đọc lựa chọn hiện tại. Trả ``None`` nếu chưa có file hoặc file
        hỏng (KHÔNG ném lỗi — coi như "chưa áp dụng lần nào")."""

        return self._read_payload_as_choices(self.config_path)

    def _read_payload_as_choices(self, path: Path) -> FirstRunChoices | None:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None
        try:
            payload = json.loads(text)
            return _payload_to_choices(payload)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def _write_atomic(self, path: Path, payload: dict[str, Any]) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f"{path.name}.tmp-{os.getpid()}")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp_path, path)

    def apply(self, choices: FirstRunChoices) -> AppliedConfigReport:
        """Ghi ``choices`` vào file config (không cần root). Giá trị trước
        đó (nếu có) được sao lưu vào file ``.bak`` để ``revert()`` dùng."""

        choices.validate()
        previous = self.read_current()

        if self.config_path.exists():
            self._config_dir.mkdir(parents=True, exist_ok=True)
            previous_text = self.config_path.read_text(encoding="utf-8")
            tmp_backup = self.backup_path.with_name(f"{self.backup_path.name}.tmp-{os.getpid()}")
            tmp_backup.write_text(previous_text, encoding="utf-8")
            os.replace(tmp_backup, self.backup_path)

        applied_at = self._clock().isoformat()
        payload = _choices_to_payload(choices, applied_at)
        self._write_atomic(self.config_path, payload)

        return AppliedConfigReport(
            config_path=str(self.config_path),
            backup_path=str(self.backup_path) if self.backup_path.exists() else None,
            previous=previous,
            current=choices,
        )

    @property
    def apply_report_path(self) -> Path:
        return self._config_dir / _APPLY_REPORT_FILENAME

    def write_apply_report(self, report: RuntimeApplyReport) -> Path:
        """Ghi lại ``RuntimeApplyReport`` (kết quả ``apply_runtime_desktop_
        settings``) ra JSON cạnh ``welcome.json`` — "log" để chẩn đoán sau,
        KHÔNG BAO GIỜ ``raise``: lỗi ghi file (đĩa đầy/quyền) bị nuốt ở đây,
        coi là MẤT LOG chứ không phải lỗi làm sập wizard (cùng nguyên tắc
        fail-safe với toàn bộ ``apply_runtime_desktop_settings``)."""

        try:
            payload: dict[str, Any] = {
                "schema_version": _SCHEMA_VERSION,
                "applied_at": report.applied_at,
                "outcomes": [asdict(outcome) for outcome in report.outcomes],
            }
            self._write_atomic(self.apply_report_path, payload)
        except OSError:
            pass  # noqa: S110 - "log" tự nguyện; mất log KHÔNG phải lỗi làm sập wizard
        return self.apply_report_path

    def revert(self) -> FirstRunChoices | None:
        """Khôi phục config về giá trị TRƯỚC lần ``apply()`` gần nhất (từ
        file ``.bak``). Trả giá trị đã khôi phục, hoặc ``None`` nếu không có
        backup để hoàn tác (chưa từng ``apply()`` quá 1 lần)."""

        if not self.backup_path.exists():
            return None
        restored = self._read_payload_as_choices(self.backup_path)
        backup_text = self.backup_path.read_text(encoding="utf-8")
        self._config_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self.config_path.with_name(f"{self.config_path.name}.tmp-{os.getpid()}")
        tmp_path.write_text(backup_text, encoding="utf-8")
        os.replace(tmp_path, self.config_path)
        os.remove(self.backup_path)
        return restored


class WelcomeDoneMarker:
    """Đánh dấu "đã chạy chào mừng lần đầu" bằng MỘT file rỗng dưới
    ``config_dir`` (mặc định ``~/.config/namios/welcome-done``).

    LÝ DO CẦN FILE NÀY: ``etc/skel/.config/autostart/namios-welcome.desktop``
    tự chạy ``namios-welcome`` ở **MỌI** lần đăng nhập KDE (XDG Desktop Entry
    Specification không có trường "chỉ chạy một lần duy nhất" — comment trong
    chính file .desktop đó đã ghi rõ: cơ chế "chỉ 1 lần" phải do chính mã
    Python ``namios_welcome`` tự làm). Không có marker này, wizard sẽ mở lại
    mỗi lần người dùng đăng nhập — ngược hẳn tinh thần "tiếp cận nhẹ nhàng"
    (Phụ lục 13 §6: không được làm phiền người dùng lặp lại).

    ``is_done()``/``mark_done()`` không phụ thuộc GUI — test được bằng
    ``tmp_path`` như ``ConfigApplier`` (xem ``tests/unit/welcome/``). Người
    dùng muốn chạy lại wizard thủ công vẫn làm được bất cứ lúc nào bằng lệnh
    ``namios-welcome`` (wrapper hệ thống do hook 0300 tạo) — marker chỉ chặn
    việc TỰ ĐỘNG mở lại, không khoá tính năng."""

    def __init__(self, config_dir: Path | str) -> None:
        self._config_dir = Path(config_dir)

    @property
    def marker_path(self) -> Path:
        return self._config_dir / _DONE_MARKER_FILENAME

    def is_done(self) -> bool:
        """``True`` nếu đã chạy chào mừng xong ở một lần đăng nhập trước."""

        return self.marker_path.exists()

    def mark_done(self, *, clock: Callable[[], datetime] | None = None) -> Path:
        """Ghi marker (ghi lại nhiều lần vẫn an toàn — idempotent). Ghi
        atomic giống ``ConfigApplier._write_atomic`` (tmp file + ``os.replace``)
        để không bao giờ để lại file rỗng/dở dang nếu bị ngắt giữa chừng."""

        self._config_dir.mkdir(parents=True, exist_ok=True)
        timestamp = (clock if clock is not None else _default_clock)().isoformat()
        tmp_path = self.marker_path.with_name(f"{_DONE_MARKER_FILENAME}.tmp-{os.getpid()}")
        tmp_path.write_text(timestamp + "\n", encoding="utf-8")
        os.replace(tmp_path, self.marker_path)
        return self.marker_path


# --- Áp dụng THẬT lên desktop session (10/11/2026) -------------------------
#
# Mọi hàm ``_apply_*`` dưới đây theo ĐÚNG một khuôn: tự bọc try/except RIÊNG
# của mình, KHÔNG BAO GIỜ để lỗi thoát ra ngoài — trả về ``RuntimeApplyOutcome``
# dù thành công/bỏ qua/lỗi. "Bỏ qua" (skipped) được dùng chủ động khi áp
# THẬT có rủi ro ghi sai (vd trỏ default app vào một desktop-entry không tồn
# tại, hoặc đặt máy in mặc định chưa từng cấu hình trong CUPS) — im lặng bỏ
# qua còn an toàn hơn áp một giá trị chắc chắn sai.


def _which_absolute(program: str) -> str | None:
    """``shutil.which`` rồi ép ``str`` tuyệt đối — khớp đúng yêu cầu
    ``namios_security.run_argv``/``ArgvSafeExec`` ("argv[0] phải là đường
    dẫn tuyệt đối đã allowlist"). Trả ``None`` nếu không tìm thấy lệnh (máy
    thiếu gói tương ứng) — KHÔNG đoán đường dẫn cố định, để không gọi nhầm
    một binary khác trùng tên nằm ở nơi bất thường."""

    found = shutil.which(program)
    return found if found is not None else None


def _redacted(text: str) -> str:
    """``redact_text`` (``namios_security``) cho MỌI chuỗi có thể chứa
    output lệnh thật (``stderr``) hay thông tin máy trước khi nhét vào
    ``RuntimeApplyOutcome.detail`` — report này bị ghi ra đĩa
    (``ConfigApplier.write_apply_report``), áp cùng mức phòng thủ "log đã
    lọc" như ``namios_core.paths.logs_dir`` mô tả cho log hệ thống."""

    return redact_text(text)


def _apply_ime_method(ime_method: str, *, config_dir: Path) -> RuntimeApplyOutcome:
    """Ghi ``~/.config/fcitx5/conf/unikey.conf`` (``InputMethod=Telex``/
    ``InputMethod=VNI``) — khía cạnh "áp thật" mà hook build-time
    ``0200-fcitx5-default-im.hook.chroot`` CHỦ ĐỘNG không làm (profile skel
    đó chỉ bật sẵn engine Unikey, còn chọn Telex hay VNI theo đúng lựa chọn
    THẬT của người dùng là việc của chính namios-welcome lúc đăng nhập lần
    đầu — xem ``docs/specs/UX-WINDOWS-FAMILIAR.md`` §5). Dùng
    ``config_dir.parent`` (= ``$XDG_CONFIG_HOME``, suy từ CHÍNH tham số
    ``config_dir`` caller truyền cho ``ConfigApplier`` — KHÔNG hardcode
    ``~/.config`` lần thứ hai) để tính thư mục config fcitx5 anh em."""

    aspect = "ime_method"
    try:
        value = _FCITX5_UNIKEY_INPUT_METHOD_VALUE.get(ime_method)
        if value is None:
            return RuntimeApplyOutcome(
                aspect=aspect,
                status="skipped",
                detail=f"không nhận diện được giá trị bộ gõ: {ime_method!r}",
            )

        conf_dir = Path(config_dir).parent / "fcitx5" / "conf"
        conf_dir.mkdir(parents=True, exist_ok=True)
        conf_path = conf_dir / "unikey.conf"
        # Đọc-sửa-ghi: GIỮ mọi khoá khác người dùng đã đặt trong unikey.conf,
        # chỉ cập nhật (hoặc thêm) dòng InputMethod. Ghi đè cả file như trước
        # sẽ xoá cấu hình bộ gõ khác khi chạy lại namios-welcome.
        existing_lines: list[str] = []
        if conf_path.exists():
            try:
                existing_lines = conf_path.read_text(encoding="utf-8").splitlines()
            except OSError:
                existing_lines = []
        new_lines: list[str] = []
        replaced = False
        for line in existing_lines:
            if line.split("=", 1)[0].strip() == "InputMethod":
                new_lines.append(f"InputMethod={value}")
                replaced = True
            else:
                new_lines.append(line)
        if not replaced:
            new_lines.append(f"InputMethod={value}")
        tmp_path = conf_path.with_name(f"{conf_path.name}.tmp-{os.getpid()}")
        tmp_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        os.replace(tmp_path, conf_path)

        reload_detail = "chưa nạp lại được fcitx5: thiếu lệnh fcitx5-remote"
        fcitx5_remote = _which_absolute("fcitx5-remote")
        if fcitx5_remote is not None:
            try:
                result = run_argv([fcitx5_remote, "-r"], timeout=_APPLY_COMMAND_TIMEOUT_SECONDS)
                reload_detail = (
                    "đã yêu cầu fcitx5 nạp lại cấu hình"
                    if result.returncode == 0
                    else "fcitx5-remote -r trả về mã lỗi (không ảnh hưởng — "
                    "đăng xuất rồi đăng nhập lại vẫn sẽ nạp đúng cấu hình)"
                )
            except ExecPolicyError:
                reload_detail = (
                    "không gọi được fcitx5-remote -r (không ảnh hưởng — "
                    "đăng xuất rồi đăng nhập lại vẫn sẽ nạp đúng cấu hình)"
                )

        return RuntimeApplyOutcome(
            aspect=aspect,
            status="applied",
            detail=_redacted(f"đã ghi {conf_path} (InputMethod={value}); {reload_detail}"),
        )
    except Exception as exc:  # noqa: BLE001 - fail-safe tuyệt đối, xem đầu khối
        return RuntimeApplyOutcome(
            aspect=aspect, status="failed", detail=_redacted(f"lỗi ngoài dự kiến: {exc}")
        )


def _apply_ui_scale(ui_scale_percent: int) -> RuntimeApplyOutcome:
    """``kwriteconfig6 --file kdeglobals --group KScreen --key ScaleFactor``
    — ghi THẬT vào ``kdeglobals`` của user hiện tại lúc runtime qua
    ``kwriteconfig6`` (KDE tự resolve ``kdeglobals`` theo ``$XDG_CONFIG_HOME``
    của CHÍNH tiến trình gọi, không phải module này tính đường dẫn) — đây là
    cách hợp lệ để "đổi mặc định trong kdeglobals" mà không đụng file skel
    tĩnh (xem ràng buộc ở docstring module và ``docs/specs/
    UX-WINDOWS-FAMILIAR.md``). Có hiệu lực đầy đủ sau khi đăng xuất/đăng
    nhập lại — KHÔNG khởi động lại ``plasmashell`` giữa phiên ở đây."""

    aspect = "ui_scale_percent"
    try:
        factor = _UI_SCALE_FACTOR.get(ui_scale_percent)
        if factor is None:
            return RuntimeApplyOutcome(
                aspect=aspect,
                status="skipped",
                detail=f"không nhận diện được giá trị cỡ chữ: {ui_scale_percent!r}",
            )

        kwriteconfig6 = _which_absolute("kwriteconfig6")
        if kwriteconfig6 is None:
            return RuntimeApplyOutcome(
                aspect=aspect,
                status="skipped",
                detail=(
                    "thiếu lệnh kwriteconfig6 (có thể máy không chạy KDE Plasma, "
                    "hoặc gói liên quan chưa được cài)"
                ),
            )

        result = run_argv(
            [
                kwriteconfig6,
                "--file",
                "kdeglobals",
                "--group",
                "KScreen",
                "--key",
                "ScaleFactor",
                "--type",
                "double",
                factor,
            ],
            timeout=_APPLY_COMMAND_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            return RuntimeApplyOutcome(
                aspect=aspect,
                status="failed",
                detail=_redacted(
                    f"kwriteconfig6 trả về mã lỗi {result.returncode}: "
                    f"{result.stderr.decode('utf-8', 'replace').strip()}"
                ),
            )
        return RuntimeApplyOutcome(
            aspect=aspect,
            status="applied",
            detail=(
                f"đã ghi kdeglobals[KScreen]ScaleFactor={factor} "
                "(cần đăng xuất rồi đăng nhập lại để Plasma áp dụng đầy đủ)"
            ),
        )
    except ExecPolicyError as exc:
        return RuntimeApplyOutcome(
            aspect=aspect,
            status="failed",
            detail=_redacted(f"không gọi được kwriteconfig6: {exc.reason_vi}"),
        )
    except Exception as exc:  # noqa: BLE001 - fail-safe tuyệt đối, xem đầu khối
        return RuntimeApplyOutcome(
            aspect=aspect, status="failed", detail=_redacted(f"lỗi ngoài dự kiến: {exc}")
        )


def _resolve_desktop_id(app_value: str) -> str:
    key = app_value.strip()
    alias = _DEFAULT_APP_DESKTOP_ID_ALIASES.get(key)
    if alias is not None:
        return alias
    return key if key.endswith(".desktop") else f"{key}.desktop"


def _find_desktop_file(desktop_id: str, *, home: Path) -> Path | None:
    """Tìm ``desktop_id`` trong các thư mục ``applications/`` chuẩn XDG
    (``$XDG_DATA_HOME`` rồi từng phần tử ``$XDG_DATA_DIRS``, fallback đúng
    giá trị mặc định theo spec XDG khi biến môi trường trống — KHÔNG hardcode
    ``~/.local/share``/``/usr/share`` một mình). Trả ``None`` nếu không thấy
    ở đâu — caller dùng để KHÔNG đặt default trỏ vào app không có thật."""

    xdg_data_home_raw = os.environ.get("XDG_DATA_HOME")
    data_home = Path(xdg_data_home_raw) if xdg_data_home_raw else home / ".local" / "share"
    xdg_data_dirs_raw = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
    search_bases = [data_home, *(Path(p) for p in xdg_data_dirs_raw.split(":") if p)]
    for base in search_bases:
        candidate = base / "applications" / desktop_id
        if candidate.is_file():
            return candidate
    return None


def _apply_default_app(
    *, aspect: str, app_value: str, mime_type: str, home: Path
) -> RuntimeApplyOutcome:
    """``xdg-mime default <desktop-entry-id> <mime_type>`` — ghi THẬT vào
    ``~/.config/mimeapps.list`` của user hiện tại. CHỦ ĐỘNG bỏ qua (không
    gọi ``xdg-mime``) nếu không tìm thấy file ``.desktop`` tương ứng trong
    bất kỳ thư mục ``applications/`` chuẩn XDG nào — tránh đặt một mặc định
    trỏ vào ứng dụng không có thật trên máy (vd người dùng gõ sai tên hoặc
    gói chưa được cài)."""

    try:
        if not app_value or not app_value.strip():
            return RuntimeApplyOutcome(aspect=aspect, status="skipped", detail="chưa chọn ứng dụng")

        desktop_id = _resolve_desktop_id(app_value)
        if _find_desktop_file(desktop_id, home=home) is None:
            return RuntimeApplyOutcome(
                aspect=aspect,
                status="skipped",
                detail=(
                    f"không thấy {desktop_id} trong các thư mục applications/ — có thể "
                    "chưa cài hoặc tên không khớp; KHÔNG đặt mặc định để tránh trỏ sai"
                ),
            )

        xdg_mime = _which_absolute("xdg-mime")
        if xdg_mime is None:
            return RuntimeApplyOutcome(
                aspect=aspect, status="skipped", detail="thiếu lệnh xdg-mime"
            )

        result = run_argv(
            [xdg_mime, "default", desktop_id, mime_type], timeout=_APPLY_COMMAND_TIMEOUT_SECONDS
        )
        if result.returncode != 0:
            return RuntimeApplyOutcome(
                aspect=aspect,
                status="failed",
                detail=_redacted(
                    f"xdg-mime trả về mã lỗi {result.returncode}: "
                    f"{result.stderr.decode('utf-8', 'replace').strip()}"
                ),
            )
        return RuntimeApplyOutcome(
            aspect=aspect, status="applied", detail=f"{desktop_id} -> {mime_type}"
        )
    except ExecPolicyError as exc:
        return RuntimeApplyOutcome(
            aspect=aspect,
            status="failed",
            detail=_redacted(f"không gọi được xdg-mime: {exc.reason_vi}"),
        )
    except Exception as exc:  # noqa: BLE001 - fail-safe tuyệt đối, xem đầu khối
        return RuntimeApplyOutcome(
            aspect=aspect, status="failed", detail=_redacted(f"lỗi ngoài dự kiến: {exc}")
        )


def _apply_default_printer(printer: str | None) -> RuntimeApplyOutcome:
    """``lpoptions -d <printer>`` — ghi THẬT vào ``~/.cups/lpoptions`` của
    user hiện tại, nhưng CHỈ SAU KHI xác nhận ``lpstat -p <printer>`` nhận
    diện được máy in đó trong CUPS (tránh đặt default trỏ vào một tên máy in
    chưa từng cấu hình — rủi ro giống hệt ``_apply_default_app``)."""

    aspect = "default_printer"
    try:
        if printer is None or not printer.strip():
            return RuntimeApplyOutcome(
                aspect=aspect,
                status="skipped",
                detail="chưa chọn máy in mặc định (bỏ qua bước này)",
            )
        name = printer.strip()

        lpstat = _which_absolute("lpstat")
        if lpstat is None:
            return RuntimeApplyOutcome(
                aspect=aspect,
                status="skipped",
                detail="thiếu lệnh lpstat (chưa cài CUPS client)",
            )
        check = run_argv([lpstat, "-p", name], timeout=_APPLY_COMMAND_TIMEOUT_SECONDS)
        if check.returncode != 0:
            return RuntimeApplyOutcome(
                aspect=aspect,
                status="skipped",
                detail=_redacted(
                    f"máy in '{name}' chưa cấu hình trong CUPS — KHÔNG đặt mặc định để tránh trỏ sai"
                ),
            )

        lpoptions = _which_absolute("lpoptions")
        if lpoptions is None:
            return RuntimeApplyOutcome(
                aspect=aspect, status="skipped", detail="thiếu lệnh lpoptions"
            )
        result = run_argv([lpoptions, "-d", name], timeout=_APPLY_COMMAND_TIMEOUT_SECONDS)
        if result.returncode != 0:
            return RuntimeApplyOutcome(
                aspect=aspect,
                status="failed",
                detail=_redacted(
                    f"lpoptions trả về mã lỗi {result.returncode}: "
                    f"{result.stderr.decode('utf-8', 'replace').strip()}"
                ),
            )
        return RuntimeApplyOutcome(
            aspect=aspect, status="applied", detail=_redacted(f"đặt máy in mặc định: {name}")
        )
    except ExecPolicyError as exc:
        return RuntimeApplyOutcome(
            aspect=aspect,
            status="failed",
            detail=_redacted(f"không gọi được lpstat/lpoptions: {exc.reason_vi}"),
        )
    except Exception as exc:  # noqa: BLE001 - fail-safe tuyệt đối, xem đầu khối
        return RuntimeApplyOutcome(
            aspect=aspect, status="failed", detail=_redacted(f"lỗi ngoài dự kiến: {exc}")
        )


def apply_runtime_desktop_settings(
    choices: FirstRunChoices,
    *,
    config_dir: Path,
    home: Path,
    clock: Callable[[], datetime] | None = None,
) -> RuntimeApplyReport:
    """Áp THẬT ``choices`` (đã ghi qua ``ConfigApplier.apply``) lên desktop
    session hiện tại — đây là phần trước đây CHƯA làm (vá lỗ hổng "chỉ ghi
    welcome.json"). CHỈ áp những gì wizard THẬT đã thu thập (``ime_method``/
    ``ui_scale_percent``/3 app mặc định/``default_printer``) — KHÔNG có
    ngôn ngữ hiển thị hay múi giờ ở đây vì ``FirstRunChoices`` KHÔNG có field
    nào cho 2 việc đó (ngôn ngữ Plasma Shell mặc định + timezone
    ``Asia/Ho_Chi_Minh`` đã là mặc định hệ thống đặt lúc build — xem
    ``etc/skel/.config/plasma-localerc`` + hook ``0110-timezone.hook.chroot``
    — người dùng tự đổi qua System Settings, không phải việc của wizard
    này).

    KHÔNG BAO GIỜ ``raise``: mỗi khía cạnh gọi một hàm ``_apply_*`` đã tự cô
    lập lỗi của riêng nó (xem docstring từng hàm) — hàm này chỉ gom kết quả,
    không có logic nào ở tầng này có thể tự nó ném lỗi ngoài việc gọi 6 hàm
    con kia theo thứ tự cố định."""

    outcomes = (
        _apply_ime_method(choices.ime_method, config_dir=config_dir),
        _apply_ui_scale(choices.ui_scale_percent),
        _apply_default_app(
            aspect="default_app_docx",
            app_value=choices.default_app_docx,
            mime_type=_MIME_TYPE_DOCX,
            home=home,
        ),
        _apply_default_app(
            aspect="default_app_xlsx",
            app_value=choices.default_app_xlsx,
            mime_type=_MIME_TYPE_XLSX,
            home=home,
        ),
        _apply_default_app(
            aspect="default_app_pdf",
            app_value=choices.default_app_pdf,
            mime_type=_MIME_TYPE_PDF,
            home=home,
        ),
        _apply_default_printer(choices.default_printer),
    )
    applied_at = (clock if clock is not None else _default_clock)().isoformat()
    return RuntimeApplyReport(outcomes=outcomes, applied_at=applied_at)
