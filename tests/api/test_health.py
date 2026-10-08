

def test_health_status_code_200(api_client):
    response = api_client.get('/health')
    assert response.status_code == 200

def test_health_return_json(api_client):
    response = api_client.get('/health')
    assert response.headers['Content-Type'] == 'application/json'

def test_health_response_body_has_all_fields(api_client):
    body = api_client.get('/health').json()

    expected = {
        "status",
        "app",
        "version",
        "anthropic_model",
        "api_key_configured",
        "knowledge_base_exists"
    }
    assert set(body.keys()) == expected

def test_health_response_body_has_types(api_client):
    body = api_client.get('/health').json()

    assert isinstance(body['status'], str)
    assert isinstance(body['app'], str)
    assert isinstance(body['version'], str)
    assert isinstance(body['anthropic_model'], str)
    assert isinstance(body['api_key_configured'], bool)
    assert isinstance(body['knowledge_base_exists'], bool)

def test_health_status_ok(api_client):
    body = api_client.get('/health').json()
    assert body['status'] == 'ok'
    assert body['app'] == 'PhoneBook RAG AI Testing'
    assert body['version'] == '0.3.0'
    assert body['anthropic_model'] == 'claude-sonnet-5'
    assert body['api_key_configured'] is True
    assert body['knowledge_base_exists'] is True

def test_health_does_not_show_api_key(api_client):
    response = api_client.get('/health')
    assert "sk-ant" not in response.text