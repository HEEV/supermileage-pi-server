from os import getenv


def get_env_flags():
    """retrieve and return environment flags"""
    return {
        "DISABLE_REMOTE": getenv("DISABLE_REMOTE", "False") == "True",
        "DISABLE_LOCAL": getenv("DISABLE_LOCAL", "False") == "True",
        "DISABLE_DISPLAY": getenv("DISABLE_DISPLAY", "False") == "True",
        "TESTING": getenv("TESTING", "False") == "True",
    }
