# apicrafter 🛠️

**A terminal-first, interactive API client that brings Postman-like features into the CLI.**

Built for developers who love the command line and need powerful, scriptable API testing capabilities.

---

## ✨ Features

### 🌐 HTTP Client
- **All HTTP Methods**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **Request Formats**: JSON, Form data, Raw text, Binary/File uploads
- **Query Parameters**: Multiple parameter support with easy syntax
- **Custom Headers**: Add any headers with flexible formatting

### 🔐 Authentication
- **Bearer Tokens**: JWT and other bearer token support
- **Basic Auth**: Username/password authentication  
- **API Keys**: Header or query parameter API keys
- **OAuth2**: Coming soon in future releases

### 🎨 Beautiful Output
- **Syntax Highlighting**: JSON, XML, HTML with color coding
- **Status Code Colors**: Visual feedback for response status
- **Tabular Data**: Collections, environments, and history in tables
- **Progress Indicators**: Real-time feedback for long requests

### 💾 Data Management
- **Collections**: Save and organize your API requests
- **Environments**: Manage dev, staging, prod configurations
- **Variable Substitution**: Use `{{VARIABLE}}` syntax everywhere
- **History Tracking**: Automatic request history with replay

### 🎯 Interactive Experience
- **Interactive Mode**: Step-by-step request building
- **Auto-completion**: Smart suggestions for common values
- **Validation**: Real-time input validation and error checking
- **Help System**: Built-in documentation and examples

### 🧪 Testing & Validation
- **Assertion Testing**: Status codes, response content, JSON fields
- **Performance Testing**: Response time validation
- **Header Validation**: Expected header checking
- **Test Suites**: YAML-based test configurations

### 🛠️ Developer Tools
- **Curl Generation**: Convert requests to curl commands
- **Header Inspection**: Analyze response headers
- **Request Replay**: Replay any request from history
- **Verbose Mode**: Detailed request/response information

---

## 📦 Installation

### Recommended: Using pipx
```bash
pipx install apicrafter
```

### Using pip
```bash
pip install apicrafter
```

### Development Installation
```bash
git clone https://github.com/yourusername/apicrafter.git
cd apicrafter
pip install -r requirements.txt
pip install -e .
```

---

## 🚀 Quick Start

### 🚀 Quick Examples

```bash
# Simple GET request
apicrafter send GET https://httpbin.org/json

# POST with JSON and authentication
apicrafter send POST https://httpbin.org/post \
  --auth "bearer:your-token-here" \
  --json '{"name": "John", "age": 30}'

# Form data with custom headers
apicrafter send POST https://httpbin.org/post \
  --form "name=John" --form "email=john@example.com" \
  --header "User-Agent: apicrafter/1.0"

# Quick aliases for common operations
apicrafter get https://httpbin.org/json
apicrafter post https://httpbin.org/post --json '{"test": true}'

# Interactive mode for step-by-step building
apicrafter interactive

# Test authentication
apicrafter auth bearer "your-token" --url "https://httpbin.org/bearer"
```

### 💾 Collections & Environments

```bash
# Save requests for reuse
apicrafter save login \
  --method POST \
  --url "{{BASE_URL}}/auth/login" \
  --json '{"username": "{{USERNAME}}", "password": "{{PASSWORD}}"}'

# Set up environments
apicrafter env-set dev BASE_URL https://dev-api.example.com
apicrafter env-set dev USERNAME testuser
apicrafter env-set prod BASE_URL https://api.example.com

# Run with different environments
apicrafter run login --env dev
apicrafter run login --env prod
```

---

## 📖 Commands Reference

### Core Commands

