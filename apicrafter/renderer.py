"""Response rendering and pretty printing using Rich."""

import json
import xml.dom.minidom
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .http_client import ResponseData
from .storage import HistoryEntry


class ResponseRenderer:
    """Renders HTTP responses with pretty formatting."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize the renderer."""
        self.console = console or Console()

    def render_response(
        self, response: ResponseData, show_headers: bool = True
    ) -> None:
        """
        Render a complete HTTP response.

        Args:
            response: ResponseData object to render
            show_headers: Whether to show response headers
        """
        # Status line
        status_color = self._get_status_color(response.status_code)
        status_text = Text()
        status_text.append(f"{response.method} ", style="bold cyan")
        status_text.append(f"{response.url}\n", style="dim")
        status_text.append(
            f"Status: {response.status_code}", style=f"bold {status_color}"
        )
        status_text.append(f" • Time: {response.response_time:.3f}s", style="dim")

        self.console.print(
            Panel(status_text, title="Request Info", border_style=status_color)
        )

        # Headers
        if show_headers and response.headers:
            self.render_headers(response.headers)

        # Body
        if response.text or response.content:
            self.render_body(response)

    def render_headers(self, headers: Dict[str, str]) -> None:
        """Render response headers in a table."""
        table = Table(
            title="Response Headers", show_header=True, header_style="bold magenta"
        )
        table.add_column("Header", style="cyan")
        table.add_column("Value", style="white")

        for name, value in headers.items():
            table.add_row(name, value)

        self.console.print(table)
        self.console.print()

    def render_body(self, response: ResponseData) -> None:
        """Render response body with appropriate syntax highlighting."""
        if not response.text:
            self.console.print("[dim]Empty response body[/dim]")
            return

        content_type = response.headers.get("content-type", "").lower()

        # Try to render as JSON first if it's JSON data
        if response.json_data is not None:
            self._render_json(response.json_data)
        # HTML content
        elif "text/html" in content_type:
            self._render_html(response.text)
        # XML content
        elif "xml" in content_type or response.text.strip().startswith("<?xml"):
            self._render_xml(response.text)
        # Plain text or unknown
        else:
            self._render_text(response.text, content_type)

    def _render_json(self, json_data: Any) -> None:
        """Render JSON data with syntax highlighting."""
        try:
            json_obj = JSON.from_data(json_data)
            self.console.print(
                Panel(json_obj, title="Response Body (JSON)", border_style="green")
            )
        except Exception:
            # Fallback to regular text
            json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
            self.console.print(
                Panel(syntax, title="Response Body (JSON)", border_style="green")
            )

    def _render_html(self, html_content: str) -> None:
        """Render HTML content with syntax highlighting."""
        try:
            # Try to format HTML nicely (basic formatting)
            syntax = Syntax(
                html_content,
                "html",
                theme="monokai",
                line_numbers=False,
                word_wrap=True,
            )
            self.console.print(
                Panel(syntax, title="Response Body (HTML)", border_style="blue")
            )
        except Exception:
            self.console.print(
                Panel(html_content, title="Response Body (HTML)", border_style="blue")
            )

    def _render_xml(self, xml_content: str) -> None:
        """Render XML content with syntax highlighting and formatting."""
        try:
            # Try to pretty print XML
            dom = xml.dom.minidom.parseString(xml_content)
            pretty_xml = dom.toprettyxml(indent="  ")
            # Remove extra empty lines
            lines = [line for line in pretty_xml.split("\n") if line.strip()]
            formatted_xml = "\n".join(lines)

            syntax = Syntax(formatted_xml, "xml", theme="monokai", line_numbers=False)
            self.console.print(
                Panel(syntax, title="Response Body (XML)", border_style="yellow")
            )
        except Exception:
            # Fallback to regular text with XML syntax highlighting
            syntax = Syntax(xml_content, "xml", theme="monokai", line_numbers=False)
            self.console.print(
                Panel(syntax, title="Response Body (XML)", border_style="yellow")
            )

    def _render_text(self, text_content: str, content_type: str) -> None:
        """Render plain text content."""
        # Try to detect language for syntax highlighting
        lexer = self._detect_lexer(content_type, text_content)

        if lexer:
            try:
                syntax = Syntax(
                    text_content,
                    lexer,
                    theme="monokai",
                    line_numbers=False,
                    word_wrap=True,
                )
                self.console.print(
                    Panel(
                        syntax,
                        title=f"Response Body ({lexer.upper()})",
                        border_style="white",
                    )
                )
                return
            except Exception:
                pass

        # Fallback to plain text
        self.console.print(
            Panel(text_content, title="Response Body (Text)", border_style="white")
        )

    def _detect_lexer(self, content_type: str, content: str) -> Optional[str]:
        """Detect appropriate lexer for syntax highlighting."""
        # Check content type first
        if "javascript" in content_type or "application/json" in content_type:
            return "javascript"
        elif "python" in content_type:
            return "python"
        elif "css" in content_type:
            return "css"
        elif "yaml" in content_type:
            return "yaml"

        # Try to detect from content
        content_lower = content.lower().strip()
        if content_lower.startswith(("#!/usr/bin/python", "#!/usr/bin/env python")):
            return "python"
        elif content_lower.startswith("#!/bin/bash") or content_lower.startswith(
            "#!/bin/sh"
        ):
            return "bash"

        return None

    def _get_status_color(self, status_code: int) -> str:
        """Get color for HTTP status code."""
        if 200 <= status_code < 300:
            return "green"
        elif 300 <= status_code < 400:
            return "yellow"
        elif 400 <= status_code < 500:
            return "red"
        elif 500 <= status_code < 600:
            return "bright_red"
        else:
            return "white"

    def render_history(
        self, history: List[HistoryEntry], limit: Optional[int] = None
    ) -> None:
        """Render request history in a table."""
        if not history:
            self.console.print("[dim]No request history found[/dim]")
            return

        table = Table(
            title="Request History", show_header=True, header_style="bold magenta"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Method", style="cyan", width=8)
        table.add_column("URL", style="white")
        table.add_column("Status", style="white", width=8)
        table.add_column("Time", style="dim", width=8)
        table.add_column("Timestamp", style="dim", width=20)

        entries_to_show = history[-limit:] if limit else history

        for i, entry in enumerate(entries_to_show, 1):
            status_str = str(entry.status_code) if entry.status_code else "Error"
            status_color = self._get_status_color(entry.status_code or 0)
            time_str = f"{entry.response_time:.3f}s" if entry.response_time else "N/A"
            timestamp_str = entry.timestamp.strftime("%m/%d %H:%M:%S")

            table.add_row(
                str(i),
                entry.method,
                entry.url,
                f"[{status_color}]{status_str}[/{status_color}]",
                time_str,
                timestamp_str,
            )

        self.console.print(table)

    def render_collections(self, collections: Dict[str, Any]) -> None:
        """Render available collections and requests."""
        if not collections:
            self.console.print("[dim]No collections found[/dim]")
            return

        for coll_name, collection in collections.items():
            # Collection header
            self.console.print(f"\n[bold cyan]Collection: {coll_name}[/bold cyan]")
            if hasattr(collection, "description") and collection.description:
                self.console.print(f"[dim]{collection.description}[/dim]")

            # Requests table
            if hasattr(collection, "requests") and collection.requests:
                table = Table(show_header=True, header_style="bold magenta", box=None)
                table.add_column("Request", style="white")
                table.add_column("Method", style="cyan", width=8)
                table.add_column("URL", style="dim")

                for req_name, request in collection.requests.items():
                    table.add_row(req_name, request.method, request.url)

                self.console.print(table)
            else:
                self.console.print("[dim]  No requests in this collection[/dim]")

    def render_environments(self, environments: Dict[str, Any]) -> None:
        """Render available environments."""
        if not environments:
            self.console.print("[dim]No environments found[/dim]")
            return

        for env_name, env in environments.items():
            self.console.print(f"\n[bold green]Environment: {env_name}[/bold green]")

            if hasattr(env, "variables") and env.variables:
                table = Table(show_header=True, header_style="bold magenta", box=None)
                table.add_column("Variable", style="cyan")
                table.add_column("Value", style="white")

                for var_name, var_value in env.variables.items():
                    # Mask sensitive values
                    display_value = var_value
                    if any(
                        sensitive in var_name.lower()
                        for sensitive in ["password", "secret", "key", "token"]
                    ):
                        display_value = "*" * len(var_value) if var_value else ""

                    table.add_row(var_name, display_value)

                self.console.print(table)
            else:
                self.console.print("[dim]  No variables in this environment[/dim]")

    def render_test_results(
        self, test_name: str, results: Dict[str, bool], all_passed: bool
    ) -> None:
        """Render test results."""
        status_color = "green" if all_passed else "red"
        status_text = "PASSED" if all_passed else "FAILED"

        self.console.print(
            f"\n[bold {status_color}]Test '{test_name}': {status_text}[/bold {status_color}]"
        )

        if results:
            table = Table(show_header=True, header_style="bold magenta", box=None)
            table.add_column("Assertion", style="white")
            table.add_column("Result", style="white", width=10)

            for assertion, passed in results.items():
                result_color = "green" if passed else "red"
                result_text = "✓ PASS" if passed else "✗ FAIL"
                table.add_row(
                    assertion, f"[{result_color}]{result_text}[/{result_color}]"
                )

            self.console.print(table)

    def print_error(self, message: str) -> None:
        """Print an error message."""
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def print_success(self, message: str) -> None:
        """Print a success message."""
        self.console.print(f"[bold green]Success:[/bold green] {message}")

    def print_info(self, message: str) -> None:
        """Print an info message."""
        self.console.print(f"[bold blue]Info:[/bold blue] {message}")
