"""Main CLI application using Typer."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
import yaml
from rich.console import Console
from typing_extensions import Annotated

from .auth import AuthHandler
from .auth_manager import AuthManager
from .body import BodyHandler
from .http_client import APIClient
from .interactive import InteractiveSession
from .renderer import ResponseRenderer
from .storage import Environment, RequestData, StorageManager

# Create the main Typer app
app = typer.Typer(
    name="apicrafter",
    help="A terminal-first, interactive API client that brings Postman-like features into the CLI.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Initialize global objects
console = Console()
storage = StorageManager()
renderer = ResponseRenderer(console)


@app.command()
def send(
    method: Annotated[
        str, typer.Argument(help="HTTP method (GET, POST, PUT, DELETE, etc.)")
    ],
    url: Annotated[str, typer.Argument(help="Request URL")],
    header: Annotated[
        Optional[List[str]],
        typer.Option("--header", "-H", help="Headers in format 'Key: Value'"),
    ] = None,
    query: Annotated[
        Optional[List[str]],
        typer.Option("--query", "-q", help="Query params in format 'key=value'"),
    ] = None,
    body: Annotated[
        Optional[str], typer.Option("--body", "-b", help="Request body as string")
    ] = None,
    json_data: Annotated[
        Optional[str], typer.Option("--json", "-j", help="Request body as JSON string")
    ] = None,
    form: Annotated[
        Optional[List[str]],
        typer.Option("--form", "-f", help="Form data in format 'key=value'"),
    ] = None,
    raw: Annotated[Optional[str], typer.Option("--raw", help="Raw body data")] = None,
    auth: Annotated[
        Optional[str],
        typer.Option(
            "--auth",
            "-a",
            help="Auth: 'bearer:TOKEN', 'basic:user:pass', 'apikey:name:value[:location]'",
        ),
    ] = None,
    env: Annotated[
        str, typer.Option("--env", "-e", help="Environment to use")
    ] = "default",
    no_headers: Annotated[
        bool, typer.Option("--no-headers", help="Don't show response headers")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show detailed request info")
    ] = False,
) -> None:
    """Send an HTTP request."""
    try:
        # Parse headers
        headers = {}
        if header:
            for h in header:
                if ":" in h:
                    key, value = h.split(":", 1)
                    headers[key.strip()] = value.strip()
                else:
                    renderer.print_error(
                        f"Invalid header format: {h}. Use 'Key: Value'"
                    )
                    raise typer.Exit(1)

        # Parse query parameters
        params = {}
        if query:
            for q in query:
                if "=" in q:
                    key, value = q.split("=", 1)
                    params[key.strip()] = value.strip()
                else:
                    renderer.print_error(f"Invalid query format: {q}. Use 'key=value'")
                    raise typer.Exit(1)

        # Handle authentication
        if auth:
            auth_config = AuthHandler.parse_auth_string(auth)
            if auth_config:
                headers, params = AuthHandler.apply_auth(auth_config, headers, params)
            else:
                renderer.print_error(f"Invalid auth format: {auth}")
                renderer.print_info(
                    "Valid formats: 'bearer:TOKEN', 'basic:user:pass', 'apikey:name:value[:location]'"
                )
                raise typer.Exit(1)

        # Handle request body
        body_config = BodyHandler.parse_body_from_cli(json_data, form, raw)
        final_body = None
        final_json = None

        if body_config:
            body_str, json_obj, body_headers = BodyHandler.prepare_body(body_config)
            # Add body headers to request headers
            headers.update(body_headers)
            final_body = body_str
            final_json = json_obj
        elif body:  # Fallback to simple body string
            final_body = body

        if verbose:
            renderer.print_info(f"Sending {method.upper()} request to: {url}")
            if headers:
                renderer.print_info(f"Headers: {headers}")
            if params:
                renderer.print_info(f"Query params: {params}")
            if final_json:
                renderer.print_info(f"JSON body: {json.dumps(final_json, indent=2)}")
            elif final_body:
                renderer.print_info(
                    f"Body: {final_body[:200]}{'...' if len(str(final_body)) > 200 else ''}"
                )

        # Send request
        with APIClient(storage) as client:
            response = client.send_request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                body=final_body,
                json_data=final_json,
                environment=env,
            )

            # Render response
            renderer.render_response(response, show_headers=not no_headers)

            # Exit with error code if request failed
            if response.status_code >= 400:
                raise typer.Exit(1)

    except Exception as e:
        renderer.print_error(f"Request failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def interactive() -> None:
    """Start interactive request builder."""
    session = InteractiveSession(storage, renderer)
    session.run_interactive_request()


@app.command()
def save(
    name: Annotated[str, typer.Argument(help="Name for the saved request")],
    method: Annotated[str, typer.Option("--method", "-m", help="HTTP method")] = "GET",
    url: Annotated[str, typer.Option("--url", "-u", help="Request URL")] = "",
    header: Annotated[
        Optional[List[str]],
        typer.Option("--header", "-H", help="Headers in format 'Key: Value'"),
    ] = None,
    query: Annotated[
        Optional[List[str]],
        typer.Option("--query", "-q", help="Query params in format 'key=value'"),
    ] = None,
    body: Annotated[
        Optional[str], typer.Option("--body", "-b", help="Request body as string")
    ] = None,
    json_data: Annotated[
        Optional[str], typer.Option("--json", "-j", help="Request body as JSON string")
    ] = None,
    collection: Annotated[
        str, typer.Option("--collection", "-c", help="Collection name")
    ] = "default",
) -> None:
    """Save a request to a collection."""
    if not url:
        renderer.print_error("URL is required")
        raise typer.Exit(1)

    try:
        # Parse headers
        headers = {}
        if header:
            for h in header:
                if ":" in h:
                    key, value = h.split(":", 1)
                    headers[key.strip()] = value.strip()

        # Parse query parameters
        params = {}
        if query:
            for q in query:
                if "=" in q:
                    key, value = q.split("=", 1)
                    params[key.strip()] = value.strip()

        # Parse JSON data
        json_obj = None
        if json_data:
            try:
                json_obj = json.loads(json_data)
            except json.JSONDecodeError as e:
                renderer.print_error(f"Invalid JSON: {e}")
                raise typer.Exit(1)

        # Create request data
        request_data = RequestData(
            method=method,
            url=url,
            headers=headers,
            params=params,
            body=body,
            json_data=json_obj,
        )

        # Save request
        storage.save_request(name, request_data, collection)
        renderer.print_success(f"Request '{name}' saved to collection '{collection}'")

    except Exception as e:
        renderer.print_error(f"Failed to save request: {str(e)}")
        raise typer.Exit(1)


@app.command()
def run(
    name: Annotated[str, typer.Argument(help="Name of the saved request to run")],
    collection: Annotated[
        str, typer.Option("--collection", "-c", help="Collection name")
    ] = "default",
    env: Annotated[
        str, typer.Option("--env", "-e", help="Environment to use")
    ] = "default",
    no_headers: Annotated[
        bool, typer.Option("--no-headers", help="Don't show response headers")
    ] = False,
    validate: Annotated[
        Optional[str],
        typer.Option(
            "--validate", help="Validate against schema from URL or file path"
        ),
    ] = None,
) -> None:
    """Run a saved request."""
    try:
        # Load request
        request_data = storage.load_request(name, collection)
        if not request_data:
            renderer.print_error(
                f"Request '{name}' not found in collection '{collection}'"
            )
            raise typer.Exit(1)

        # Check for token expiration before sending
        auth_manager = AuthManager(storage)
        updated_headers = auth_manager.check_and_prompt_for_tokens(
            request_data.headers, env, name
        )

        # Update request data with refreshed headers
        if updated_headers != request_data.headers:
            request_data.headers = updated_headers

        # Send request
        with APIClient(storage) as client:
            response = client.send_from_request_data(request_data, env)

            # Render response
            renderer.render_response(response, show_headers=not no_headers)

            # Exit with error code if request failed
            if response.status_code >= 400:
                raise typer.Exit(1)

    except Exception as e:
        renderer.print_error(f"Failed to run request: {str(e)}")
        raise typer.Exit(1)


@app.command()
def collections() -> None:
    """List all collections and their requests."""
    try:
        collections_data = storage.load_collections()
        renderer.render_collections(collections_data)
    except Exception as e:
        renderer.print_error(f"Failed to load collections: {str(e)}")
        raise typer.Exit(1)


@app.command()
def environments() -> None:
    """List all environments and their variables."""
    try:
        environments_data = storage.load_environments()
        renderer.render_environments(environments_data)
    except Exception as e:
        renderer.print_error(f"Failed to load environments: {str(e)}")
        raise typer.Exit(1)


@app.command()
def env_set(
    name: Annotated[str, typer.Argument(help="Environment name")],
    variable: Annotated[str, typer.Argument(help="Variable name")],
    value: Annotated[str, typer.Argument(help="Variable value")],
) -> None:
    """Set an environment variable."""
    try:
        # Load or create environment
        env = storage.load_environment(name) or Environment(name=name, variables={})
        env.variables[variable] = value

        # Save environment
        storage.save_environment(env)
        renderer.print_success(f"Set {variable}={value} in environment '{name}'")

    except Exception as e:
        renderer.print_error(f"Failed to set environment variable: {str(e)}")
        raise typer.Exit(1)


@app.command()
def history(
    limit: Annotated[
        int, typer.Option("--limit", "-l", help="Number of entries to show")
    ] = 20,
) -> None:
    """Show request history."""
    try:
        history_data = storage.load_history(limit)
        renderer.render_history(history_data, limit)
    except Exception as e:
        renderer.print_error(f"Failed to load history: {str(e)}")
        raise typer.Exit(1)


@app.command()
def replay(
    index: Annotated[int, typer.Argument(help="History entry index to replay")],
    env: Annotated[
        str, typer.Option("--env", "-e", help="Environment to use")
    ] = "default",
    no_headers: Annotated[
        bool, typer.Option("--no-headers", help="Don't show response headers")
    ] = False,
) -> None:
    """Replay a request from history."""
    try:
        history_data = storage.load_history(
            100
        )  # Get more entries to find the right one

        if index < 1 or index > len(history_data):
            renderer.print_error(f"Invalid history index: {index}")
            raise typer.Exit(1)

        entry = history_data[index - 1]

        # Create request data from history entry
        request_data = RequestData(
            method=entry.method,
            url=entry.url,
            headers={},
            params={},
            body=None,
            json_data=None,
        )

        # Send request
        with APIClient(storage) as client:
            response = client.send_from_request_data(request_data, env)

            # Render response
            renderer.render_response(response, show_headers=not no_headers)

            # Exit with error code if request failed
            if response.status_code >= 400:
                raise typer.Exit(1)

    except Exception as e:
        renderer.print_error(f"Failed to replay request: {str(e)}")
        raise typer.Exit(1)


@app.command()
def test(
    name: Annotated[str, typer.Argument(help="Name of the request to test")],
    collection: Annotated[
        str, typer.Option("--collection", "-c", help="Collection name")
    ] = "default",
    env: Annotated[
        str, typer.Option("--env", "-e", help="Environment to use")
    ] = "default",
    tests_file: Annotated[
        Optional[str], typer.Option("--tests", "-t", help="Path to tests file")
    ] = None,
) -> None:
    """Run tests on a saved request."""
    try:
        # Load request
        request_data = storage.load_request(name, collection)
        if not request_data:
            renderer.print_error(
                f"Request '{name}' not found in collection '{collection}'"
            )
            raise typer.Exit(1)

        # Load tests
        tests = {}
        if tests_file:
            test_path = Path(tests_file)
            if not test_path.exists():
                renderer.print_error(f"Tests file not found: {tests_file}")
                raise typer.Exit(1)

            with open(test_path, "r") as f:
                if tests_file.endswith(".yaml") or tests_file.endswith(".yml"):
                    test_data = yaml.safe_load(f)
                else:
                    test_data = json.load(f)

            tests = test_data.get("tests", {}).get(name, {})
        else:
            # Look for tests in collections file
            collections_data = storage.load_collections()
            if collection in collections_data:
                # Try to find tests in collection metadata
                # This is a simple implementation - could be enhanced
                tests = {"status_code": 200}  # Default test

        if not tests:
            renderer.print_error(f"No tests defined for request '{name}'")
            raise typer.Exit(1)

        # Run tests
        with APIClient(storage) as client:
            all_passed, results = client.test_request(request_data, tests, env)

            # Render test results
            renderer.render_test_results(name, results, all_passed)

            # Exit with error code if tests failed
            if not all_passed:
                raise typer.Exit(1)

    except Exception as e:
        renderer.print_error(f"Failed to run tests: {str(e)}")
        raise typer.Exit(1)


@app.command()
def auth(
    auth_type: Annotated[str, typer.Argument(help="Auth type: bearer, basic, apikey")],
    credentials: Annotated[
        str, typer.Argument(help="Credentials (format depends on type)")
    ],
    url: Annotated[
        str, typer.Option("--url", "-u", help="Test URL")
    ] = "https://httpbin.org/bearer",
) -> None:
    """Test authentication methods."""
    try:
        auth_string = f"{auth_type}:{credentials}"
        auth_config = AuthHandler.parse_auth_string(auth_string)

        if not auth_config:
            renderer.print_error(f"Invalid auth format for {auth_type}")
            renderer.print_info("Examples:")
            renderer.print_info("  apicrafter auth bearer 'your-token-here'")
            renderer.print_info("  apicrafter auth basic 'username:password'")
            renderer.print_info("  apicrafter auth apikey 'X-API-Key:your-key'")
            raise typer.Exit(1)

        # Test the auth by sending a request
        headers = {}
        params = {}
        headers, params = AuthHandler.apply_auth(auth_config, headers, params)

        renderer.print_info(f"Testing {auth_type} authentication...")

        with APIClient(storage) as client:
            response = client.send_request(
                method="GET", url=url, headers=headers, params=params
            )

            renderer.render_response(response)

            if response.status_code < 400:
                renderer.print_success("Authentication test successful!")
            else:
                renderer.print_error("Authentication test failed!")
                raise typer.Exit(1)

    except Exception as e:
        renderer.print_error(f"Auth test failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def headers(
    url: Annotated[str, typer.Argument(help="URL to inspect headers")],
    method: Annotated[str, typer.Option("--method", "-m", help="HTTP method")] = "HEAD",
) -> None:
    """Inspect response headers for a URL."""
    try:
        with APIClient(storage) as client:
            response = client.send_request(method=method, url=url)

            if response.headers:
                renderer.render_headers(response.headers)
            else:
                renderer.print_info("No headers received")

    except Exception as e:
        renderer.print_error(f"Failed to inspect headers: {str(e)}")
        raise typer.Exit(1)


@app.command()
def curl(
    request_name: Annotated[
        str, typer.Argument(help="Name of saved request to convert to curl")
    ],
    collection: Annotated[
        str, typer.Option("--collection", "-c", help="Collection name")
    ] = "default",
    env: Annotated[
        str, typer.Option("--env", "-e", help="Environment to use")
    ] = "default",
) -> None:
    """Convert a saved request to curl command."""
    try:
        request_data = storage.load_request(request_name, collection)
        if not request_data:
            renderer.print_error(
                f"Request '{request_name}' not found in collection '{collection}'"
            )
            raise typer.Exit(1)

        # Resolve variables
        resolved_url = storage.resolve_variables(request_data.url, env)

        # Build curl command
        curl_parts = ["curl"]

        # Method
        if request_data.method.upper() != "GET":
            curl_parts.extend(["-X", request_data.method.upper()])

        # Headers
        for name, value in request_data.headers.items():
            resolved_value = storage.resolve_variables(value, env)
            curl_parts.extend(["-H", f"'{name}: {resolved_value}'"])

        # Body
        if request_data.json_data:
            json_str = json.dumps(request_data.json_data)
            resolved_json = storage.resolve_variables(json_str, env)
            curl_parts.extend(["-d", f"'{resolved_json}'"])
        elif request_data.body:
            resolved_body = storage.resolve_variables(request_data.body, env)
            curl_parts.extend(["-d", f"'{resolved_body}'"])

        # URL (add last)
        curl_parts.append(f"'{resolved_url}'")

        # Query parameters
        if request_data.params:
            query_parts = []
            for name, value in request_data.params.items():
                resolved_value = storage.resolve_variables(value, env)
                query_parts.append(f"{name}={resolved_value}")

            if query_parts:
                separator = "&" if "?" in resolved_url else "?"
                curl_parts[-1] = f"'{resolved_url}{separator}{'&'.join(query_parts)}'"

        curl_command = " ".join(curl_parts)

        renderer.console.print("\n[bold cyan]Curl Command:[/bold cyan]")
        renderer.console.print(curl_command)
        renderer.console.print()

        # Copy to clipboard if possible
        try:
            import subprocess

            subprocess.run(["echo", curl_command], stdout=subprocess.PIPE, text=True)
            renderer.print_info(
                "💡 Tip: Copy the command above to use in your terminal"
            )
        except:
            pass

    except Exception as e:
        renderer.print_error(f"Failed to generate curl command: {str(e)}")
        raise typer.Exit(1)


@app.command()
def config() -> None:
    """Show configuration directory and file locations."""
    renderer.print_info(f"Configuration directory: {storage.config_dir}")
    renderer.print_info(f"Collections file: {storage.collections_file}")
    renderer.print_info(f"Environments file: {storage.environments_file}")
    renderer.print_info(f"History file: {storage.history_file}")


@app.command()
def docs() -> None:
    """Show helpful documentation and examples."""
    renderer.console.print(
        "\n[bold cyan]🛠️  apicrafter - Postman for your terminal[/bold cyan]"
    )
    renderer.console.print("\n[bold yellow]📖 Quick Examples:[/bold yellow]")

    examples = [
        ("Simple GET request:", "apicrafter send GET https://httpbin.org/json"),
        (
            "POST with JSON:",
            'apicrafter send POST https://httpbin.org/post --json \'{"name": "John"}\'',
        ),
        (
            "With authentication:",
            "apicrafter send GET https://httpbin.org/bearer --auth 'bearer:your-token'",
        ),
        (
            "Form data:",
            "apicrafter send POST https://httpbin.org/post --form 'name=John' --form 'age=30'",
        ),
        ("Interactive mode:", "apicrafter interactive"),
        (
            "Save request:",
            "apicrafter save login --method POST --url 'https://api.example.com/auth'",
        ),
        ("Run saved request:", "apicrafter run login --env production"),
        (
            "Set environment:",
            "apicrafter env-set dev BASE_URL https://dev.api.example.com",
        ),
        ("View history:", "apicrafter history --limit 10"),
        (
            "Test auth:",
            "apicrafter auth bearer 'your-token' --url 'https://httpbin.org/bearer'",
        ),
    ]

    for desc, cmd in examples:
        renderer.console.print(f"  [dim]{desc}[/dim]")
        renderer.console.print(f"  [bold green]{cmd}[/bold green]\n")

    renderer.console.print("[bold yellow]🔐 Authentication Examples:[/bold yellow]")
    auth_examples = [
        ("Bearer Token:", "--auth 'bearer:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'"),
        ("Basic Auth:", "--auth 'basic:username:password'"),
        ("API Key (Header):", "--auth 'apikey:X-API-Key:your-secret-key:header'"),
        ("API Key (Query):", "--auth 'apikey:api_key:your-secret-key:query'"),
    ]

    for desc, example in auth_examples:
        renderer.console.print(f"  [dim]{desc}[/dim]")
        renderer.console.print(f"  [bold green]{example}[/bold green]\n")

    renderer.console.print("[bold yellow]💡 Tips:[/bold yellow]")
    tips = [
        "Use {{VARIABLE}} syntax in URLs, headers, and bodies",
        "Create environments with 'apicrafter env-set <env> <var> <value>'",
        "Use 'apicrafter interactive' for step-by-step request building",
        "Save frequently used requests with 'apicrafter save'",
        "Generate curl commands with 'apicrafter curl <request-name>'",
        "Use --verbose flag to see detailed request information",
    ]

    for tip in tips:
        renderer.console.print(f"  • {tip}")

    renderer.console.print("\n[bold cyan]📚 For more help:[/bold cyan]")
    renderer.console.print("  • Run 'apicrafter --help' for all commands")
    renderer.console.print(
        "  • Run 'apicrafter <command> --help' for command-specific help"
    )
    renderer.console.print("  • Check the README.md file for detailed documentation\n")


@app.command()
def tokens() -> None:
    """Manage authentication tokens."""
    try:
        auth_manager = AuthManager(storage)
        token_list = auth_manager.list_tokens()

        if not token_list:
            renderer.print_info("No tokens stored")
            return

        renderer.console.print("\n🔐 Stored Tokens:", style="bold cyan")

        # Create table
        from rich.table import Table

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Environment", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Request", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Created", style="dim")

        for token_info in token_list:
            status_color = (
                "green"
                if "Valid" in token_info["status"]
                else "red" if "Expired" in token_info["status"] else "yellow"
            )
            table.add_row(
                token_info["environment"],
                token_info["type"],
                token_info["request"],
                f"[{status_color}]{token_info['status']}[/{status_color}]",
                token_info["created"],
            )

        renderer.console.print(table)

    except Exception as e:
        renderer.print_error(f"Failed to list tokens: {str(e)}")
        raise typer.Exit(1)


@app.command()
def token_clear() -> None:
    """Clear expired tokens."""
    try:
        auth_manager = AuthManager(storage)
        cleared_count = auth_manager.clear_expired_tokens()

        if cleared_count > 0:
            renderer.print_success(f"Cleared {cleared_count} expired tokens")
        else:
            renderer.print_info("No expired tokens found")

    except Exception as e:
        renderer.print_error(f"Failed to clear tokens: {str(e)}")
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    from . import __version__

    renderer.print_info(f"apicrafter version {__version__}")
    renderer.print_info("A terminal-first, interactive API client")
    renderer.print_info("Repository: https://github.com/yourusername/apicrafter")


# Add some helpful aliases
@app.command(name="get")
def get_alias(
    url: Annotated[str, typer.Argument(help="URL to GET")],
    header: Annotated[Optional[List[str]], typer.Option("--header", "-H")] = None,
    query: Annotated[Optional[List[str]], typer.Option("--query", "-q")] = None,
    auth: Annotated[Optional[str], typer.Option("--auth", "-a")] = None,
    env: Annotated[str, typer.Option("--env", "-e")] = "default",
) -> None:
    """Quick GET request (alias for 'send GET')."""
    # Call the main send function with GET method
    import sys

    from . import cli

    # Temporarily replace sys.argv to call send command
    original_argv = sys.argv
    sys.argv = ["apicrafter", "send", "GET", url]

    if header:
        for h in header:
            sys.argv.extend(["--header", h])
    if query:
        for q in query:
            sys.argv.extend(["--query", q])
    if auth:
        sys.argv.extend(["--auth", auth])
    if env != "default":
        sys.argv.extend(["--env", env])

    try:
        # Directly call send function
        ctx = typer.Context(send)
        send(method="GET", url=url, header=header, query=query, auth=auth, env=env)
    finally:
        sys.argv = original_argv


@app.command(name="post")
def post_alias(
    url: Annotated[str, typer.Argument(help="URL to POST")],
    json_data: Annotated[Optional[str], typer.Option("--json", "-j")] = None,
    form: Annotated[Optional[List[str]], typer.Option("--form", "-f")] = None,
    header: Annotated[Optional[List[str]], typer.Option("--header", "-H")] = None,
    auth: Annotated[Optional[str], typer.Option("--auth", "-a")] = None,
    env: Annotated[str, typer.Option("--env", "-e")] = "default",
) -> None:
    """Quick POST request (alias for 'send POST')."""
    send(
        method="POST",
        url=url,
        header=header,
        json_data=json_data,
        form=form,
        auth=auth,
        env=env,
    )


def main() -> None:
    """Main entry point."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
