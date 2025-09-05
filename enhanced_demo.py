#!/usr/bin/env python3
"""
Enhanced demo script showcasing all apicrafter features.
This demonstrates the new authentication, body handling, and CLI enhancements.
"""

import json
import tempfile
from pathlib import Path

def demo_auth_features():
    """Demonstrate authentication features."""
    print("\n🔐 AUTHENTICATION FEATURES")
    print("=" * 60)
    
    try:
        from apicrafter.auth import AuthHandler, AuthType, AuthConfig
        
        print("✅ Authentication module loaded successfully!")
        
        # Demo different auth types
        auth_examples = [
            ("Bearer Token", "bearer:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"),
            ("Basic Auth", "basic:username:password123"),
            ("API Key (Header)", "apikey:X-API-Key:secret123:header"),
            ("API Key (Query)", "apikey:api_key:secret456:query")
        ]
        
        print("\n🔧 Parsing Authentication Strings:")
        for desc, auth_string in auth_examples:
            config = AuthHandler.parse_auth_string(auth_string)
            if config:
                print(f"  ✅ {desc}")
                print(f"     Input: {auth_string}")
                print(f"     Type: {config.auth_type}")
                print(f"     Credentials: {config.credentials}")
                if hasattr(config, 'location') and config.location:
                    print(f"     Location: {config.location}")
                print()
        
        # Demo applying auth
        print("🔧 Applying Authentication:")
        headers = {"Content-Type": "application/json"}
        params = {}
        
        bearer_config = AuthConfig(
            auth_type=AuthType.BEARER,
            credentials={"token": "test-token-123"}
        )
        
        updated_headers, updated_params = AuthHandler.apply_auth(bearer_config, headers.copy(), params.copy())
        print(f"  Bearer Auth Applied:")
        print(f"    Headers: {updated_headers}")
        print()
        
    except ImportError as e:
        print(f"❌ Could not import auth module: {e}")
        print("💡 Run 'pip install -r requirements.txt' to install dependencies")

def demo_body_features():
    """Demonstrate body handling features."""
    print("\n📄 BODY HANDLING FEATURES")
    print("=" * 60)
    
    try:
        from apicrafter.body import BodyHandler, BodyType, BodyConfig
        
        print("✅ Body handling module loaded successfully!")
        
        # Demo JSON body
        print("\n🔧 JSON Body Handling:")
        json_config = BodyConfig(
            body_type=BodyType.JSON,
            content={"name": "John Doe", "age": 30, "active": True, "scores": [85, 92, 78]}
        )
        
        body_str, json_data, headers = BodyHandler.prepare_body(json_config)
        print(f"  JSON Config: {json_config.content}")
        print(f"  Prepared JSON: {json_data}")
        print(f"  Headers Added: {headers}")
        print()
        
        # Demo form data
        print("🔧 Form Data Handling:")
        form_config = BodyConfig(
            body_type=BodyType.FORM_DATA,
            content={"username": "johndoe", "email": "john@example.com", "subscribe": "true"}
        )
        
        body_str, json_data, headers = BodyHandler.prepare_body(form_config)
        print(f"  Form Config: {form_config.content}")
        print(f"  Prepared Body: {body_str}")
        print(f"  Headers Added: {headers}")
        print()
        
        # Demo CLI parsing
        print("🔧 CLI Body Parsing:")
        cli_examples = [
            ('{"name": "Alice", "role": "admin"}', None, None, "JSON"),
            (None, ["name=Bob", "role=user", "active=true"], None, "Form Data"),
            (None, None, "Plain text content here", "Raw Text")
        ]
        
        for json_str, form_list, raw_str, desc in cli_examples:
            config = BodyHandler.parse_body_from_cli(json_str, form_list, raw_str)
            if config:
                print(f"  {desc} Parsing:")
                print(f"    Type: {config.body_type}")
                print(f"    Content: {config.content}")
                print()
        
    except ImportError as e:
        print(f"❌ Could not import body module: {e}")
        print("💡 Run 'pip install -r requirements.txt' to install dependencies")

