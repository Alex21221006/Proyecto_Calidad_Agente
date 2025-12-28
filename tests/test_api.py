# tests/test_api.py
import importlib
import os

import pytest


@pytest.fixture()
def api_module(monkeypatch):
    """
    Recarga el módulo api.index con variables de entorno controladas.
    Así podemos probar MOCK_MODE ON/OFF y TOKEN presente/ausente.
    """
    # Limpia variables para partir “neutro”
    monkeypatch.delenv("MOCK_MODE", raising=False)
    monkeypatch.delenv("DECOLECTA_TOKEN", raising=False)

    # Importa y devuelve el módulo
    import api.index as m
    importlib.reload(m)
    return m


def make_client(module):
    module.app.testing = True
    return module.app.test_client()


# --------------------------
# HOME
# --------------------------
def test_home_ok(api_module):
    client = make_client(api_module)
    res = client.get("/")
    assert res.status_code == 200
    body = res.data.decode("utf-8")
    assert "API Decolecta funcionando" in body


# --------------------------
# DNI - validaciones básicas
# --------------------------
def test_dni_missing_numero_returns_400(api_module):
    client = make_client(api_module)
    res = client.get("/api/dni")  # sin ?numero
    assert res.status_code == 400
    assert res.get_json()["error"] == "Falta ?numero"


def test_dni_token_missing_and_mock_off_returns_500(monkeypatch):
    # MOCK_MODE=0 y TOKEN vacío -> debe dar 500
    monkeypatch.setenv("MOCK_MODE", "0")
    monkeypatch.delenv("DECOLECTA_TOKEN", raising=False)

    import api.index as m
    importlib.reload(m)

    client = make_client(m)
    res = client.get("/api/dni?numero=72951012")
    assert res.status_code == 500
    data = res.get_json()
    assert "Falta DECOLECTA_TOKEN" in data["error"]


# --------------------------
# DNI - modo MOCK
# --------------------------
def test_dni_mock_ok(monkeypatch):
    monkeypatch.setenv("MOCK_MODE", "1")
    monkeypatch.delenv("DECOLECTA_TOKEN", raising=False)

    import api.index as m
    importlib.reload(m)

    client = make_client(m)
    res = client.get("/api/dni?numero=72951012")
    assert res.status_code == 200
    data = res.get_json()
    assert data["numero"] == "72951012"
    assert "nombres" in data
    assert "apellidoPaterno" in data
    assert "apellidoMaterno" in data
    assert "nombreCompleto" in data


def test_dni_mock_not_found(monkeypatch):
    monkeypatch.setenv("MOCK_MODE", "1")

    import api.index as m
    importlib.reload(m)

    client = make_client(m)
    res = client.get("/api/dni?numero=99999999")
    assert res.status_code == 404
    assert "No se encontró" in res.get_json()["error"]


# --------------------------
# RUC - validaciones básicas
# --------------------------
def test_ruc_missing_numero_returns_400(api_module):
    client = make_client(api_module)
    res = client.get("/api/ruc")  # sin ?numero
    assert res.status_code == 400
    assert res.get_json()["error"] == "Falta ?numero"


def test_ruc_token_missing_and_mock_off_returns_500(monkeypatch):
    monkeypatch.setenv("MOCK_MODE", "0")
    monkeypatch.delenv("DECOLECTA_TOKEN", raising=False)

    import api.index as m
    importlib.reload(m)

    client = make_client(m)
    res = client.get("/api/ruc?numero=12345678901")
    assert res.status_code == 500
    assert "Falta DECOLECTA_TOKEN" in res.get_json()["error"]


# --------------------------
# RUC - modo MOCK
# --------------------------
def test_ruc_mock_ok(monkeypatch):
    monkeypatch.setenv("MOCK_MODE", "1")

    import api.index as m
    importlib.reload(m)

    client = make_client(m)
    res = client.get("/api/ruc?numero=12345678901")
    assert res.status_code == 200
    data = res.get_json()
    assert data["numero"] == "12345678901"
    assert data["razonSocial"] == "EMPRESA DEMO S.A.C."


# --------------------------
# Modo REAL - sin internet (mockeando requests.get)
# --------------------------
def test_dni_real_success_parsing(monkeypatch):
    """
    Simula respuesta 200 del proveedor y verifica el parseo a tu formato final.
    """
    monkeypatch.setenv("MOCK_MODE", "0")
    monkeypatch.setenv("DECOLECTA_TOKEN", "token_fake")

    import api.index as m
    importlib.reload(m)

    class FakeResp:
        status_code = 200

        def json(self):
            return {
                "data": {
                    "document_number": "11111111",
                    "nombres": "CARLOS",
                    "apellidoPaterno": "LOPEZ",
                    "apellidoMaterno": "DIAZ",
                }
            }

    def fake_get(url, headers=None, timeout=None):
        return FakeResp()

    monkeypatch.setattr(m.requests, "get", fake_get)

    client = make_client(m)
    res = client.get("/api/dni?numero=11111111")
    assert res.status_code == 200
    data = res.get_json()
    assert data["numero"] == "11111111"
    assert data["nombres"] == "CARLOS"
    assert data["apellidoPaterno"] == "LOPEZ"
    assert data["apellidoMaterno"] == "DIAZ"
    assert "LOPEZ DIAZ CARLOS" in data["nombreCompleto"]


def test_dni_real_provider_error_status(monkeypatch):
    """
    Simula respuesta no-200 del proveedor para validar tu rama:
    if status != 200: return error, status
    """
    monkeypatch.setenv("MOCK_MODE", "0")
    monkeypatch.setenv("DECOLECTA_TOKEN", "token_fake")

    import api.index as m
    importlib.reload(m)

    class FakeResp:
        status_code = 401

        def json(self):
            return {"message": "Unauthorized"}

    def fake_get(url, headers=None, timeout=None):
        return FakeResp()

    monkeypatch.setattr(m.requests, "get", fake_get)

    client = make_client(m)
    res = client.get("/api/dni?numero=22222222")
    assert res.status_code == 401
    assert res.get_json()["error"] in ("Unauthorized", "API error")
