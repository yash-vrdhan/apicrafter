"""Tests for storage functionality."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from apicrafter.storage import Environment, HistoryEntry, RequestData, StorageManager


@pytest.fixture
def temp_storage():
    """Create a temporary storage manager for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield StorageManager(Path(temp_dir))


def test_storage_initialization(temp_storage):
    """Test storage manager initialization."""
    assert temp_storage.config_dir.exists()
    assert temp_storage.collections_file.exists()
    assert temp_storage.environments_file.exists()
    assert temp_storage.history_file.exists()


def test_save_and_load_request(temp_storage):
    """Test saving and loading requests."""
    request_data = RequestData(
        method="POST",
        url="https://api.example.com/users",
        headers={"Content-Type": "application/json"},
        json_data={"name": "Test User"},
    )

    # Save request
    temp_storage.save_request("create-user", request_data, "test-collection")

    # Load request
    loaded_request = temp_storage.load_request("create-user", "test-collection")

    assert loaded_request is not None
    assert loaded_request.method == "POST"
    assert loaded_request.url == "https://api.example.com/users"
    assert loaded_request.headers == {"Content-Type": "application/json"}
    assert loaded_request.json_data == {"name": "Test User"}


def test_save_and_load_environment(temp_storage):
    """Test saving and loading environments."""
    env = Environment(
        name="test",
        variables={"BASE_URL": "https://test.api.com", "API_KEY": "test-key-123"},
    )

    # Save environment
    temp_storage.save_environment(env)

    # Load environment
    loaded_env = temp_storage.load_environment("test")

    assert loaded_env is not None
    assert loaded_env.name == "test"
    assert loaded_env.variables["BASE_URL"] == "https://test.api.com"
    assert loaded_env.variables["API_KEY"] == "test-key-123"


def test_history_tracking(temp_storage):
    """Test history tracking functionality."""
    entry = HistoryEntry(
        timestamp=datetime.now(),
        method="GET",
        url="https://api.example.com/users",
        status_code=200,
        response_time=0.5,
        success=True,
    )

    # Add to history
    temp_storage.add_to_history(entry)

    # Load history
    history = temp_storage.load_history(10)

    assert len(history) == 1
    assert history[0].method == "GET"
    assert history[0].url == "https://api.example.com/users"
    assert history[0].status_code == 200
    assert history[0].success is True


def test_variable_resolution(temp_storage):
    """Test environment variable resolution."""
    # Create test environment
    env = Environment(
        name="test",
        variables={
            "BASE_URL": "https://api.example.com",
            "USER_ID": "123",
            "TOKEN": "secret-token",
        },
    )
    temp_storage.save_environment(env)

    # Test variable resolution
    text = "{{BASE_URL}}/users/{{USER_ID}}?token={{TOKEN}}"
    resolved = temp_storage.resolve_variables(text, "test")

    expected = "https://api.example.com/users/123?token=secret-token"
    assert resolved == expected


def test_variable_resolution_missing_env(temp_storage):
    """Test variable resolution with missing environment."""
    text = "{{BASE_URL}}/users/{{USER_ID}}"
    resolved = temp_storage.resolve_variables(text, "nonexistent")

    # Should return original text if environment doesn't exist
    assert resolved == text


def test_collections_persistence(temp_storage):
    """Test that collections persist across storage manager instances."""
    # Create first storage manager and save data
    request_data = RequestData(
        method="GET",
        url="https://api.example.com/test",
        headers={"Accept": "application/json"},
    )
    temp_storage.save_request("test-request", request_data, "test-collection")

    # Create new storage manager with same directory
    new_storage = StorageManager(temp_storage.config_dir)

    # Load data with new storage manager
    loaded_request = new_storage.load_request("test-request", "test-collection")

    assert loaded_request is not None
    assert loaded_request.method == "GET"
    assert loaded_request.url == "https://api.example.com/test"
