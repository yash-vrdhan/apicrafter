#!/usr/bin/env python3
"""
Demo script showing apicrafter functionality.
This demonstrates the core features without requiring full installation.
"""

import json
import tempfile
from pathlib import Path

# Mock the dependencies for demo purposes
class MockConsole:
    def print(self, text, **kwargs):
        print(f"[DEMO] {text}")

class MockRenderer:
    def __init__(self):
        self.console = MockConsole()
    
    def print_info(self, message):
        print(f"ℹ️  {message}")
    
    def print_success(self, message):
        print(f"✅ {message}")
    
    def print_error(self, message):
        print(f"❌ {message}")

def demo_storage():
    """Demonstrate storage functionality."""
    print("\n🗄️  STORAGE DEMO")
    print("=" * 50)
    
    # Import our storage classes
    try:
        from apicrafter.storage import StorageManager, RequestData, Environment
        
        # Create temporary storage
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(Path(temp_dir))
            renderer = MockRenderer()
            
            # Demo: Save a request
            request_data = RequestData(
                method="GET",
                url="https://jsonplaceholder.typicode.com/posts/{{POST_ID}}",
                headers={"Accept": "application/json"},
                params={"userId": "{{USER_ID}}"}
            )
            
            storage.save_request("get-post", request_data, "demo-collection")
            renderer.print_success("Saved request 'get-post' to collection 'demo-collection'")
            
            # Demo: Create environment
            env = Environment(
                name="demo",
                variables={
                    "POST_ID": "1",
                    "USER_ID": "123",
                    "BASE_URL": "https://jsonplaceholder.typicode.com"
                }
            )
            storage.save_environment(env)
            renderer.print_success("Created environment 'demo' with variables")
            
            # Demo: Variable resolution
            test_url = "{{BASE_URL}}/posts/{{POST_ID}}"
            resolved_url = storage.resolve_variables(test_url, "demo")
            print(f"🔄 Variable resolution:")
            print(f"   Original: {test_url}")
            print(f"   Resolved: {resolved_url}")
            
            # Demo: Load saved request
            loaded_request = storage.load_request("get-post", "demo-collection")
            if loaded_request:
                renderer.print_success("Successfully loaded saved request")
                print(f"   Method: {loaded_request.method}")
                print(f"   URL: {loaded_request.url}")
                print(f"   Headers: {loaded_request.headers}")
            
            # Demo: List collections
            collections = storage.load_collections()
            print(f"\n📚 Collections found: {list(collections.keys())}")
            
            # Demo: List environments
            environments = storage.load_environments()
            print(f"🌍 Environments found: {list(environments.keys())}")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Run 'pip install -r requirements.txt' to install dependencies")

def demo_cli_structure():
    """Show the CLI command structure."""
    print("\n🖥️  CLI COMMANDS DEMO")
    print("=" * 50)
    
    commands = {
        "send": "Send HTTP requests directly",
        "interactive": "Interactive request builder",
        "save": "Save requests to collections", 
        "run": "Execute saved requests",
        "collections": "List all collections",
        "environments": "List all environments",
        "env-set": "Set environment variables",
        "history": "Show request history",
        "replay": "Replay request from history",
        "test": "Run tests on requests",
        "config": "Show configuration locations",
        "version": "Show version information"
    }
    
    print("Available commands:")
    for cmd, desc in commands.items():
        print(f"  📌 apicrafter {cmd:<12} - {desc}")
    
    print("\n💡 Example usage:")
    examples = [
        "apicrafter send GET https://jsonplaceholder.typicode.com/posts/1",
        "apicrafter interactive",
        "apicrafter save login --method POST --url 'https://api.example.com/auth'",
        "apicrafter run login --env production",
        "apicrafter env-set dev BASE_URL https://dev.api.example.com",
        "apicrafter history --limit 10"
    ]
    
    for example in examples:
        print(f"  🚀 {example}")

def demo_features():
    """Showcase key features."""
    print("\n✨ KEY FEATURES DEMO")
    print("=" * 50)
    
    features = [
        "🌐 HTTP Methods: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS",
        "📝 Request Formats: JSON, Form data, Raw text, Custom headers",
        "🎨 Pretty Output: Syntax highlighting for JSON, XML, HTML",
        "💾 Collections: Organize and save your API requests",
        "🌍 Environments: Manage dev/staging/prod configurations",
        "🔄 Variables: Use {{VARIABLE}} syntax for dynamic values",
        "📚 History: Track all requests with timestamps and response times",
        "🧪 Testing: Basic assertions for status codes, response content",
        "🎯 Interactive: Firebase CLI-style menus and prompts",
        "⚡ Performance: Built on httpx for fast, async-capable requests"
    ]
    
    for feature in features:
        print(f"  {feature}")

def demo_file_structure():
    """Show the project file structure."""
    print("\n📁 PROJECT STRUCTURE")
    print("=" * 50)
    
    structure = """
apicrafter/
├── __init__.py          # Package initialization
├── cli.py              # Main CLI application (Typer)
├── http_client.py      # HTTP client wrapper (httpx)
├── storage.py          # Collections/environments/history
├── interactive.py      # Interactive prompts (questionary)
├── renderer.py         # Pretty output formatting (rich)
└── tests/              # Test suite
    ├── __init__.py
    ├── test_storage.py
    └── test_http_client.py

Configuration files:
~/.apicrafter/
├── collections.yaml    # Saved requests and collections
├── envs.yaml          # Environment variables
└── history.log        # Request history
    """
    
    print(structure)

def main():
    """Run the demo."""
    print("🛠️  APICRAFTER DEMO")
    print("=" * 60)
    print("A terminal-first, interactive API client")
    print("Bringing Postman-like features to the CLI!")
    print("=" * 60)
    
    demo_features()
    demo_cli_structure()
    demo_file_structure()
    demo_storage()
    
    print("\n🚀 GETTING STARTED")
    print("=" * 50)
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Install package: pip install -e .")
    print("3. Run: apicrafter --help")
    print("4. Try: apicrafter send GET https://httpbin.org/json")
    print("5. Interactive: apicrafter interactive")
    
    print("\n📦 INSTALLATION")
    print("=" * 50)
    print("When ready for production:")
    print("  pipx install apicrafter  # (after publishing to PyPI)")
    print("  # or")
    print("  pip install apicrafter")

if __name__ == "__main__":
    main()
