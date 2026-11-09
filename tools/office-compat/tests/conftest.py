# -*- coding: utf-8 -*-
"""Cho pytest thấy package ``namioffice_inspect`` (thư mục cha) khi chạy từ
bất kỳ đâu — cùng quy ước với tools/update-center-prototype/tests/conftest.py."""
import os
import sys

_TOOL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TOOL_DIR not in sys.path:
    sys.path.insert(0, _TOOL_DIR)
