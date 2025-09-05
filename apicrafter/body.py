"""Request body handling module."""

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
from urllib.parse import urlencode

import questionary
from pydantic import BaseModel


class BodyType(str, Enum):
    """Supported request body types."""

    NONE = "none"
    JSON = "json"
    FORM_DATA = "form"
    RAW = "raw"
    BINARY = "binary"


class BodyConfig(BaseModel):
    """Request body configuration."""

    body_type: BodyType
    content: Union[str, Dict[str, Any], None] = None
    content_type: Optional[str] = None
    files: Dict[str, str] = {}  # For file uploads


class BodyHandler:
    """Handles different request body types."""

    @staticmethod
    def prepare_body(
        body_config: BodyConfig,
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]], Dict[str, str]]:
        """
        Prepare request body based on configuration.

        Args:
            body_config: Body configuration

        Returns:
            Tuple of (body_string, json_data, headers_to_add)
        """
        headers_to_add = {}

        if body_config.body_type == BodyType.NONE:
            return None, None, headers_to_add

        elif body_config.body_type == BodyType.JSON:
            if isinstance(body_config.content, dict):
                json_data = body_config.content
                headers_to_add["Content-Type"] = "application/json"
                return None, json_data, headers_to_add
            elif isinstance(body_config.content, str):
                try:
                    json_data = json.loads(body_config.content)
                    headers_to_add["Content-Type"] = "application/json"
                    return None, json_data, headers_to_add
                except json.JSONDecodeError:
                    # Fallback to raw string
                    return body_config.content, None, headers_to_add

        elif body_config.body_type == BodyType.FORM_DATA:
            if isinstance(body_config.content, dict):
                form_string = urlencode(body_config.content)
                headers_to_add["Content-Type"] = "application/x-www-form-urlencoded"
                return form_string, None, headers_to_add

        elif body_config.body_type == BodyType.RAW:
            if body_config.content_type:
                headers_to_add["Content-Type"] = body_config.content_type
            return str(body_config.content), None, headers_to_add

        elif body_config.body_type == BodyType.BINARY:
            # Handle binary data (files)
            if body_config.content_type:
                headers_to_add["Content-Type"] = body_config.content_type
            return str(body_config.content), None, headers_to_add

        return None, None, headers_to_add

    @staticmethod
    def parse_body_from_cli(
        body_string: Optional[str], form_data: Optional[list], raw_data: Optional[str]
    ) -> Optional[BodyConfig]:
        """
        Parse body configuration from CLI arguments.

        Args:
            body_string: JSON body string
            form_data: List of form data pairs
            raw_data: Raw body data

        Returns:
            BodyConfig object or None
        """
        if body_string:
            # Try to parse as JSON first
            try:
                json_obj = json.loads(body_string)
                return BodyConfig(body_type=BodyType.JSON, content=json_obj)
            except json.JSONDecodeError:
                # Fallback to raw
                return BodyConfig(body_type=BodyType.RAW, content=body_string)

        elif form_data:
            form_dict = {}
            files_dict = {}

            for item in form_data:
                if "=" in item:
                    key, value = item.split("=", 1)
                    # Check if it's a file reference
                    if value.startswith("@"):
                        file_path = value[1:]  # Remove @ prefix
                        if os.path.exists(file_path):
                            files_dict[key] = file_path
                        else:
                            form_dict[key] = value  # Keep as-is if file doesn't exist
                    else:
                        form_dict[key] = value

            return BodyConfig(
                body_type=BodyType.FORM_DATA, content=form_dict, files=files_dict
            )

        elif raw_data:
            return BodyConfig(body_type=BodyType.RAW, content=raw_data)

        return None

    @staticmethod
    def interactive_body_setup(method: str) -> Optional[BodyConfig]:
        """
        Interactive body setup for requests.

        Args:
            method: HTTP method

        Returns:
            BodyConfig object or None
        """
        # Only show body options for methods that typically have bodies
        if method.upper() not in ["POST", "PUT", "PATCH"]:
            return BodyConfig(body_type=BodyType.NONE)

        if not questionary.confirm("Add request body?", default=False).ask():
            return BodyConfig(body_type=BodyType.NONE)

        body_type = questionary.select(
            "Select body type:",
            choices=[
                questionary.Choice("JSON", BodyType.JSON),
                questionary.Choice("Form Data", BodyType.FORM_DATA),
                questionary.Choice("Raw Text", BodyType.RAW),
                questionary.Choice("Binary/File", BodyType.BINARY),
            ],
        ).ask()

        if not body_type:
            return BodyConfig(body_type=BodyType.NONE)

        if body_type == BodyType.JSON:
            return BodyHandler._setup_json_body()

        elif body_type == BodyType.FORM_DATA:
            return BodyHandler._setup_form_data_body()

        elif body_type == BodyType.RAW:
            return BodyHandler._setup_raw_body()

        elif body_type == BodyType.BINARY:
            return BodyHandler._setup_binary_body()

        return BodyConfig(body_type=BodyType.NONE)

    @staticmethod
    def _setup_json_body() -> BodyConfig:
        """Setup JSON body interactively."""
        questionary.print(
            "Enter JSON data (press Ctrl+D or Ctrl+Z when done):", style="fg:cyan"
        )

        # Multi-line JSON input
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass

        json_text = "\n".join(lines).strip()

        if not json_text:
            # Fallback to simple key-value input
            return BodyHandler._setup_json_from_keyvalue()

        try:
            json_obj = json.loads(json_text)
            return BodyConfig(body_type=BodyType.JSON, content=json_obj)
        except json.JSONDecodeError as e:
            questionary.print(f"Invalid JSON: {e}", style="fg:red")
            questionary.print("Falling back to key-value input...", style="fg:yellow")
            return BodyHandler._setup_json_from_keyvalue()

    @staticmethod
    def _setup_json_from_keyvalue() -> BodyConfig:
        """Setup JSON body from key-value pairs."""
        json_data = {}

        while True:
            key = questionary.text("JSON key (or press Enter to finish):").ask()
            if not key or not key.strip():
                break

            value = questionary.text(f"Value for '{key}':").ask()
            if value:
                # Try to parse as number or boolean
                if value.lower() == "true":
                    json_data[key] = True
                elif value.lower() == "false":
                    json_data[key] = False
                elif value.isdigit():
                    json_data[key] = int(value)
                elif value.replace(".", "").isdigit():
                    json_data[key] = float(value)
                else:
                    json_data[key] = value

            if not questionary.confirm("Add another field?", default=False).ask():
                break

        return BodyConfig(body_type=BodyType.JSON, content=json_data)

    @staticmethod
    def _setup_form_data_body() -> BodyConfig:
        """Setup form data body interactively."""
        form_data = {}
        files = {}

        while True:
            field_name = questionary.text(
                "Form field name (or press Enter to finish):"
            ).ask()
            if not field_name or not field_name.strip():
                break

            is_file = questionary.confirm("Is this a file upload?", default=False).ask()

            if is_file:
                file_path = questionary.path("File path:").ask()
                if file_path and os.path.exists(file_path):
                    files[field_name] = file_path
                else:
                    questionary.print("File not found, skipping...", style="fg:yellow")
            else:
                field_value = questionary.text(f"Value for '{field_name}':").ask()
                if field_value:
                    form_data[field_name] = field_value

            if not questionary.confirm("Add another field?", default=False).ask():
                break

        return BodyConfig(body_type=BodyType.FORM_DATA, content=form_data, files=files)

    @staticmethod
    def _setup_raw_body() -> BodyConfig:
        """Setup raw body interactively."""
        content_type = questionary.text(
            "Content-Type (optional):", default="text/plain"
        ).ask()

        questionary.print(
            "Enter raw body content (press Ctrl+D or Ctrl+Z when done):",
            style="fg:cyan",
        )

        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass

        raw_content = "\n".join(lines)

        return BodyConfig(
            body_type=BodyType.RAW,
            content=raw_content,
            content_type=content_type or None,
        )

    @staticmethod
    def _setup_binary_body() -> BodyConfig:
        """Setup binary body interactively."""
        file_path = questionary.path("File path:").ask()

        if not file_path or not os.path.exists(file_path):
            questionary.print("File not found", style="fg:red")
            return BodyConfig(body_type=BodyType.NONE)

        # Try to detect content type
        content_type = BodyHandler._detect_content_type(file_path)

        confirmed_content_type = questionary.text(
            "Content-Type:", default=content_type
        ).ask()

        # Read file content
        try:
            with open(file_path, "rb") as f:
                content = f.read()

            return BodyConfig(
                body_type=BodyType.BINARY,
                content=content,
                content_type=confirmed_content_type,
            )
        except Exception as e:
            questionary.print(f"Error reading file: {e}", style="fg:red")
            return BodyConfig(body_type=BodyType.NONE)

    @staticmethod
    def _detect_content_type(file_path: str) -> str:
        """Detect content type from file extension."""
        ext = Path(file_path).suffix.lower()

        content_types = {
            ".json": "application/json",
            ".xml": "application/xml",
            ".html": "text/html",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".zip": "application/zip",
            ".tar": "application/x-tar",
            ".gz": "application/gzip",
        }

        return content_types.get(ext, "application/octet-stream")


