def test_openapi_metadata_matches_portas_abertas_project(client):
    """Restoring inherited metadata must make this fail."""
    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    info = response.json()["info"]
    assert info["title"] == "Portas Abertas API"
    assert info["description"] == (
        "API do evento Portas Abertas para gerenciamento da programação, "
        "locais, eixos de conhecimento e painel administrativo."
    )


def test_health_identifies_portas_abertas_service(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "Portas Abertas API"


def test_root_serves_public_site(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 200
    assert "UFFS de Portas Abertas" in response.text


def test_openapi_uses_public_api_paths_and_simple_tags(client):
    schema = client.get("/api/openapi.json").json()

    assert "/api/schedule" in schema["paths"]
    assert "/api/locations" in schema["paths"]
    assert "/api/knowledge-axes" in schema["paths"]
    assert not any(
        path in {"/schedule", "/locations", "/knowledge-axes"} for path in schema["paths"]
    )

    documented_tags = {
        tag
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict)
        for tag in operation.get("tags", [])
    }
    assert {"schedule", "locations", "knowledge-axes"} <= documented_tags
    assert not any(tag.startswith("admin-") for tag in documented_tags)
