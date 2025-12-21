# api.py
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# ===== Carga de variables .env =====
load_dotenv()
MOCK_MODE = os.getenv("MOCK_MODE", "0") == "1"  # Pon MOCK_MODE=1 en .env para modo demo
TOKEN = (os.getenv("DECOLECTA_TOKEN") or "").strip()

if not TOKEN and not MOCK_MODE:
    raise RuntimeError("Falta variable DECOLECTA_TOKEN en .env (o usa MOCK_MODE=1 para pruebas).")

# ===== App =====
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Habilita CORS solo para /api/*

def _bearer():
    return {"Accept": "application/json", "Authorization": f"Bearer {TOKEN}"}

# ===== Endpoints =====
@app.get("/api/dni")
def dni():
    numero = (request.args.get("numero") or "").strip()
    if not numero:
        return jsonify({"error": "Falta ?numero"}), 400

    # --- MODO DEMO (si lo activaste) ---
    if os.getenv("MOCK_MODE", "0") == "1":
        mockbook = {
            "72951012": {"nombres": "MANUEL ALEXANDER", "apellidoPaterno": "BERMEJO", "apellidoMaterno": "LOPEZ"},
            "00000001": {"nombres": "JUAN", "apellidoPaterno": "PEREZ", "apellidoMaterno": "GARCIA"},
            "00000002": {"nombres": "MARIA", "apellidoPaterno": "GOMEZ", "apellidoMaterno": "ROJAS"},
        }
        info = mockbook.get(numero)
        if not info:
            return jsonify({"error": "No se encontró información para ese DNI."}), 404
        return jsonify({
            "numero": numero,
            "nombres": info["nombres"],
            "apellidoPaterno": info["apellidoPaterno"],
            "apellidoMaterno": info["apellidoMaterno"],
            "nombreCompleto": f"{info['apellidoPaterno']} {info['apellidoMaterno']} {info['nombres']}".strip()
        })

    # --- PROVEEDOR REAL ---
    url = f"https://api.decolecta.com/v1/reniec/dni?numero={numero}"
    try:
        r = requests.get(url, headers=_bearer(), timeout=12)
        status = r.status_code
        data = r.json()
    except Exception as e:
        return jsonify({"error": "No se pudo conectar al proveedor", "detail": str(e)}), 502

    print("Decolecta status:", status)
    print("Decolecta data:", data)

    # Normaliza varias formas posibles de payload
    raw = data.get("data", data) if isinstance(data, dict) else {}

    # Soporta nombres que se ven en tu log:
    # first_name, first_last_name, second_last_name, full_name, document_number
    nombres = (
        raw.get("nombres")
        or raw.get("first_name")
        or ""
    ).strip()

    ap_pat = (
        raw.get("apellidoPaterno")
        or raw.get("apellido_paterno")
        or raw.get("first_last_name")
        or ""
    ).strip()

    ap_mat = (
        raw.get("apellidoMaterno")
        or raw.get("apellido_materno")
        or raw.get("second_last_name")
        or ""
    ).strip()

    # Usa full_name si viene listo
    nombre_completo = (
        raw.get("full_name")
        or " ".join([ap_pat, ap_mat, nombres])
    ).strip()

    # 👇 Algunos proveedores devuelven 404 aun cuando hay datos.
    # Si logramos extraer nombres, devolvemos 200 igualmente.
    if any([nombres, ap_pat, ap_mat, nombre_completo]):
        return jsonify({
            "numero": raw.get("document_number", numero),
            "nombres": nombres,
            "apellidoPaterno": ap_pat,
            "apellidoMaterno": ap_mat,
            "nombreCompleto": nombre_completo
        }), 200

    # Si realmente no hay datos, respeta el status original
    if status != 200:
        return jsonify({"error": data.get("message") or "API error", "detail": data}), status

    return jsonify({"error": "No se encontró información para ese DNI."}), 404


@app.get("/api/ruc")
def ruc():
    """
    GET /api/ruc?numero=XXXXXXXXXXX
    Pasa la respuesta tal cual desde el proveedor (o mock simple si activas MOCK_MODE).
    """
    numero = (request.args.get("numero") or "").strip()
    if not numero:
        return jsonify({"error": "Falta ?numero"}), 400

    if MOCK_MODE:
        # Mock muy básico para pruebas
        return jsonify({
            "numero": numero,
            "razonSocial": "EMPRESA DEMO S.A.C.",
            "estado": "ACTIVO",
            "condicion": "HABIDO",
            "direccion": "Av. Principal 123, Puerto Maldonado"
        }), 200

    url = f"https://api.decolecta.com/v1/sunat/ruc?numero={numero}"
    try:
        r = requests.get(url, headers=_bearer(), timeout=12)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": "No se pudo conectar al proveedor", "detail": str(e)}), 502


@app.get("/")
def home():
    return (
        "<h2>✅ API Decolecta funcionando correctamente</h2>"
        "<p>Usa <code>/api/dni?numero=XXXXXXXX</code> o <code>/api/ruc?numero=XXXXXXXXXXX</code></p>"
        f"<p>MOCK_MODE={'ON' if MOCK_MODE else 'OFF'}</p>"
    )

# ===== Run (solo dev). En servidor usa gunicorn/uvicorn =====
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