def demo_body_functionality():
    """Demo function to show body functionality."""
    print("📄 Body Handling Demo")
    print("=" * 50)

    # Demo JSON body
    json_config = BodyConfig(
        body_type=BodyType.JSON, content={"name": "John", "age": 30, "active": True}
    )

    body_str, json_data, headers = BodyHandler.prepare_body(json_config)
    print("🔧 JSON Body:")
    print(f"   JSON Data: {json_data}")
    print(f"   Headers: {headers}")
    print()

    # Demo form data
    form_config = BodyConfig(
        body_type=BodyType.FORM_DATA,
        content={"username": "john", "email": "john@example.com"},
    )

    body_str, json_data, headers = BodyHandler.prepare_body(form_config)
    print("🔧 Form Data:")
    print(f"   Body: {body_str}")
    print(f"   Headers: {headers}")
    print()

    # Demo CLI parsing
    cli_json = '{"test": true, "count": 42}'
    config = BodyHandler.parse_body_from_cli(cli_json, None, None)
    if config:
        print("🔧 CLI JSON Parsing:")
        print(f"   Type: {config.body_type}")
        print(f"   Content: {config.content}")
    print()

    # Demo form parsing
    form_list = ["name=John", "age=30", "file=@/path/to/file.txt"]
    config = BodyHandler.parse_body_from_cli(None, form_list, None)
    if config:
        print("🔧 CLI Form Parsing:")
        print(f"   Type: {config.body_type}")
        print(f"   Content: {config.content}")
        print(f"   Files: {config.files}")


if __name__ == "__main__":
    demo_body_functionality()
