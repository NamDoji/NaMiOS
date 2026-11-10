# -*- coding: utf-8 -*-
"""Cho pytest thấy (a) các package ``namios_*`` thật dưới ``src/`` và (b) module
prototype ``tools/update-center-prototype/`` (fault_inject/update_service/
boot_health/staged_deploy/update_contract/sign_test_repo) khi chạy bộ T09
(Phụ lục 09) từ BẤT KỲ đâu — không chỉ khi rootdir pytest tự nạp
``pyproject.toml`` (``[tool.pytest.ini_options] pythonpath=["src", "."]``).

Hai đường path này được cộng thêm một cách TƯỜNG MINH ở đây (không phụ thuộc
caller có đứng ở repo root hay gọi ``python3 -m pytest tools/pl09-tests`` hay
không) để bộ test T09 REUSE THẬT các engine đã có — KHÔNG fork lại logic.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_HERE))  # tools/pl09-tests -> tools -> repo root

_SRC_DIR = os.path.join(_REPO_ROOT, "src")
_UPDATE_PROTO_DIR = os.path.join(_REPO_ROOT, "tools", "update-center-prototype")

for _p in (_SRC_DIR, _UPDATE_PROTO_DIR, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
