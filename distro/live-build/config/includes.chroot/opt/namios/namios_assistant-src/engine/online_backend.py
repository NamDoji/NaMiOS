"""Backend TRỰC TUYẾN (online LLM) — TUỲ CHỌN, chỉ gọi khi người dùng/operator
đã tự cấu hình đủ ``api_key``/``model``/``base_url`` (xem ``namios_assistant.
config``). KHÔNG BAO GIỜ tự đoán một nhà cung cấp mặc định, KHÔNG BAO GIỜ
giả vờ gọi được khi thiếu cấu hình — ``AssistantEngine`` luôn có đường lùi về
``OfflineKbBackend`` khi backend này không cấu hình hoặc gọi lỗi.

Chỉ dùng thư viện chuẩn (``urllib``) — KHÔNG thêm phụ thuộc pip mới cho một
lệnh gọi HTTP JSON đơn giản. Giao thức giả định tương thích kiểu "OpenAI chat
completions" (``POST {base_url}/chat/completions``) vì đây là hình dạng phổ
biến nhất cho cổng/API-gateway tương thích nhiều nhà cung cấp; operator trỏ
``base_url`` tới bất kỳ dịch vụ nào implement đúng hình dạng này.

AN TOÀN: đây là MỘT lệnh gọi HTTPS lấy dữ liệu JSON do chính operator cấu
hình đích đến (``base_url`` không phải do input người dùng/trang web suy ra)
— không phải ``curl|bash``, không ``eval``, không thực thi nội dung trả về;
phản hồi CHỈ được đọc như văn bản (``choices[0].message.content``) để hiển
thị, không bao giờ được thực thi."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from namios_assistant.config import AssistantConfig

__all__ = ["OnlineBackendError", "OnlineLlmBackend"]

#: Chặn đọc phản hồi vô hạn (phòng server trả về một luồng khổng lồ/kẹt) —
#: 2 MB đủ rộng cho một câu trả lời chat text, không hợp lý để lớn hơn nhiều.
_MAX_RESPONSE_BYTES = 2_000_000

_DEFAULT_SYSTEM_PROMPT_VI = (
    "Bạn là NaMi Assistant, một trợ lý kỹ thuật nói tiếng Việt (có thể trả "
    "lời tiếng Anh khi được hỏi bằng tiếng Anh) cho hệ điều hành NaMi (Debian "
    "+ KDE Plasma). Người dùng dán một thông báo lỗi hoặc văn bản trích từ ảnh "
    "chụp màn hình. Trả lời ngắn gọn: (1) nguyên nhân có khả năng nhất, (2) các "
    "bước sửa theo thứ tự, (3) cách hoàn tác nếu bước sửa có rủi ro. KHÔNG bịa "
    "tên lệnh/đường dẫn file nếu không chắc — nói rõ khi không chắc thay vì "
    "đoán liều."
)


@dataclass
class OnlineBackendError(Exception):
    """Backend online không trả lời được — lý do con người đọc được, ĐÃ qua
    xử lý để không rò rỉ bí mật (xem caller ``AssistantEngine`` dùng
    ``namios_security.redact_text`` trước khi hiển thị/ghi log ``reason``)."""

    reason: str

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return self.reason


class OnlineLlmBackend:
    """Gọi một API chat-completions tương thích OpenAI, theo cấu hình
    ``AssistantConfig`` do caller truyền vào (KHÔNG tự đọc config/env lần
    thứ hai ở đây — ``namios_assistant.config.load_config`` là nguồn duy
    nhất, giữ việc đọc cấu hình tập trung một chỗ)."""

    def __init__(self, config: AssistantConfig) -> None:
        self._config = config

    @property
    def is_configured(self) -> bool:
        """``True`` CHỈ KHI cả ba (``api_key``, ``model``, ``base_url``) đều
        có giá trị — thiếu BẤT KỲ cái nào cũng coi là "chưa cấu hình", không
        đoán giá trị mặc định thay người dùng (tránh gọi nhầm nhà cung cấp)."""

        return bool(self._config.api_key) and bool(self._config.model) and bool(
            self._config.base_url
        )

    def ask(self, prompt: str, *, subsystem: str | None, system_prompt: str | None = None) -> str:
        """Gọi API; trả nội dung trả lời (chuỗi). Raise ``OnlineBackendError``
        cho MỌI tình huống không lấy được câu trả lời hợp lệ (thiếu cấu
        hình/lỗi mạng/timeout/phản hồi sai định dạng) — caller (``AssistantEngine``)
        bắt lỗi này để rơi về offline KB, KHÔNG để lộ ra UI như một crash."""

        if not self.is_configured:
            raise OnlineBackendError(
                "Chưa cấu hình đủ api_key/model/base_url cho backend AI trực tuyến."
            )

        assert self._config.api_key is not None
        assert self._config.model is not None
        assert self._config.base_url is not None

        effective_system_prompt = system_prompt or _DEFAULT_SYSTEM_PROMPT_VI
        user_content = prompt
        if subsystem:
            user_content = f"[subsystem đoán được: {subsystem}]\n{prompt}"

        payload = {
            "model": self._config.model,
            "messages": [
                {"role": "system", "content": effective_system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.2,
        }

        url = self._config.base_url.rstrip("/") + "/chat/completions"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._config.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(
                request, timeout=self._config.request_timeout_seconds
            ) as response:
                raw = response.read(_MAX_RESPONSE_BYTES)
        except urllib.error.HTTPError as exc:
            raise OnlineBackendError(
                f"API trực tuyến trả mã lỗi HTTP {exc.code}."
            ) from exc
        except urllib.error.URLError as exc:
            raise OnlineBackendError(
                f"Không gọi được API trực tuyến (mạng/DNS/timeout): {exc.reason}."
            ) from exc
        except TimeoutError as exc:
            raise OnlineBackendError("API trực tuyến không phản hồi kịp thời (timeout).") from exc

        try:
            parsed = json.loads(raw)
            content = parsed["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise OnlineBackendError(
                "Phản hồi từ API trực tuyến không đúng định dạng mong đợi "
                "(choices[0].message.content)."
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise OnlineBackendError("API trực tuyến trả nội dung rỗng.")

        return content.strip()
