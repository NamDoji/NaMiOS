"""Intent → cấu trúc (SAI-001, Phụ lục 04).

Ánh xạ một câu tiếng Việt tự do (có/không dấu) thành ``IntentResult`` có cấu
trúc. ``ModelProvider`` là SEAM để sau này cắm một model ngôn ngữ thật —
``parse_intent`` chỉ phụ thuộc Protocol này, không phụ thuộc provider cụ thể.

``FakeModelProvider`` ở M0 là luật DỰA TRÊN TỪ KHOÁ, TẤT ĐỊNH (không
ngẫu nhiên, không gọi mạng) — dùng cho test/CLI khi chưa nối model thật.

Bất biến an toàn (nghiệm thu T01 Phụ lục 04): KHÔNG BAO GIỜ tự suy đoán
người nộp hồ sơ (``nguoi_nop``) hoặc khoản tiền (``so_tien``) khi văn bản
không nêu tường minh — thông tin thiếu PHẢI xuất hiện trong ``unknowns`` để
orchestrator hỏi lại, không được tự lấp đầy bằng suy diễn.
"""

from __future__ import annotations

import re
from typing import Protocol

from namios_eco.search import fold_vn
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._types import IntentResult

__all__ = ["ModelProvider", "FakeModelProvider", "parse_intent"]


class ModelProvider(Protocol):
    """Seam cho một model hiểu ngôn ngữ (SAI-001). ``parse_intent`` gọi qua
    Protocol này — cắm ``FakeModelProvider`` (M0) hoặc một LLM thật sau này
    mà không đổi chữ ký caller."""

    def interpret(self, utterance: str) -> IntentResult:
        """Trả ``IntentResult`` thô từ một câu tiếng Việt tự do.

        KHÔNG được tự suy đoán người nộp hồ sơ hoặc khoản tiền khi văn bản
        không nêu tường minh — những trường đó PHẢI xuất hiện trong
        ``unknowns`` thay vì bị lấp đầy bằng giá trị bịa.
        """
        ...  # pragma: no cover - Protocol, không có thân hàm thật


# ---------------------------------------------------------------------------
# FakeModelProvider — luật từ khoá tất định (accent-insensitive qua fold_vn)
# ---------------------------------------------------------------------------

#: Mẫu động từ → intent. Khớp theo TỪ/CỤM TỪ có ranh giới (``\b``) trên văn
#: bản đã fold (không dấu, casefold) — tránh khớp nhầm vào giữa từ khác
#: (ví dụ "in" không khớp nhầm bên trong "minh"). Thứ tự = thứ tự ưu tiên khi
#: một câu (hiếm khi) chứa nhiều cụm khớp.
_VERB_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(cai|install)\b"), "install_app"),
    (re.compile(r"\b(nop|ke khai|thue|submit)\b"), "submit_filing"),
    (re.compile(r"\b(mo|open)\b"), "open_app"),
    (re.compile(r"\b(in|print)\b"), "print_document"),
)

#: Tên app đã biết → ``target_app`` chuẩn hoá. Khớp SUBSTRING trên văn bản đã
#: fold (đúng theo đặc tả — không ranh giới từ, vd "zalo" khớp cả "zaloweb").
_KNOWN_APPS: tuple[tuple[str, str], ...] = (
    ("misa", "misa"),
    ("word", "word"),
    ("excel", "excel"),
    ("zalo", "zalo"),
)

#: Từ khoá payer/amount dùng để coi là đã nêu TƯỜNG MINH trong văn bản — còn
#: lại luôn coi là CHƯA RÕ (thiên về an toàn: không chắc thì hỏi lại).
_PAYER_MARKERS: tuple[str, ...] = (
    "nguoi nop",
    "nguoi nop thue",
    "thay mat",
    "cho ong",
    "cho ba",
    "cong ty",
    "doanh nghiep",
    "ho va ten",
    "ho ten",
    "mst",
)
_AMOUNT_UNIT_MARKERS: tuple[str, ...] = ("vnd", "dong", "nghin", "trieu", "ty")
_AMOUNT_SYMBOLS: tuple[str, ...] = ("đ", "₫", "$")


def _has_word(folded: str, word: str) -> bool:
    """``True`` nếu ``word`` (có thể nhiều từ, cách nhau bằng space) xuất
    hiện trong ``folded`` với ranh giới từ ở cả hai đầu."""

    return re.search(rf"\b{re.escape(word)}\b", folded) is not None


def _detect_intent(folded: str) -> str:
    for pattern, intent_name in _VERB_RULES:
        if pattern.search(folded):
            return intent_name
    return "unknown"


def _detect_app(folded: str) -> str | None:
    for keyword, app_name in _KNOWN_APPS:
        if keyword in folded:
            return app_name
    return None


