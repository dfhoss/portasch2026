import pytest
from clients.json_store import PersistenceError
from fastapi import status


@pytest.mark.parametrize("path", ["/api/institutions", "/api/participants"])
def test_catalog_routes_require_authentication(client, path):
    assert client.get(path).status_code == status.HTTP_401_UNAUTHORIZED


def test_institution_crud_returns_public_contract(client, auth_headers):
    created = client.post(
        "/api/institutions",
        headers=auth_headers,
        json={
            "name": "  Escola Nova ",
            "state": "SC",
            "city": "Chapecó",
            "description": "  texto ",
        },
    )
    assert created.status_code == status.HTTP_201_CREATED
    institution = created.json()
    assert institution["name"] == "Escola Nova"
    identifier = institution["id"]
    assert client.get(f"/api/institutions/{identifier}", headers=auth_headers).json() == institution
    updated = client.put(
        f"/api/institutions/{identifier}",
        headers=auth_headers,
        json={"name": "Escola Editada", "state": "PR", "city": "Curitiba", "description": ""},
    )
    assert updated.status_code == status.HTTP_200_OK
    assert updated.json() == {
        "id": identifier,
        "name": "Escola Editada",
        "state": "PR",
        "city": "Curitiba",
        "description": None,
    }
    deleted = client.delete(f"/api/institutions/{identifier}", headers=auth_headers)
    assert deleted.status_code == status.HTTP_204_NO_CONTENT
    assert deleted.content == b""


def test_participant_crud_normalizes_cpf_and_alias(client, auth_headers):
    institution = client.get("/api/institutions", headers=auth_headers).json()[0]
    response = client.post(
        "/api/participants",
        headers=auth_headers,
        json={
            "name": "Aluno",
            "cpf": "529.982.247-25",
            "email": " aluno@example.org ",
            "institutionId": institution["id"],
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    participant = response.json()
    assert participant["cpf"] == "52998224725"
    assert participant["institutionId"] == institution["id"]
    listed = client.get("/api/participants", headers=auth_headers)
    assert listed.status_code == status.HTTP_200_OK
    listed_participant = next(item for item in listed.json() if item["id"] == participant["id"])
    assert listed_participant["cpf"] == "***.***.***-25"
    assert "52998224725" not in listed.text
    assert (
        client.get(f"/api/participants/{participant['id']}", headers=auth_headers).json()
        == participant
    )
    assert (
        client.put(
            f"/api/participants/{participant['id']}",
            headers=auth_headers,
            json={
                "name": "Aluno 2",
                "cpf": "52998224725",
                "email": "novo@example.org",
                "institutionId": institution["id"],
            },
        ).status_code
        == status.HTTP_200_OK
    )
    assert (
        client.delete(f"/api/participants/{participant['id']}", headers=auth_headers).status_code
        == status.HTTP_204_NO_CONTENT
    )


def test_api_maps_not_found_duplicate_invalid_and_in_use(client, auth_headers):
    assert client.get("/api/institutions/missing", headers=auth_headers).status_code == 404
    payload = {"name": "Conflito", "state": "SC", "city": "Chapecó"}
    assert client.post("/api/institutions", headers=auth_headers, json=payload).status_code == 201
    assert (
        client.post(
            "/api/institutions", headers=auth_headers, json={**payload, "name": " conflito "}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/institutions", headers=auth_headers, json={**payload, "name": " "}
        ).status_code
        == 422
    )
    institution = client.get("/api/institutions", headers=auth_headers).json()[0]
    participant = {
        "name": "Aluno",
        "cpf": "52998224725",
        "email": "a@e.com",
        "institutionId": institution["id"],
    }
    assert (
        client.post("/api/participants", headers=auth_headers, json=participant).status_code == 201
    )
    assert (
        client.delete(f"/api/institutions/{institution['id']}", headers=auth_headers).status_code
        == 409
    )
    assert (
        client.post("/api/participants", headers=auth_headers, json=participant).status_code == 409
    )
    assert (
        client.post(
            "/api/participants", headers=auth_headers, json={**participant, "cpf": "123"}
        ).status_code
        == 422
    )


@pytest.mark.parametrize("path", ["/api/institutions", "/api/participants"])
def test_catalog_routes_reject_invalid_jwt(client, path):
    response = client.get(path, headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("method", ["get", "delete"])
def test_missing_participant_get_and_delete_return_404(client, auth_headers, method):
    response = getattr(client, method)(
        "/api/participants/participant-missing", headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_missing_participant_put_returns_404(client, auth_headers):
    response = client.put(
        "/api/participants/participant-missing",
        headers=auth_headers,
        json={
            "name": "Aluno",
            "cpf": "52998224725",
            "email": "a@e.com",
            "institutionId": "institution-001",
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("method", ["post", "put"])
def test_participant_missing_institution_returns_404(client, auth_headers, method):
    payload = {
        "name": "Aluno",
        "cpf": "52998224725",
        "email": "a@e.com",
        "institutionId": "institution-missing",
    }
    if method == "put":
        path = "/api/participants/participant-001"
        client.post(
            "/api/participants",
            headers=auth_headers,
            json={**payload, "institutionId": "institution-001"},
        )
    else:
        path = "/api/participants"
    response = getattr(client, method)(path, headers=auth_headers, json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_institution_delete_conflict_contains_participant_references(client, auth_headers):
    institution_id = "institution-001"
    created = client.post(
        "/api/participants",
        headers=auth_headers,
        json={
            "name": "Aluno",
            "cpf": "52998224725",
            "email": "a@e.com",
            "institutionId": institution_id,
        },
    )
    assert created.status_code == status.HTTP_201_CREATED
    response = client.delete(f"/api/institutions/{institution_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert created.json()["id"] in response.json()["detail"]["references"]


@pytest.mark.parametrize(
    ("path", "filename"),
    [("/api/institutions", "institutions.json"), ("/api/participants", "participants.json")],
)
def test_catalog_read_failures_are_stable_500(
    client, auth_headers, temporary_database, path, filename
):
    catalog_path = getattr(temporary_database, filename.removesuffix(".json"))
    catalog_path.write_text("{invalid", encoding="utf-8")
    response = client.get(path, headers=auth_headers)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {
        "detail": {"message": "Não foi possível salvar as alterações", "references": []}
    }
    assert str(catalog_path) not in response.text
    assert "traceback" not in response.text.lower()
    assert "invalid" not in response.text


@pytest.mark.parametrize("resource", ["institutions", "participants"])
def test_catalog_write_failures_are_stable_500(client, auth_headers, monkeypatch, resource):
    module = __import__(f"clients.{resource}", fromlist=["atomic_write_json"])

    def fail_write(*args, **kwargs):
        raise PersistenceError("private path and traceback")

    monkeypatch.setattr(module, "atomic_write_json", fail_write)
    if resource == "institutions":
        path, payload = "/api/institutions", {"name": "Nova", "state": "SC", "city": "Chapecó"}
    else:
        path, payload = (
            "/api/participants",
            {
                "name": "Aluno",
                "cpf": "52998224725",
                "email": "a@e.com",
                "institutionId": "institution-001",
            },
        )
    response = client.post(path, headers=auth_headers, json=payload)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {
        "detail": {"message": "Não foi possível salvar as alterações", "references": []}
    }
    assert "private path" not in response.text
    assert "traceback" not in response.text.lower()
