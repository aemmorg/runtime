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

"""Unit tests for CeleryBroker and CeleryBackend class hierarchies."""

import os
import pytest
from cl.runtime.tasks.celery.broker.celery_broker import CeleryBroker
from cl.runtime.tasks.celery.broker.sqlite_celery_broker import SqliteCeleryBroker
from cl.runtime.tasks.celery.broker.mongo_celery_broker import MongoCeleryBroker
from cl.runtime.tasks.celery.broker.redis_celery_broker import RedisCeleryBroker
from cl.runtime.tasks.celery.broker.rabbitmq_celery_broker import RabbitmqCeleryBroker
from cl.runtime.tasks.celery.backend.celery_backend import CeleryBackend
from cl.runtime.tasks.celery.backend.sqlite_celery_backend import SqliteCeleryBackend
from cl.runtime.tasks.celery.backend.mongo_celery_backend import MongoCeleryBackend


# --- CeleryBroker registry tests ---


def test_broker_registry_contains_all_types():
    """Verify all built-in broker types are registered."""
    CeleryBroker._ensure_registry()
    assert "SqliteCeleryBroker" in CeleryBroker._registry
    assert "MongoCeleryBroker" in CeleryBroker._registry
    assert "RedisCeleryBroker" in CeleryBroker._registry
    assert "RabbitmqCeleryBroker" in CeleryBroker._registry


def test_broker_create_returns_correct_type():
    """Verify CeleryBroker.create returns the correct subclass."""
    assert isinstance(CeleryBroker.create("SqliteCeleryBroker"), SqliteCeleryBroker)
    assert isinstance(CeleryBroker.create("MongoCeleryBroker"), MongoCeleryBroker)
    assert isinstance(CeleryBroker.create("RedisCeleryBroker"), RedisCeleryBroker)
    assert isinstance(CeleryBroker.create("RabbitmqCeleryBroker"), RabbitmqCeleryBroker)


def test_broker_create_unknown_type_raises():
    """Verify CeleryBroker.create raises for an unknown type name."""
    with pytest.raises(RuntimeError, match="Unknown Celery broker type"):
        CeleryBroker.create("NonexistentBroker")


# --- CeleryBackend registry tests ---


def test_backend_registry_contains_all_types():
    """Verify all built-in backend types are registered."""
    CeleryBackend._ensure_registry()
    assert "SqliteCeleryBackend" in CeleryBackend._registry
    assert "MongoCeleryBackend" in CeleryBackend._registry


def test_backend_create_returns_correct_type():
    """Verify CeleryBackend.create returns the correct subclass."""
    assert isinstance(CeleryBackend.create("SqliteCeleryBackend"), SqliteCeleryBackend)
    assert isinstance(CeleryBackend.create("MongoCeleryBackend"), MongoCeleryBackend)


def test_backend_create_unknown_type_raises():
    """Verify CeleryBackend.create raises for an unknown type name."""
    with pytest.raises(RuntimeError, match="Unknown Celery backend type"):
        CeleryBackend.create("NonexistentBackend")


# --- SqliteCeleryBroker tests ---


def test_sqlite_broker_resolve_uri_default():
    """SqliteCeleryBroker builds a default path when uri_template is None."""
    broker = SqliteCeleryBroker()
    uri = broker.resolve_uri(None, "TestEnv")
    assert "sqlalchemy+sqlite:///" in uri
    assert "celery.testenv.sqlite" in uri


def test_sqlite_broker_resolve_uri_concrete():
    """SqliteCeleryBroker returns a concrete URI unchanged."""
    broker = SqliteCeleryBroker()
    uri = broker.resolve_uri("sqlalchemy+sqlite:///custom/path.db", "TestEnv")
    assert uri == "sqlalchemy+sqlite:///custom/path.db"


def test_sqlite_broker_resolve_uri_template():
    """SqliteCeleryBroker builds a default path when the template has unresolved placeholders."""
    broker = SqliteCeleryBroker()
    uri = broker.resolve_uri("sqlalchemy+sqlite:///{project_dir}/celery-{env_id}.db", "TestEnv")
    assert "sqlalchemy+sqlite:///" in uri
    assert "celery.testenv.sqlite" in uri


def test_sqlite_broker_delete_existing_tasks(tmp_path):
    """SqliteCeleryBroker.delete_existing_tasks removes the SQLite file."""
    db_file = tmp_path / "celery.db"
    db_file.write_text("")
    uri = f"sqlalchemy+sqlite:///{db_file}"

    broker = SqliteCeleryBroker()
    broker.delete_existing_tasks(uri, "test-queue")
    assert not db_file.exists()


def test_sqlite_broker_delete_existing_tasks_missing_file(tmp_path):
    """SqliteCeleryBroker.delete_existing_tasks is a no-op when file does not exist."""
    db_file = tmp_path / "nonexistent.db"
    uri = f"sqlalchemy+sqlite:///{db_file}"

    broker = SqliteCeleryBroker()
    broker.delete_existing_tasks(uri, "test-queue")


# --- MongoCeleryBroker tests ---


def test_mongo_broker_resolve_uri_template():
    """MongoCeleryBroker resolves {env_id} in the URI template."""
    broker = MongoCeleryBroker()
    uri = broker.resolve_uri("mongodb://host:27017/celery-{env_id}", "Prod")
    assert uri == "mongodb://host:27017/celery-Prod"


