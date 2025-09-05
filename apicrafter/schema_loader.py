"""Schema loader for OpenAPI and JSON schemas."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse

import httpx
import yaml
from pydantic import BaseModel

from .storage import StorageManager


class SchemaEndpoint(BaseModel):
    """Model for an API endpoint schema."""

    method: str
    path: str
    summary: Optional[str] = None
    description: Optional[str] = None
    headers: Dict[str, Any] = {}
    query_params: Dict[str, Any] = {}
    body_schema: Optional[Dict[str, Any]] = None
    auth_schema: Optional[Dict[str, Any]] = None
    responses: Dict[str, Any] = {}


class APISchema(BaseModel):
    """Model for complete API schema."""

    title: str = "API"
    version: str = "1.0.0"
    base_url: str = ""
    endpoints: List[SchemaEndpoint] = []
    components: Dict[str, Any] = {}
    security_schemes: Dict[str, Any] = {}


class SchemaLoader:
    """Loads and parses API schemas from various sources."""

    def __init__(self, storage_manager: Optional[StorageManager] = None):
        """Initialize schema loader."""
        self.storage = storage_manager or StorageManager()
        self.cache_dir = self.storage.config_dir / "schema_cache"
        self.cache_dir.mkdir(exist_ok=True)

    def load_schema_from_url(self, base_url: str) -> Optional[APISchema]:
        """
        Fetch OpenAPI schema from URL.

        Tries common OpenAPI endpoints:
        - /openapi.json
        - /swagger.json
        - /docs/openapi.json
        - /api-docs

        Args:
            base_url: Base URL of the API

        Returns:
            APISchema object or None if not found
        """
        # Normalize base URL
        if not base_url.startswith(("http://", "https://")):
            base_url = f"https://{base_url}"

        # Common OpenAPI endpoints to try
        common_paths = [
            "/openapi.json",
            "/swagger.json",
            "/docs/openapi.json",
            "/api-docs",
            "/swagger/v1/swagger.json",
            "/v1/openapi.json",
            "/api/openapi.json",
        ]

        for path in common_paths:
            try:
                url = urljoin(base_url, path)
                logging.info(f"Trying to load schema from: {url}")

                with httpx.Client(timeout=10.0) as client:
                    response = client.get(url)

                    if response.status_code == 200:
                        schema_data = response.json()
                        api_schema = self._parse_openapi_schema(schema_data, base_url)

                        # Cache the schema
                        self._cache_schema(base_url, schema_data)

                        return api_schema

            except Exception as e:
                logging.debug(f"Failed to load schema from {url}: {e}")
                continue

        # Try to load from cache if all URLs failed
        cached_schema = self._load_cached_schema(base_url)
        if cached_schema:
            return self._parse_openapi_schema(cached_schema, base_url)

        return None

    def load_schema_from_file(self, file_path: str) -> Optional[APISchema]:
        """
        Load schema from local YAML/JSON file.

        Args:
            file_path: Path to schema file

        Returns:
            APISchema object or None if failed
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logging.error(f"Schema file not found: {file_path}")
                return None

            with open(path, "r", encoding="utf-8") as f:
                if path.suffix.lower() in [".yaml", ".yml"]:
                    schema_data = yaml.safe_load(f)
                else:
                    schema_data = json.load(f)

            # Determine base URL from file or use placeholder
            base_url = schema_data.get("servers", [{}])[0].get(
                "url", "https://api.example.com"
            )

            return self._parse_openapi_schema(schema_data, base_url)

        except Exception as e:
            logging.error(f"Failed to load schema from file {file_path}: {e}")
            return None

    def get_endpoint_schema(
        self, schema: APISchema, method: str, path: str
    ) -> Optional[SchemaEndpoint]:
        """
        Get schema for specific endpoint and method.

        Args:
            schema: APISchema object
            method: HTTP method (GET, POST, etc.)
            path: API path

        Returns:
            SchemaEndpoint object or None if not found
        """
        method = method.upper()

        for endpoint in schema.endpoints:
            if endpoint.method == method and self._path_matches(endpoint.path, path):
                return endpoint

        return None

    def _parse_openapi_schema(
        self, schema_data: Dict[str, Any], base_url: str
    ) -> APISchema:
        """Parse OpenAPI schema into our internal format."""
        info = schema_data.get("info", {})

        api_schema = APISchema(
            title=info.get("title", "API"),
            version=info.get("version", "1.0.0"),
            base_url=base_url,
            components=schema_data.get("components", {}),
            security_schemes=schema_data.get("components", {}).get(
                "securitySchemes", {}
            ),
        )

        # Parse paths
        paths = schema_data.get("paths", {})

        for path, path_data in paths.items():
            for method, method_data in path_data.items():
                if method.lower() in [
                    "get",
                    "post",
                    "put",
                    "patch",
                    "delete",
                    "head",
                    "options",
                ]:
                    endpoint = self._parse_endpoint(
                        path, method.upper(), method_data, api_schema.components
                    )
                    api_schema.endpoints.append(endpoint)

        return api_schema

    def _parse_endpoint(
        self,
        path: str,
        method: str,
        method_data: Dict[str, Any],
        components: Dict[str, Any],
    ) -> SchemaEndpoint:
        """Parse individual endpoint from OpenAPI spec."""
        endpoint = SchemaEndpoint(
            method=method,
            path=path,
            summary=method_data.get("summary"),
            description=method_data.get("description"),
        )

        # Parse parameters (headers and query)
        parameters = method_data.get("parameters", [])

        for param in parameters:
            param_name = param.get("name")
            param_in = param.get("in")
            param_schema = param.get("schema", {})
            param_required = param.get("required", False)
            param_description = param.get("description", "")

            param_def = {
                "type": param_schema.get("type", "string"),
                "required": param_required,
                "description": param_description,
                "default": param_schema.get("default"),
                "enum": param_schema.get("enum"),
                "example": param.get("example") or param_schema.get("example"),
            }

            if param_in == "header":
                endpoint.headers[param_name] = param_def
            elif param_in == "query":
                endpoint.query_params[param_name] = param_def

        # Parse request body
        request_body = method_data.get("requestBody", {})
        if request_body:
            content = request_body.get("content", {})

            # Try JSON first, then form data
            for content_type in [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data",
            ]:
                if content_type in content:
                    schema = content[content_type].get("schema", {})
                    endpoint.body_schema = self._resolve_schema_ref(schema, components)
                    break

        # Parse security requirements
        security = method_data.get("security", [])
        if security:
            # Take the first security requirement
            first_security = security[0]
            for scheme_name in first_security.keys():
                endpoint.auth_schema = {
                    "scheme": scheme_name,
                    "type": "bearer",  # Default, will be refined based on security scheme
                }
                break

        # Parse responses
        responses = method_data.get("responses", {})
        endpoint.responses = responses

        return endpoint

    def _resolve_schema_ref(
        self, schema: Dict[str, Any], components: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve $ref references in schema."""
        if "$ref" in schema:
            ref_path = schema["$ref"]
            if ref_path.startswith("#/components/schemas/"):
                schema_name = ref_path.split("/")[-1]
                return components.get("schemas", {}).get(schema_name, {})

        # Recursively resolve refs in properties
        if "properties" in schema:
            resolved_properties = {}
            for prop_name, prop_schema in schema["properties"].items():
                resolved_properties[prop_name] = self._resolve_schema_ref(
                    prop_schema, components
                )
            schema = schema.copy()
            schema["properties"] = resolved_properties

        return schema

    def _path_matches(self, schema_path: str, request_path: str) -> bool:
        """Check if request path matches schema path (with path parameters)."""
        # Simple implementation - can be enhanced for complex path matching
        schema_parts = schema_path.strip("/").split("/")
        request_parts = request_path.strip("/").split("/")

        if len(schema_parts) != len(request_parts):
            return False

        for schema_part, request_part in zip(schema_parts, request_parts):
            # Path parameter (e.g., {id})
            if schema_part.startswith("{") and schema_part.endswith("}"):
                continue
            # Exact match required
            elif schema_part != request_part:
                return False

        return True

    def _cache_schema(self, base_url: str, schema_data: Dict[str, Any]) -> None:
        """Cache schema data locally."""
        try:
            # Create cache filename from URL
            url_hash = str(abs(hash(base_url)))
            cache_file = self.cache_dir / f"schema_{url_hash}.json"

            cache_entry = {
                "url": base_url,
                "schema": schema_data,
                "cached_at": str(Path().cwd()),  # Simple timestamp
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f, indent=2)

            logging.info(f"Cached schema for {base_url}")

        except Exception as e:
            logging.error(f"Failed to cache schema: {e}")

    def _load_cached_schema(self, base_url: str) -> Optional[Dict[str, Any]]:
        """Load cached schema if available."""
        try:
            url_hash = str(abs(hash(base_url)))
            cache_file = self.cache_dir / f"schema_{url_hash}.json"

            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_entry = json.load(f)

                if cache_entry.get("url") == base_url:
                    logging.info(f"Using cached schema for {base_url}")
                    return cache_entry.get("schema")

        except Exception as e:
            logging.debug(f"Failed to load cached schema: {e}")

        return None

    def list_endpoints(
        self, schema: APISchema, filter_method: Optional[str] = None
    ) -> List[Tuple[str, str]]:
        """
        List all endpoints in schema.

        Args:
            schema: APISchema object
            filter_method: Optional method filter (GET, POST, etc.)

        Returns:
            List of (method, path) tuples
        """
        endpoints = []

        for endpoint in schema.endpoints:
            if filter_method is None or endpoint.method == filter_method.upper():
                endpoints.append((endpoint.method, endpoint.path))

        return sorted(endpoints)

    def get_schema_summary(self, schema: APISchema) -> Dict[str, Any]:
        """Get summary information about the schema."""
        method_counts = {}

        for endpoint in schema.endpoints:
            method_counts[endpoint.method] = method_counts.get(endpoint.method, 0) + 1

        return {
            "title": schema.title,
            "version": schema.version,
            "base_url": schema.base_url,
            "total_endpoints": len(schema.endpoints),
            "methods": method_counts,
            "has_auth": bool(schema.security_schemes),
        }


def demo_schema_loader():
    """Demo function to show schema loader functionality."""
    print("📋 SCHEMA LOADER DEMO")
    print("=" * 50)

    loader = SchemaLoader()

    # Demo with a sample OpenAPI schema
    sample_schema = {
        "openapi": "3.0.0",
        "info": {"title": "User API", "version": "1.0.0"},
        "servers": [{"url": "https://api.example.com"}],
        "paths": {
            "/users": {
                "get": {
                    "summary": "List users",
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "schema": {"type": "integer", "default": 1},
                        },
                        {
                            "name": "Authorization",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                    ],
                },
                "post": {
                    "summary": "Create user",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "username": {"type": "string"},
                                        "email": {"type": "string"},
                                        "age": {"type": "integer"},
                                    },
                                    "required": ["username", "email"],
                                }
                            }
                        }
                    },
                },
            }
        },
    }

    # Parse the sample schema
    api_schema = loader._parse_openapi_schema(sample_schema, "https://api.example.com")

    print("✅ Schema loaded successfully!")
    print(f"Title: {api_schema.title}")
    print(f"Version: {api_schema.version}")
    print(f"Base URL: {api_schema.base_url}")
    print(f"Endpoints: {len(api_schema.endpoints)}")

    print("\n🔧 Endpoints:")
    for endpoint in api_schema.endpoints:
        print(f"  {endpoint.method} {endpoint.path}")
        if endpoint.summary:
            print(f"    Summary: {endpoint.summary}")
        if endpoint.headers:
            print(f"    Headers: {list(endpoint.headers.keys())}")
        if endpoint.query_params:
            print(f"    Query Params: {list(endpoint.query_params.keys())}")
        if endpoint.body_schema:
            print(f"    Body Schema: {endpoint.body_schema.get('type', 'object')}")
        print()

    # Demo endpoint lookup
    print("🔧 Endpoint Lookup:")
    get_users = loader.get_endpoint_schema(api_schema, "GET", "/users")
    if get_users:
        print(f"Found: {get_users.method} {get_users.path}")
        print(f"Query params: {get_users.query_params}")
        print(f"Headers: {get_users.headers}")

    post_users = loader.get_endpoint_schema(api_schema, "POST", "/users")
    if post_users:
        print(f"Found: {post_users.method} {post_users.path}")
        print(f"Body schema: {post_users.body_schema}")


if __name__ == "__main__":
    demo_schema_loader()
