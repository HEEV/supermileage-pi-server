from utils import get_env_flags


def test_get_env_flags(default_env):
    """Test retrieval of environment flags"""
    flags = get_env_flags()
    assert flags["DISABLE_REMOTE"] is True # TODO: #22 Change to False when RemoteTrasmitter is implemented
    assert flags["DISABLE_LOCAL"] is False
    assert flags["DISABLE_DISPLAY"] is False
    assert flags["TESTING"] is True
