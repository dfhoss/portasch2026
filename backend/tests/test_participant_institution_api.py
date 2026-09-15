import pytest
from fastapi import status


@pytest.mark.parametrize("path", ["/institutions", "/participants"])
def test_catalog_routes_require_authentication(client, path):
    assert client.get(path).status_code == status.HTTP_401_UNAUTHORIZED


def test_institution_crud_returns_public_contract(client, auth_headers):
    created = client.post(
        "/institutions",
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
    assert client.get(f"/institutions/{identifier}", headers=auth_headers).json() == institution
    updated = client.put(
        f"/institutions/{identifier}",
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
    deleted = client.delete(f"/institutions/{identifier}", headers=auth_headers)
    assert deleted.status_code == status.HTTP_204_NO_CONTENT
    assert deleted.content == b""


def test_participant_crud_normalizes_cpf_and_alias(client, auth_headers):
    institution = client.get("/institutions", headers=auth_headers).json()[0]
    response = client.post(
        "/participants",
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
    assert (
        client.get(f"/participants/{participant['id']}", headers=auth_headers).json() == participant
    )
    assert (
        client.put(
            f"/participants/{participant['id']}",
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
        client.delete(f"/participants/{participant['id']}", headers=auth_headers).status_code
        == status.HTTP_204_NO_CONTENT
    )


def test_api_maps_not_found_duplicate_invalid_and_in_use(client, auth_headers):
    assert client.get("/institutions/missing", headers=auth_headers).status_code == 404
    payload = {"name": "Conflito", "state": "SC", "city": "Chapecó"}
    assert client.post("/institutions", headers=auth_headers, json=payload).status_code == 201
    assert (
        client.post(
            "/institutions", headers=auth_headers, json={**payload, "name": " conflito "}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/institutions", headers=auth_headers, json={**payload, "name": " "}
        ).status_code
        == 422
    )
    institution = client.get("/institutions", headers=auth_headers).json()[0]
    participant = {
        "name": "Aluno",
        "cpf": "52998224725",
        "email": "a@e.com",
        "institutionId": institution["id"],
    }
    assert client.post("/participants", headers=auth_headers, json=participant).status_code == 201
    assert (
        client.delete(f"/institutions/{institution['id']}", headers=auth_headers).status_code == 409
    )
    assert client.post("/participants", headers=auth_headers, json=participant).status_code == 409
    assert (
        client.post(
            "/participants", headers=auth_headers, json={**participant, "cpf": "123"}
        ).status_code
        == 422
    )
