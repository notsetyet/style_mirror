# -*- coding: utf-8 -*-
"""
StyleMirror 测试配置文件

提供共享的 fixtures 和测试配置
"""

import pytest
import os
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================
# 全局 Fixtures
# ============================================

@pytest.fixture(scope="session")
def project_root_path():
    """返回项目根目录路径"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def data_dir(project_root_path):
    """返回数据目录路径"""
    return project_root_path / "data"


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    """每个测试前重置环境变量"""
    # 清除可能影响测试的环境变量
    env_vars = ["OPENAI_API_KEY", "OPENAI_BASE_URL"]
    
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
    
    yield
    
    # 测试后清理
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)


# ============================================
# 测试标记配置
# ============================================

def pytest_configure(config):
    """注册自定义测试标记"""
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试"
    )
    config.addinivalue_line(
        "markers", "api: 需要 API 调用的测试"
    )