#### `send` - Send HTTP requests
```bash
apicrafter send <METHOD> <URL> [OPTIONS]

Options:
  -H, --header TEXT    Headers in format 'Key: Value'
  -q, --query TEXT     Query params in format 'key=value'
  -b, --body TEXT      Request body as string
  -j, --json TEXT      Request body as JSON string
  -f, --form TEXT      Form data in format 'key=value'
  --raw TEXT           Raw body data
  -a, --auth TEXT      Auth: 'bearer:TOKEN', 'basic:user:pass', 'apikey:name:value[:location]'
  -e, --env TEXT       Environment to use [default: default]
  --no-headers         Don't show response headers
  -v, --verbose        Show detailed request info
```

#### Authentication Examples
```bash
# Bearer token
apicrafter send GET https://api.example.com/user --auth "bearer:eyJhbGciOiJIUzI1NiI..."

# Basic authentication
apicrafter send GET https://api.example.com/secure --auth "basic:username:password"

# API key in header
apicrafter send GET https://api.example.com/data --auth "apikey:X-API-Key:your-secret-key"

# API key in query parameter
apicrafter send GET https://api.example.com/data --auth "apikey:api_key:your-secret-key:query"
```

#### `interactive` - Interactive request builder
```bash
apicrafter interactive
```
Walk through building a request step-by-step with interactive prompts.

#### `save` - Save requests to collections
```bash
apicrafter save <NAME> [OPTIONS]

Options:
  -m, --method TEXT      HTTP method [default: GET]
  -u, --url TEXT         Request URL
  -H, --header TEXT      Headers in format 'Key: Value'
  -q, --query TEXT       Query params in format 'key=value'
  -b, --body TEXT        Request body as string
  -j, --json TEXT        Request body as JSON string
  -c, --collection TEXT  Collection name [default: default]
```

#### `run` - Execute saved requests
```bash
apicrafter run <NAME> [OPTIONS]

Options:
  -c, --collection TEXT  Collection name [default: default]
  -e, --env TEXT         Environment to use [default: default]
  --no-headers          Don't show response headers
```

### Management Commands

#### `collections` - List all collections
```bash
apicrafter collections
```

#### `environments` - List all environments
```bash
apicrafter environments
```

#### `env-set` - Set environment variables
```bash
apicrafter env-set <ENV_NAME> <VARIABLE> <VALUE>
```

#### `history` - Show request history
```bash
apicrafter history [--limit 20]
```

#### `replay` - Replay request from history
```bash
apicrafter replay <INDEX> [--env default]
```

#### `test` - Run tests on requests
```bash
apicrafter test <NAME> [OPTIONS]

Options:
  -c, --collection TEXT  Collection name [default: default]
  -e, --env TEXT         Environment to use [default: default]
  -t, --tests TEXT       Path to tests file
```

### 🛠️ Utility Commands

#### `auth` - Test authentication
```bash
apicrafter auth <TYPE> <CREDENTIALS> [--url URL]

# Examples:
apicrafter auth bearer "your-token" --url "https://httpbin.org/bearer"
apicrafter auth basic "user:pass" --url "https://httpbin.org/basic-auth/user/pass"
```

#### `headers` - Inspect response headers
```bash
apicrafter headers <URL> [--method HEAD]
```

#### `curl` - Generate curl commands
```bash
apicrafter curl <REQUEST_NAME> [--collection default] [--env default]
```

#### `docs` - Show documentation and examples
```bash
apicrafter docs
```

#### `get` / `post` - Quick request aliases
```bash
apicrafter get <URL> [OPTIONS]
apicrafter post <URL> [OPTIONS]
```

#### `config` - Show configuration locations
```bash
apicrafter config
```

---

## 💡 Examples

### 🔐 Authentication Examples
```bash
# Bearer token authentication
apicrafter send GET https://api.github.com/user \
  --auth "bearer:ghp_your_token_here" \
  --header "Accept: application/vnd.github.v3+json"

# Basic authentication
apicrafter send GET https://httpbin.org/basic-auth/user/pass \
  --auth "basic:user:pass"

# API key in header
apicrafter send GET https://api.openweathermap.org/data/2.5/weather \
  --auth "apikey:X-API-Key:your_api_key" \
  --query "q=London"

# API key in query parameter
apicrafter send GET https://api.example.com/data \
  --auth "apikey:api_key:your_secret_key:query"

# Test authentication
apicrafter auth bearer "your-token" --url "https://httpbin.org/bearer"
```