def demo_cli_commands():
    """Demonstrate CLI command examples."""
    print("\n🖥️  CLI COMMANDS SHOWCASE")
    print("=" * 60)
    
    print("🚀 Basic Commands:")
    basic_commands = [
        ("Simple GET", "apicrafter send GET https://httpbin.org/json"),
        ("GET with auth", "apicrafter send GET https://httpbin.org/bearer --auth 'bearer:your-token'"),
        ("POST with JSON", "apicrafter send POST https://httpbin.org/post --json '{\"name\": \"John\"}'"),
        ("POST with form", "apicrafter send POST https://httpbin.org/post --form 'name=John' --form 'age=30'"),
        ("With headers", "apicrafter send GET https://httpbin.org/headers --header 'User-Agent: apicrafter/1.0'"),
        ("With query params", "apicrafter send GET https://httpbin.org/get --query 'page=1' --query 'limit=10'"),
    ]
    
    for desc, cmd in basic_commands:
        print(f"  {desc}:")
        print(f"    {cmd}")
        print()
    
    print("🔐 Authentication Commands:")
    auth_commands = [
        ("Bearer token", "apicrafter send GET https://httpbin.org/bearer --auth 'bearer:eyJhbGciOiJIUzI1NiI...'"),
        ("Basic auth", "apicrafter send GET https://httpbin.org/basic-auth/user/pass --auth 'basic:user:pass'"),
        ("API key header", "apicrafter send GET https://httpbin.org/get --auth 'apikey:X-API-Key:secret123'"),
        ("API key query", "apicrafter send GET https://httpbin.org/get --auth 'apikey:api_key:secret123:query'"),
        ("Test auth", "apicrafter auth bearer 'your-token' --url 'https://httpbin.org/bearer'"),
    ]
    
    for desc, cmd in auth_commands:
        print(f"  {desc}:")
        print(f"    {cmd}")
        print()
    
    print("💾 Collection & Environment Commands:")
    collection_commands = [
        ("Save request", "apicrafter save login --method POST --url 'https://api.example.com/auth'"),
        ("Run saved request", "apicrafter run login --env production"),
        ("Set environment", "apicrafter env-set dev BASE_URL https://dev.api.example.com"),
        ("Set API key", "apicrafter env-set prod API_KEY your-production-key"),
        ("List collections", "apicrafter collections"),
        ("List environments", "apicrafter environments"),
    ]
    
    for desc, cmd in collection_commands:
        print(f"  {desc}:")
        print(f"    {cmd}")
        print()
    
    print("🛠️  Utility Commands:")
    utility_commands = [
        ("Interactive mode", "apicrafter interactive"),
        ("View history", "apicrafter history --limit 10"),
        ("Replay request", "apicrafter replay 5"),
        ("Generate curl", "apicrafter curl login --env prod"),
        ("Inspect headers", "apicrafter headers https://httpbin.org/get"),
        ("Show documentation", "apicrafter docs"),
        ("Quick GET", "apicrafter get https://httpbin.org/json"),
        ("Quick POST", "apicrafter post https://httpbin.org/post --json '{\"test\": true}'"),
    ]
    
    for desc, cmd in utility_commands:
        print(f"  {desc}:")
        print(f"    {cmd}")
        print()

def demo_environment_features():
    """Demonstrate environment and variable features."""
    print("\n🌍 ENVIRONMENT & VARIABLES")
    print("=" * 60)
    
    try:
        from apicrafter.storage import StorageManager, Environment
        
        # Create temporary storage
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(Path(temp_dir))
            
            print("✅ Storage system loaded successfully!")
            
            # Create demo environments
            environments = {
                "development": Environment(
                    name="development",
                    variables={
                        "BASE_URL": "https://dev-api.example.com",
                        "API_KEY": "dev-key-123",
                        "USER_ID": "test-user",
                        "TIMEOUT": "30"
                    }
                ),
                "staging": Environment(
                    name="staging",
                    variables={
                        "BASE_URL": "https://staging-api.example.com",
                        "API_KEY": "staging-key-456",
                        "USER_ID": "staging-user",
                        "TIMEOUT": "60"
                    }
                ),
                "production": Environment(
                    name="production",
                    variables={
                        "BASE_URL": "https://api.example.com",
                        "API_KEY": "{{PROD_API_KEY}}",  # Nested variable
                        "USER_ID": "{{PROD_USER_ID}}",
                        "TIMEOUT": "120"
                    }
                )
            }
            
            # Save environments
            for env in environments.values():
                storage.save_environment(env)
            
            print("\n🔧 Environment Variable Resolution:")
            test_strings = [
                "{{BASE_URL}}/users/{{USER_ID}}",
                "Authorization: Bearer {{API_KEY}}",
                "timeout={{TIMEOUT}}&user={{USER_ID}}",
                "https://{{BASE_URL}}/api/v1/data?key={{API_KEY}}"
            ]
            
            for env_name in ["development", "staging"]:
                print(f"\n  Environment: {env_name}")
                for test_string in test_strings:
                    resolved = storage.resolve_variables(test_string, env_name)
                    print(f"    Original:  {test_string}")
                    print(f"    Resolved:  {resolved}")
                    print()
            
            # Demo nested variables (production env)
            print("  Environment: production (with nested variables)")
            for test_string in test_strings[:2]:  # Just first two to show concept
                resolved = storage.resolve_variables(test_string, "production")
                print(f"    Original:  {test_string}")
                print(f"    Resolved:  {resolved}")
                print(f"    Note: {{PROD_API_KEY}} and {{PROD_USER_ID}} would need to be set")
                print()
                
    except ImportError as e:
        print(f"❌ Could not import storage module: {e}")
        print("💡 Run 'pip install -r requirements.txt' to install dependencies")

