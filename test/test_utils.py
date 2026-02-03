from utils import get_env_flags


def test_get_env_flags(default_env):
    """Test retrieval of environment flags"""
    flags = get_env_flags()
    assert flags["DISABLE_REMOTE"] is False
    assert flags["DISABLE_LOCAL"] is False
    assert flags["DISABLE_DISPLAY"] is False
    assert flags["TESTING"] is True
