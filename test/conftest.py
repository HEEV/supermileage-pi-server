import pytest, os

@pytest.fixture
def env():
    """fixture providing basic environment for testing"""
    os.environ['TESTING'] = 'True'
    os.environ['CONFIG_FILE_PATH'] = './test/testfiles/car_config.json'
    os.environ['DB_HOST'] = 'localhost'
    os.environ['DB_USER'] = 'user'
    os.environ['DB_PASSWORD'] = 'password'
    os.environ['DB_PORT'] = '27017'
    os.environ['DB'] = 'database'