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

Use `cacheio.Cache` to easily get a synchronous cache instance. If `cachelib` is installed, it'll automatically provide a `SimpleCache` instance.

```python
from cacheio import Cache

# Get a simple in-memory cache instance
my_cache = Cache.get()

# Use the cache
my_cache.set("my_key", "my_value", timeout=300)
value = my_cache.get("my_key")

print(f"Retrieved value: {value}")
```

### Asynchronous Caching

Use `cacheio.AsyncCache` for a clean asynchronous interface. If `aiocache` is installed, this will provide an `aiocache` instance.

```python
import asyncio
from cacheio import AsyncCache

async def main():
    # Get an asynchronous cache instance
    my_async_cache = AsyncCache.get()

    # Use the cache asynchronously
    await my_async_cache.set("my_async_key", "my_async_value", ttl=300)
    async_value = await my_async_cache.get("my_async_key")

    print(f"Retrieved async value: {async_value}")

if __name__ == "__main__":
    # Ensure you have a running event loop
    asyncio.run(main())
```

---

## Contributing

We welcome contributions! Please feel free to open an issue or submit a pull request on our [GitHub repository](https://github.com/bnlucas/cacheio).

## License

`cacheio` is distributed under the terms of the MIT license. See the [LICENSE](https://github.com/bnlucas/cacheio/blob/main/LICENSE) file for details.
