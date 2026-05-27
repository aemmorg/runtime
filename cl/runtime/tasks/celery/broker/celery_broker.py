# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from abc import ABC
from abc import abstractmethod
from typing import ClassVar


class CeleryBroker(ABC):
    """Abstract base for Celery message broker implementations."""

    _registry: ClassVar[dict[str, type["CeleryBroker"]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "__abstractmethods__", None):
            CeleryBroker._registry[cls.__name__] = cls

    @classmethod
    def create(cls, broker_type_name: str) -> "CeleryBroker":
        """Create a broker instance by class name."""
        cls._ensure_registry()
        if broker_type_name not in cls._registry:
            valid = ", ".join(sorted(cls._registry.keys()))
            raise RuntimeError(f"Unknown Celery broker type: {broker_type_name}. Valid types: {valid}")
        return cls._registry[broker_type_name]()

    @classmethod
    def _ensure_registry(cls) -> None:
        """Import all built-in broker implementations to populate the registry."""
        if cls._registry:
            return
        import cl.runtime.tasks.celery.broker.mongo_celery_broker  # noqa: F401
        import cl.runtime.tasks.celery.broker.rabbitmq_celery_broker  # noqa: F401
        import cl.runtime.tasks.celery.broker.redis_celery_broker  # noqa: F401
        import cl.runtime.tasks.celery.broker.sqlite_celery_broker  # noqa: F401

    @abstractmethod
    def resolve_uri(self, uri_template: str | None, env_id: str) -> str:
        """Resolve the broker URI from a template and environment id."""

    @abstractmethod
    def delete_existing_tasks(self, uri: str, queue: str) -> None:
        """Delete existing tasks and clean up broker-specific state."""
