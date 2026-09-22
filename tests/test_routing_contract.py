def test_public_site_is_the_root_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "UFFS de Portas Abertas" in response.text


def test_admin_dashboard_is_served_at_admin(client):
    response = client.get("/admin")

    assert response.status_code == 200
    assert 'id="login-view"' in response.text


def test_api_documentation_is_served_under_api_prefix(client):
    response = client.get("/api/docs")

    assert response.status_code == 200
    assert "Portas Abertas API" in response.text


def test_api_routes_are_served_under_api_prefix(client):
    response = client.get("/api/schedule")

    assert response.status_code == 401


def test_unprefixed_api_route_is_not_publicly_available(client):
    response = client.get("/schedule")

    assert response.status_code == 404
