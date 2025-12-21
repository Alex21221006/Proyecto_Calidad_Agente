# api/index.py
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# ===== Carga de variables (Vercel usa Environment Variables, no .env) =====
load_dotenv()

MOCK_MODE = os.getenv("MOCK_MODE", "0") == "1"
TOKEN = (os.getenv("DECOLECTA_TOKEN") or "").strip()

# ===== App =====
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

def _bearer():
    return {"Accept": "application/json", "Authorization": f"Bearer {TOKEN}"}

def _require_token_or_mock():
    if MOCK_MODE:
        return None
    if not TOKEN:
        return jsonify({"error": "Falta DECOLECTA_TOKEN en variables de entorno (o usa MOCK_MODE=1)."}), 500
    return None

# ===== Endpoints =====
@app.get("/api/dni")
def dni():
    numero = (request.args.get("numero") or "").strip()
    if not numero:
        return jsonify({"error": "Falta ?numero"}), 400

    err = _require_token_or_mock()
    if err:
        return err

    # --- MODO DEMO ---
    if MOCK_MODE:
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

    raw = data.get("data", data) if isinstance(data, dict) else {}

    nombres = (raw.get("nombres") or raw.get("first_name") or "").strip()
    ap_pat = (raw.get("apellidoPaterno") or raw.get("apellido_paterno") or raw.get("first_last_name") or "").strip()
    ap_mat = (raw.get("apellidoMaterno") or raw.get("apellido_materno") or raw.get("second_last_name") or "").strip()

    nombre_completo = (raw.get("full_name") or " ".join([ap_pat, ap_mat, nombres])).strip()

    if any([nombres, ap_pat, ap_mat, nombre_completo]):
        return jsonify({
            "numero": raw.get("document_number", numero),
            "nombres": nombres,
            "apellidoPaterno": ap_pat,
            "apellidoMaterno": ap_mat,
            "nombreCompleto": nombre_completo
        }), 200

    if status != 200:
        return jsonify({"error": data.get("message") or "API error", "detail": data}), status

    return jsonify({"error": "No se encontró información para ese DNI."}), 404


@app.get("/api/ruc")
def ruc():
    numero = (request.args.get("numero") or "").strip()
    if not numero:
        return jsonify({"error": "Falta ?numero"}), 400

    err = _require_token_or_mock()
    if err:
        return err

    if MOCK_MODE:
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
        "<h2>✅ API Decolecta funcionando (Vercel)</h2>"
        "<p>Usa <code>/api/dni?numero=XXXXXXXX</code> o <code>/api/ruc?numero=XXXXXXXXXXX</code></p>"
        f"<p>MOCK_MODE={'ON' if MOCK_MODE else 'OFF'}</p>"
    )
