from time import perf_counter


def no_cache_bench(f, n, *args, **kwargs):
    total = 0
    for _ in range(n):
        t = perf_counter()
        _ = f(*args, **kwargs)
        total += perf_counter() - t
        f.cache_clear()
    print(total / n)
    return total / n


def cache_bench(f, n, *args, **kwargs):
    total = 0
    for _ in range(n):
        t = perf_counter()
        _ = f(*args, **kwargs)
        total += perf_counter() - t
    print(total / n)
    return total / n


if __name__ == "__main__":
    n = 100000
    from pathvein._path_utils import iterdir
    from pathlib import Path

    p = Path(".").resolve()

    print("No cache")
    no_cache_bench(iterdir, n, p)
    print("Cache")
    cache_bench(iterdir, n, p)
