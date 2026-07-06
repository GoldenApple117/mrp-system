"""pytest 配置：确保 backend/ 在 Python 路径中"""
import sys
import os

# 确保 backend/ 目录在路径中，让 tests/ 能正常 import app
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TESTS_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
