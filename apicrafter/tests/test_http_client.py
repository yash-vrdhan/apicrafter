"""Tests for HTTP client functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest

from apicrafter.http_client import APIClient, ResponseData
from apicrafter.storage import RequestData, StorageManager


@pytest.fixture
def temp_storage():
    """Create a temporary storage manager for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield StorageManager(Path(temp_dir))


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    response = Mock()
    response.status_code = 200
    response.headers = {"Content-Type": "application/json"}
    response.content = b'{"message": "success"}'
    response.text = '{"message": "success"}'
    response.json.return_value = {"message": "success"}
    response.url = "https://api.example.com/test"
    return response


def test_response_data_creation():
    """Test ResponseData model creation."""
    response_data = ResponseData(
        status_code=200,
        headers={"Content-Type": "application/json"},
        content=b'{"test": true}',
        text='{"test": true}',
        json_data={"test": True},
        response_time=0.5,
        url="https://api.example.com/test",
        method="GET",
    )

    assert response_data.status_code == 200
    assert response_data.headers["Content-Type"] == "application/json"
    assert response_data.json_data == {"test": True}
    assert response_data.response_time == 0.5


@patch("apicrafter.http_client.httpx.Client")
def test_send_request_success(mock_client_class, temp_storage, mock_response):
    """Test successful HTTP request."""
    # Setup mock
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    mock_client.request.return_value = mock_response

    # Create client and send request
    client = APIClient(temp_storage)
    response = client.send_request(
        method="GET",
        url="https://api.example.com/test",
        headers={"Accept": "application/json"},
    )

    # Verify request was made correctly
    mock_client.request.assert_called_once()
    call_args = mock_client.request.call_args
    assert call_args[1]["method"] == "GET"
    assert call_args[1]["url"] == "https://api.example.com/test"
    assert call_args[1]["headers"]["Accept"] == "application/json"

    # Verify response
    assert response.status_code == 200
    assert response.json_data == {"message": "success"}


@patch("apicrafter.http_client.httpx.Client")
def test_send_request_with_json(mock_client_class, temp_storage, mock_response):
    """Test HTTP request with JSON data."""
    # Setup mock
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    mock_client.request.return_value = mock_response

    # Create client and send request
    client = APIClient(temp_storage)
    json_data = {"name": "test", "value": 123}

    response = client.send_request(
        method="POST", url="https://api.example.com/test", json_data=json_data
    )

    # Verify JSON data was passed correctly
    call_args = mock_client.request.call_args
    assert call_args[1]["json"] == json_data


@patch("apicrafter.http_client.httpx.Client")
def test_send_request_with_environment_variables(
    mock_client_class, temp_storage, mock_response
):
    """Test HTTP request with environment variable resolution."""
    # Setup environment
    from apicrafter.storage import Environment

    env = Environment(
        name="test",
        variables={"BASE_URL": "https://api.example.com", "API_KEY": "test-key-123"},
    )
    temp_storage.save_environment(env)

    # Setup mock
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    mock_client.request.return_value = mock_response

    # Create client and send request with variables
    client = APIClient(temp_storage)
    response = client.send_request(
        method="GET",
        url="{{BASE_URL}}/test",
        headers={"Authorization": "Bearer {{API_KEY}}"},
        environment="test",
    )

    # Verify variables were resolved
    call_args = mock_client.request.call_args
    assert call_args[1]["url"] == "https://api.example.com/test"
    assert call_args[1]["headers"]["Authorization"] == "Bearer test-key-123"


def test_send_from_request_data(temp_storage):
    """Test sending request from RequestData object."""
    request_data = RequestData(
        method="POST",
        url="https://api.example.com/users",
        headers={"Content-Type": "application/json"},
        json_data={"name": "Test User"},
    )

    with patch("apicrafter.http_client.httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"id": 1, "name": "Test User"}'
        mock_response.text = '{"id": 1, "name": "Test User"}'
        mock_response.json.return_value = {"id": 1, "name": "Test User"}
        mock_response.url = "https://api.example.com/users"
        mock_client.request.return_value = mock_response

        client = APIClient(temp_storage)
        response = client.send_from_request_data(request_data)

        assert response.status_code == 201
        assert response.json_data == {"id": 1, "name": "Test User"}


def test_basic_request_testing(temp_storage):
    """Test basic request testing functionality."""
    request_data = RequestData(
        method="GET", url="https://api.example.com/health", headers={}
    )

    tests = {
        "status_code": 200,
        "body_contains": "healthy",
        "json_field": {"status": "ok"},
    }

    with patch("apicrafter.http_client.httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"status": "ok", "message": "healthy"}'
        mock_response.text = '{"status": "ok", "message": "healthy"}'
        mock_response.json.return_value = {"status": "ok", "message": "healthy"}
        mock_response.url = "https://api.example.com/health"
        mock_client.request.return_value = mock_response

        client = APIClient(temp_storage)
        all_passed, results = client.test_request(request_data, tests)

        assert all_passed is True
        assert results["status_code"] is True
        assert results["body_contains"] is True
        assert results["json_field.status"] is True


@patch("apicrafter.http_client.httpx.Client")
def test_request_failure_handling(mock_client_class, temp_storage):
    """Test handling of request failures."""
    # Setup mock to raise exception
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    mock_client.request.side_effect = httpx.ConnectError("Connection failed")

    # Create client and send request
    client = APIClient(temp_storage)
    response = client.send_request(
        method="GET", url="https://invalid-url.example.com/test"
    )

    # Verify error response
    assert response.status_code == 0
    assert "Connection failed" in response.text
    assert response.json_data is None
