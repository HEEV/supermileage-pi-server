import struct
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
import os
import main


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment variables and global state before each test"""
    # Save original values
    original_values = {}
    for var in ['DISABLE_REMOTE', 'DISABLE_LOCAL', 'DISABLE_DISPLAY', 'TESTING']:
        original_values[var] = os.environ.get(var)
    
    # Clear only the DISABLE_* env vars before test
    for var in ['DISABLE_REMOTE', 'DISABLE_LOCAL', 'DISABLE_DISPLAY']:
        os.environ.pop(var, None)
    
    # Reset global state BEFORE test
    main.distance_traveled = 0
    main.last_update = 0
    
    yield
    
    # Reset global state AFTER test (critical for test isolation)
    main.distance_traveled = 0
    main.last_update = 0
    
    # Restore original values after test
    for var, value in original_values.items():
        if value is None:
            os.environ.pop(var, None)
        else:
            os.environ[var] = value

@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies for main loop tests"""
    with patch('main.web.AppRunner') as mock_runner, \
         patch('main.web.TCPSite') as mock_site, \
         patch('main.asyncpg.connect') as mock_db, \
         patch('main.create_serial_conn') as mock_serial, \
         patch('builtins.open', mock_open()):
        
        # Setup serial mock
        mock_ser = MagicMock()
        mock_ser.read_response.side_effect = [
            struct.pack('<ffffBBBBBH', 
                                25.3,  # speed
                                5.2,   # airspeed
                                78.2,  # engineTemp
                                65.4,  # radTemp
                                0, 1, 0, 1, 0,  # digital channels
                                100),  # analog channel
            "",
            KeyboardInterrupt() 
        ]
        mock_serial.return_value = mock_ser
        
        # Setup database mock
        mock_conn = AsyncMock()
        mock_db.return_value = mock_conn
        
        # Setup web server mocks
        mock_runner.return_value = AsyncMock()
        mock_site.return_value = AsyncMock()
        
        yield {
            'serial': mock_ser,
            'db': mock_conn,
            'runner': mock_runner,
            'site': mock_site
        }


# Test get_env_flags function
def test_get_env_flags_all_enabled():
    """All flags should be True when set"""
    os.environ['DISABLE_REMOTE'] = 'True'
    os.environ['DISABLE_LOCAL'] = 'True'
    os.environ['DISABLE_DISPLAY'] = 'True'
    os.environ['TESTING'] = 'True'
    
    flags = main.get_env_flags()
    assert flags['DISABLE_REMOTE']
    assert flags['DISABLE_LOCAL']
    assert flags['DISABLE_DISPLAY']
    assert flags['TESTING']


# Test DISABLE_DISPLAY flag
@pytest.mark.asyncio
async def test_disable_display_blocks_socket_emit(mock_dependencies):
    """DISABLE_DISPLAY should prevent socket emissions"""
    os.environ['DISABLE_DISPLAY'] = 'True'
    os.environ['TESTING'] = 'True'
    
    with patch('main.localDisplaySio.emit') as mock_emit:
        try:
            await main.main()
        except KeyboardInterrupt:
            pass
        
        mock_emit.assert_not_called()


@pytest.mark.asyncio
async def test_enable_display_allows_socket_emit(mock_dependencies):
    """Socket emissions should work when DISABLE_DISPLAY is False"""
    os.environ['TESTING'] = 'True'
    
    with patch('main.localDisplaySio.emit') as mock_emit:
        try:
            await main.main()
        except KeyboardInterrupt:
            pass
        
        mock_emit.assert_called()


# Test DISABLE_REMOTE flag
@pytest.mark.asyncio
async def test_disable_remote_blocks_database(mock_dependencies):
    """DISABLE_REMOTE should prevent database insertions"""
    os.environ['DISABLE_REMOTE'] = 'True'
    os.environ['TESTING'] = 'True'
    
    # Provide enough data points to trigger DB insert (20+)
    mock_dependencies['serial'].read_response.side_effect = (
        ["12.5,25.3,1543.7,1,0,1,78.2,65.4", ""] * 25 + [KeyboardInterrupt()]
    )
    
    try:
        await main.main()
    except KeyboardInterrupt:
        pass
    
    mock_dependencies['db'].execute.assert_not_called()

@pytest.mark.asyncio
async def test_enable_remote_allows_database(mock_dependencies):
    """Database insertions should work when DISABLE_REMOTE is False"""
    os.environ['TESTING'] = 'True'
    
    # Provide enough data points to trigger DB insert (20+)
    mock_dependencies['serial'].read_response.side_effect = (
        [struct.pack('<ffffBBBBBH', 
                                25.3,  # speed
                                5.2,   # airspeed
                                78.2,  # engineTemp
                                65.4,  # radTemp
                                0, 1, 0, 1, 0,  # digital channels
                                100),  # analog channel
        ""] * 25 + [KeyboardInterrupt()]
    )
    
    try:
        await main.main()
    except KeyboardInterrupt:
        pass
    
    mock_dependencies['db'].execute.assert_called()

# Test DISABLE_LOCAL flag

@pytest.mark.asyncio
async def test_disable_local_blocks_csv_write(mock_dependencies):
    """DISABLE_LOCAL should prevent CSV file writes in the loop"""
    os.environ['DISABLE_LOCAL'] = 'True'
    os.environ['TESTING'] = 'True'
    
    mock_file = mock_open()
    with patch('builtins.open', mock_file):
        try:
            await main.main()
        except KeyboardInterrupt:
            pass
        
        # Count how many times we opened file in append mode ('a')
        append_calls = [call for call in mock_file.call_args_list 
                       if len(call[0]) > 1 and call[0][1] == 'a']
        
        # Should not have any append operations when DISABLE_LOCAL is True
        assert len(append_calls) == 0


@pytest.mark.asyncio
async def test_enable_local_allows_csv_write(mock_dependencies):
    """CSV writing should work when DISABLE_LOCAL is False"""
    os.environ['TESTING'] = 'True'
    
    mock_file = mock_open()
    with patch('builtins.open', mock_file):
        try:
            await main.main()
        except KeyboardInterrupt:
            pass
        
        # Count how many times we opened file in append mode ('a')
        append_calls = [call for call in mock_file.call_args_list 
                       if len(call[0]) > 1 and call[0][1] == 'a']
        
        # Should have at least one append operation when DISABLE_LOCAL is False
        assert len(append_calls) > 0