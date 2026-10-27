# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for the JSON cache."""

import pytest
from graphrag_cache.json_cache import JsonCache
from graphrag_storage.file_storage import FileStorage
from graphrag_storage.memory_storage import MemoryStorage


@pytest.mark.asyncio
async def test_json_cache_round_trip_and_persistence(tmp_path):
    storage = FileStorage(base_dir=str(tmp_path))
    cache = JsonCache(storage)

    await cache.set("key", {"text": "héllo", "items": [1, 2, 3]})

    assert await cache.has("key")
    assert await cache.get("key") == {"text": "héllo", "items": [1, 2, 3]}
    assert await JsonCache(storage).get("key") == {
        "text": "héllo",
        "items": [1, 2, 3],
    }


@pytest.mark.asyncio
async def test_json_cache_overwrites_and_deletes_values(tmp_path):
    cache = JsonCache(FileStorage(base_dir=str(tmp_path)))

    await cache.set("key", "first")
    await cache.set("key", "second")
    await cache.set("ignored", None)

    assert await cache.get("key") == "second"
    assert not await cache.has("ignored")

    await cache.delete("key")

    assert not await cache.has("key")
    assert await cache.get("key") is None


@pytest.mark.asyncio
async def test_json_cache_child_namespaces_are_isolated(tmp_path):
    cache = JsonCache(FileStorage(base_dir=str(tmp_path)))
    first_child = cache.child("first")
    second_child = cache.child("second")

    await first_child.set("key", "first-value")
    await second_child.set("key", "second-value")

    assert await first_child.get("key") == "first-value"
    assert await second_child.get("key") == "second-value"
    assert await cache.get("key") is None


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "[]",
        '"value"',
        "null",
        '{"debug": "missing result"}',
        "[1, 2, 3]",
        "12345",
        "true",
    ],
)
@pytest.mark.asyncio
async def test_json_cache_removes_invalid_payload(tmp_path, payload):
    storage = FileStorage(base_dir=str(tmp_path))
    cache = JsonCache(storage)

    # Directly inject corrupted or non-dict payload into storage
    await storage.set("invalid", payload)

    assert await cache.has("invalid")
    assert await cache.get("invalid") is None
    assert not await cache.has("invalid")
