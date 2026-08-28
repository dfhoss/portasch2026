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
