import os
import struct
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

import main


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment variables and global state before each test"""
    # Save original values
    original_values = {}
    for var in ["DISABLE_REMOTE", "DISABLE_LOCAL", "DISABLE_DISPLAY", "TESTING"]:
        original_values[var] = os.environ.get(var)

    # Clear only the DISABLE_* env vars before test
    for var in ["DISABLE_REMOTE", "DISABLE_LOCAL", "DISABLE_DISPLAY"]:
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
    with (
        patch("main.web.AppRunner") as mock_runner,
        patch("main.web.TCPSite") as mock_site,
        patch("main.SmSerial") as mock_serial,
        patch("main.open", mock_open()) as mock_file,
    ):
        # Setup serial mock
        mock_ser = MagicMock()
        mock_ser.read_response.side_effect = [
            struct.pack(
                "<ffffBBBBBH",
                25.3,  # speed
                5.2,  # airspeed
                78.2,  # engineTemp
                65.4,  # radTemp
                0,
                1,
                0,
                1,
                0,  # digital channels
                100,
            ),  # analog channel
            "",
            KeyboardInterrupt(),
        ]
        mock_serial.return_value = mock_ser

        # Setup web server mocks
        mock_runner.return_value = AsyncMock()
        mock_site.return_value = AsyncMock()

        yield {
            "serial": mock_ser,
            "runner": mock_runner,
            "site": mock_site,
            "file_mock": mock_file,
        }


# Test DISABLE_DISPLAY flag
@pytest.mark.asyncio
async def test_disable_display_blocks_socket_emit(mock_dependencies, default_env):
    """DISABLE_DISPLAY should prevent socket emissions"""
    os.environ["DISABLE_DISPLAY"] = "True"

    with patch("main.localDisplaySio.emit") as mock_emit:
        try:
            await main.main()
        except KeyboardInterrupt:
            pass

        mock_emit.assert_not_called()


@pytest.mark.asyncio
async def test_enable_display_allows_socket_emit(mock_dependencies, default_env):
    """Socket emissions should work when DISABLE_DISPLAY is False"""
    with patch("main.localDisplaySio.emit") as mock_emit:
        try:
            await main.main()
        except KeyboardInterrupt:
            pass

        mock_emit.assert_called()


# Test DISABLE_REMOTE flag
# TODO: #22 Write tests for this when RemoteTransmitter is implemented


# Test DISABLE_LOCAL flag
@pytest.mark.asyncio
async def test_disable_local_blocks_csv_write(mock_dependencies, default_env):
    """DISABLE_LOCAL should prevent CSV file writes in the loop"""
    os.environ["DISABLE_LOCAL"] = "True"

    try:
        await main.main()
    except KeyboardInterrupt:
        pass

    # Count how many times we opened file in append mode ('a')
    mock_file = mock_dependencies["file_mock"]
    append_calls = [
        call
        for call in mock_file.call_args_list
        if len(call[0]) > 1 and call[0][1] == "a"
    ]

    # Should not have any append operations when DISABLE_LOCAL is True
    assert len(append_calls) == 0


@pytest.mark.asyncio
async def test_enable_local_allows_csv_write(mock_dependencies, default_env):
    """CSV writing should work when DISABLE_LOCAL is False"""
    with patch("main.LocalTransmitter._write_to_csv") as mock_write:
        try:
            await main.main()
        except KeyboardInterrupt:
            pass

        # Should have called _write_to_csv at least once when DISABLE_LOCAL is False
        assert mock_write.call_count > 0