def demo_testing_features():
    """Demonstrate testing and assertion features."""
    print("\n🧪 TESTING & ASSERTIONS")
    print("=" * 60)
    
    print("✅ Testing framework integrated into HTTP client!")
    
    print("\n🔧 Available Test Assertions:")
    assertions = [
        ("status_code", "Expected HTTP status code", "200, 201, 404, etc."),
        ("body_contains", "Text that should be in response body", "\"success\", \"error\", \"token\""),
        ("body_equals", "Exact response body match", "\"OK\", \"{\\\"status\\\": \\\"ok\\\"}\""),
        ("json_field", "JSON field value checks (dot notation)", "{\"user.name\": \"John\", \"status\": \"active\"}"),
        ("max_response_time", "Maximum response time in seconds", "2.0, 5.0, 10.0"),
        ("headers", "Expected header values", "{\"Content-Type\": \"application/json\"}")
    ]
    
    for name, desc, example in assertions:
        print(f"  {name}:")
        print(f"    Description: {desc}")
        print(f"    Example: {example}")
        print()
    
    print("🔧 Test Configuration Example (YAML):")
    test_config = """
tests:
  api_health:
    status_code: 200
    body_contains: "healthy"
    max_response_time: 2.0
    json_field:
      status: "ok"
      version: "1.0"
    headers:
      Content-Type: "application/json"
  
  user_login:
    status_code: 200
    body_contains: "token"
    json_field:
      success: true
      user.role: "user"
    max_response_time: 5.0
"""
    
    print(test_config)
    
    print("🔧 Running Tests:")
    test_commands = [
        "apicrafter test api_health --tests tests.yaml",
        "apicrafter test user_login --collection auth --env staging",
        "apicrafter test all_endpoints --tests api_tests.yaml --env production"
    ]
    
    for cmd in test_commands:
        print(f"  {cmd}")
    print()

def main():
    """Run the enhanced demo."""
    print("🛠️  APICRAFTER ENHANCED DEMO")
    print("=" * 80)
    print("🚀 A terminal-first, interactive API client with advanced features!")
    print("=" * 80)
    
    demo_auth_features()
    demo_body_features()
    demo_environment_features()
    demo_testing_features()
    demo_cli_commands()
    
    print("\n🎯 NEW FEATURES SUMMARY")
    print("=" * 60)
    
    features = [
        "🔐 Comprehensive Authentication (Bearer, Basic, API Key)",
        "📄 Advanced Body Handling (JSON, Form, Raw, Binary)",
        "🌍 Enhanced Environment System with Variable Resolution",
        "🖥️  Extended CLI with New Commands and Aliases",
        "🧪 Improved Testing Framework with Multiple Assertions",
        "🛠️  Utility Commands (curl generation, header inspection)",
        "📚 Interactive Documentation and Examples",
        "⚡ Performance Optimizations and Better Error Handling"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\n🚀 GETTING STARTED")
    print("=" * 60)
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Install package: pip install -e .")
    print("3. Try the new features:")
    print("   • apicrafter docs                    # Show documentation")
    print("   • apicrafter interactive             # Interactive mode")
    print("   • apicrafter get https://httpbin.org/json  # Quick GET")
    print("   • apicrafter auth bearer 'token'     # Test authentication")
    print("   • apicrafter send POST https://httpbin.org/post --json '{\"test\": true}'")
    
    print("\n📦 READY FOR PRODUCTION!")
    print("=" * 60)
    print("All features are implemented and tested. Ready for:")
    print("  • PyPI publication")
    print("  • pipx installation")
    print("  • Production use")
    print("  • Community contributions")

if __name__ == "__main__":
    main()
