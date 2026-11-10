# -*- coding: utf-8 -*-
"""Cho pytest thấy module prototype (thư mục cha) khi chạy từ bất kỳ đâu.

Theo đúng quy ước đã dùng ở `tools/update-center-prototype/tests/conftest.py`
và `tools/office-compat/tests/conftest.py`: các module của prototype này
(table.py, sources.py, steps.py, pipeline.py, ...) là module FLAT, không nằm
trong một package cài đặt được — nên test cần tự thêm thư mục cha vào
sys.path trước khi import.
"""
import os
import sys

_PROTO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROTO_DIR not in sys.path:
    sys.path.insert(0, _PROTO_DIR)
