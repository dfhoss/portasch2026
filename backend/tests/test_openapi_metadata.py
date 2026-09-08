def test_openapi_metadata_matches_portas_abertas_project(client):
    """Restoring inherited GeoGIS/OCR metadata must make this fail."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    info = response.json()["info"]
    assert info["title"] == "Portas Abertas API"
    assert info["description"] == (
        "API do evento Portas Abertas para gerenciamento da programação, "
        "locais, eixos de conhecimento e painel administrativo."
    )


def test_root_redirect_and_openapi_description_point_to_admin_panel(client):
    """Documenting the root as a docs redirect or changing its target must make this fail."""
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/home"

    root_operation = client.get("/openapi.json").json()["paths"]["/"]["get"]
    description = root_operation["description"]
    assert "painel administrativo" in description.lower()
    assert "`/home`" in description
    assert "Redirecionamento para documentação" not in description


def test_openapi_uses_public_api_paths_and_simple_tags(client):
    schema = client.get("/openapi.json").json()

    assert "/schedule" in schema["paths"]
    assert "/locations" in schema["paths"]
    assert "/knowledge-axes" in schema["paths"]
    assert not any(path.startswith("/admin/api/") for path in schema["paths"])

    documented_tags = {
        tag
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict)
        for tag in operation.get("tags", [])
    }
    assert {"schedule", "locations", "knowledge-axes"} <= documented_tags
    assert not any(tag.startswith("admin-") for tag in documented_tags)
