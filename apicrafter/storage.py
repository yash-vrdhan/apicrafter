"""Storage management for collections, environments, and history."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class RequestData(BaseModel):
    """Model for storing request data."""

    method: str
    url: str
    headers: Dict[str, str] = Field(default_factory=dict)
    params: Dict[str, str] = Field(default_factory=dict)
    body: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = None


class Collection(BaseModel):
    """Model for a collection of requests."""

    name: str
    requests: Dict[str, RequestData] = Field(default_factory=dict)
    description: Optional[str] = None


class Environment(BaseModel):
    """Model for environment variables."""

    name: str
    variables: Dict[str, str] = Field(default_factory=dict)


class HistoryEntry(BaseModel):
    """Model for a history entry."""

    timestamp: datetime
    method: str
    url: str
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    success: bool = True


class StorageManager:
    """Manages storage of collections, environments, and history."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize storage manager."""
        if config_dir is None:
            config_dir = Path.home() / ".apicrafter"

        self.config_dir = config_dir
        self.collections_file = config_dir / "collections.yaml"
        self.environments_file = config_dir / "envs.yaml"
        self.history_file = config_dir / "history.log"

        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)

        # Initialize files if they don't exist
        self._init_files()

    def _init_files(self) -> None:
        """Initialize configuration files if they don't exist."""
        if not self.collections_file.exists():
            self.collections_file.write_text("collections: {}\n")

        if not self.environments_file.exists():
            default_env = {
                "environments": {"default": {"name": "default", "variables": {}}}
            }
            with open(self.environments_file, "w") as f:
                yaml.dump(default_env, f, default_flow_style=False)

        if not self.history_file.exists():
            self.history_file.touch()

    def save_request(
        self, name: str, request_data: RequestData, collection: str = "default"
    ) -> None:
        """Save a request to a collection."""
        collections = self.load_collections()

        if collection not in collections:
            collections[collection] = Collection(name=collection)

        collections[collection].requests[name] = request_data
        self._save_collections(collections)

    def load_request(
        self, name: str, collection: str = "default"
    ) -> Optional[RequestData]:
        """Load a request from a collection."""
        collections = self.load_collections()

        if collection in collections and name in collections[collection].requests:
            return collections[collection].requests[name]

        return None

    def load_collections(self) -> Dict[str, Collection]:
        """Load all collections."""
        try:
            with open(self.collections_file, "r") as f:
                data = yaml.safe_load(f) or {}

            collections = {}
            for coll_name, coll_data in data.get("collections", {}).items():
                requests = {}
                for req_name, req_data in coll_data.get("requests", {}).items():
                    requests[req_name] = RequestData(**req_data)

                collections[coll_name] = Collection(
                    name=coll_name,
                    requests=requests,
                    description=coll_data.get("description"),
                )

            return collections
        except Exception as e:
            logging.error(f"Error loading collections: {e}")
            return {}

    def _save_collections(self, collections: Dict[str, Collection]) -> None:
        """Save collections to file."""
        data = {"collections": {}}

        for coll_name, collection in collections.items():
            requests_data = {}
            for req_name, request in collection.requests.items():
                requests_data[req_name] = request.model_dump(exclude_none=True)

            data["collections"][coll_name] = {
                "name": collection.name,
                "requests": requests_data,
            }

            if collection.description:
                data["collections"][coll_name]["description"] = collection.description

        with open(self.collections_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def save_environment(self, env: Environment) -> None:
        """Save an environment."""
        environments = self.load_environments()
        environments[env.name] = env
        self._save_environments(environments)

    def load_environment(self, name: str) -> Optional[Environment]:
        """Load an environment by name."""
        environments = self.load_environments()
        return environments.get(name)

    def load_environments(self) -> Dict[str, Environment]:
        """Load all environments."""
        try:
            with open(self.environments_file, "r") as f:
                data = yaml.safe_load(f) or {}

            environments = {}
            for env_name, env_data in data.get("environments", {}).items():
                environments[env_name] = Environment(
                    name=env_name, variables=env_data.get("variables", {})
                )

            return environments
        except Exception as e:
            logging.error(f"Error loading environments: {e}")
            return {}

    def _save_environments(self, environments: Dict[str, Environment]) -> None:
        """Save environments to file."""
        data = {"environments": {}}

        for env_name, env in environments.items():
            data["environments"][env_name] = {
                "name": env.name,
                "variables": env.variables,
            }

        with open(self.environments_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def add_to_history(self, entry: HistoryEntry) -> None:
        """Add an entry to request history."""
        try:
            with open(self.history_file, "a") as f:
                f.write(json.dumps(entry.model_dump(), default=str) + "\n")
        except Exception as e:
            logging.error(f"Error saving to history: {e}")

    def load_history(self, limit: int = 50) -> List[HistoryEntry]:
        """Load request history."""
        try:
            entries = []
            with open(self.history_file, "r") as f:
                lines = f.readlines()

                # Get the last 'limit' lines
                for line in lines[-limit:]:
                    if line.strip():
                        data = json.loads(line.strip())
                        # Parse datetime string back to datetime object
                        if isinstance(data["timestamp"], str):
                            data["timestamp"] = datetime.fromisoformat(
                                data["timestamp"]
                            )
                        entries.append(HistoryEntry(**data))

            return entries
        except Exception as e:
            logging.error(f"Error loading history: {e}")
            return []

    def resolve_variables(self, text: str, environment: str = "default") -> str:
        """Resolve environment variables in text using {{VAR}} syntax."""
        env = self.load_environment(environment)
        if not env:
            return text

        resolved = text
        for var_name, var_value in env.variables.items():
            resolved = resolved.replace(f"{{{{{var_name}}}}}", var_value)

        return resolved
