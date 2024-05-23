from functools import wraps


def cache(func):
    """
    Decorator that caches the results of a function.
    """
    cache_data = {}

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create a key based on the function arguments
        key = (args, tuple(kwargs.items()))
        if key in cache_data:
            return cache_data[key]
        result = func(*args, **kwargs)
        cache_data[key] = result
        return result

    return wrapper


@cache
def expensive_computation(x, y):
    # Simulate an expensive computation
    result = x**y
    return result


if __name__ == "__main__":
    # Example usage
    print(expensive_computation(2, 10))  # First call, computes the result
    print(expensive_computation(2, 10))  # Second call, returns the cached result

    @cache
    def fetch_data_from_db(query):
        # Simulate a database query
        return f"Results for {query}"

    # Example usage
    print(fetch_data_from_db("SELECT * FROM users"))  # First call, fetches data
    print(fetch_data_from_db("SELECT * FROM users"))  # Second call, returns the cached result
