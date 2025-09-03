"""Shared pytest fixtures for the drum machine test suite."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        yield Path(tmpfile.name)
        # Clean up
        try:
            os.unlink(tmpfile.name)
        except FileNotFoundError:
            pass


@pytest.fixture
def mock_config():
    """Mock configuration object."""
    config = Mock()
    config.get_sound_dir.return_value = "/fake/sound/dir"
    config.get_preset_dir.return_value = "/fake/preset/dir"
    config.get_volume.return_value = 0.8
    config.get_tempo.return_value = 120
    return config


@pytest.fixture
def mock_pygame():
    """Mock pygame module."""
    with patch('pygame.mixer') as mock_mixer:
        mock_mixer.init.return_value = None
        mock_mixer.quit.return_value = None
        mock_mixer.Sound.return_value = Mock()
        yield mock_mixer


@pytest.fixture
def mock_mido():
    """Mock mido module for MIDI functionality."""
    with patch('mido.MidiFile') as mock_midi:
        mock_file = Mock()
        mock_file.tracks = []
        mock_file.ticks_per_beat = 480
        mock_midi.return_value = mock_file
        yield mock_midi


@pytest.fixture
def sample_sound_files(temp_dir):
    """Create sample sound files for testing."""
    sound_files = []
    sound_names = ['kick.wav', 'snare.wav', 'hihat.wav', 'crash.wav']
    
    for name in sound_names:
        sound_file = temp_dir / name
        sound_file.write_bytes(b'fake_wav_data')  # Minimal fake WAV content
        sound_files.append(sound_file)
    
    return sound_files


@pytest.fixture
def sample_preset_file(temp_dir):
    """Create a sample preset file for testing."""
    preset_content = """<?xml version="1.0" encoding="UTF-8"?>
<preset>
    <name>Test Preset</name>
    <tempo>120</tempo>
    <patterns>
        <pattern name="kick" steps="1000100010001000"/>
        <pattern name="snare" steps="0000100000001000"/>
        <pattern name="hihat" steps="1010101010101010"/>
    </patterns>
</preset>"""
    
    preset_file = temp_dir / "test_preset.xml"
    preset_file.write_text(preset_content)
    return preset_file


@pytest.fixture
def mock_gtk():
    """Mock GTK components."""
    with patch('gi.repository.Gtk') as mock_gtk_module:
        # Mock common GTK widgets
        mock_window = Mock()
        mock_button = Mock()
        mock_grid = Mock()
        mock_label = Mock()
        
        mock_gtk_module.Window.return_value = mock_window
        mock_gtk_module.Button.return_value = mock_button
        mock_gtk_module.Grid.return_value = mock_grid
        mock_gtk_module.Label.return_value = mock_label
        
        yield mock_gtk_module


@pytest.fixture
def mock_gio():
    """Mock GIO components."""
    with patch('gi.repository.Gio') as mock_gio_module:
        mock_application = Mock()
        mock_gio_module.Application.return_value = mock_application
        yield mock_gio_module


@pytest.fixture
def isolate_file_system():
    """Isolate tests from the real file system."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up a clean test environment for each test."""
    # Set test-specific environment variables
    monkeypatch.setenv('TESTING', '1')
    
    # Mock file paths to prevent tests from accessing real system files
    test_data_dir = Path(__file__).parent / 'test_data'
    monkeypatch.setenv('TEST_DATA_DIR', str(test_data_dir))


@pytest.fixture
def drum_pattern_data():
    """Sample drum pattern data for testing."""
    return {
        'kick': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'hihat': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        'crash': [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }


@pytest.fixture
def mock_file_dialog():
    """Mock file dialog responses."""
    with patch('gi.repository.Gtk.FileChooserDialog') as mock_dialog:
        mock_instance = Mock()
        mock_dialog.return_value = mock_instance
        mock_instance.run.return_value = 1  # GTK_RESPONSE_OK
        mock_instance.get_filename.return_value = '/fake/file/path.mid'
        yield mock_instance


@pytest.fixture
def capturing_logger():
    """Capture log messages for testing."""
    import logging
    from io import StringIO
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logger = logging.getLogger('drum_machine')
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    yield log_capture
    
    logger.removeHandler(handler)