def test_mongo_broker_resolve_uri_context_id():
    """MongoCeleryBroker resolves {context_id} for backward compatibility."""
    broker = MongoCeleryBroker()
    uri = broker.resolve_uri("mongodb://host:27017/celery-{context_id}", "Prod")
    assert uri == "mongodb://host:27017/celery-Prod"


def test_mongo_broker_resolve_uri_concrete():
    """MongoCeleryBroker returns a concrete URI unchanged."""
    broker = MongoCeleryBroker()
    uri = broker.resolve_uri("mongodb://host:27017/celery-fixed", "Prod")
    assert uri == "mongodb://host:27017/celery-fixed"


def test_mongo_broker_resolve_uri_none_raises():
    """MongoCeleryBroker raises when uri_template is None."""
    broker = MongoCeleryBroker()
    with pytest.raises(RuntimeError, match="Celery broker URI is not specified"):
        broker.resolve_uri(None, "Prod")


# --- RedisCeleryBroker tests ---


def test_redis_broker_resolve_uri_template():
    """RedisCeleryBroker resolves {env_id} in the URI template."""
    broker = RedisCeleryBroker()
    uri = broker.resolve_uri("redis://host:6379/{env_id}", "Prod")
    assert uri == "redis://host:6379/Prod"


def test_redis_broker_resolve_uri_concrete():
    """RedisCeleryBroker returns a concrete URI unchanged."""
    broker = RedisCeleryBroker()
    uri = broker.resolve_uri("redis://host:6379/0", "Prod")
    assert uri == "redis://host:6379/0"


def test_redis_broker_resolve_uri_none_raises():
    """RedisCeleryBroker raises when uri_template is None."""
    broker = RedisCeleryBroker()
    with pytest.raises(RuntimeError, match="Celery broker URI is not specified"):
        broker.resolve_uri(None, "Prod")


# --- RabbitmqCeleryBroker tests ---


def test_rabbitmq_broker_resolve_uri_template():
    """RabbitmqCeleryBroker resolves {env_id} in the URI template."""
    broker = RabbitmqCeleryBroker()
    uri = broker.resolve_uri("amqp://user:pass@host:5672/{env_id}", "Prod")
    assert uri == "amqp://user:pass@host:5672/Prod"


def test_rabbitmq_broker_resolve_uri_concrete():
    """RabbitmqCeleryBroker returns a concrete URI unchanged."""
    broker = RabbitmqCeleryBroker()
    uri = broker.resolve_uri("amqp://user:pass@host:5672//", "Prod")
    assert uri == "amqp://user:pass@host:5672//"


def test_rabbitmq_broker_resolve_uri_none_raises():
    """RabbitmqCeleryBroker raises when uri_template is None."""
    broker = RabbitmqCeleryBroker()
    with pytest.raises(RuntimeError, match="Celery broker URI is not specified"):
        broker.resolve_uri(None, "Prod")


# --- SqliteCeleryBackend tests ---


def test_sqlite_backend_resolve_uri_default():
    """SqliteCeleryBackend builds a default path when uri_template is None."""
    backend = SqliteCeleryBackend()
    uri = backend.resolve_uri(None, "TestEnv")
    assert "db+sqlite:///" in uri
    assert "celery-backend.testenv.sqlite" in uri


def test_sqlite_backend_resolve_uri_concrete():
    """SqliteCeleryBackend returns a concrete URI unchanged."""
    backend = SqliteCeleryBackend()
    uri = backend.resolve_uri("db+sqlite:///custom/backend.db", "TestEnv")
    assert uri == "db+sqlite:///custom/backend.db"


def test_sqlite_backend_resolve_uri_template():
    """SqliteCeleryBackend builds a default path when the template has unresolved placeholders."""
    backend = SqliteCeleryBackend()
    uri = backend.resolve_uri("db+sqlite:///{project_dir}/backend-{env_id}.db", "TestEnv")
    assert "db+sqlite:///" in uri
    assert "celery-backend.testenv.sqlite" in uri


# --- MongoCeleryBackend tests ---


def test_mongo_backend_resolve_uri_template():
    """MongoCeleryBackend resolves {env_id} in the URI template."""
    backend = MongoCeleryBackend()
    uri = backend.resolve_uri("mongodb://host:27017/backend-{env_id}", "Prod")
    assert uri == "mongodb://host:27017/backend-Prod"


def test_mongo_backend_resolve_uri_context_id():
    """MongoCeleryBackend resolves {context_id} for backward compatibility."""
    backend = MongoCeleryBackend()
    uri = backend.resolve_uri("mongodb://host:27017/backend-{context_id}", "Prod")
    assert uri == "mongodb://host:27017/backend-Prod"


def test_mongo_backend_resolve_uri_concrete():
    """MongoCeleryBackend returns a concrete URI unchanged."""
    backend = MongoCeleryBackend()
    uri = backend.resolve_uri("mongodb://host:27017/backend-fixed", "Prod")
    assert uri == "mongodb://host:27017/backend-fixed"


def test_mongo_backend_resolve_uri_none_raises():
    """MongoCeleryBackend raises when uri_template is None."""
    backend = MongoCeleryBackend()
    with pytest.raises(RuntimeError, match="Celery backend URI is not specified"):
        backend.resolve_uri(None, "Prod")
