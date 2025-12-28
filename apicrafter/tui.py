from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import (
    Header,
    Footer,
    Static,
    ListView,
    ListItem,
    Label,
    Pretty,
    TabbedContent,
    TabPane,
)
import json
import httpx

from textual.worker import run_worker

from .storage import StorageManager, RequestData
from .http_client import APIClient, ResponseData


class CollectionList(ListView):
    """A widget to display a list of collections."""


class RequestList(ListView):
    """A widget to display a list of requests in a collection."""


class RequestDetail(Static):
    """A widget to display the details of a request."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.request_data: RequestData | None = None

    def update_request(self, request_data: RequestData):
        self.request_data = request_data
        self.update()

    def render(self):
        if not self.request_data:
            return "Select a request to view details."

        headers = "\n".join(
            f"  {k}: {v}" for k, v in self.request_data.headers.items()
        )
        return f"""
[bold]Method:[/bold] {self.request_data.method}
[bold]URL:[/bold] {self.request_data.url}
[bold]Headers:[/bold]
{headers}
[bold]Body:[/bold]
"""


class ResponseView(Static):
    """A widget to display the API response."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.response_data = None

    def update_response(self, response_data):
        self.response_data = response_data
        self.update()

    def render(self):
        if not self.response_data:
            return "No response yet."

        headers = "\n".join(
            f"  {k}: {v}" for k, v in self.response_data.headers.items()
        )
        return f"""
[bold]Status:[/bold] {self.response_data.status_code}
[bold]Headers:[/bold]
{headers}
"""


class ApiCrafterTUI(App):
    """A Textual-based TUI for ApiCrafter."""

    CSS_PATH = "tui.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("right", "focus_next", "Focus Next"),
        ("left", "focus_previous", "Focus Previous"),
        ("enter", "send_request", "Send Request"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = StorageManager()
        self.collections = self.storage.load_collections()
        self.current_collection = None
        self.current_request = None

    def action_send_request(self) -> None:
        """Sends the selected API request."""
        if self.current_request:
            run_worker(self.send_request_worker, thread=True)

    async def send_request_worker(self) -> None:
        """Worker to send the request and update the UI."""
        try:
            with APIClient() as client:
                response = client.send_from_request_data(self.current_request)

                def update_ui():
                    self.query_one(ResponseView).update_response(response)
                    response_body = self.query_one("#response-body")
                    try:
                        data = json.loads(response.text)
                        response_body.update(data)
                    except json.JSONDecodeError:
                        response_body.update(response.text)

                self.call_from_thread(update_ui)
        except httpx.RequestError as e:
            error_text = f"Request failed: {self.current_request.method} {self.current_request.url}\n\n{e}"
            error_response = ResponseData(
                status_code=0,
                headers={},
                content=error_text.encode(),
                text=error_text,
                response_time=0,
                url=self.current_request.url,
                method=self.current_request.method,
            )

            def update_error_ui():
                self.query_one(ResponseView).update_response(error_response)
                self.query_one("#response-body").update(error_text)

            self.call_from_thread(update_error_ui)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Container(id="main-container"):
            with Vertical(id="left-pane"):
                yield CollectionList(id="collections")
                yield RequestList(id="requests")
            with TabbedContent(id="right-pane"):
                with TabPane("Request", id="request-pane"):
                    yield RequestDetail(id="request-detail")
                    yield Pretty("", id="request-body")
                with TabPane("Response", id="response-pane"):
                    yield ResponseView(id="response-view")
                    yield Pretty("", id="response-body")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        collection_list = self.query_one(CollectionList)
        for collection_name in self.collections.keys():
            collection_list.append(ListItem(Label(collection_name)))
        self.query_one(CollectionList).focus()

    def on_focus(self, event: App.Focus) -> None:
        """Called when a widget is focused."""
        for list_view in self.query(ListView):
            list_view.remove_class("focused")
        if isinstance(self.focused, ListView):
            self.focused.add_class("focused")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Called when a list item is selected."""
        if isinstance(event.list_view, CollectionList):
            self.current_collection = event.item.children[0].renderable
            requests = self.collections.get(self.current_collection, {})
            request_list = self.query_one(RequestList)
            request_list.clear()
            for request_name in requests.keys():
                request_list.append(ListItem(Label(request_name)))
        elif isinstance(event.list_view, RequestList):
            request_name = event.item.children[0].renderable
            self.current_request = self.storage.load_request(
                request_name, self.current_collection
            )
            if self.current_request:
                self.query_one(RequestDetail).update_request(self.current_request)
                self.query_one("#request-body").update(self.current_request.body or "")


if __name__ == "__main__":
    app = ApiCrafterTUI()
    app.run()
