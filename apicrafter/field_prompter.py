"""Dynamic field prompter based on API schemas."""

import json
from typing import Any, Dict, List, Optional, Union

import questionary
from questionary import Choice

from .auth import AuthHandler, AuthType
from .schema_loader import SchemaEndpoint


class FieldPrompter:
    """Generates dynamic prompts based on API schemas."""

    def __init__(self):
        """Initialize field prompter."""
        pass

    def prompt_for_headers(self, headers_schema: Dict[str, Any]) -> Dict[str, str]:
        """
        Prompt user for headers based on schema.

        Args:
            headers_schema: Dictionary of header definitions

        Returns:
            Dictionary of header name -> value
        """
        headers = {}

        if not headers_schema:
            return headers

        print("📝 Headers:")

        # Sort headers: required first, then optional
        sorted_headers = sorted(
            headers_schema.items(),
            key=lambda x: (not x[1].get("required", False), x[0]),
        )

        for header_name, header_def in sorted_headers:
            required = header_def.get("required", False)
            description = header_def.get("description", "")
            default = header_def.get("default")
            header_type = header_def.get("type", "string")
            enum_values = header_def.get("enum")
            example = header_def.get("example")

            # Build prompt message
            prompt_msg = f"  {header_name}"
            if required:
                prompt_msg += " (required)"
            if description:
                prompt_msg += f" - {description}"
            if example:
                prompt_msg += f" [example: {example}]"

            # Handle different input types
            if enum_values:
                # Enum values as choices
                choices = [Choice(str(val), str(val)) for val in enum_values]
                if not required:
                    choices.insert(0, Choice("(skip)", None))

                value = questionary.select(prompt_msg + ":", choices=choices).ask()
            else:
                # Regular text input
                default_text = ""
                if default is not None:
                    default_text = str(default)

                validate_func = None
                if required:
                    validate_func = (
                        lambda x: len(x.strip()) > 0 or f"{header_name} is required"
                    )

                if (
                    header_type == "password"
                    or "password" in header_name.lower()
                    or "secret" in header_name.lower()
                ):
                    value = questionary.password(
                        prompt_msg + ":", default=default_text, validate=validate_func
                    ).ask()
                else:
                    value = questionary.text(
                        prompt_msg + ":", default=default_text, validate=validate_func
                    ).ask()

            if value is not None and value != "":
                headers[header_name] = str(value)

        return headers

    def prompt_for_query_params(self, query_schema: Dict[str, Any]) -> Dict[str, str]:
        """
        Prompt user for query parameters based on schema.

        Args:
            query_schema: Dictionary of query parameter definitions

        Returns:
            Dictionary of parameter name -> value
        """
        params = {}

        if not query_schema:
            return params

        print("🔍 Query Parameters:")

        # Sort parameters: required first, then optional
        sorted_params = sorted(
            query_schema.items(), key=lambda x: (not x[1].get("required", False), x[0])
        )

        for param_name, param_def in sorted_params:
            required = param_def.get("required", False)
            description = param_def.get("description", "")
            default = param_def.get("default")
            param_type = param_def.get("type", "string")
            enum_values = param_def.get("enum")
            example = param_def.get("example")

            # Build prompt message
            prompt_msg = f"  {param_name}"
            if required:
                prompt_msg += " (required)"
            if description:
                prompt_msg += f" - {description}"
            if example:
                prompt_msg += f" [example: {example}]"

            # Handle different input types
            if enum_values:
                # Enum values as choices
                choices = [Choice(str(val), str(val)) for val in enum_values]
                if not required:
                    choices.insert(0, Choice("(skip)", None))

                value = questionary.select(prompt_msg + ":", choices=choices).ask()
            else:
                # Regular text input with type-specific validation
                default_text = ""
                if default is not None:
                    default_text = str(default)

                validate_func = None
                if required:
                    validate_func = (
                        lambda x: len(x.strip()) > 0 or f"{param_name} is required"
                    )
                elif param_type == "integer":
                    validate_func = (
                        lambda x: x == ""
                        or x.lstrip("-").isdigit()
                        or "Must be a number"
                    )
                elif param_type == "number":
                    validate_func = (
                        lambda x: x == "" or self._is_float(x) or "Must be a number"
                    )
                elif param_type == "boolean":
                    validate_func = (
                        lambda x: x == ""
                        or x.lower() in ["true", "false", "1", "0"]
                        or "Must be true/false"
                    )

                value = questionary.text(
                    prompt_msg + ":", default=default_text, validate=validate_func
                ).ask()

            if value is not None and value != "":
                # For query parameters, always store as strings (URL parameters are strings)
                # But validate the type first
                if param_type == "integer" and value.lstrip("-").isdigit():
                    params[param_name] = str(
                        int(value)
                    )  # Convert to int then back to string
                elif param_type == "number" and self._is_float(value):
                    params[param_name] = str(
                        float(value)
                    )  # Convert to float then back to string
                elif param_type == "boolean":
                    params[param_name] = str(
                        value.lower() in ["true", "1"]
                    ).lower()  # Convert to string
                else:
                    params[param_name] = str(value)

        return params

    def prompt_for_body(self, body_schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Prompt user for request body based on schema.

        Args:
            body_schema: Body schema definition

        Returns:
            Dictionary representing the request body or None
        """
        if not body_schema:
            return None

        print("📄 Request Body:")

        schema_type = body_schema.get("type", "object")

        if schema_type == "object":
            return self._prompt_for_object(body_schema, "  ")
        elif schema_type == "array":
            return self._prompt_for_array(body_schema, "  ")
        else:
            # Simple type
            return self._prompt_for_simple_type(body_schema, "body", "  ")

    def _prompt_for_object(
        self, schema: Dict[str, Any], indent: str = ""
    ) -> Dict[str, Any]:
        """Prompt for object properties recursively."""
        obj = {}
        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))

        if not properties:
            # Free-form object
            questionary.print(f"{indent}Free-form object - enter JSON:", style="dim")
            json_text = questionary.text(f"{indent}JSON:", multiline=True).ask()
            if json_text:
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    questionary.print(f"{indent}Invalid JSON, skipping", style="red")
            return {}

        # Sort properties: required first, then optional
        sorted_props = sorted(
            properties.items(), key=lambda x: (x[0] not in required_fields, x[0])
        )

        for prop_name, prop_schema in sorted_props:
            required = prop_name in required_fields
            description = prop_schema.get("description", "")
            default = prop_schema.get("default")
            example = prop_schema.get("example")

            # Build prompt message
            prompt_msg = f"{indent}{prop_name}"
            if required:
                prompt_msg += " (required)"
            if description:
                prompt_msg += f" - {description}"
            if example:
                prompt_msg += f" [example: {example}]"

            value = self._prompt_for_property(
                prop_schema, prop_name, prompt_msg, required, default
            )

            if value is not None:
                obj[prop_name] = value

        return obj

    def _prompt_for_array(self, schema: Dict[str, Any], indent: str = "") -> List[Any]:
        """Prompt for array items."""
        items_schema = schema.get("items", {})
        min_items = schema.get("minItems", 0)
        max_items = schema.get("maxItems", 10)  # Reasonable default

        items = []

        questionary.print(f"{indent}Array items:", style="dim")

        while len(items) < max_items:
            if len(items) >= min_items:
                if not questionary.confirm(
                    f"{indent}Add item #{len(items) + 1}?", default=False
                ).ask():
                    break

            item_value = self._prompt_for_property(
                items_schema,
                f"item_{len(items)}",
                f"{indent}  Item #{len(items) + 1}",
                len(items) < min_items,
                None,
            )

            if item_value is not None:
                items.append(item_value)
            elif len(items) >= min_items:
                break

        return items

    def _prompt_for_property(
        self,
        prop_schema: Dict[str, Any],
        prop_name: str,
        prompt_msg: str,
        required: bool,
        default: Any,
    ) -> Any:
        """Prompt for a single property based on its schema."""
        prop_type = prop_schema.get("type", "string")
        enum_values = prop_schema.get("enum")

        if enum_values:
            # Enum values as choices
            choices = [Choice(str(val), val) for val in enum_values]
            if not required:
                choices.insert(0, Choice("(skip)", None))

            return questionary.select(prompt_msg + ":", choices=choices).ask()

        elif prop_type == "boolean":
            if not required:
                return questionary.confirm(
                    prompt_msg + ":",
                    default=bool(default) if default is not None else False,
                ).ask()
            else:
                return questionary.confirm(prompt_msg + ":").ask()

        elif prop_type == "integer":
            default_text = str(default) if default is not None else ""
            validate_func = (
                lambda x: x == "" or x.lstrip("-").isdigit() or "Must be a number"
            )
            if required:
                validate_func = lambda x: x.lstrip("-").isdigit() or "Must be a number"

            value = questionary.text(
                prompt_msg + ":", default=default_text, validate=validate_func
            ).ask()
            return int(value) if value and value.lstrip("-").isdigit() else None

        elif prop_type == "number":
            default_text = str(default) if default is not None else ""
            validate_func = lambda x: x == "" or self._is_float(x) or "Must be a number"
            if required:
                validate_func = lambda x: self._is_float(x) or "Must be a number"

            value = questionary.text(
                prompt_msg + ":", default=default_text, validate=validate_func
            ).ask()
            return float(value) if value and self._is_float(value) else None

        elif prop_type == "object":
            if questionary.confirm(
                f"{prompt_msg} (object) - add properties?", default=required
            ).ask():
                return self._prompt_for_object(prop_schema, "    ")
            return None

        elif prop_type == "array":
            if questionary.confirm(
                f"{prompt_msg} (array) - add items?", default=required
            ).ask():
                return self._prompt_for_array(prop_schema, "    ")
            return None

        else:  # string or unknown type
            default_text = str(default) if default is not None else ""
            validate_func = None
            if required:
                validate_func = (
                    lambda x: len(x.strip()) > 0 or f"{prop_name} is required"
                )

            # Check for password fields
            if "password" in prop_name.lower() or "secret" in prop_name.lower():
                return questionary.password(
                    prompt_msg + ":", default=default_text, validate=validate_func
                ).ask()
            else:
                return questionary.text(
                    prompt_msg + ":", default=default_text, validate=validate_func
                ).ask()

    def _prompt_for_simple_type(
        self, schema: Dict[str, Any], field_name: str, indent: str
    ) -> Any:
        """Prompt for a simple (non-object, non-array) type."""
        return self._prompt_for_property(
            schema, field_name, f"{indent}{field_name}", True, schema.get("default")
        )

    def _is_float(self, value: str) -> bool:
        """Check if string can be converted to float."""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def prompt_for_auth(self, auth_schema: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Handle authorization prompting based on schema.

        Args:
            auth_schema: Authentication schema definition

        Returns:
            Dictionary with auth configuration or None
        """
        if not auth_schema:
            return None

        print("🔐 Authentication:")

        scheme_type = auth_schema.get("type", "bearer")
        scheme_name = auth_schema.get("scheme", "default")

        if scheme_type.lower() == "bearer":
            token = questionary.password("  Bearer Token:").ask()
            if token:
                return {"type": "bearer", "token": token}

        elif scheme_type.lower() == "basic":
            username = questionary.text("  Username:").ask()
            password = questionary.password("  Password:").ask()
            if username and password:
                return {"type": "basic", "username": username, "password": password}

        elif scheme_type.lower() == "apikey":
            key_name = questionary.text("  API Key Name:", default="X-API-Key").ask()
            key_value = questionary.password("  API Key Value:").ask()
            location = questionary.select(
                "  Location:",
                choices=[
                    Choice("Header", "header"),
                    Choice("Query Parameter", "query"),
                ],
            ).ask()

            if key_name and key_value:
                return {
                    "type": "apikey",
                    "key_name": key_name,
                    "key_value": key_value,
                    "location": location,
                }

        return None

    def prompt_for_endpoint(self, endpoints: List[tuple]) -> Optional[tuple]:
        """
        Prompt user to select an endpoint from available options.

        Args:
            endpoints: List of (method, path) tuples

        Returns:
            Selected (method, path) tuple or None
        """
        if not endpoints:
            print("No endpoints available")
            return None

        if len(endpoints) == 1:
            return endpoints[0]

        # Group by method for better organization
        methods = {}
        for method, path in endpoints:
            if method not in methods:
                methods[method] = []
            methods[method].append(path)

        # Create choices
        choices = []
        for method in sorted(methods.keys()):
            for path in sorted(methods[method]):
                display_name = f"{method.ljust(7)} {path}"
                choices.append(Choice(display_name, (method, path)))

        selected = questionary.select("Select an endpoint:", choices=choices).ask()

        return selected

    def show_endpoint_summary(self, endpoint: SchemaEndpoint) -> None:
        """Show a summary of the endpoint schema."""
        print(f"\n📋 Endpoint: {endpoint.method} {endpoint.path}")

        if endpoint.summary:
            print(f"Summary: {endpoint.summary}")

        if endpoint.description:
            print(f"Description: {endpoint.description}")

        # Show what will be prompted for
        sections = []
        if endpoint.auth_schema:
            sections.append("🔐 Authentication")
        if endpoint.headers:
            sections.append(f"📝 Headers ({len(endpoint.headers)})")
        if endpoint.query_params:
            sections.append(f"🔍 Query Parameters ({len(endpoint.query_params)})")
        if endpoint.body_schema:
            sections.append("📄 Request Body")

        if sections:
            print("Will prompt for: " + " • ".join(sections))

        print()


def demo_field_prompter():
    """Demo function to show field prompter functionality."""
    print("📝 FIELD PROMPTER DEMO")
    print("=" * 50)

    prompter = FieldPrompter()

    # Demo headers prompting
    headers_schema = {
        "Authorization": {
            "type": "string",
            "required": True,
            "description": "Bearer token for authentication",
        },
        "Content-Type": {
            "type": "string",
            "enum": ["application/json", "application/xml"],
            "default": "application/json",
        },
        "User-Agent": {"type": "string", "example": "MyApp/1.0"},
    }

    print("✅ Headers schema loaded")
    print("Headers to prompt for:", list(headers_schema.keys()))

    # Demo query params
    query_schema = {
        "page": {"type": "integer", "default": 1, "description": "Page number"},
        "limit": {"type": "integer", "description": "Items per page"},
        "sort": {"type": "string", "enum": ["asc", "desc"], "default": "asc"},
    }

    print("✅ Query parameters schema loaded")
    print("Query params to prompt for:", list(query_schema.keys()))

    # Demo body schema
    body_schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string", "description": "User's login name"},
            "email": {"type": "string", "description": "User's email address"},
            "age": {"type": "integer", "description": "User's age"},
            "active": {"type": "boolean", "default": True},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["username", "email"],
    }

    print("✅ Body schema loaded")
    print("Body properties:", list(body_schema.get("properties", {}).keys()))
    print("Required fields:", body_schema.get("required", []))


if __name__ == "__main__":
    demo_field_prompter()
