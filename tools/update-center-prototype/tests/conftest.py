# -*- coding: utf-8 -*-
"""Cho pytest thấy module prototype (thư mục cha) khi chạy từ bất kỳ đâu."""
import os
import sys

_PROTO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROTO_DIR not in sys.path:
    sys.path.insert(0, _PROTO_DIR)
