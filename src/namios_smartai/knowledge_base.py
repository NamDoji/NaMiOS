"""Knowledge Base có nguồn (SAI-025).

Tách 4 tầng provenance — (a) tài liệu chính thức, (b) chứng nhận NaMiOS, (c)
ghi nhận cộng đồng CHƯA kiểm, (d) suy luận AI — và CHỈ chứng nhận NaMiOS
(``NAMIOS_CERT``) mới khẳng định được mức thử thật trên NaMiOS. Mỗi câu trả lời
kỹ thuật kèm provenance + ngày + app/version + mức tin cậy; thông tin cũ được
đánh dấu. KHÔNG dùng lời đồn cộng đồng/AI để cài driver hay kết luận chạy được.

Bất biến cốt lõi (nghiệm thu SAI-025): hỏi "MISA chạy được không?" trả ĐÚNG mức
thử của sản phẩm/version CỤ THỂ, hoặc "chưa kiểm" — KHÔNG suy từ version khác,
KHÔNG để nguồn cộng đồng/AI nâng mức thử.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._types import KbAnswer, KbEntry, Provenance, TestedLevel

__all__ = ["KnowledgeBase", "trust_rank"]

#: Thứ hạng độ tin theo nguồn (cao hơn = đáng tin hơn). Dùng để chọn nguồn
#: THÔNG TIN chủ đạo khi KHÔNG có chứng nhận — KHÔNG để nâng mức thử.
_TRUST_RANK: dict[Provenance, int] = {
    Provenance.NAMIOS_CERT: 3,
    Provenance.OFFICIAL_DOC: 2,
    Provenance.COMMUNITY_UNVERIFIED: 1,
    Provenance.AI_INFERENCE: 0,
}

#: Mức thử hợp lệ từ một chứng nhận NaMiOS (các giá trị khác bỏ qua).
_CERT_LEVELS: frozenset[TestedLevel] = frozenset(
    {TestedLevel.VERIFIED, TestedLevel.PARTIAL, TestedLevel.FAILED}
)

#: Thứ tự "an toàn" khi HAI chứng nhận cùng MỐC THỜI GIAN: chọn mức BẢO THỦ hơn
#: (FAILED) để KHÔNG bao giờ over-claim "chạy được" (fail-closed, SAI-025).
_LEVEL_SAFETY: dict[TestedLevel, int] = {
    TestedLevel.FAILED: 0,
    TestedLevel.PARTIAL: 1,
    TestedLevel.VERIFIED: 2,
}

#: Mốc "cũ nhất" (UTC-aware) cho chứng nhận có ngày KHÔNG parse được — ngày hỏng
#: KHÔNG được coi là "mới nhất" để đè chứng nhận có ngày thật (fail-closed).
_EPOCH_MIN = datetime.min.replace(tzinfo=UTC)


def trust_rank(provenance: Provenance) -> int:
    """Thứ hạng độ tin của một provenance (SAI-025)."""

    return _TRUST_RANK[provenance]


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.combine(date.fromisoformat(value), datetime.min.time())
        except ValueError:
            return None


def _parse_utc(value: str) -> datetime | None:
    """Parse ISO rồi chuẩn hoá về UTC-aware để so sánh NHẤT QUÁN — tránh (a) bẫy
    so-chuỗi (``"2026-9-1" > "2026-10-01"``) và (b) trộn naive/aware gây lỗi khi
    mốc có offset múi giờ. Không parse được → ``None``."""

    dt = _parse_iso(value)
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


class KnowledgeBase:
    """Kho kiến thức có provenance. ``answer()`` tổng hợp TRUNG THỰC mức thử của
    một app/version cụ thể — chỉ chứng nhận NaMiOS nâng được mức thử."""

    def __init__(self) -> None:
        self._entries: list[KbEntry] = []

    def add(self, entry: KbEntry) -> None:
        self._entries.append(entry)

    def _match(self, app_id: str, app_version: str) -> list[KbEntry]:
        """Các mẩu kiến thức khớp CHÍNH XÁC (app_id, version) sau chuẩn hoá.
        Version khác = không khớp (không suy sang version khác)."""

        a, v = _norm(app_id), _norm(app_version)
        return [e for e in self._entries if _norm(e.app_id) == a and _norm(e.app_version) == v]

    def _is_stale(self, entry: KbEntry, now: str | None) -> bool:
        """Đánh dấu cũ khi BIẾT CHẮC đã quá ``valid_until`` (tất định). Không
        biết ``now`` hoặc không khai hạn → không tự suy là cũ."""

        if not entry.valid_until or not now:
            return False
        vu, nw = _parse_utc(entry.valid_until), _parse_utc(now)
        return vu is not None and nw is not None and nw > vu

    def answer(self, app_id: str, app_version: str, *, now: str | None = None) -> KbAnswer:
        """Trả ``KbAnswer`` cho (app, version) CỤ THỂ.

        Quy tắc trung thực:
        - Mức thử (``tested_level``) CHỈ lấy từ chứng nhận NaMiOS cho ĐÚNG
          version; chứng nhận mới nhất (theo ``as_of``) thắng — một FAILED mới
          đè một VERIFIED cũ (hồi quy trung thực).
        - Không có chứng nhận → ``UNTESTED`` = "chưa kiểm", DÙ có ghi nhận cộng
          đồng/AI tích cực (lời đồn/AI KHÔNG nâng mức thử).
        - ``install_guidance_allowed`` chỉ True khi có chứng nhận (không FAILED)
          hoặc tài liệu chính thức — KHÔNG để cộng đồng/AI một mình cho phép cài.
        """

        matched = self._match(app_id, app_version)

        # Chứng nhận NaMiOS cho đúng version (chỉ mức thử hợp lệ). Chọn MỚI NHẤT
        # theo NGÀY THẬT (parse + UTC; ngày hỏng → coi cũ nhất, KHÔNG được đè
        # chứng nhận có ngày thật); cùng mốc → ưu tiên mức BẢO THỦ hơn (FAILED
        # đè VERIFIED) để không over-claim (fail-closed, SAI-025).
        cert_entries = [
            e
            for e in matched
            if e.provenance == Provenance.NAMIOS_CERT and e.tested_level in _CERT_LEVELS
        ]
        governing_cert = max(
            cert_entries,
            key=lambda e: (_parse_utc(e.as_of) or _EPOCH_MIN, -_LEVEL_SAFETY[e.tested_level]),
            default=None,
        )

        governing: KbEntry | None
        if governing_cert is not None:
            level = governing_cert.tested_level
            governing = governing_cert
            key = {
                TestedLevel.VERIFIED: "sai.kb.verified",
                TestedLevel.PARTIAL: "sai.kb.partial",
                TestedLevel.FAILED: "sai.kb.failed",
            }[level]
            # Chỉ dẫn cài khi chứng nhận cho biết chạy được (không FAILED).
            install_ok = level in (TestedLevel.VERIFIED, TestedLevel.PARTIAL)
        else:
            level = TestedLevel.UNTESTED
            # Không chứng nhận → chọn nguồn THÔNG TIN đáng tin nhất để diễn giải,
            # nhưng mức thử vẫn UNTESTED ("chưa kiểm").
            governing = max(matched, key=lambda e: trust_rank(e.provenance), default=None)
            if governing is None:
                key = "sai.kb.untested"
            elif governing.provenance == Provenance.OFFICIAL_DOC:
                key = "sai.kb.untested_doc"
            elif governing.provenance == Provenance.COMMUNITY_UNVERIFIED:
                key = "sai.kb.untested_community"
            else:  # AI_INFERENCE
                key = "sai.kb.untested_ai"
            # Chỉ tài liệu chính thức mới đủ căn cứ cho chỉ dẫn cài; cộng đồng/AI
            # một mình KHÔNG được (SAI-025: không dùng lời đồn để cài driver).
            install_ok = governing is not None and governing.provenance == Provenance.OFFICIAL_DOC

        as_of = governing.as_of if governing is not None else None
        confidence = governing.confidence if governing is not None else 0.0
        provenance = governing.provenance if governing is not None else None
        stale = self._is_stale(governing, now) if governing is not None else False

        answer_vi = t(key, lang=Lang.VI, app=app_id, version=app_version, as_of=as_of or "")
        if stale:
            answer_vi += t("sai.kb.stale_suffix", lang=Lang.VI)

        return KbAnswer(
            app_id=app_id,
            app_version=app_version,
            tested_level=level,
            provenance=provenance,
            as_of=as_of,
            confidence=confidence,
            stale=stale,
            install_guidance_allowed=install_ok,
            answer_vi=answer_vi,
            sources=tuple(matched),
        )
