import json
from pathlib import Path

import pytest
from clients.json_store import PersistenceError
from fastapi import status


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def canonical_schedule(
    *, location: str | None = "Auditório do Bloco A", axis: str | None = "geral"
) -> dict:
    group = {
        "id": "grupo",
        "title": "Grupo",
        "items": [
            {
                "id": "atividade",
                "title": "Atividade",
                "sessions": [
                    {
                        "startTime": "09:00",
                        "endTime": "10:00",
                        "location": location,
                    }
                ],
            }
        ],
    }
    if axis is not None:
        group["knowledgeAxis"] = axis
    return {
        "version": 1,
        "eventDate": "2026-10-26",
        "sections": [{"id": "secao", "title": "Seção", "groups": [group]}],
    }


@pytest.mark.parametrize(
    "path",
    [
        "/admin/api/schedule",
        "/admin/api/locations",
        "/admin/api/knowledge-axes",
    ],
)
def test_admin_api_prefixes_require_authentication(client, path: str):
    """Removing CurrentTokenData from any administrative router must make this fail."""
    response = client.get(path)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("PUT", "/admin/api/schedule", canonical_schedule()),
        ("POST", "/admin/api/locations", {"name": "Novo local"}),
        ("PUT", "/admin/api/locations/loc-001", {"name": "Novo local"}),
        ("DELETE", "/admin/api/locations/loc-001", None),
        ("POST", "/admin/api/knowledge-axes", {"name": "Novo eixo"}),
        ("PUT", "/admin/api/knowledge-axes/geral", {"name": "Novo eixo"}),
        ("DELETE", "/admin/api/knowledge-axes/geral", None),
    ],
)
def test_admin_mutation_routes_require_authentication(
    client, method: str, path: str, payload: dict | None
):
    """Removing authentication from any administrative write route must make this fail."""
    response = client.request(method, path, json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_schedule_returns_public_json(client, auth_headers):
    """Failing to register or serialize the schedule route must make this fail."""
    response = client.get("/admin/api/schedule", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["version"] == 1
    assert payload["eventDate"] == "2026-10-26"
    assert "event_date" not in payload
    group = payload["sections"][0]["groups"][0]
    assert group["knowledgeAxis"] == "geral"
    assert "knowledge_axis" not in group
    session = group["items"][0]["sessions"][0]
    assert session["startTime"] == "08:30"
    assert session["endTime"] == "21:00"


@pytest.mark.parametrize("failure", ["missing", "malformed-json", "invalid-document"])
def test_get_schedule_maps_read_failures_to_structured_non_leaking_500(
    client, auth_headers, temporary_database, failure: str
):
    """Letting schedule read errors escape the HTTP boundary must make this fail."""
    if failure == "missing":
        temporary_database.schedule.unlink()
    elif failure == "malformed-json":
        temporary_database.schedule.write_text('{"private filesystem detail":', encoding="utf-8")
    else:
        temporary_database.schedule.write_text(
            json.dumps({"version": 0, "eventDate": "not-a-date", "sections": []}),
            encoding="utf-8",
        )

    response = client.get("/admin/api/schedule", headers=auth_headers)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {
        "detail": {"message": "Não foi possível carregar a agenda", "references": []}
    }
    assert "private filesystem detail" not in response.text
    assert str(temporary_database.schedule) not in response.text


def test_put_schedule_persists_and_returns_backend_generated_ids(
    client, auth_headers, temporary_database
):
    """Trusting missing client IDs instead of canonicalizing them must make this fail."""
    payload = canonical_schedule()
    payload["sections"][0]["id"] = ""
    payload["sections"][0]["groups"][0].pop("id")
    payload["sections"][0]["groups"][0]["items"][0]["id"] = None

    response = client.put("/admin/api/schedule", json=payload, headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    returned = response.json()
    assert returned["sections"][0]["id"] == "secao"
    assert returned["sections"][0]["groups"][0]["id"] == "grupo"
    assert returned["sections"][0]["groups"][0]["items"][0]["id"] == "atividade"
    returned_group = returned["sections"][0]["groups"][0]
    assert returned_group["knowledgeAxis"] == "geral"
    assert "knowledge_axis" not in returned_group
    returned_session = returned_group["items"][0]["sessions"][0]
    assert returned_session["startTime"] == "09:00"
    assert returned_session["endTime"] == "10:00"
    assert read_json(temporary_database.schedule) == returned


@pytest.mark.parametrize(
    ("location", "axis", "reference"),
    [
        ("Local inexistente", "geral", "Local inexistente"),
        ("Auditórios dos Blocos A e B", "eixo-inexistente", "eixo-inexistente"),
    ],
)
def test_put_schedule_maps_invalid_catalog_references_to_structured_conflict(
    client, auth_headers, location: str, axis: str, reference: str
):
    """Persisting dangling location or axis references must make this fail."""
    response = client.put(
        "/admin/api/schedule",
        json=canonical_schedule(location=location, axis=axis),
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    detail = response.json()["detail"]
    assert detail["message"].startswith("Referências inválidas na agenda")
    assert reference in detail["references"]


def test_list_locations_returns_catalog(client, auth_headers):
    """Returning anything except the real temporary location catalog must make this fail."""
    response = client.get("/admin/api/locations", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["id"] == "loc-001"
    assert response.json()[0]["name"] == "Auditório do Bloco A"
    assert response.json()[0]["category"] == "blocos"


def test_location_crud_create_rename_and_delete(client, auth_headers):
    """Breaking any successful location write contract must make this fail."""
    created = client.post(
        "/admin/api/locations", json={"name": "  Novo auditório  "}, headers=auth_headers
    )
    assert created.status_code == status.HTTP_201_CREATED
    assert created.json()["id"] == "loc-039"
    assert created.json()["name"] == "Novo auditório"

    renamed = client.put(
        "/admin/api/locations/loc-039",
        json={"name": "Auditório renovado"},
        headers=auth_headers,
    )
    assert renamed.status_code == status.HTTP_200_OK
    assert renamed.json()["name"] == "Auditório renovado"

    deleted = client.delete("/admin/api/locations/loc-039", headers=auth_headers)
    assert deleted.status_code == status.HTTP_204_NO_CONTENT
    assert deleted.content == b""
    assert all(
        item["id"] != "loc-039"
        for item in client.get("/admin/api/locations", headers=auth_headers).json()
    )


def test_location_group_can_be_created_with_a_category(client, auth_headers):
    response = client.post(
        "/admin/api/locations/groups",
        json={"name": "Bloco novo", "category": "blocos"},
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "Bloco novo"
    assert response.json()["category"] == "blocos"


def test_list_knowledge_axes_returns_catalog(client, auth_headers):
    """Returning anything except the real temporary axis catalog must make this fail."""
    response = client.get("/admin/api/knowledge-axes", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert {"id": "geral", "name": "Geral"} in response.json()


def test_knowledge_axis_crud_create_rename_and_delete(client, auth_headers):
    """Breaking any successful knowledge-axis write contract must make this fail."""
    created = client.post(
        "/admin/api/knowledge-axes",
        json={"name": "  Ciências do Mar  "},
        headers=auth_headers,
    )
    assert created.status_code == status.HTTP_201_CREATED
    assert created.json() == {"id": "ciencias-do-mar", "name": "Ciências do Mar"}

    renamed = client.put(
        "/admin/api/knowledge-axes/ciencias-do-mar",
        json={"name": "Ciências oceânicas"},
        headers=auth_headers,
    )
    assert renamed.status_code == status.HTTP_200_OK
    assert renamed.json() == {"id": "ciencias-do-mar", "name": "Ciências oceânicas"}

    deleted = client.delete("/admin/api/knowledge-axes/ciencias-do-mar", headers=auth_headers)
    assert deleted.status_code == status.HTTP_204_NO_CONTENT
    assert deleted.content == b""
    assert all(
        item["id"] != "ciencias-do-mar"
        for item in client.get("/admin/api/knowledge-axes", headers=auth_headers).json()
    )


@pytest.mark.parametrize(
    ("prefix", "missing_id"),
    [
        ("/admin/api/locations", "loc-999"),
        ("/admin/api/knowledge-axes", "eixo-inexistente"),
    ],
)
def test_catalog_missing_resource_maps_to_structured_404(
    client, auth_headers, prefix: str, missing_id: str
):
    """Leaking ResourceNotFoundError as a server error must make this fail."""
    response = client.put(
        f"{prefix}/{missing_id}", json={"name": "Novo nome"}, headers=auth_headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"]["references"] == []
    assert missing_id in response.json()["detail"]["message"]


@pytest.mark.parametrize(
    ("prefix", "name"),
    [
        ("/admin/api/locations", "  AUDITÓRIO DO BLOCO A  "),
        ("/admin/api/knowledge-axes", "  GERAL  "),
    ],
)
def test_catalog_normalized_duplicate_maps_to_structured_409(
    client, auth_headers, prefix: str, name: str
):
    """Comparing duplicate names without normalization must make this fail."""
    response = client.post(prefix, json={"name": name}, headers=auth_headers)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"]["references"] == []
    assert response.json()["detail"]["message"].startswith("Já existe")


@pytest.mark.parametrize(
    ("path", "resource_id"),
    [
        ("/admin/api/locations/loc-001", "loc-001"),
        ("/admin/api/knowledge-axes/geral", "geral"),
    ],
)
def test_catalog_delete_in_use_maps_to_structured_409_with_references(
    client, auth_headers, path: str, resource_id: str
):
    """Deleting used resources or dropping their references must make this fail."""
    response = client.delete(path, headers=auth_headers)

    assert response.status_code == status.HTTP_409_CONFLICT
    detail = response.json()["detail"]
    assert resource_id in detail["message"]
    assert detail["references"]


@pytest.mark.parametrize(
    ("prefix", "name"),
    [
        ("/admin/api/locations", "   "),
        ("/admin/api/knowledge-axes", "!!!"),
    ],
)
def test_catalog_invalid_cleaned_name_maps_to_structured_422(
    client, auth_headers, prefix: str, name: str
):
    """Accepting unusable display names or leaking domain validation must make this fail."""
    response = client.post(prefix, json={"name": name}, headers=auth_headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["detail"]["references"] == []
    assert response.json()["detail"]["message"].startswith("O nome de")


class FailingRepository:
    def create(self, name: str, *args, **kwargs) -> dict:
        raise PersistenceError("filesystem path and internal secret")


@pytest.mark.parametrize(
    ("dependency_module", "dependency_name", "prefix"),
    [
        ("routes.locations", "get_location_repository", "/admin/api/locations"),
        (
            "routes.knowledge_axes",
            "get_knowledge_axis_repository",
            "/admin/api/knowledge-axes",
        ),
    ],
)
def test_catalog_persistence_failure_maps_to_non_leaking_500(
    client,
    auth_headers,
    dependency_module: str,
    dependency_name: str,
    prefix: str,
):
    """Exposing persistence exception text through the API must make this fail."""
    import importlib

    from app import app

    dependency = getattr(importlib.import_module(dependency_module), dependency_name)
    app.dependency_overrides[dependency] = FailingRepository

    response = client.post(prefix, json={"name": "Novo nome"}, headers=auth_headers)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {
        "detail": {"message": "Não foi possível salvar as alterações", "references": []}
    }
    assert "filesystem" not in response.text


def test_schedule_persistence_failure_maps_to_non_leaking_500(client, auth_headers):
    """Exposing schedule persistence internals through the API must make this fail."""
    from app import app
    from routes.schedule import get_schedule_replacer

    def fail_replace(document, path):
        raise PersistenceError("filesystem path and internal secret")

    app.dependency_overrides[get_schedule_replacer] = lambda: fail_replace

    response = client.put("/admin/api/schedule", json=canonical_schedule(), headers=auth_headers)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {
        "detail": {"message": "Não foi possível salvar as alterações", "references": []}
    }
    assert "filesystem" not in response.text
