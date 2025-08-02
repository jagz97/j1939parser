import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from j1939parser.core import stream_vehicle_positions


def test_stream_vehicle_positions_from_file():
    """Test streaming vehicle positions from a log file."""
    # Create a temporary file with CAN log data
    log_content = """(1609459200.000000) can0 18FEF34A [8] 0E 23 6A 93 1E DE 81 34
(1609459201.000000) can0 18FEF34A [8] 0F 24 6B 94 1F DF 82 35
(1609459202.000000) can0 12345678 [8] 01 02 03 04 05 06 07 08
(1609459203.000000) can0 18FEF34A [8] 10 25 6C 95 20 E0 83 36
"""
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as temp_file:
        temp_file.write(log_content)
        temp_file.flush()
        
        try:
            # Mock the follow function to return lines immediately instead of waiting
            with patch('j1939parser.core.follow') as mock_follow:
                mock_follow.return_value = iter(log_content.strip().split('\n'))
                
                generator = stream_vehicle_positions(temp_file.name)
                
                # Get first valid position
                lat1, lon1 = next(generator)
                assert abs(lat1 - 37.3206542) < 1e-6
                assert abs(lon1 - (-121.9073762)) < 1e-6
                
        finally:
            os.unlink(temp_file.name)


def test_stream_vehicle_positions_file_not_found():
    """Test behavior when file doesn't exist - should try CAN interface."""
    non_existent_file = "/path/that/does/not/exist.log"
    
    # Mock can module to be None (not available)
    with patch('j1939parser.core.can', None):
        with pytest.raises(ImportError, match="Live CAN interface requires 'python-can'"):
            generator = stream_vehicle_positions(non_existent_file)
            next(generator)


def test_stream_vehicle_positions_can_interface_success():
    """Test successful CAN interface streaming."""
    # Mock CAN message
    mock_msg = MagicMock()
    mock_msg.arbitration_id = 0x18FEF34A  # PGN 0xFEF3 + source address
    mock_msg.data = bytes([0x0E, 0x23, 0x6A, 0x93, 0x1E, 0xDE, 0x81, 0x34])
    mock_msg.dlc = 8
    
    # Mock CAN bus
    mock_bus = MagicMock()
    mock_bus.recv.side_effect = [mock_msg, None]  # One message, then None to stop
    
    with patch('j1939parser.core.can') as mock_can_module:
        # Mock the Bus constructor completely to avoid socket creation
        mock_can_module.interface.Bus = MagicMock(return_value=mock_bus)
        
        with patch('j1939parser.core.is_raspberry_pi', return_value=True):
            generator = stream_vehicle_positions("can0")
            
            lat, lon = next(generator)
            assert abs(lat - 37.3206542) < 1e-6
            assert abs(lon - (-121.9073762)) < 1e-6


def test_stream_vehicle_positions_can_interface_bus_error():
    """Test CAN interface bus creation error."""
    with patch('j1939parser.core.can') as mock_can_module:
        mock_can_module.interface.Bus = MagicMock(side_effect=Exception("Cannot open CAN interface"))
        
        with pytest.raises(RuntimeError, match="Could not open CAN interface 'can0'"):
            generator = stream_vehicle_positions("can0")
            next(generator)


def test_stream_vehicle_positions_can_wrong_pgn():
    """Test CAN interface with wrong PGN (should be ignored)."""
    # Mock CAN message with wrong PGN
    mock_msg = MagicMock()
    mock_msg.arbitration_id = 0x18F0034A  # Wrong PGN
    mock_msg.data = bytes([0x0E, 0x23, 0x6A, 0x93, 0x1E, 0xDE, 0x81, 0x34])
    mock_msg.dlc = 8
    
    mock_bus = MagicMock()
    mock_bus.recv.side_effect = [mock_msg, None]  # Wrong PGN message, then None
    
    with patch('j1939parser.core.can') as mock_can_module:
        mock_can_module.interface.Bus = MagicMock(return_value=mock_bus)
        
        generator = stream_vehicle_positions("can0")
        
        # Should not yield anything for wrong PGN
        with pytest.raises(StopIteration):
            next(generator)


def test_stream_vehicle_positions_can_wrong_dlc():
    """Test CAN interface with wrong data length (should be ignored)."""
    # Mock CAN message with wrong DLC
    mock_msg = MagicMock()
    mock_msg.arbitration_id = 0x18FEF34A  # Correct PGN
    mock_msg.data = bytes([0x0E, 0x23, 0x6A])  # Only 3 bytes
    mock_msg.dlc = 3
    
    mock_bus = MagicMock()
    mock_bus.recv.side_effect = [mock_msg, None]  # Wrong DLC message, then None
    
    with patch('j1939parser.core.can') as mock_can_module:
        mock_can_module.interface.Bus = MagicMock(return_value=mock_bus)
        
        generator = stream_vehicle_positions("can0")
        
        # Should not yield anything for wrong DLC
        with pytest.raises(StopIteration):
            next(generator)


def test_stream_vehicle_positions_can_none_message():
    """Test CAN interface with None message (should be ignored)."""
    mock_bus = MagicMock()
    mock_bus.recv.side_effect = [None, None]  # None messages
    
    with patch('j1939parser.core.can') as mock_can_module:
        mock_can_module.interface.Bus = MagicMock(return_value=mock_bus)
        
        generator = stream_vehicle_positions("can0")
        
        # Should not yield anything for None messages
        with pytest.raises(StopIteration):
            next(generator)


def test_stream_vehicle_positions_non_raspberry_pi_warning(capsys):
    """Test warning message when not on Raspberry Pi."""
    with patch('j1939parser.core.can') as mock_can_module:
        mock_bus = MagicMock()
        mock_bus.recv.side_effect = [None]  # One None message to stop quickly
        mock_can_module.interface.Bus = MagicMock(return_value=mock_bus)
        
        with patch('j1939parser.core.is_raspberry_pi', return_value=False):
            generator = stream_vehicle_positions("can0")
            
            try:
                next(generator)
            except StopIteration:
                pass
            
            # Check that warning was printed
            captured = capsys.readouterr()
            assert "Warning: Live CAN access is typically supported on Raspberry Pi" in captured.out
