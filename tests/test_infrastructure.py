"""Test to validate that the testing infrastructure is working correctly."""

import pytest
from pathlib import Path


def test_pytest_is_working():
    """Basic test to ensure pytest is functioning."""
    assert True


def test_fixtures_are_available(temp_dir, mock_config):
    """Test that custom fixtures are working."""
    assert temp_dir.exists()
    assert temp_dir.is_dir()
    assert hasattr(mock_config, 'get_sound_dir')


def test_markers_are_configured():
    """Test that custom markers are properly configured."""
    # This test should run without warnings about unknown markers
    pass


@pytest.mark.unit
def test_unit_marker():
    """Test with unit marker."""
    assert True


@pytest.mark.integration
def test_integration_marker():
    """Test with integration marker."""
    assert True


@pytest.mark.slow
def test_slow_marker():
    """Test with slow marker."""
    assert True


def test_temp_file_fixture(temp_file):
    """Test the temp_file fixture."""
    assert temp_file.exists()
    
    # Write some content
    temp_file.write_text("test content")
    assert temp_file.read_text() == "test content"


def test_sample_sound_files_fixture(sample_sound_files):
    """Test the sample_sound_files fixture."""
    assert len(sample_sound_files) == 4
    assert all(f.exists() for f in sample_sound_files)
    assert any('kick.wav' in f.name for f in sample_sound_files)


def test_drum_pattern_data_fixture(drum_pattern_data):
    """Test the drum_pattern_data fixture."""
    assert 'kick' in drum_pattern_data
    assert 'snare' in drum_pattern_data
    assert len(drum_pattern_data['kick']) == 16


def test_mock_pygame_fixture(mock_pygame):
    """Test the mock_pygame fixture."""
    assert hasattr(mock_pygame, 'init')
    assert hasattr(mock_pygame, 'Sound')


def test_isolate_file_system_fixture(isolate_file_system):
    """Test the file system isolation fixture."""
    test_file = isolate_file_system / "test_file.txt"
    test_file.write_text("isolated test")
    assert test_file.exists()
    assert test_file.read_text() == "isolated test"