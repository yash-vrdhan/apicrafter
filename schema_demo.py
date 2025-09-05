#!/usr/bin/env python3
"""
Schema-Driven API Client Demo
Demonstrates the new schema-driven features of apicrafter.
"""

import json
import tempfile
from pathlib import Path

def create_sample_openapi_schema():
    """Create a sample OpenAPI schema for demonstration."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "User Management API",
            "version": "1.2.0",
            "description": "A comprehensive API for managing users and their data"
        },
        "servers": [
            {"url": "https://api.userservice.com", "description": "Production server"},
            {"url": "https://dev-api.userservice.com", "description": "Development server"}
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                },
                "apiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                }
            },
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "example": 123},
                        "username": {"type": "string", "minLength": 3, "maxLength": 50},
                        "email": {"type": "string", "format": "email"},
                        "age": {"type": "integer", "minimum": 0, "maximum": 150},
                        "active": {"type": "boolean", "default": True},
                        "role": {"type": "string", "enum": ["user", "admin", "moderator"]},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "profile": {
                            "type": "object",
                            "properties": {
                                "firstName": {"type": "string"},
                                "lastName": {"type": "string"},
                                "bio": {"type": "string", "maxLength": 500}
                            }
                        }
                    },
                    "required": ["username", "email"]
                }
            }
        },
        "paths": {
            "/users": {
                "get": {
                    "summary": "List all users",
                    "description": "Retrieve a paginated list of users with optional filtering",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "description": "Page number for pagination",
                            "schema": {"type": "integer", "default": 1, "minimum": 1}
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "description": "Number of users per page",
                            "schema": {"type": "integer", "default": 10, "minimum": 1, "maximum": 100}
                        },
                        {
                            "name": "role",
                            "in": "query",
                            "description": "Filter by user role",
                            "schema": {"type": "string", "enum": ["user", "admin", "moderator"]}
                        },
                        {
                            "name": "active",
                            "in": "query",
                            "description": "Filter by active status",
                            "schema": {"type": "boolean"}
                        },
                        {
                            "name": "Authorization",
                            "in": "header",
                            "required": True,
                            "description": "Bearer token for authentication",
                            "schema": {"type": "string", "example": "Bearer eyJhbGciOiJIUzI1NiI..."}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of users",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "users": {"type": "array", "items": {"$ref": "#/components/schemas/User"}},
                                            "total": {"type": "integer"},
                                            "page": {"type": "integer"},
                                            "limit": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create a new user",
                    "description": "Create a new user account with the provided information",
                    "security": [{"apiKeyAuth": []}],
                    "parameters": [
                        {
                            "name": "X-API-Key",
                            "in": "header",
                            "required": True,
                            "description": "API key for authentication",
                            "schema": {"type": "string", "example": "ak_live_123456789abcdef"}
                        },
                        {
                            "name": "Content-Type",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string", "enum": ["application/json"]}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"},
                                "example": {
                                    "username": "johndoe",
                                    "email": "john@example.com",
                                    "age": 30,
                                    "role": "user",
                                    "profile": {
                                        "firstName": "John",
                                        "lastName": "Doe",
                                        "bio": "Software developer with 5 years of experience"
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                }
            },
            "/users/{id}": {
                "get": {
                    "summary": "Get user by ID",
                    "description": "Retrieve a specific user by their unique identifier",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "description": "User ID",
                            "schema": {"type": "integer", "example": 123}
                        },
                        {
                            "name": "Authorization",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "User details",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "404": {
                            "description": "User not found"
                        }
                    }
                },
                "put": {
                    "summary": "Update user",
                    "description": "Update an existing user's information",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        },
                        {
                            "name": "Authorization",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "User updated successfully"},
                        "404": {"description": "User not found"}
                    }
                },
                "delete": {
                    "summary": "Delete user",
                    "description": "Remove a user from the system",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        },
                        {
                            "name": "Authorization",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "204": {"description": "User deleted successfully"},
                        "404": {"description": "User not found"}
                    }
                }
            },
            "/health": {
                "get": {
                    "summary": "Health check",
                    "description": "Check if the API is running and healthy",
                    "responses": {
                        "200": {
                            "description": "API is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "healthy"},
                                            "timestamp": {"type": "string", "format": "date-time"},
                                            "version": {"type": "string", "example": "1.2.0"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

def demo_schema_loading():
    """Demonstrate schema loading functionality."""
    print("\n📋 SCHEMA LOADING DEMO")
    print("=" * 60)
    
    try:
        from apicrafter.schema_loader import SchemaLoader
        
        loader = SchemaLoader()
        
        # Create a temporary schema file
        schema_data = create_sample_openapi_schema()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema_data, f, indent=2)
            schema_file = f.name
        
        print(f"✅ Created temporary schema file: {schema_file}")
        
        # Load schema from file
        api_schema = loader.load_schema_from_file(schema_file)
        
        if api_schema:
            print(f"✅ Schema loaded successfully!")
            print(f"   Title: {api_schema.title}")
            print(f"   Version: {api_schema.version}")
            print(f"   Base URL: {api_schema.base_url}")
            print(f"   Endpoints: {len(api_schema.endpoints)}")
            
            # Show summary
            summary = loader.get_schema_summary(api_schema)
            print(f"   Methods: {summary['methods']}")
            
            # List all endpoints
            print("\n🔗 Available Endpoints:")
            for method, path in loader.list_endpoints(api_schema):
                endpoint = loader.get_endpoint_schema(api_schema, method, path)
                desc = f" - {endpoint.summary}" if endpoint.summary else ""
                print(f"   {method.ljust(7)} {path}{desc}")
            
            # Show detailed endpoint info
            print("\n🔍 Detailed Endpoint Example (POST /users):")
            post_users = loader.get_endpoint_schema(api_schema, "POST", "/users")
            if post_users:
                print(f"   Summary: {post_users.summary}")
                print(f"   Description: {post_users.description}")
                print(f"   Required headers: {[h for h, d in post_users.headers.items() if d.get('required')]}")
                print(f"   Body schema type: {post_users.body_schema.get('type') if post_users.body_schema else 'None'}")
                if post_users.body_schema and post_users.body_schema.get('properties'):
                    required = post_users.body_schema.get('required', [])
                    print(f"   Required body fields: {required}")
        
        # Clean up
        Path(schema_file).unlink()
        
    except ImportError as e:
        print(f"❌ Could not import schema loader: {e}")
        print("💡 Install dependencies to see full demo")

def demo_field_prompting():
    """Demonstrate field prompting functionality."""
    print("\n📝 FIELD PROMPTING DEMO")
    print("=" * 60)
    
    try:
        from apicrafter.field_prompter import FieldPrompter
        
        prompter = FieldPrompter()
        
        # Sample schemas for demonstration
        headers_schema = {
            "Authorization": {
                "type": "string",
                "required": True,
                "description": "Bearer token for authentication",
                "example": "Bearer eyJhbGciOiJIUzI1NiI..."
            },
            "Content-Type": {
                "type": "string",
                "enum": ["application/json", "application/xml"],
                "default": "application/json",
                "description": "Content type of the request"
            },
            "X-Request-ID": {
                "type": "string",
                "description": "Unique identifier for request tracing"
            }
        }
        
        query_schema = {
            "page": {
                "type": "integer",
                "default": 1,
                "minimum": 1,
                "description": "Page number for pagination"
            },
            "limit": {
                "type": "integer",
                "default": 10,
                "minimum": 1,
                "maximum": 100,
                "description": "Number of items per page"
            },
            "role": {
                "type": "string",
                "enum": ["user", "admin", "moderator"],
                "description": "Filter by user role"
            }
        }
        
        body_schema = {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50,
                    "description": "Unique username for the account"
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "User's email address"
                },
                "age": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 150,
                    "description": "User's age in years"
                },
                "active": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether the user account is active"
                },
                "role": {
                    "type": "string",
                    "enum": ["user", "admin", "moderator"],
                    "default": "user",
                    "description": "User's role in the system"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags associated with the user"
                },
                "profile": {
                    "type": "object",
                    "properties": {
                        "firstName": {"type": "string"},
                        "lastName": {"type": "string"},
                        "bio": {"type": "string", "maxLength": 500}
                    },
                    "description": "User profile information"
                }
            },
            "required": ["username", "email"]
        }
        
        print("✅ Field prompter loaded successfully!")
        print("\n🔧 Schema structures prepared:")
        print(f"   Headers: {list(headers_schema.keys())}")
        print(f"   Query params: {list(query_schema.keys())}")
        print(f"   Body properties: {list(body_schema.get('properties', {}).keys())}")
        print(f"   Required body fields: {body_schema.get('required', [])}")
        
        print("\n💡 In interactive mode, these would generate:")
        print("   • Dynamic prompts based on field types")
        print("   • Validation based on schema constraints")
        print("   • Default values from schema")
        print("   • Enum choices as dropdown menus")
        print("   • Required field validation")
        print("   • Nested object prompting")
        
    except ImportError as e:
        print(f"❌ Could not import field prompter: {e}")

def demo_validation():
    """Demonstrate request validation functionality."""
    print("\n✅ VALIDATION DEMO")
    print("=" * 60)
    
    try:
        from apicrafter.validator import RequestValidator
        from apicrafter.schema_loader import SchemaEndpoint
        
        validator = RequestValidator()
        
        # Create sample endpoint for validation
        endpoint = SchemaEndpoint(
            method="POST",
            path="/users",
            summary="Create a new user",
            headers={
                "Authorization": {"type": "string", "required": True},
                "Content-Type": {"type": "string", "enum": ["application/json"], "required": True}
            },
            query_params={
                "validate": {"type": "boolean", "default": False}
            },
            body_schema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "minLength": 3, "maxLength": 50},
                    "email": {"type": "string", "pattern": r"^[^@]+@[^@]+\.[^@]+$"},
                    "age": {"type": "integer", "minimum": 0, "maximum": 150},
                    "role": {"type": "string", "enum": ["user", "admin", "moderator"]}
                },
                "required": ["username", "email"]
            }
        )
        
        print("✅ Validation engine loaded successfully!")
        print(f"   Endpoint: {endpoint.method} {endpoint.path}")
        print(f"   Required headers: {[h for h, d in endpoint.headers.items() if d.get('required')]}")
        print(f"   Required body fields: {endpoint.body_schema.get('required', [])}")
        
        # Test cases
        test_cases = [
            {
                "name": "Valid Request",
                "headers": {"Authorization": "Bearer token123", "Content-Type": "application/json"},
                "query_params": {"validate": "true"},
                "body": {"username": "johndoe", "email": "john@example.com", "age": 25, "role": "user"},
                "expected": "valid"
            },
            {
                "name": "Missing Required Header",
                "headers": {"Content-Type": "application/json"},
                "body": {"username": "johndoe", "email": "john@example.com"},
                "expected": "invalid"
            },
            {
                "name": "Invalid Email Format",
                "headers": {"Authorization": "Bearer token123", "Content-Type": "application/json"},
                "body": {"username": "johndoe", "email": "invalid-email", "age": 25},
                "expected": "invalid"
            },
            {
                "name": "Username Too Short",
                "headers": {"Authorization": "Bearer token123", "Content-Type": "application/json"},
                "body": {"username": "jo", "email": "john@example.com"},
                "expected": "invalid"
            },
            {
                "name": "Invalid Enum Value",
                "headers": {"Authorization": "Bearer token123", "Content-Type": "application/json"},
                "body": {"username": "johndoe", "email": "john@example.com", "role": "superuser"},
                "expected": "invalid"
            }
        ]
        
        print("\n🔧 Validation Test Cases:")
        for test_case in test_cases:
            result = validator.validate_request(
                endpoint=endpoint,
                headers=test_case.get("headers", {}),
                query_params=test_case.get("query_params", {}),
                body=test_case.get("body"),
                method="POST"
            )
            
            status = "✅ PASS" if result.is_valid else "❌ FAIL"
            print(f"   {test_case['name']}: {status}")
            
            if not result.is_valid:
                print(f"      Errors: {len(result.errors)}")
                for error in result.errors[:2]:  # Show first 2 errors
                    print(f"        • {error.field}: {error.message}")
            
            if result.warnings:
                print(f"      Warnings: {len(result.warnings)}")
        
    except ImportError as e:
        print(f"❌ Could not import validator: {e}")

def demo_cli_commands():
    """Show CLI command examples for schema-driven features."""
    print("\n🖥️  CLI COMMANDS DEMO")
    print("=" * 60)
    
    print("🚀 Schema Management Commands:")
    schema_commands = [
        ("Load schema from URL", "apicrafter schema load https://api.example.com"),
        ("Load schema from file", "apicrafter schema load ./openapi.json"),
        ("Show all endpoints", "apicrafter schema show https://api.example.com"),
        ("Show specific endpoint", "apicrafter schema show https://api.example.com --endpoint 'GET /users'"),
    ]
    
    for desc, cmd in schema_commands:
        print(f"  {desc}:")
        print(f"    {cmd}")
        print()
    
    print("🔍 Validation Commands:")
    validation_commands = [
        ("Validate with schema URL", "apicrafter send POST /users --json '{\"name\":\"John\"}' --validate https://api.example.com"),
        ("Validate with schema file", "apicrafter send POST /users --json '{\"name\":\"John\"}' --validate ./schema.json"),
        ("Validate saved request", "apicrafter run create-user --validate https://api.example.com"),
    ]
    
    for desc, cmd in validation_commands:
        print(f"  {desc}:")
        print(f"    {cmd}")
        print()
    
    print("🎯 Interactive Schema Mode:")
    interactive_commands = [
        ("Schema-driven interactive", "apicrafter interactive"),
        ("Then choose: 'Use schema-driven mode'", "-> Select schema source (URL or file)"),
        ("Auto-generated prompts", "-> Prompts generated from OpenAPI spec"),
        ("Built-in validation", "-> Request validated before sending"),
    ]
    
    for desc, note in interactive_commands:
        print(f"  {desc}:")
        print(f"    {note}")
        print()

def demo_workflow():
    """Show a complete workflow example."""
    print("\n🔄 COMPLETE WORKFLOW DEMO")
    print("=" * 60)
    
    print("📋 Step-by-step schema-driven API testing:")
    
    workflow_steps = [
        ("1. Load API Schema", [
            "apicrafter schema load https://api.userservice.com",
            "# Loads OpenAPI spec and caches locally",
            "# Shows available endpoints and methods"
        ]),
        
        ("2. Explore Endpoints", [
            "apicrafter schema show https://api.userservice.com",
            "# Lists all available endpoints",
            "# GET /users, POST /users, GET /users/{id}, etc."
        ]),
        
        ("3. View Endpoint Details", [
            "apicrafter schema show https://api.userservice.com --endpoint 'POST /users'",
            "# Shows required headers, query params, body schema",
            "# Displays validation rules and examples"
        ]),
        
        ("4. Interactive Request Building", [
            "apicrafter interactive",
            "# Choose 'Use schema-driven mode'",
            "# Select schema source",
            "# Pick endpoint from list",
            "# Auto-generated prompts based on schema"
        ]),
        
        ("5. Schema Validation", [
            "# Request automatically validated against schema",
            "# Shows errors for missing required fields",
            "# Provides suggestions and examples"
        ]),
        
        ("6. CLI with Validation", [
            "apicrafter send POST https://api.userservice.com/users \\",
            "  --json '{\"username\": \"johndoe\", \"email\": \"john@example.com\"}' \\",
            "  --auth 'bearer:your-token' \\",
            "  --validate https://api.userservice.com"
        ]),
        
        ("7. Save and Reuse", [
            "# Save validated requests to collections",
            "# Run with different environments",
            "# Validate saved requests before execution"
        ])
    ]
    
    for step_title, commands in workflow_steps:
        print(f"\n{step_title}:")
        for cmd in commands:
            if cmd.startswith("#"):
                print(f"    {cmd}")
            else:
                print(f"  $ {cmd}")

def main():
    """Run the complete schema-driven demo."""
    print("🛠️  APICRAFTER SCHEMA-DRIVEN DEMO")
    print("=" * 80)
    print("🚀 Demonstrates the new schema-driven features!")
    print("   • OpenAPI schema loading and parsing")
    print("   • Dynamic field prompting based on schemas")
    print("   • Request validation against schemas")
    print("   • Interactive schema-driven mode")
    print("   • CLI validation flags")
    print("=" * 80)
    
    demo_schema_loading()
    demo_field_prompting()
    demo_validation()
    demo_cli_commands()
    demo_workflow()
    
    print("\n🎉 SCHEMA-DRIVEN FEATURES SUMMARY")
    print("=" * 80)
    
    features = [
        "📋 Schema Loading: OpenAPI 3.0 support from URLs and files",
        "🔍 Schema Parsing: Comprehensive endpoint and component extraction",
        "📝 Dynamic Prompting: Auto-generated forms based on schema definitions",
        "✅ Request Validation: Real-time validation against schema constraints",
        "🎯 Interactive Mode: Schema-driven request building with guided prompts",
        "🖥️  CLI Integration: Validation flags for all send/run commands",
        "💾 Schema Caching: Local caching for improved performance",
        "🔄 Auto-defaults: Automatic application of schema default values",
        "🎨 Rich UI: Beautiful validation results and error messages",
        "🛠️  Developer Tools: Schema exploration and endpoint documentation"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\n🚀 READY TO USE!")
    print("=" * 80)
    print("All schema-driven features are implemented and ready for production:")
    print("  • Install dependencies: pip install -r requirements.txt")
    print("  • Install package: pip install -e .")
    print("  • Try schema mode: apicrafter interactive")
    print("  • Validate requests: apicrafter send --validate <schema>")
    print("  • Explore schemas: apicrafter schema show <url>")
    
    print("\n📚 Perfect for:")
    use_cases = [
        "API-first development workflows",
        "Contract testing and validation",
        "Interactive API exploration",
        "Documentation-driven development",
        "Quality assurance and testing",
        "Developer onboarding and training"
    ]
    
    for use_case in use_cases:
        print(f"  • {use_case}")

if __name__ == "__main__":
    main()