def _mentions_version(utterance: str, folded: str) -> bool:
    if re.search(r"\d", utterance):
        return True
    return _has_word(folded, "ban") or _has_word(folded, "version")


def _mentions_payer(folded: str) -> bool:
    return any(_has_word(folded, marker) for marker in _PAYER_MARKERS)


def _mentions_amount(utterance: str, folded: str) -> bool:
    if any(symbol in utterance for symbol in _AMOUNT_SYMBOLS):
        return True
    if not re.search(r"\d", utterance):
        return False
    return any(_has_word(folded, unit) for unit in _AMOUNT_UNIT_MARKERS)


def _confidence_for(*, verb_matched: bool, app_matched: bool) -> float:
    if verb_matched and app_matched:
        return 0.9
    if verb_matched:
        return 0.6
    return 0.3


def _detect_unknowns(intent_name: str, utterance: str, folded: str) -> tuple[str, ...]:
    """Liệt kê thông tin còn thiếu — KHÔNG BAO GIỜ tự lấp đầy. Thiên về an
    toàn: không nhận diện được tín hiệu tường minh → coi là chưa rõ."""

    unknowns: list[str] = []
    if intent_name in ("install_app", "submit_filing") and not _mentions_version(utterance, folded):
        unknowns.append("version")
    if intent_name == "install_app":
        unknowns.append("license")
    if intent_name == "submit_filing":
        if not _mentions_payer(folded):
            unknowns.append("nguoi_nop")
        if not _mentions_amount(utterance, folded):
            unknowns.append("so_tien")
    return tuple(unknowns)


class FakeModelProvider:
    """Provider luật-từ-khoá TẤT ĐỊNH (M0) — không ngẫu nhiên, không mạng.

    Cùng một câu đầu vào luôn trả về ``IntentResult`` giống hệt (so sánh
    bằng giá trị — ``IntentResult`` là ``@dataclass(frozen=True)``)."""

    def interpret(self, utterance: str) -> IntentResult:
        folded = fold_vn(utterance)
        intent_name = _detect_intent(folded)
        target_app = _detect_app(folded)
        verb_matched = intent_name != "unknown"
        confidence = _confidence_for(verb_matched=verb_matched, app_matched=target_app is not None)
        unknowns = _detect_unknowns(intent_name, utterance, folded)
        return IntentResult(
            intent=intent_name,
            target_app=target_app,
            target_data=None,
            required_outcome=None,
            constraints=(),
            unknowns=unknowns,
            confidence=confidence,
        )


# ---------------------------------------------------------------------------
# parse_intent — gọi provider rồi áp lớp an toàn SAU (post-process)
# ---------------------------------------------------------------------------


def _scrub_implied_payer_or_amount(result: IntentResult) -> IntentResult:
    """Lớp an toàn SAU provider: nếu ``nguoi_nop``/``so_tien`` đã bị đánh dấu
    CHƯA RÕ (``unknowns``) thì ``target_data``/``required_outcome`` của kết
    quả cuối cùng KHÔNG được "ngầm" mang theo người nộp/khoản tiền.

    Với ``FakeModelProvider`` điều này luôn đúng sẵn (không có logic nào gán
    ``target_data``/``required_outcome``). Hàm này là lớp phòng thủ cho khi
    ``provider`` là một model ngôn ngữ thật sau này — model có thể "ảo giác"
    ra số tiền/người nộp dù chính nó đã liệt kê vào ``unknowns``."""

    if result.intent != "submit_filing":
        return result

    missing_payer = "nguoi_nop" in result.unknowns
    missing_amount = "so_tien" in result.unknowns
    if not (missing_payer or missing_amount):
        return result

    new_target_data = None if missing_payer else result.target_data
    new_required_outcome = None if missing_amount else result.required_outcome
    if new_target_data == result.target_data and new_required_outcome == result.required_outcome:
        return result

    return IntentResult(
        intent=result.intent,
        target_app=result.target_app,
        target_data=new_target_data,
        required_outcome=new_required_outcome,
        constraints=result.constraints,
        unknowns=result.unknowns,
        confidence=result.confidence,
    )


def parse_intent(utterance: str, provider: ModelProvider) -> IntentResult:
    """Ánh xạ ``utterance`` (tiếng Việt, có/không dấu) → ``IntentResult``
    (SAI-001) qua ``provider``, rồi áp lớp an toàn tất định sau đó.

    Nếu ``confidence < 0.5`` kết quả vẫn được trả nguyên (không tự "nâng"
    hay che giấu) — caller (orchestrator) là nơi hiển thị
    ``sai.intent.low_confidence`` và xin xác nhận lại, không phải hàm này.
    """

    raw = provider.interpret(utterance)
    return _scrub_implied_payer_or_amount(raw)
