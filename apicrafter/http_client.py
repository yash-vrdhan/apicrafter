"""HTTP client wrapper using httpx."""

import json
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Union

import httpx
from pydantic import BaseModel

from .storage import HistoryEntry, RequestData, StorageManager


class ResponseData(BaseModel):
    """Model for HTTP response data."""

    status_code: int
    headers: Dict[str, str]
    content: bytes
    text: str
    json_data: Optional[Dict[str, Any]] = None
    response_time: float
    url: str
    method: str


class APIClient:
    """HTTP client wrapper for making API requests."""

    def __init__(self, storage_manager: Optional[StorageManager] = None):
        """Initialize the API client."""
        self.storage = storage_manager or StorageManager()
        self.client = httpx.Client(timeout=30.0)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.client.close()

    def send_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        json_data: Optional[Dict[str, Any]] = None,
        environment: str = "default",
        save_to_history: bool = True,
    ) -> ResponseData:
        """
        Send an HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Request URL
            headers: Request headers
            params: Query parameters
            body: Request body as string
            json_data: Request body as JSON
            environment: Environment name for variable resolution
            save_to_history: Whether to save request to history

        Returns:
            ResponseData object with response information
        """
        # Resolve environment variables
        resolved_url = self.storage.resolve_variables(url, environment)
        resolved_headers = {}
        if headers:
            for key, value in headers.items():
                resolved_headers[key] = self.storage.resolve_variables(
                    value, environment
                )

        resolved_params = {}
        if params:
            for key, value in params.items():
                resolved_params[key] = self.storage.resolve_variables(
                    value, environment
                )

        resolved_body = None
        if body:
            resolved_body = self.storage.resolve_variables(body, environment)

        # Prepare request data
        request_kwargs = {
            "method": method.upper(),
            "url": resolved_url,
            "headers": resolved_headers,
            "params": resolved_params,
        }

        if json_data:
            request_kwargs["json"] = json_data
        elif resolved_body:
            request_kwargs["content"] = resolved_body

        # Send request and measure time
        start_time = time.time()
        success = True

        try:
            response = self.client.request(**request_kwargs)
            response_time = time.time() - start_time

            # Try to parse JSON
            json_response = None
            try:
                json_response = response.json()
            except (json.JSONDecodeError, ValueError):
                pass

            response_data = ResponseData(
                status_code=response.status_code,
                headers=dict(response.headers),
                content=response.content,
                text=response.text,
                json_data=json_response,
                response_time=response_time,
                url=str(response.url),
                method=method.upper(),
            )

        except Exception as e:
            success = False
            response_time = time.time() - start_time

            # Create error response
            response_data = ResponseData(
                status_code=0,
                headers={},
                content=b"",
                text=f"Request failed: {str(e)}",
                json_data=None,
                response_time=response_time,
                url=resolved_url,
                method=method.upper(),
            )

        # Save to history if requested
        if save_to_history:
            history_entry = HistoryEntry(
                timestamp=datetime.now(),
                method=method.upper(),
                url=resolved_url,
                status_code=response_data.status_code if success else None,
                response_time=response_time,
                success=success,
            )
            self.storage.add_to_history(history_entry)

        return response_data

    def send_from_request_data(
        self,
        request_data: RequestData,
        environment: str = "default",
        save_to_history: bool = True,
    ) -> ResponseData:
        """
        Send a request from stored RequestData.

        Args:
            request_data: RequestData object
            environment: Environment name for variable resolution
            save_to_history: Whether to save request to history

        Returns:
            ResponseData object with response information
        """
        return self.send_request(
            method=request_data.method,
            url=request_data.url,
            headers=request_data.headers,
            params=request_data.params,
            body=request_data.body,
            json_data=request_data.json_data,
            environment=environment,
            save_to_history=save_to_history,
        )

    def test_request(
        self,
        request_data: RequestData,
        tests: Dict[str, Any],
        environment: str = "default",
    ) -> Tuple[bool, Dict[str, bool]]:
        """
        Test a request against defined assertions.

        Args:
            request_data: RequestData object
            tests: Dictionary of test assertions
            environment: Environment name for variable resolution

        Returns:
            Tuple of (all_passed, individual_results)
        """
        response = self.send_from_request_data(
            request_data, environment, save_to_history=False
        )

        results = {}

        # Test status code
        if "status_code" in tests:
            expected_status = tests["status_code"]
            results["status_code"] = response.status_code == expected_status

        # Test response body contains text
        if "body_contains" in tests:
            expected_text = tests["body_contains"]
            results["body_contains"] = expected_text in response.text

        # Test response body equals text
        if "body_equals" in tests:
            expected_body = tests["body_equals"]
            results["body_equals"] = response.text.strip() == expected_body.strip()

        # Test JSON field values
        if "json_field" in tests and response.json_data:
            for field_path, expected_value in tests["json_field"].items():
                try:
                    # Simple dot notation support (e.g., "user.name")
                    current = response.json_data
                    for part in field_path.split("."):
                        current = current[part]
                    results[f"json_field.{field_path}"] = current == expected_value
                except (KeyError, TypeError):
                    results[f"json_field.{field_path}"] = False

        # Test response time
        if "max_response_time" in tests:
            max_time = tests["max_response_time"]
            results["max_response_time"] = response.response_time <= max_time

        # Test headers
        if "headers" in tests:
            for header_name, expected_value in tests["headers"].items():
                actual_value = response.headers.get(header_name, "")
                results[f"headers.{header_name}"] = actual_value == expected_value

        all_passed = all(results.values()) if results else True
        return all_passed, results

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()
