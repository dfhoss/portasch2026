def test_public_site_is_served_from_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "UFFS de Portas Abertas" in response.text