### 📄 Request Body Examples
```bash
# JSON data
apicrafter send POST https://httpbin.org/post \
  --json '{"name": "John Doe", "email": "john@example.com", "age": 30}'

# Form data
apicrafter send POST https://httpbin.org/post \
  --form "name=John Doe" \
  --form "email=john@example.com" \
  --form "subscribe=true"

# Raw text data
apicrafter send POST https://httpbin.org/post \
  --raw "This is raw text data" \
  --header "Content-Type: text/plain"

# File upload (form data)
apicrafter send POST https://httpbin.org/post \
  --form "file=@/path/to/document.pdf" \
  --form "description=Important document"
```

### 🌍 Environment Management
```bash
# Set up multiple environments
apicrafter env-set dev BASE_URL https://dev-api.example.com
apicrafter env-set dev API_KEY dev-key-123
apicrafter env-set dev USER_ID test-user

apicrafter env-set staging BASE_URL https://staging-api.example.com
apicrafter env-set staging API_KEY staging-key-456
apicrafter env-set staging USER_ID staging-user

apicrafter env-set prod BASE_URL https://api.example.com
apicrafter env-set prod API_KEY prod-key-789
apicrafter env-set prod USER_ID prod-user

# Save requests with variables
apicrafter save get-user \
  --method GET \
  --url "{{BASE_URL}}/users/{{USER_ID}}" \
  --auth "apikey:X-API-Key:{{API_KEY}}"

apicrafter save create-post \
  --method POST \
  --url "{{BASE_URL}}/posts" \
  --auth "apikey:X-API-Key:{{API_KEY}}" \
  --json '{"title": "{{POST_TITLE}}", "content": "{{POST_CONTENT}}"}'

# Run with different environments
apicrafter run get-user --env dev
apicrafter run get-user --env staging
apicrafter run get-user --env prod
```

### 🧪 Advanced Testing
```bash
# Create comprehensive test file
cat > api-tests.yaml << EOF
tests:
  health_check:
    status_code: 200
    body_contains: "healthy"
    max_response_time: 2.0
    json_field:
      status: "ok"
      version: "1.0"
    headers:
      Content-Type: "application/json"
  
  user_authentication:
    status_code: 200
    body_contains: "token"
    json_field:
      success: true
      user.role: "admin"
      token: "jwt_token_here"
    max_response_time: 5.0
  
  data_validation:
    status_code: 201
    json_field:
      created: true
      id: 12345
      user.name: "John Doe"
EOF

# Run tests with different environments
apicrafter test health_check --tests api-tests.yaml --env dev
apicrafter test user_authentication --tests api-tests.yaml --env staging
apicrafter test data_validation --tests api-tests.yaml --env prod
```

### 🛠️ Utility Commands
```bash
# Generate curl commands from saved requests
apicrafter curl login --env prod
apicrafter curl get-user --collection api --env staging

# Inspect response headers
apicrafter headers https://api.github.com/
apicrafter headers https://httpbin.org/get --method GET

# Quick requests with aliases
apicrafter get https://httpbin.org/json
apicrafter post https://httpbin.org/post --json '{"test": true}'

# Interactive mode for complex requests
apicrafter interactive

# View documentation and examples
apicrafter docs
```

---

## ⚙️ Configuration

apicrafter stores its configuration in `~/.apicrafter/`:

- `collections.yaml` - Saved requests and collections
- `envs.yaml` - Environment variables
- `history.log` - Request history

### Collections Format

