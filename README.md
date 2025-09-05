# 🛠️ apicrafter

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A terminal-first, interactive API client that brings Postman-like features into the CLI. Built with modern Python tooling and designed for developers who prefer the command line.

## ✨ Features

- 🌐 **Full HTTP Support** - GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- 📝 **Multiple Request Formats** - JSON, Form data, Raw text, Custom headers
- 🎨 **Beautiful Output** - Syntax highlighting for JSON, XML, HTML responses
- 💾 **Collections** - Save and organize your API requests
- 🌍 **Environments** - Manage dev/staging/prod configurations with variables
- 🔄 **Variable Substitution** - Use `{{VARIABLE}}` syntax for dynamic values
- 📚 **Request History** - Track all requests with timestamps and response times
- 🧪 **Basic Testing** - Assertions for status codes, response content, and more
- 🎯 **Interactive Mode** - Firebase CLI-style menus and prompts
- ⚡ **High Performance** - Built on httpx for fast, async-capable requests

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/apicrafter.git
cd apicrafter

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Verify installation
apicrafter --help
```

### Basic Usage

```bash
# Send a simple GET request
apicrafter send GET https://jsonplaceholder.typicode.com/posts/1

# Send a POST request with JSON data
apicrafter send POST https://httpbin.org/post \
  --header "Content-Type: application/json" \
  --data '{"title": "Hello", "body": "World"}'

# Interactive mode for guided request building
apicrafter interactive
```

## 📖 Documentation

### Core Commands

#### Send Requests
```bash
# Basic request
apicrafter send GET https://api.example.com/users

# With headers
apicrafter send POST https://api.example.com/users \
  --header "Authorization: Bearer token123" \
  --header "Content-Type: application/json"

# With JSON data
apicrafter send POST https://api.example.com/users \
  --data '{"name": "John", "email": "john@example.com"}'

# With form data
apicrafter send POST https://api.example.com/login \
  --form username=john \
  --form password=secret

# With query parameters
apicrafter send GET https://api.example.com/users \
  --param page=1 \
  --param limit=10
```

#### Collections Management
```bash
# Save a request to a collection
apicrafter save get-users \
  --method GET \
  --url "https://api.example.com/users" \
  --header "Authorization: Bearer {{TOKEN}}"

# Run a saved request
apicrafter run get-users

# List all collections
apicrafter collections

# List requests in a collection
apicrafter collections get-users
```

#### Environment Management
```bash
# Set environment variables
apicrafter env-set dev BASE_URL https://dev-api.example.com
apicrafter env-set dev TOKEN dev_token_123

apicrafter env-set prod BASE_URL https://api.example.com
apicrafter env-set prod TOKEN prod_token_456

# List environments
apicrafter environments

# Run request with specific environment
apicrafter run get-users --env dev
```

#### Request History
```bash
# View request history
apicrafter history

# View last 10 requests
apicrafter history --limit 10

# Replay a request from history
apicrafter replay 1

# Replay with different environment
apicrafter replay 1 --env prod
```

#### Testing
```bash
# Test a request with assertions
apicrafter test GET https://api.example.com/health \
  --assert-status 200 \
  --assert-json "status:healthy"

# Test saved request
apicrafter test get-users --assert-status 200
```

### Interactive Mode

The interactive mode provides a guided experience for building requests:

```bash
apicrafter interactive
```

This will present you with:
- Step-by-step request building
- Collection and environment management
- Request saving and organization
- History browsing and replay

### Configuration

apicrafter stores its configuration in `~/.apicrafter/`:

```
~/.apicrafter/
├── collections.yaml    # Saved requests and collections
├── envs.yaml          # Environment variables
└── history.log        # Request history
```

### Environment Variables

Use the `{{VARIABLE}}` syntax in your requests for dynamic values:

```yaml
# In collections.yaml
- name: get-user
  method: GET
  url: "{{BASE_URL}}/users/{{USER_ID}}"
  headers:
    Authorization: "Bearer {{TOKEN}}"
```

```yaml
# In envs.yaml
dev:
  BASE_URL: "https://dev-api.example.com"
  TOKEN: "dev_token_123"
  USER_ID: "1"

prod:
  BASE_URL: "https://api.example.com"
  TOKEN: "prod_token_456"
  USER_ID: "1"
```

## 🏗️ Development

### Project Structure

```
apicrafter/
├── __init__.py              # Package initialization
├── cli.py                   # Main CLI application (Typer)
├── http_client.py          # HTTP client wrapper (httpx)
├── storage.py              # Collections/environments/history
├── interactive.py          # Interactive prompts (questionary)
├── renderer.py             # Pretty output formatting (rich)
├── auth_manager.py         # Authentication management
├── validator.py            # Request validation
├── schema_loader.py        # Schema loading utilities
├── field_prompter.py       # Interactive field prompting
├── body.py                 # Request body handling
└── tests/                  # Test suite
    ├── __init__.py
    ├── test_storage.py
    └── test_http_client.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apicrafter

# Run specific test file
pytest tests/test_storage.py
```

### Code Quality

```bash
# Format code
black apicrafter/

# Sort imports
isort apicrafter/

# Type checking
mypy apicrafter/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [httpx](https://github.com/encode/httpx) - Modern HTTP client
- [typer](https://github.com/tiangolo/typer) - CLI framework
- [rich](https://github.com/Textualize/rich) - Beautiful terminal output
- [questionary](https://github.com/tmbo/questionary) - Interactive prompts
- [pydantic](https://github.com/pydantic/pydantic) - Data validation

## 📊 Roadmap

- [ ] TUI mode with full-screen interface
- [ ] Authentication helpers (JWT, OAuth2)
- [ ] WebSocket support
- [ ] GraphQL support
- [ ] Postman collection import/export
- [ ] Request/response diffing
- [ ] API documentation generation
- [ ] Performance testing and benchmarking

---

**Made with ❤️ for the terminal-loving developer community**
