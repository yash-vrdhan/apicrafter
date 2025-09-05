"""Request validation engine for schema compliance."""

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from .schema_loader import APISchema, SchemaEndpoint


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"{field}: {message}")


class ValidationResult:
    """Result of request validation."""

    def __init__(self):
        self.is_valid = True
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []

    def add_error(self, field: str, message: str, value: Any = None) -> None:
        """Add a validation error."""
        self.is_valid = False
        self.errors.append(ValidationError(field, message, value))

    def add_warning(self, message: str) -> None:
        """Add a validation warning."""
        self.warnings.append(message)

    def add_suggestion(self, message: str) -> None:
        """Add a validation suggestion."""
        self.suggestions.append(message)

    def get_summary(self) -> str:
        """Get a human-readable summary of validation results."""
        if self.is_valid:
            summary = "✅ Request is valid"
            if self.warnings:
                summary += f" ({len(self.warnings)} warnings)"
        else:
            summary = f"❌ Request has {len(self.errors)} validation errors"

        return summary


class RequestValidator:
    """Validates HTTP requests against API schemas."""

    def __init__(self):
        """Initialize request validator."""
        pass

    def validate_request(
        self,
        endpoint: SchemaEndpoint,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        body: Optional[Union[Dict[str, Any], str]] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate a complete HTTP request against endpoint schema.

        Args:
            endpoint: SchemaEndpoint to validate against
            headers: Request headers
            query_params: Query parameters
            body: Request body (dict for JSON, str for raw)
            method: HTTP method (optional, for additional validation)
            path: Request path (optional, for path parameter validation)

        Returns:
            ValidationResult object
        """
        result = ValidationResult()

        # Validate method matches
        if method and method.upper() != endpoint.method:
            result.add_error(
                "method", f"Expected {endpoint.method}, got {method.upper()}"
            )

        # Validate headers
        if endpoint.headers:
            header_result = self.validate_headers(endpoint.headers, headers or {})
            result.errors.extend(header_result.errors)
            result.warnings.extend(header_result.warnings)

        # Validate query parameters
        if endpoint.query_params:
            query_result = self.validate_query_params(
                endpoint.query_params, query_params or {}
            )
            result.errors.extend(query_result.errors)
            result.warnings.extend(query_result.warnings)

        # Validate request body
        if endpoint.body_schema:
            body_result = self.validate_body(endpoint.body_schema, body)
            result.errors.extend(body_result.errors)
            result.warnings.extend(body_result.warnings)
        elif body:
            result.add_warning("Request body provided but not expected by schema")

        # Validate path parameters
        if path:
            path_result = self.validate_path_parameters(endpoint.path, path)
            result.errors.extend(path_result.errors)

        # Update overall validity
        result.is_valid = len(result.errors) == 0

        # Add suggestions
        self._add_suggestions(result, endpoint, headers, query_params, body)

        return result

    def validate_headers(
        self, headers_schema: Dict[str, Any], headers: Dict[str, str]
    ) -> ValidationResult:
        """Validate request headers against schema."""
        result = ValidationResult()

        # Check required headers
        for header_name, header_def in headers_schema.items():
            if header_def.get("required", False):
                # Case-insensitive header lookup
                header_found = False
                for actual_header in headers.keys():
                    if actual_header.lower() == header_name.lower():
                        header_found = True
                        break

                if not header_found:
                    result.add_error(
                        f"headers.{header_name}", "Required header is missing"
                    )

        # Validate header values
        for header_name, header_value in headers.items():
            # Find matching schema (case-insensitive)
            schema_def = None
            schema_name = None
            for schema_header_name, schema_header_def in headers_schema.items():
                if schema_header_name.lower() == header_name.lower():
                    schema_def = schema_header_def
                    schema_name = schema_header_name
                    break

            if schema_def:
                field_result = self.validate_field_value(
                    f"headers.{schema_name}", header_value, schema_def
                )
                result.errors.extend(field_result.errors)
                result.warnings.extend(field_result.warnings)
            else:
                result.add_warning(f"Unexpected header: {header_name}")

        return result

    def validate_query_params(
        self, query_schema: Dict[str, Any], query_params: Dict[str, str]
    ) -> ValidationResult:
        """Validate query parameters against schema."""
        result = ValidationResult()

        # Check required parameters
        for param_name, param_def in query_schema.items():
            if param_def.get("required", False) and param_name not in query_params:
                result.add_error(
                    f"query.{param_name}", "Required query parameter is missing"
                )

        # Validate parameter values
        for param_name, param_value in query_params.items():
            if param_name in query_schema:
                field_result = self.validate_field_value(
                    f"query.{param_name}", param_value, query_schema[param_name]
                )
                result.errors.extend(field_result.errors)
                result.warnings.extend(field_result.warnings)
            else:
                result.add_warning(f"Unexpected query parameter: {param_name}")

        return result

    def validate_body(
        self, body_schema: Dict[str, Any], body: Optional[Union[Dict[str, Any], str]]
    ) -> ValidationResult:
        """Validate request body against schema."""
        result = ValidationResult()

        if body is None:
            # Check if body is required
            if body_schema.get("required", False):
                result.add_error("body", "Request body is required")
            return result

        # If body is a string, try to parse as JSON
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                result.add_error("body", "Request body must be valid JSON")
                return result

        # Validate based on schema type
        schema_type = body_schema.get("type", "object")

        if schema_type == "object":
            object_result = self.validate_object(body, body_schema, "body")
            result.errors.extend(object_result.errors)
            result.warnings.extend(object_result.warnings)
        elif schema_type == "array":
            array_result = self.validate_array(body, body_schema, "body")
            result.errors.extend(array_result.errors)
            result.warnings.extend(array_result.warnings)
        else:
            field_result = self.validate_field_value("body", body, body_schema)
            result.errors.extend(field_result.errors)
            result.warnings.extend(field_result.warnings)

        return result

    def validate_object(
        self, obj: Any, schema: Dict[str, Any], field_path: str
    ) -> ValidationResult:
        """Validate object against object schema."""
        result = ValidationResult()

        if not isinstance(obj, dict):
            result.add_error(field_path, f"Expected object, got {type(obj).__name__}")
            return result

        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))

        # Check required fields
        for required_field in required_fields:
            if required_field not in obj:
                result.add_error(
                    f"{field_path}.{required_field}", "Required field is missing"
                )

        # Validate each property
        for prop_name, prop_value in obj.items():
            if prop_name in properties:
                prop_schema = properties[prop_name]
                prop_result = self.validate_field_value(
                    f"{field_path}.{prop_name}", prop_value, prop_schema
                )
                result.errors.extend(prop_result.errors)
                result.warnings.extend(prop_result.warnings)
            else:
                # Check if additional properties are allowed
                additional_properties = schema.get("additionalProperties", True)
                if additional_properties is False:
                    result.add_error(
                        f"{field_path}.{prop_name}", "Additional property not allowed"
                    )
                elif additional_properties is not True:
                    # Additional properties have a schema
                    prop_result = self.validate_field_value(
                        f"{field_path}.{prop_name}", prop_value, additional_properties
                    )
                    result.errors.extend(prop_result.errors)
                    result.warnings.extend(prop_result.warnings)

        return result

    def validate_array(
        self, arr: Any, schema: Dict[str, Any], field_path: str
    ) -> ValidationResult:
        """Validate array against array schema."""
        result = ValidationResult()

        if not isinstance(arr, list):
            result.add_error(field_path, f"Expected array, got {type(arr).__name__}")
            return result

        # Check array constraints
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")

        if min_items is not None and len(arr) < min_items:
            result.add_error(
                field_path,
                f"Array must have at least {min_items} items, got {len(arr)}",
            )

        if max_items is not None and len(arr) > max_items:
            result.add_error(
                field_path, f"Array must have at most {max_items} items, got {len(arr)}"
            )

        # Validate items
        items_schema = schema.get("items", {})
        if items_schema:
            for i, item in enumerate(arr):
                item_result = self.validate_field_value(
                    f"{field_path}[{i}]", item, items_schema
                )
                result.errors.extend(item_result.errors)
                result.warnings.extend(item_result.warnings)

        return result

    def validate_field_value(
        self, field_path: str, value: Any, schema: Dict[str, Any]
    ) -> ValidationResult:
        """Validate a single field value against its schema."""
        result = ValidationResult()

        field_type = schema.get("type", "string")
        enum_values = schema.get("enum")
        pattern = schema.get("pattern")
        min_length = schema.get("minLength")
        max_length = schema.get("maxLength")
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")

        # Type validation
        if field_type == "string" and not isinstance(value, str):
            result.add_error(
                field_path, f"Expected string, got {type(value).__name__}", value
            )
        elif field_type == "integer" and not isinstance(value, int):
            result.add_error(
                field_path, f"Expected integer, got {type(value).__name__}", value
            )
        elif field_type == "number" and not isinstance(value, (int, float)):
            result.add_error(
                field_path, f"Expected number, got {type(value).__name__}", value
            )
        elif field_type == "boolean" and not isinstance(value, bool):
            result.add_error(
                field_path, f"Expected boolean, got {type(value).__name__}", value
            )
        elif field_type == "array" and not isinstance(value, list):
            result.add_error(
                field_path, f"Expected array, got {type(value).__name__}", value
            )
        elif field_type == "object" and not isinstance(value, dict):
            result.add_error(
                field_path, f"Expected object, got {type(value).__name__}", value
            )

        # Enum validation
        if enum_values and value not in enum_values:
            result.add_error(
                field_path, f"Value must be one of {enum_values}, got {value}", value
            )

        # String-specific validations
        if isinstance(value, str):
            if pattern and not re.match(pattern, value):
                result.add_error(
                    field_path, f"Value does not match pattern: {pattern}", value
                )

            if min_length is not None and len(value) < min_length:
                result.add_error(
                    field_path,
                    f"String must be at least {min_length} characters, got {len(value)}",
                    value,
                )

            if max_length is not None and len(value) > max_length:
                result.add_error(
                    field_path,
                    f"String must be at most {max_length} characters, got {len(value)}",
                    value,
                )

        # Numeric validations
        if isinstance(value, (int, float)):
            if minimum is not None and value < minimum:
                result.add_error(
                    field_path, f"Value must be at least {minimum}, got {value}", value
                )

            if maximum is not None and value > maximum:
                result.add_error(
                    field_path, f"Value must be at most {maximum}, got {value}", value
                )

        # Recursive validation for objects and arrays
        if field_type == "object" and isinstance(value, dict):
            object_result = self.validate_object(value, schema, field_path)
            result.errors.extend(object_result.errors)
            result.warnings.extend(object_result.warnings)
        elif field_type == "array" and isinstance(value, list):
            array_result = self.validate_array(value, schema, field_path)
            result.errors.extend(array_result.errors)
            result.warnings.extend(array_result.warnings)

        return result

    def validate_path_parameters(
        self, schema_path: str, actual_path: str
    ) -> ValidationResult:
        """Validate path parameters by comparing schema path with actual path."""
        result = ValidationResult()

        schema_parts = schema_path.strip("/").split("/")
        actual_parts = actual_path.strip("/").split("/")

        if len(schema_parts) != len(actual_parts):
            result.add_error(
                "path",
                f"Path structure mismatch: expected {schema_path}, got {actual_path}",
            )
            return result

        for i, (schema_part, actual_part) in enumerate(zip(schema_parts, actual_parts)):
            if schema_part.startswith("{") and schema_part.endswith("}"):
                # Path parameter - validate it's not empty
                if not actual_part:
                    param_name = schema_part[1:-1]  # Remove braces
                    result.add_error(
                        f"path.{param_name}", "Path parameter cannot be empty"
                    )
            elif schema_part != actual_part:
                result.add_error(
                    "path",
                    f"Path segment mismatch at position {i}: expected '{schema_part}', got '{actual_part}'",
                )

        return result

    def _add_suggestions(
        self,
        result: ValidationResult,
        endpoint: SchemaEndpoint,
        headers: Optional[Dict[str, str]],
        query_params: Optional[Dict[str, str]],
        body: Optional[Union[Dict[str, Any], str]],
    ) -> None:
        """Add helpful suggestions to the validation result."""

        # Suggest missing optional fields with defaults
        if endpoint.headers:
            for header_name, header_def in endpoint.headers.items():
                if not header_def.get("required", False) and header_def.get("default"):
                    if not headers or header_name not in headers:
                        result.add_suggestion(
                            f"Consider adding header '{header_name}' with default value: {header_def['default']}"
                        )

        if endpoint.query_params:
            for param_name, param_def in endpoint.query_params.items():
                if not param_def.get("required", False) and param_def.get("default"):
                    if not query_params or param_name not in query_params:
                        result.add_suggestion(
                            f"Consider adding query parameter '{param_name}' with default value: {param_def['default']}"
                        )

        # Suggest examples if available
        if endpoint.body_schema and not body:
            example = endpoint.body_schema.get("example")
            if example:
                result.add_suggestion(
                    f"Example request body: {json.dumps(example, indent=2)}"
                )

    def get_validation_summary(self, result: ValidationResult) -> str:
        """Get a detailed validation summary for display."""
        lines = [result.get_summary()]

        if result.errors:
            lines.append("\n❌ Errors:")
            for error in result.errors:
                lines.append(f"  • {error.field}: {error.message}")
                if error.value is not None:
                    lines.append(f"    Got: {error.value}")

        if result.warnings:
            lines.append("\n⚠️  Warnings:")
            for warning in result.warnings:
                lines.append(f"  • {warning}")

        if result.suggestions:
            lines.append("\n💡 Suggestions:")
            for suggestion in result.suggestions:
                lines.append(f"  • {suggestion}")

        return "\n".join(lines)


def demo_validator():
    """Demo function to show validator functionality."""
    print("✅ VALIDATION ENGINE DEMO")
    print("=" * 50)

    validator = RequestValidator()

    # Create a sample endpoint schema
    from .schema_loader import SchemaEndpoint

    endpoint = SchemaEndpoint(
        method="POST",
        path="/users",
        headers={
            "Authorization": {"type": "string", "required": True},
            "Content-Type": {"type": "string", "enum": ["application/json"]},
        },
        query_params={"validate": {"type": "boolean", "default": False}},
        body_schema={
            "type": "object",
            "properties": {
                "username": {"type": "string", "minLength": 3},
                "email": {"type": "string", "pattern": r"^[^@]+@[^@]+\.[^@]+$"},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
            },
            "required": ["username", "email"],
        },
    )

    print("✅ Sample endpoint schema created")
    print(f"Method: {endpoint.method}")
    print(f"Path: {endpoint.path}")
    print(
        f"Required headers: {[h for h, d in endpoint.headers.items() if d.get('required')]}"
    )
    print(f"Required body fields: {endpoint.body_schema.get('required', [])}")

    # Test valid request
    print("\n🔧 Testing valid request:")
    valid_headers = {
        "Authorization": "Bearer token123",
        "Content-Type": "application/json",
    }
    valid_body = {"username": "johndoe", "email": "john@example.com", "age": 25}

    result = validator.validate_request(
        endpoint=endpoint, headers=valid_headers, body=valid_body, method="POST"
    )

    print(f"Valid request result: {result.get_summary()}")

    # Test invalid request
    print("\n🔧 Testing invalid request:")
    invalid_headers = {"Content-Type": "application/json"}  # Missing Authorization
    invalid_body = {
        "username": "jo",
        "email": "invalid-email",
    }  # Short username, invalid email

    result = validator.validate_request(
        endpoint=endpoint, headers=invalid_headers, body=invalid_body, method="POST"
    )

    print(f"Invalid request result: {result.get_summary()}")
    print(f"Errors: {len(result.errors)}")
    for error in result.errors:
        print(f"  • {error.field}: {error.message}")


if __name__ == "__main__":
    demo_validator()
