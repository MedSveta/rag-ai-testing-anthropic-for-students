

def test_health_status_code_200(api_client):
    response = api_client.get('/health')
    assert response.status_code == 200

def test_health_return_json(api_client):
    response = api_client.get('/health')
    assert response.headers['Content-Type'] == 'application/json'