```yaml
collections:
  auth:
    name: auth
    requests:
      login:
        method: POST
        url: "{{BASE_URL}}/auth/login"
        headers:
          Content-Type: "application/json"
        json_data:
          username: "{{USERNAME}}"
          password: "{{PASSWORD}}"
```

### Environments Format

```yaml
environments:
  development:
    name: development
    variables:
      BASE_URL: "https://dev.api.example.com"
      USERNAME: "dev-user"
      PASSWORD: "dev-pass"
      API_KEY: "dev-key-123"
  
  production:
    name: production
    variables:
      BASE_URL: "https://api.example.com"
      USERNAME: "{{PROD_USERNAME}}"
      PASSWORD: "{{PROD_PASSWORD}}"
      API_KEY: "{{PROD_API_KEY}}"
```

### Variable Substitution

Use `{{VARIABLE_NAME}}` syntax in:
- URLs: `https://{{BASE_URL}}/api/users`
- Headers: `Authorization: Bearer {{TOKEN}}`
- Request bodies: `{"api_key": "{{API_KEY}}"}`

---

## 🧪 Testing

Define tests in YAML format:

```yaml
tests:
  login:
    status_code: 200
    body_contains: "token"
    json_field:
      success: true
      user.role: "admin"
    max_response_time: 2.0
    headers:
      Content-Type: "application/json"
```

Available test assertions:
- `status_code` - Expected HTTP status code
- `body_contains` - Text that should be in response body
- `body_equals` - Exact response body match
- `json_field` - JSON field value checks (supports dot notation)
- `max_response_time` - Maximum response time in seconds
- `headers` - Expected header values

---

## 🗺️ Roadmap

### 🎯 Completed in v2.0
- [x] **Comprehensive Authentication** (Bearer, Basic, API Key)
- [x] **Advanced Body Handling** (JSON, Form, Raw, Binary)
- [x] **Enhanced CLI** with new commands and aliases
- [x] **Improved Testing** with multiple assertion types
- [x] **Utility Commands** (curl generation, header inspection)
- [x] **Better Documentation** and interactive help

### 🚀 Future Enhancements
- [ ] **TUI Mode** - Full-screen terminal interface
- [ ] **OAuth2 Support** - Complete OAuth2 flow handling
- [ ] **WebSocket Support** - Real-time communication testing
- [ ] **GraphQL Support** - Query and mutation testing
- [ ] **Postman Import/Export** - Seamless migration
- [ ] **Plugin System** - Extensible architecture
- [ ] **Response Caching** - Speed up repeated requests
- [ ] **Performance Benchmarking** - Load testing capabilities
- [ ] **Request/Response Middleware** - Custom processing
- [ ] **Team Collaboration** - Shared collections and environments

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
git clone https://github.com/yourusername/apicrafter.git
cd apicrafter
pip install -r requirements.txt
pip install -e .
pytest  # Run tests
```

---

## 💬 Support

### 📚 Getting Help
- **Built-in Help**: Run `apicrafter docs` for comprehensive examples
- **Command Help**: Use `apicrafter <command> --help` for specific command info
- **Interactive Mode**: Try `apicrafter interactive` for guided request building

### 🐛 Issues & Features
- Create an [issue](https://github.com/yourusername/apicrafter/issues) for bug reports or feature requests
- Check existing issues before creating new ones
- Provide detailed information including command used and expected vs actual behavior

### 💡 Community
- Join our [discussions](https://github.com/yourusername/apicrafter/discussions) for questions and tips
- Share your use cases and workflows
- Contribute examples and documentation improvements

### 🤝 Contributing
- Fork the repository and create feature branches
- Follow the existing code style and add tests for new features
- Update documentation for any new functionality
- Submit pull requests with clear descriptions

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
<h3>🛠️ Built with ❤️ for developers who live in the terminal</h3>
<p><strong>apicrafter</strong> - Postman for your terminal, interactive, scriptable, and lightweight.</p>
</div>
