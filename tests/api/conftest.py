import pytest
import os
import httpx

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

@pytest.fixture(scope='session')
def api_client():
    client = httpx.Client(base_url=BASE_URL, timeout=100)
    try:
        client.get("/health")
    except httpx.ConnectError:
        client.close()
        pytest.skip("API server not available")
    yield client
    client.close()




