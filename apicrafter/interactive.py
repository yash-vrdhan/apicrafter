"""Interactive prompts and menus using questionary."""

import json
from typing import Any, Dict, List, Optional, Tuple

import questionary
from questionary import Choice

from .auth import AuthHandler
from .auth_manager import AuthManager
from .body import BodyHandler
from .field_prompter import FieldPrompter
from .http_client import APIClient, ResponseData
from .renderer import ResponseRenderer
from .schema_loader import SchemaLoader
from .storage import RequestData, StorageManager
from .validator import RequestValidator


class InteractiveSession:
    """Handles interactive CLI sessions."""

    def __init__(
        self,
        storage: Optional[StorageManager] = None,
        renderer: Optional[ResponseRenderer] = None,
    ):
        """Initialize interactive session."""
        self.storage = storage or StorageManager()
        self.renderer = renderer or ResponseRenderer()
        self.client = APIClient(self.storage)
        self.schema_loader = SchemaLoader(self.storage)
        self.field_prompter = FieldPrompter()
        self.validator = RequestValidator()
        self.auth_manager = AuthManager(self.storage)

    def run_interactive_request(self) -> None:
        """Run an interactive request builder session."""
        try:
            self.renderer.print_info("Starting interactive request builder...")

            # Ask if user wants to use schema-driven mode
            use_schema = questionary.confirm(
                "Do you want to use schema-driven mode? (requires API schema)",
                default=False,
            ).ask()

            if use_schema:
                self.run_schema_driven_request()
            else:
                self.run_manual_request()

        finally:
            self.client.close()

    def run_schema_driven_request(self) -> None:
        """Run schema-driven interactive request builder."""
        try:
            # Get schema source
            schema_source = questionary.select(
                "How do you want to load the API schema?",
                choices=[
                    Choice("From URL (e.g., https://api.example.com)", "url"),
                    Choice("From local file", "file"),
                    Choice("Skip schema (manual mode)", "skip"),
                ],
            ).ask()

            if schema_source == "skip":
                self.run_manual_request()
                return

            # Load schema
            schema = None
            if schema_source == "url":
                base_url = questionary.text(
                    "Enter the API base URL:",
                    validate=lambda x: len(x.strip()) > 0 or "URL cannot be empty",
                ).ask()

                if base_url:
                    self.renderer.print_info(f"Loading schema from {base_url}...")
                    schema = self.schema_loader.load_schema_from_url(base_url)

            elif schema_source == "file":
                file_path = questionary.path("Enter path to schema file:").ask()

                if file_path:
                    self.renderer.print_info(f"Loading schema from {file_path}...")
                    schema = self.schema_loader.load_schema_from_file(file_path)

            if not schema:
                self.renderer.print_error(
                    "Failed to load schema. Falling back to manual mode."
                )
                self.run_manual_request()
                return

            # Show schema summary
            summary = self.schema_loader.get_schema_summary(schema)
            self.renderer.print_success(
                f"Loaded schema: {summary['title']} v{summary['version']}"
            )
            self.renderer.print_info(f"Found {summary['total_endpoints']} endpoints")

            # Let user choose endpoint
            endpoints = self.schema_loader.list_endpoints(schema)
            selected_endpoint = self.field_prompter.prompt_for_endpoint(endpoints)

            if not selected_endpoint:
                self.renderer.print_info("No endpoint selected.")
                return

            method, path = selected_endpoint
            endpoint_schema = self.schema_loader.get_endpoint_schema(
                schema, method, path
            )

            if not endpoint_schema:
                self.renderer.print_error("Could not find endpoint schema.")
                return

            # Show endpoint summary
            self.field_prompter.show_endpoint_summary(endpoint_schema)

            # Build the full URL
            full_url = schema.base_url.rstrip("/") + path
            resolved_url = questionary.text(
                "Confirm/edit the URL:", default=full_url
            ).ask()

            if not resolved_url:
                return

            # Schema-driven prompting
            headers = {}
            params = {}
            body_data = None
            json_data = None

            # Authentication
            if endpoint_schema.auth_schema:
                auth_data = self.field_prompter.prompt_for_auth(
                    endpoint_schema.auth_schema
                )
                if auth_data:
                    # Convert to our auth format and apply
                    from .auth import AuthConfig, AuthType

                    if auth_data["type"] == "bearer":
                        auth_config = AuthConfig(
                            auth_type=AuthType.BEARER,
                            credentials={"token": auth_data["token"]},
                        )
                    elif auth_data["type"] == "basic":
                        auth_config = AuthConfig(
                            auth_type=AuthType.BASIC,
                            credentials={
                                "username": auth_data["username"],
                                "password": auth_data["password"],
                            },
                        )
                    elif auth_data["type"] == "apikey":
                        auth_config = AuthConfig(
                            auth_type=AuthType.API_KEY,
                            credentials={
                                "key_name": auth_data["key_name"],
                                "key_value": auth_data["key_value"],
                            },
                            location=auth_data["location"],
                        )

                    headers, params = AuthHandler.apply_auth(
                        auth_config, headers, params
                    )

            # Headers
            if endpoint_schema.headers:
                schema_headers = self.field_prompter.prompt_for_headers(
                    endpoint_schema.headers
                )
                headers.update(schema_headers)

            # Query parameters
            if endpoint_schema.query_params:
                schema_params = self.field_prompter.prompt_for_query_params(
                    endpoint_schema.query_params
                )
                params.update(schema_params)

            # Request body
            if endpoint_schema.body_schema:
                body_obj = self.field_prompter.prompt_for_body(
                    endpoint_schema.body_schema
                )
                if body_obj:
                    json_data = body_obj
                    headers["Content-Type"] = "application/json"

            # Choose environment for variable resolution
            environment = self._choose_environment()

            # Validate request before sending
            validation_result = self.validator.validate_request(
                endpoint=endpoint_schema,
                headers=headers,
                query_params=params,
                body=json_data,
                method=method,
                path=path,
            )

            # Show validation results
            if not validation_result.is_valid:
                self.renderer.console.print(
                    "\n⚠️  Request validation failed:", style="bold red"
                )
                for error in validation_result.errors:
                    self.renderer.console.print(
                        f"  • {error.field}: {error.message}", style="red"
                    )

                if not questionary.confirm("Send request anyway?", default=False).ask():
                    self.renderer.print_info("Request cancelled.")
                    return
            else:
                self.renderer.console.print(
                    "\n✅ Request validation passed", style="bold green"
                )

            if validation_result.warnings:
                self.renderer.console.print("\n⚠️  Warnings:", style="bold yellow")
                for warning in validation_result.warnings:
                    self.renderer.console.print(f"  • {warning}", style="yellow")

            if validation_result.suggestions:
                self.renderer.console.print("\n💡 Suggestions:", style="bold blue")
                for suggestion in validation_result.suggestions:
                    self.renderer.console.print(f"  • {suggestion}", style="blue")

            # Show request summary
            self._show_request_summary(
                method, resolved_url, headers, params, None, json_data, environment
            )

            if not questionary.confirm("Send this request?", default=True).ask():
                self.renderer.print_info("Request cancelled.")
                return

            # Check for token expiration before sending
            headers = self.auth_manager.check_and_prompt_for_tokens(
                headers, environment, None
            )

            # Send request
            self.renderer.print_info("Sending request...")

            response = self.client.send_request(
                method=method,
                url=resolved_url,
                headers=headers,
                params=params,
                json_data=json_data,
                environment=environment,
            )

            # Display response
            self.renderer.render_response(response)

            # Ask to save request
            self._offer_save_request(
                method, resolved_url, headers, params, None, json_data
            )

        except Exception as e:
            self.renderer.print_error(f"Schema-driven request failed: {str(e)}")

    def run_manual_request(self) -> None:
        """Run manual interactive request builder (original functionality)."""
        try:

            # Choose request method
            method = questionary.select(
                "Select HTTP method:",
                choices=[
                    Choice("GET", "GET"),
                    Choice("POST", "POST"),
                    Choice("PUT", "PUT"),
                    Choice("PATCH", "PATCH"),
                    Choice("DELETE", "DELETE"),
                    Choice("HEAD", "HEAD"),
                    Choice("OPTIONS", "OPTIONS"),
                ],
            ).ask()

            if not method:
                return

            # Get URL
            url = questionary.text(
                "Enter the URL:",
                validate=lambda x: len(x.strip()) > 0 or "URL cannot be empty",
            ).ask()

            if not url:
                return

            # Authentication
            auth_config = AuthHandler.interactive_auth_setup()

            # Headers
            headers = self._collect_headers()

            # Query parameters
            params = self._collect_query_params()

            # Apply authentication to headers/params
            if auth_config:
                headers, params = AuthHandler.apply_auth(auth_config, headers, params)

            # Request body
            body_config = BodyHandler.interactive_body_setup(method)
            body_data = None
            json_data = None

            if body_config:
                body_str, json_obj, body_headers = BodyHandler.prepare_body(body_config)
                headers.update(body_headers)
                body_data = body_str
                json_data = json_obj

            # Choose environment
            environment = self._choose_environment()

            # Confirm request
            self._show_request_summary(
                method,
                url,
                headers,
                params,
                body_data,
                json_data,
                environment,
                auth_config,
            )

            if not questionary.confirm("Send this request?", default=True).ask():
                self.renderer.print_info("Request cancelled.")
                return

            # Check for token expiration before sending
            headers = self.auth_manager.check_and_prompt_for_tokens(
                headers, environment, None
            )

            # Send request
            self.renderer.print_info("Sending request...")

            try:
                response = self.client.send_request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    body=body_data,
                    json_data=json_data,
                    environment=environment,
                )

                # Display response
                self.renderer.render_response(response)

                # Ask to save request
                self._offer_save_request(
                    method, url, headers, params, body_data, json_data
                )

            except Exception as e:
                self.renderer.print_error(f"Request failed: {str(e)}")

        except Exception as e:
            self.renderer.print_error(f"Manual request failed: {str(e)}")

    def _collect_headers(self) -> Dict[str, str]:
        """Collect headers interactively."""
        headers = {}

        if questionary.confirm("Add headers?", default=False).ask():
            while True:
                header_name = questionary.text(
                    "Header name (or press Enter to finish):"
                ).ask()
                if not header_name or not header_name.strip():
                    break

                header_value = questionary.text(f"Value for '{header_name}':").ask()
                if header_value:
                    headers[header_name.strip()] = header_value.strip()

                if not questionary.confirm("Add another header?", default=False).ask():
                    break

        return headers

    def _collect_query_params(self) -> Dict[str, str]:
        """Collect query parameters interactively."""
        params = {}

        if questionary.confirm("Add query parameters?", default=False).ask():
            while True:
                param_name = questionary.text(
                    "Parameter name (or press Enter to finish):"
                ).ask()
                if not param_name or not param_name.strip():
                    break

                param_value = questionary.text(f"Value for '{param_name}':").ask()
                if param_value:
                    params[param_name.strip()] = param_value.strip()

                if not questionary.confirm(
                    "Add another parameter?", default=False
                ).ask():
                    break

        return params

    def _collect_body_data(self) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Collect request body data interactively."""
        if not questionary.confirm("Add request body?", default=False).ask():
            return None, None

        body_type = questionary.select(
            "Select body type:",
            choices=[
                Choice("JSON", "json"),
                Choice("Raw text", "raw"),
                Choice("Form data", "form"),
            ],
        ).ask()

        if body_type == "json":
            json_text = questionary.text(
                "Enter JSON data:", multiline=True, validate=self._validate_json
            ).ask()

            if json_text:
                try:
                    json_data = json.loads(json_text)
                    return None, json_data
                except json.JSONDecodeError:
                    self.renderer.print_error("Invalid JSON format")
                    return None, None

        elif body_type == "raw":
            raw_text = questionary.text("Enter raw body data:", multiline=True).ask()
            return raw_text, None

        elif body_type == "form":
            # Collect form data
            form_data = {}
            while True:
                field_name = questionary.text(
                    "Form field name (or press Enter to finish):"
                ).ask()
                if not field_name or not field_name.strip():
                    break

                field_value = questionary.text(f"Value for '{field_name}':").ask()
                if field_value:
                    form_data[field_name.strip()] = field_value.strip()

                if not questionary.confirm("Add another field?", default=False).ask():
                    break

            if form_data:
                # Convert to URL-encoded format
                from urllib.parse import urlencode

                return urlencode(form_data), None

        return None, None

    def _validate_json(self, text: str) -> bool:
        """Validate JSON format."""
        if not text.strip():
            return True  # Empty is OK

        try:
            json.loads(text)
            return True
        except json.JSONDecodeError:
            return "Invalid JSON format"

    def _choose_environment(self) -> str:
        """Choose environment interactively."""
        environments = self.storage.load_environments()

        if len(environments) <= 1:
            return "default"

        choices = [Choice(env_name, env_name) for env_name in environments.keys()]

        environment = questionary.select(
            "Select environment:", choices=choices, default="default"
        ).ask()

        return environment or "default"

    def _show_request_summary(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Dict[str, str],
        body: Optional[str],
        json_data: Optional[Dict[str, Any]],
        environment: str,
        auth_config=None,
    ) -> None:
        """Show a summary of the request to be sent."""
        self.renderer.console.print("\n[bold cyan]Request Summary:[/bold cyan]")
        self.renderer.console.print(f"Method: [bold]{method}[/bold]")
        self.renderer.console.print(f"URL: [bold]{url}[/bold]")
        self.renderer.console.print(f"Environment: [bold]{environment}[/bold]")

        if auth_config and auth_config.auth_type.value != "none":
            auth_type_display = auth_config.auth_type.value.title()
            self.renderer.console.print(
                f"Authentication: [bold]{auth_type_display}[/bold]"
            )

        if headers:
            self.renderer.console.print("\nHeaders:")
            for name, value in headers.items():
                self.renderer.console.print(f"  {name}: {value}")

        if params:
            self.renderer.console.print("\nQuery Parameters:")
            for name, value in params.items():
                self.renderer.console.print(f"  {name}: {value}")

        if json_data:
            self.renderer.console.print("\nJSON Body:")
            self.renderer.console.print(f"  {json.dumps(json_data, indent=2)}")
        elif body:
            self.renderer.console.print(f"\nBody:\n  {body}")

        self.renderer.console.print()

    def _offer_save_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Dict[str, str],
        body: Optional[str],
        json_data: Optional[Dict[str, Any]],
    ) -> None:
        """Offer to save the request to a collection."""
        if questionary.confirm("Save this request?", default=False).ask():
            request_name = questionary.text(
                "Enter a name for this request:",
                validate=lambda x: len(x.strip()) > 0 or "Name cannot be empty",
            ).ask()

            if request_name:
                collection_name = (
                    questionary.text("Collection name:", default="default").ask()
                    or "default"
                )

                request_data = RequestData(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    body=body,
                    json_data=json_data,
                )

                try:
                    self.storage.save_request(
                        request_name, request_data, collection_name
                    )
                    self.renderer.print_success(
                        f"Request saved as '{request_name}' in collection '{collection_name}'"
                    )
                except Exception as e:
                    self.renderer.print_error(f"Failed to save request: {str(e)}")

    def choose_saved_request(self) -> Optional[Tuple[str, str]]:
        """Choose a saved request interactively."""
        collections = self.storage.load_collections()

        if not collections:
            self.renderer.print_error("No saved requests found")
            return None

        # Build choices list
        choices = []
        for coll_name, collection in collections.items():
            if hasattr(collection, "requests"):
                for req_name in collection.requests.keys():
                    display_name = (
                        f"{req_name} ({coll_name})"
                        if coll_name != "default"
                        else req_name
                    )
                    choices.append(Choice(display_name, (req_name, coll_name)))

        if not choices:
            self.renderer.print_error("No saved requests found")
            return None

        selected = questionary.select("Select a saved request:", choices=choices).ask()

        return selected

    def choose_environment_interactive(self) -> str:
        """Choose environment interactively."""
        environments = self.storage.load_environments()

        if not environments:
            self.renderer.print_error("No environments found")
            return "default"

        choices = [Choice(env_name, env_name) for env_name in environments.keys()]

        environment = questionary.select(
            "Select environment:", choices=choices, default="default"
        ).ask()

        return environment or "default"

    def run_collection_manager(self) -> None:
        """Run interactive collection management."""
        while True:
            action = questionary.select(
                "Collection Management:",
                choices=[
                    Choice("View collections", "view"),
                    Choice("Create new collection", "create"),
                    Choice("Delete collection", "delete"),
                    Choice("Back to main menu", "back"),
                ],
            ).ask()

            if action == "back" or not action:
                break
            elif action == "view":
                collections = self.storage.load_collections()
                self.renderer.render_collections(collections)
            elif action == "create":
                self._create_collection_interactive()
            elif action == "delete":
                self._delete_collection_interactive()

    def _create_collection_interactive(self) -> None:
        """Create a new collection interactively."""
        name = questionary.text(
            "Collection name:",
            validate=lambda x: len(x.strip()) > 0 or "Name cannot be empty",
        ).ask()

        if not name:
            return

        description = questionary.text("Description (optional):").ask()

        # Create empty collection by saving it
        from .storage import Collection

        collection = Collection(name=name, description=description)
        collections = self.storage.load_collections()
        collections[name] = collection
        self.storage._save_collections(collections)

        self.renderer.print_success(f"Collection '{name}' created")

    def _delete_collection_interactive(self) -> None:
        """Delete a collection interactively."""
        collections = self.storage.load_collections()

        if not collections:
            self.renderer.print_error("No collections found")
            return

        choices = [
            Choice(name, name) for name in collections.keys() if name != "default"
        ]

        if not choices:
            self.renderer.print_error(
                "No collections available for deletion (cannot delete 'default')"
            )
            return

        collection_name = questionary.select(
            "Select collection to delete:", choices=choices
        ).ask()

        if not collection_name:
            return

        if questionary.confirm(
            f"Delete collection '{collection_name}' and all its requests?",
            default=False,
        ).ask():
            del collections[collection_name]
            self.storage._save_collections(collections)
            self.renderer.print_success(f"Collection '{collection_name}' deleted")
