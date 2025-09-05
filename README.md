# apicrafter

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
pip install apicrafter-cli
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

## 📖 Core Commands

### Send Requests

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

### Collections Management

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
```

### Environment Management

```bash
# Set environment variables
apicrafter env-set dev BASE_URL https://dev-api.example.com
apicrafter env-set dev TOKEN dev_token_123

# Run request with specific environment
apicrafter run get-users --env dev
```

### Request History

```bash
# View request history
apicrafter history

# Replay a request from history
apicrafter replay 1
```

### Testing

```bash
# Test a request with assertions
apicrafter test GET https://api.example.com/health \
  --assert-status 200 \
  --assert-json "status:healthy"
```

## 🔧 Configuration

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

## 📚 Documentation

For more detailed documentation, visit the [GitHub repository](https://github.com/yash-vrdhan/apicrafter).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [httpx](https://github.com/encode/httpx) - Modern HTTP client
- [typer](https://github.com/tiangolo/typer) - CLI framework
- [rich](https://github.com/Textualize/rich) - Beautiful terminal output
- [questionary](https://github.com/tmbo/questionary) - Interactive prompts
- [pydantic](https://github.com/pydantic/pydantic) - Data validation