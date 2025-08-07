# cacheio

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/github/license/bnlucas/cacheio)
![PyPI - Version](https://img.shields.io/pypi/v/cacheio)

A flexible and user-friendly Python caching library that provides a unified interface for both synchronous and asynchronous caching, with support for various backends.

---

## Overview 🚀

`cacheio` is designed to simplify caching in Python applications. It provides a simple, consistent API for interacting with different caching backends, whether your code is synchronous or asynchronous. The library intelligently loads dependencies based on your needs, so you only install what you use.

---

## Installation

You can install `cacheio` with pip. The library uses **optional dependency groups** to manage its backends.

### Basic Installation

To install the core library without any caching backends, run:

```bash
pip install cacheio
```

### Installing with Backends

To install the library with specific backends, use the optional dependency groups:

* **Synchronous Caching:** Use the `sync` group for `cachelib`-based backends.
    ```bash
    pip install "cacheio[sync]"
    ```

* **Asynchronous Caching:** Use the `async` group for `aiocache`-based backends.
    ```bash
    pip install "cacheio[async]"
    ```

* **Full Installation:** Use the `full` group to install both synchronous and asynchronous backends.
    ```bash
    pip install "cacheio[full]"
    ```

---

## Quick Start

### Synchronous Caching

Use `CacheFactory` to get a synchronous cache adapter. If `cachelib` is installed, this will provide an `Adapter` instance.

```python
from cacheio import CacheFactory

# Get a simple in-memory cache adapter
my_cache = CacheFactory.memory_cache()

# Use the cache
my_cache.set("my_key", "my_value", ttl=300)
value = my_cache.get("my_key")

print(f"Retrieved value: {value}")
```

### Asynchronous Caching

Use `CacheFactory` to get a clean asynchronous adapter. If `aiocache` is installed, this will provide an `AsyncAdapter` instance.

```python
import asyncio
from cacheio import CacheFactory

async def main():
    # Get an asynchronous cache adapter
    my_async_cache = CacheFactory.async_memory_cache()

    # Use the cache asynchronously
    await my_async_cache.set("my_async_key", "my_async_value", ttl=300)
    async_value = await my_async_cache.get("my_async_key")

    print(f"Retrieved async value: {async_value}")

if __name__ == "__main__":
    # Ensure you have a running event loop
    asyncio.run(main())
```

---

## Usage Examples

### 1. Synchronous Caching Example

This example demonstrates how to use the **`cached`** decorator for a synchronous method. We define a class that inherits from `Cacheable`, which automatically sets up a `cachelib`-based in-memory cache.

* **Key Function (`key_fn`)**: The `key_fn` is a crucial part of the decorator. For simple key generation, a `lambda` is a clean and efficient way to define it inline.
* **Decorator**: The `@cached` decorator handles the rest, checking the cache for the key, calling the `fetch_user` method if the key isn't found, and storing the result.

```python
import time
from cacheio import cached
from cacheio.mixins import Cacheable

# Define the class that uses caching.
# It inherits from `Cacheable` to get a default in-memory cache.
class UserService(Cacheable):
    
    # The cached decorator uses a lambda to generate a unique cache key.
    @cached(key_fn=lambda self, user_id, **kwargs: f"user:{user_id}", ttl=60)
    def fetch_user(self, user_id: int, request_id: str) -> dict:
        """Simulates a slow, expensive database call."""
        print(f"Fetching user {user_id} from database...")
        time.sleep(2)  # Simulate a 2-second network delay
        return {"id": user_id, "name": f"User_{user_id}", "request": request_id}

# --- Usage ---
user_service = UserService()

# First call: The method runs and its result is cached.
print("First call:")
user_1 = user_service.fetch_user(user_id=1, request_id="req-1")
print(f"Result: {user_1}\n")

# Second call (with same arguments): The cached result is returned instantly.
print("Second call (should be instant):")
user_2 = user_service.fetch_user(user_id=1, request_id="req-1")
print(f"Result: {user_2}\n")

# Third call (with different arguments): The cached result is still returned because the key only depends on `user_id`.
print("Third call (with different request_id, should still be instant):")
user_3 = user_service.fetch_user(user_id=1, request_id="req-2")
print(f"Result: {user_3}")
```

### 2. Asynchronous Caching Example

This example mirrors the synchronous one but uses the **`async_cached`** decorator and a class that inherits from `AsyncCacheable`, which automatically sets up an `aiocache`-based in-memory cache. The core logic remains the same, but the functions and decorators are all `async`.

* **Key Function (`key_fn`)**: The key generation logic is now a concise `lambda` function.
* **Decorator**: The `@async_cached` decorator works just like its synchronous counterpart, but it's designed to work with `awaitable` functions and asynchronous cache adapters.

```python
import asyncio
from cacheio import async_cached
from cacheio.mixins import AsyncCacheable

# Define the class that uses asynchronous caching.
# It inherits from `AsyncCacheable` for a default in-memory async cache.
class AsyncUserService(AsyncCacheable):
    
    # The async_cached decorator uses a lambda to generate a unique cache key.
    @async_cached(key_fn=lambda self, user_id, **kwargs: f"user:{user_id}", ttl=60)
    async def fetch_user(self, user_id: int, request_id: str) -> dict:
        """Simulates a slow, expensive asynchronous database call."""
        print(f"Fetching user {user_id} from database asynchronously...")
        await asyncio.sleep(2)  # Simulate a 2-second async delay
        return {"id": user_id, "name": f"User_{user_id}", "request": request_id}

# --- Usage ---
async def main():
    user_service = AsyncUserService()

    # First call: The method runs and its result is cached.
    print("First call:")
    user_1 = await user_service.fetch_user(user_id=1, request_id="req-1")
    print(f"Result: {user_1}\n")

    # Second call (with same arguments): The cached result is returned instantly.
    print("Second call (should be instant):")
    user_2 = await user_service.fetch_user(user_id=1, request_id="req-1")
    print(f"Result: {user_2}\n")

# Third call (with different arguments): The cached result is still returned.
print("Third call (with different request_id, should still be instant):")
user_3 = await user_service.fetch_user(user_id=1, request_id="req-2")
print(f"Result: {user_3}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Contributing

We welcome contributions! Please feel free to open an issue or submit a pull request on our [GitHub repository](https://github.com/bnlucas/cacheio).

## License

`cacheio` is distributed under the terms of the MIT license. See the [LICENSE](https://github.com/bnlucas/cacheio/blob/main/LICENSE) file for details.