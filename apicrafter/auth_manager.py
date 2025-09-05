"""Authentication token management with expiration detection."""

import json
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import questionary
from pydantic import BaseModel

from .storage import StorageManager


class TokenInfo(BaseModel):
    """Information about an authentication token."""

    token: str
    token_type: str  # "bearer", "api_key", etc.
    expires_at: Optional[datetime] = None
    created_at: datetime
    environment: str
    request_name: Optional[str] = None
    auto_refresh: bool = False
    refresh_token: Optional[str] = None


class AuthManager:
    """Manages authentication tokens with expiration detection and refresh prompting."""

    def __init__(self, storage: Optional[StorageManager] = None):
        """Initialize auth manager."""
        self.storage = storage or StorageManager()
        self.tokens_file = self.storage.config_dir / "tokens.json"
        self._load_tokens()

    def _load_tokens(self) -> None:
        """Load stored tokens from file."""
        try:
            if self.tokens_file.exists():
                with open(self.tokens_file, "r") as f:
                    self.tokens = json.load(f)
            else:
                self.tokens = {}
        except Exception:
            self.tokens = {}

    def _save_tokens(self) -> None:
        """Save tokens to file."""
        try:
            with open(self.tokens_file, "w") as f:
                json.dump(self.tokens, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save tokens: {e}")

    def store_token(
        self,
        token: str,
        token_type: str,
        environment: str,
        expires_in: Optional[int] = None,
        request_name: Optional[str] = None,
        auto_refresh: bool = False,
        refresh_token: Optional[str] = None,
    ) -> None:
        """
        Store a token with expiration information.

        Args:
            token: The actual token value
            token_type: Type of token (bearer, api_key, etc.)
            environment: Environment name
            expires_in: Expiration time in seconds from now
            request_name: Name of the request this token is for
            auto_refresh: Whether to auto-refresh this token
            refresh_token: Refresh token for OAuth flows
        """
        token_id = f"{environment}_{token_type}_{request_name or 'default'}"

        expires_at = None
        if expires_in:
            expires_at = datetime.now() + timedelta(seconds=expires_in)

        token_info = TokenInfo(
            token=token,
            token_type=token_type,
            expires_at=expires_at,
            created_at=datetime.now(),
            environment=environment,
            request_name=request_name,
            auto_refresh=auto_refresh,
            refresh_token=refresh_token,
        )

        self.tokens[token_id] = token_info.model_dump()
        self._save_tokens()

    def get_token(
        self, environment: str, token_type: str, request_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a token, checking for expiration and prompting for refresh if needed.

        Args:
            environment: Environment name
            token_type: Type of token
            request_name: Name of the request

        Returns:
            Valid token or None if not available
        """
        token_id = f"{environment}_{token_type}_{request_name or 'default'}"

        if token_id not in self.tokens:
            return None

        token_data = self.tokens[token_id]
        token_info = TokenInfo(**token_data)

        # Check if token is expired or about to expire (within 5 minutes)
        if token_info.expires_at:
            time_until_expiry = token_info.expires_at - datetime.now()
            if time_until_expiry.total_seconds() <= 300:  # 5 minutes
                return self._handle_expired_token(
                    token_info, environment, token_type, request_name
                )

        return token_info.token

    def _handle_expired_token(
        self,
        token_info: TokenInfo,
        environment: str,
        token_type: str,
        request_name: Optional[str],
    ) -> Optional[str]:
        """Handle expired or soon-to-expire tokens."""
        time_until_expiry = token_info.expires_at - datetime.now()
        is_expired = time_until_expiry.total_seconds() <= 0

        if is_expired:
            print(f"\n⚠️  Your {token_type} token has expired!")
        else:
            print(
                f"\n⚠️  Your {token_type} token expires in {int(time_until_expiry.total_seconds() / 60)} minutes!"
            )

        print(f"Environment: {environment}")
        if token_info.request_name:
            print(f"Request: {token_info.request_name}")

        # Ask user what to do
        choices = [
            questionary.Choice("Enter new token", "new"),
            questionary.Choice("Skip authentication", "skip"),
            questionary.Choice("Cancel request", "cancel"),
        ]

        if token_info.auto_refresh and token_info.refresh_token:
            choices.insert(0, questionary.Choice("Auto-refresh token", "refresh"))

        action = questionary.select("What would you like to do?", choices=choices).ask()

        if action == "new":
            return self._prompt_for_new_token(environment, token_type, request_name)
        elif action == "refresh" and token_info.refresh_token:
            return self._refresh_token(
                token_info, environment, token_type, request_name
            )
        elif action == "skip":
            return None
        else:  # cancel
            raise KeyboardInterrupt("Request cancelled by user")

    def _prompt_for_new_token(
        self, environment: str, token_type: str, request_name: Optional[str]
    ) -> Optional[str]:
        """Prompt user for a new token."""
        if token_type == "bearer":
            new_token = questionary.password("Enter new Bearer token:").ask()
        elif token_type == "api_key":
            new_token = questionary.password("Enter new API key:").ask()
        else:
            new_token = questionary.password(f"Enter new {token_type} token:").ask()

        if new_token:
            # Ask about expiration
            expires_in = None
            if questionary.confirm(
                "Does this token have an expiration time?", default=False
            ).ask():
                try:
                    hours = questionary.text(
                        "How many hours until expiration?", default="24"
                    ).ask()
                    expires_in = int(hours) * 3600
                except ValueError:
                    pass

            # Store the new token
            self.store_token(
                token=new_token,
                token_type=token_type,
                environment=environment,
                expires_in=expires_in,
                request_name=request_name,
            )

            return new_token

        return None

    def _refresh_token(
        self,
        token_info: TokenInfo,
        environment: str,
        token_type: str,
        request_name: Optional[str],
    ) -> Optional[str]:
        """Attempt to refresh a token (placeholder for OAuth implementation)."""
        print("🔄 Auto-refresh not yet implemented. Please enter a new token manually.")
        return self._prompt_for_new_token(environment, token_type, request_name)

    def detect_token_in_headers(
        self, headers: Dict[str, str]
    ) -> Optional[Tuple[str, str]]:
        """
        Detect if headers contain a token that might need refresh.

        Args:
            headers: Request headers

        Returns:
            Tuple of (token_type, token) if detected, None otherwise
        """
        # Check for Bearer token
        auth_header = headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return ("bearer", auth_header[7:])  # Remove "Bearer " prefix

        # Check for common API key headers
        api_key_headers = [
            "X-API-Key",
            "X-Auth-Token",
            "X-Access-Token",
            "api_key",
            "apikey",
        ]
        for header_name in api_key_headers:
            if header_name in headers:
                return ("api_key", headers[header_name])

        return None

    def check_and_prompt_for_tokens(
        self,
        headers: Dict[str, str],
        environment: str,
        request_name: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Check headers for tokens and prompt for refresh if needed.

        Args:
            headers: Request headers
            environment: Environment name
            request_name: Name of the request

        Returns:
            Updated headers with refreshed tokens
        """
        updated_headers = headers.copy()

        # Detect token in headers
        token_info = self.detect_token_in_headers(headers)
        if not token_info:
            return updated_headers

        token_type, current_token = token_info

        # Check if we have this token stored and if it's expired
        stored_token = self.get_token(environment, token_type, request_name)

        if stored_token and stored_token != current_token:
            # User has a different token, update headers
            if token_type == "bearer":
                updated_headers["Authorization"] = f"Bearer {stored_token}"
            else:
                # Find the original header and update it
                for header_name, header_value in headers.items():
                    if header_value == current_token:
                        updated_headers[header_name] = stored_token
                        break

        return updated_headers

    def extract_token_from_response(
        self, response_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract token information from API response (for OAuth flows).

        Args:
            response_text: Response body text

        Returns:
            Dictionary with token info if found
        """
        try:
            data = json.loads(response_text)

            # Common OAuth response patterns
            if "access_token" in data:
                return {
                    "token": data["access_token"],
                    "token_type": "bearer",
                    "expires_in": data.get("expires_in"),
                    "refresh_token": data.get("refresh_token"),
                }

            # Custom API patterns
            if "token" in data:
                return {
                    "token": data["token"],
                    "token_type": "bearer",
                    "expires_in": data.get("expires_in"),
                }

        except (json.JSONDecodeError, KeyError):
            pass

        return None

    def list_tokens(self) -> List[Dict[str, Any]]:
        """List all stored tokens with their status."""
        token_list = []

        for token_id, token_data in self.tokens.items():
            token_info = TokenInfo(**token_data)

            status = "Valid"
            if token_info.expires_at:
                time_until_expiry = token_info.expires_at - datetime.now()
                if time_until_expiry.total_seconds() <= 0:
                    status = "Expired"
                elif time_until_expiry.total_seconds() <= 300:  # 5 minutes
                    status = (
                        f"Expires in {int(time_until_expiry.total_seconds() / 60)} min"
                    )
                else:
                    status = f"Expires in {int(time_until_expiry.total_seconds() / 3600)} hours"

            token_list.append(
                {
                    "id": token_id,
                    "environment": token_info.environment,
                    "type": token_info.token_type,
                    "request": token_info.request_name or "default",
                    "status": status,
                    "created": token_info.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return token_list

    def clear_expired_tokens(self) -> int:
        """Remove expired tokens from storage."""
        expired_count = 0
        tokens_to_remove = []

        for token_id, token_data in self.tokens.items():
            token_info = TokenInfo(**token_data)
            if token_info.expires_at and token_info.expires_at < datetime.now():
                tokens_to_remove.append(token_id)
                expired_count += 1

        for token_id in tokens_to_remove:
            del self.tokens[token_id]

        if expired_count > 0:
            self._save_tokens()

        return expired_count


def demo_auth_manager():
    """Demo function to show auth manager functionality."""
    print("🔐 AUTH MANAGER DEMO")
    print("=" * 50)

    manager = AuthManager()

    # Demo storing a token with expiration
    print("✅ Storing a token with 1-hour expiration...")
    manager.store_token(
        token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        token_type="bearer",
        environment="production",
        expires_in=3600,  # 1 hour
        request_name="user-api",
    )

    # Demo token retrieval
    print("✅ Retrieving token...")
    token = manager.get_token("production", "bearer", "user-api")
    print(f"   Retrieved token: {token[:20]}..." if token else "   No token found")

    # Demo token listing
    print("✅ Token list:")
    tokens = manager.list_tokens()
    for token_info in tokens:
        print(
            f"   {token_info['environment']} - {token_info['type']} - {token_info['status']}"
        )

    # Demo header detection
    print("✅ Header detection:")
    headers = {"Authorization": "Bearer test-token-123"}
    detected = manager.detect_token_in_headers(headers)
    if detected:
        print(f"   Detected {detected[0]} token: {detected[1][:10]}...")

    print("\n💡 In real usage, this would:")
    print("   • Prompt for token refresh when expired")
    print("   • Auto-update headers with new tokens")
    print("   • Store tokens securely per environment")
    print("   • Handle OAuth refresh flows")


if __name__ == "__main__":
    demo_auth_manager()
