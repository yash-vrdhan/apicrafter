"""Authorization module for different auth types."""

import base64
from enum import Enum
from typing import Dict, Optional, Tuple

import questionary
from pydantic import BaseModel


class AuthType(str, Enum):
    """Supported authentication types."""

    NONE = "none"
    API_KEY = "apikey"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"  # Future implementation


class AuthConfig(BaseModel):
    """Authentication configuration."""

    auth_type: AuthType
    credentials: Dict[str, str] = {}
    location: str = "header"  # "header" or "query" for API keys


class AuthHandler:
    """Handles different authentication methods."""

    @staticmethod
    def apply_auth(
        auth_config: AuthConfig, headers: Dict[str, str], params: Dict[str, str]
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Apply authentication to request headers/params.

        Args:
            auth_config: Authentication configuration
            headers: Current request headers
            params: Current request parameters

        Returns:
            Tuple of (updated_headers, updated_params)
        """
        if auth_config.auth_type == AuthType.NONE:
            return headers, params

        elif auth_config.auth_type == AuthType.BEARER:
            token = auth_config.credentials.get("token", "")
            headers["Authorization"] = f"Bearer {token}"

        elif auth_config.auth_type == AuthType.BASIC:
            username = auth_config.credentials.get("username", "")
            password = auth_config.credentials.get("password", "")
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"

        elif auth_config.auth_type == AuthType.API_KEY:
            key_name = auth_config.credentials.get("key_name", "")
            key_value = auth_config.credentials.get("key_value", "")

            if auth_config.location == "header":
                headers[key_name] = key_value
            elif auth_config.location == "query":
                params[key_name] = key_value

        return headers, params

    @staticmethod
    def parse_auth_string(auth_string: str) -> Optional[AuthConfig]:
        """
        Parse authentication string from CLI.

        Formats:
        - bearer:TOKEN
        - apikey:KEY_NAME:KEY_VALUE[:location]
        - basic:USERNAME:PASSWORD

        Args:
            auth_string: Authentication string

        Returns:
            AuthConfig object or None if invalid
        """
        if not auth_string:
            return None

        parts = auth_string.split(":", 1)
        if len(parts) < 2:
            return None

        auth_type_str, rest = parts

        try:
            auth_type = AuthType(auth_type_str.lower())
        except ValueError:
            return None

        if auth_type == AuthType.BEARER:
            return AuthConfig(auth_type=auth_type, credentials={"token": rest})

        elif auth_type == AuthType.BASIC:
            if ":" in rest:
                username, password = rest.split(":", 1)
                return AuthConfig(
                    auth_type=auth_type,
                    credentials={"username": username, "password": password},
                )

        elif auth_type == AuthType.API_KEY:
            parts = rest.split(":")
            if len(parts) >= 2:
                key_name, key_value = parts[0], parts[1]
                location = parts[2] if len(parts) > 2 else "header"
                return AuthConfig(
                    auth_type=auth_type,
                    credentials={"key_name": key_name, "key_value": key_value},
                    location=location,
                )

        return None

    @staticmethod
    def interactive_auth_setup() -> Optional[AuthConfig]:
        """
        Interactive authentication setup.

        Returns:
            AuthConfig object or None if no auth selected
        """
        auth_choice = questionary.select(
            "Select Authorization Type:",
            choices=[
                questionary.Choice("None", AuthType.NONE),
                questionary.Choice("API Key", AuthType.API_KEY),
                questionary.Choice("Bearer Token", AuthType.BEARER),
                questionary.Choice("Basic Auth", AuthType.BASIC),
                questionary.Choice("OAuth2 (coming soon)", AuthType.OAUTH2),
            ],
        ).ask()

        if not auth_choice or auth_choice == AuthType.NONE:
            return AuthConfig(auth_type=AuthType.NONE)

        if auth_choice == AuthType.BEARER:
            token = questionary.password("Enter Bearer Token:").ask()
            if token:
                return AuthConfig(
                    auth_type=AuthType.BEARER, credentials={"token": token}
                )

        elif auth_choice == AuthType.BASIC:
            username = questionary.text("Username:").ask()
            password = questionary.password("Password:").ask()
            if username and password:
                return AuthConfig(
                    auth_type=AuthType.BASIC,
                    credentials={"username": username, "password": password},
                )

        elif auth_choice == AuthType.API_KEY:
            key_name = questionary.text(
                "API Key Name (e.g., 'X-API-Key', 'api_key'):"
            ).ask()
            key_value = questionary.password("API Key Value:").ask()

            if key_name and key_value:
                location = questionary.select(
                    "Where to send the API key?",
                    choices=[
                        questionary.Choice("Header", "header"),
                        questionary.Choice("Query Parameter", "query"),
                    ],
                ).ask()

                return AuthConfig(
                    auth_type=AuthType.API_KEY,
                    credentials={"key_name": key_name, "key_value": key_value},
                    location=location or "header",
                )

        elif auth_choice == AuthType.OAUTH2:
            questionary.print(
                "OAuth2 support is coming in a future release!", style="fg:yellow"
            )
            return AuthConfig(auth_type=AuthType.NONE)

        return AuthConfig(auth_type=AuthType.NONE)


class AuthPresets:
    """Common authentication presets."""

    COMMON_API_KEY_NAMES = [
        "X-API-Key",
        "Authorization",
        "api_key",
        "apikey",
        "key",
        "token",
        "access_token",
        "X-Auth-Token",
        "X-Access-Token",
    ]

    @classmethod
    def suggest_api_key_name(cls) -> str:
        """Suggest common API key names."""
        return (
            questionary.autocomplete(
                "API Key Name:",
                choices=cls.COMMON_API_KEY_NAMES,
                validate=lambda x: len(x.strip()) > 0 or "Key name cannot be empty",
            ).ask()
            or "X-API-Key"
        )


def demo_auth_functionality():
    """Demo function to show auth functionality."""
    print("🔐 Authentication Demo")
    print("=" * 50)

    # Demo CLI parsing
    test_cases = [
        "bearer:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "basic:username:password123",
        "apikey:X-API-Key:secret123:header",
        "apikey:api_key:secret456:query",
    ]

    for test in test_cases:
        config = AuthHandler.parse_auth_string(test)
        if config:
            print(f"✅ Parsed: {test}")
            print(f"   Type: {config.auth_type}")
            print(f"   Credentials: {config.credentials}")
            if config.auth_type == AuthType.API_KEY:
                print(f"   Location: {config.location}")
        else:
            print(f"❌ Failed to parse: {test}")
        print()

    # Demo auth application
    headers = {"Content-Type": "application/json"}
    params = {}

    bearer_config = AuthConfig(
        auth_type=AuthType.BEARER, credentials={"token": "test-token-123"}
    )

    updated_headers, updated_params = AuthHandler.apply_auth(
        bearer_config, headers.copy(), params.copy()
    )
    print(f"🔑 Bearer Auth Applied:")
    print(f"   Headers: {updated_headers}")
    print()

    api_key_config = AuthConfig(
        auth_type=AuthType.API_KEY,
        credentials={"key_name": "X-API-Key", "key_value": "secret123"},
        location="header",
    )

    updated_headers, updated_params = AuthHandler.apply_auth(
        api_key_config, headers.copy(), params.copy()
    )
    print(f"🔑 API Key Auth Applied (Header):")
    print(f"   Headers: {updated_headers}")
    print()

    api_key_query_config = AuthConfig(
        auth_type=AuthType.API_KEY,
        credentials={"key_name": "api_key", "key_value": "secret456"},
        location="query",
    )

    updated_headers, updated_params = AuthHandler.apply_auth(
        api_key_query_config, headers.copy(), params.copy()
    )
    print(f"🔑 API Key Auth Applied (Query):")
    print(f"   Params: {updated_params}")


if __name__ == "__main__":
    demo_auth_functionality()
