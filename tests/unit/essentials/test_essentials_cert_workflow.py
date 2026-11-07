"""APP11-021/028 — chứng nhận workflow per-chức-năng + kiểm version app Wine.
Bám E11-07 (app Wine của vendor tự đổi phiên bản → recipe chuyển needs_retest)
và APP11-028 nghiệm thu (YouTube xem video đạt không suy ra DRM đạt; WhatsApp
chat đạt không suy ra call đạt)."""

from __future__ import annotations

from namios_essentials import (
    AppCertProfile,
    AppFunction,
    advance_function,
    can_publish_function,
    function_state,
    is_function_supported,
    on_binary_hash_change,
    publish_function,
    with_needs_retest,
)
from namios_odc import CertState, EvidenceKind

CS = CertState
EK = EvidenceKind
AF = AppFunction


def test_watch_video_published_does_not_imply_drm_ok() -> None:
    # APP11-028 nghiệm thu đúng nguyên văn: "YouTube xem video đạt không suy
    # ra DRM mọi nội dung đạt".
    profile = AppCertProfile(
        app_id="youtube.web", version="1", functions={AF.WATCH_VIDEO: CS.PUBLISHED}
    )
    assert is_function_supported(profile, AF.WATCH_VIDEO) is True
    assert is_function_supported(profile, AF.DRM_PLAYBACK) is False
    assert function_state(profile, AF.DRM_PLAYBACK) is None  # chưa khai, không suy


def test_chat_published_does_not_imply_call_ok() -> None:
    # "WhatsApp chat đạt không suy ra call đạt."
    profile = AppCertProfile(app_id="whatsapp.web", version="1", functions={AF.CHAT: CS.PUBLISHED})
    assert is_function_supported(profile, AF.CHAT) is True
    assert is_function_supported(profile, AF.CALL_VIDEO) is False


def test_with_needs_retest_only_touches_listed_functions() -> None:
    profile = AppCertProfile(
        app_id="a",
        version="1",
        functions={AF.OPEN: CS.PUBLISHED, AF.CHAT: CS.PUBLISHED, AF.CALL_VIDEO: CS.PUBLISHED},
    )
    out = with_needs_retest(profile, [AF.CALL_VIDEO])
    assert function_state(out, AF.CALL_VIDEO) is CS.NEEDS_RETEST
    assert function_state(out, AF.CHAT) is CS.PUBLISHED  # không đụng chức năng khác
    assert function_state(profile, AF.CALL_VIDEO) is CS.PUBLISHED  # bản gốc bất biến


# --------------------------------------------------------------------------- #
# Tái dùng namios_odc.advance/can_publish/publish (APP11-028)                  #
# --------------------------------------------------------------------------- #


def test_advance_function_follows_odc_state_machine() -> None:
    profile = AppCertProfile(app_id="a", version="1")
    profile = advance_function(profile, AF.LOGIN, EK.LAB_TEST)
    assert function_state(profile, AF.LOGIN) is CS.LAB_TESTED
    profile = advance_function(profile, AF.LOGIN, EK.PILOT_SIGNOFF)
    assert function_state(profile, AF.LOGIN) is CS.PILOT_VERIFIED
    assert can_publish_function(profile, AF.LOGIN) is True
    profile = publish_function(profile, AF.LOGIN)
    assert function_state(profile, AF.LOGIN) is CS.PUBLISHED


def test_community_and_ai_evidence_never_promote_app_function() -> None:
    profile = AppCertProfile(app_id="a", version="1")
    for _ in range(20):
        profile = advance_function(profile, AF.UPLOAD, EK.COMMUNITY_REPORT)
        profile = advance_function(profile, AF.UPLOAD, EK.AI_GUESS)
    assert function_state(profile, AF.UPLOAD) is CS.REPORTED
    assert is_function_supported(profile, AF.UPLOAD) is False


def test_cannot_skip_to_published_without_pilot_signoff() -> None:
    profile = AppCertProfile(app_id="a", version="1", functions={AF.PRINT_EXPORT: CS.LAB_TESTED})
    assert can_publish_function(profile, AF.PRINT_EXPORT) is False
    published = publish_function(profile, AF.PRINT_EXPORT)
    assert function_state(published, AF.PRINT_EXPORT) is CS.LAB_TESTED  # giữ nguyên


# --------------------------------------------------------------------------- #
# E11-07 — Wine app vendor tự đổi phiên bản                                    #
# --------------------------------------------------------------------------- #


def test_e11_07_hash_change_demotes_published_functions_to_needs_retest() -> None:
    profile = AppCertProfile(
        app_id="zalo.pc",
        version="24.1",
        functions={AF.OPEN: CS.PUBLISHED, AF.CHAT: CS.PUBLISHED, AF.LOGIN: CS.PUBLISHED},
        binary_hash="hash-v24.1",
    )
    updated = on_binary_hash_change(profile, "hash-v24.2-vendor-silent")

    for func in (AF.OPEN, AF.CHAT, AF.LOGIN):
        assert function_state(updated, func) is CS.NEEDS_RETEST
        assert is_function_supported(updated, func) is False  # không tuyên bố tiếp tục hỗ trợ

    assert updated.binary_hash == "hash-v24.2-vendor-silent"
    assert updated.last_known_good_hash == "hash-v24.1"  # giữ đường quay về bản trước


def test_unchanged_hash_leaves_profile_untouched() -> None:
    profile = AppCertProfile(
        app_id="zalo.pc",
        version="24.1",
        functions={AF.OPEN: CS.PUBLISHED},
        binary_hash="hash-v24.1",
    )
    same = on_binary_hash_change(profile, "hash-v24.1")
    assert same is profile
    assert function_state(same, AF.OPEN) is CS.PUBLISHED


def test_hash_change_invalidates_every_tested_state_but_not_reported() -> None:
    # E11-07: binary đổi → MỌI trạng thái đã-KIỂM gắn với bản cũ (published,
    # pilot_verified, lab_tested) phải NEEDS_RETEST — bằng chứng kiểm cho bản
    # cũ không nói gì về bản mới, và nếu giữ lại lab_tested/pilot_verified thì
    # một PILOT_SIGNOFF/publish có thể "rửa" chứng nhận bản cũ sang bản mới.
    # REPORTED (cộng đồng báo, CHƯA kiểm) không phải chứng nhận nên giữ nguyên.
    profile = AppCertProfile(
        app_id="zalo.pc",
        version="24.1",
        functions={
            AF.OPEN: CS.PUBLISHED,
            AF.PRINT_EXPORT: CS.LAB_TESTED,
            AF.LOGIN: CS.PILOT_VERIFIED,
            AF.UPLOAD: CS.REPORTED,
        },
        binary_hash="h1",
    )
    updated = on_binary_hash_change(profile, "h2")
    assert function_state(updated, AF.OPEN) is CS.NEEDS_RETEST
    assert function_state(updated, AF.PRINT_EXPORT) is CS.NEEDS_RETEST
    assert function_state(updated, AF.LOGIN) is CS.NEEDS_RETEST
    assert function_state(updated, AF.UPLOAD) is CS.REPORTED  # chưa kiểm → giữ nguyên
