# -*- coding: utf-8 -*-
# --- SearchName (Flask): serve o site estático e a busca por nickname no mesmo serviço. --- #

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.garena import CLIENT_HOSTS, GarenaError, search_by_nickname  # noqa: E402

app = Flask(__name__)

# --- pasta do site estático (public/). --- #
PUBLIC_DIR = ROOT / "public"

# --- origens permitidas para CORS. --- #
ALLOWED_ORIGINS = {
    "https://ramonmods.onrender.com",
    "https://ramonmods.github.io",
}
LOCAL_ORIGIN = re.compile(r"^http://(?:localhost|127\.0\.0\.1)(?::\d+)?$")

# --- cache simples: (nickname, região) -> (expira_em, resultado). --- #
_CACHE: dict[tuple[str, str], tuple[float, dict]] = {}
_CACHE_TTL = 120  # --- 2 minutos --- #

# --- limite simples por IP: 20 buscas por minuto. --- #
_HITS: dict[str, list[float]] = {}
_LIMIT = 20
_WINDOW = 60


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "?"


def _rate_limited(ip: str) -> bool:
    agora = time.time()
    marcas = [t for t in _HITS.get(ip, []) if agora - t < _WINDOW]
    marcas.append(agora)
    _HITS[ip] = marcas
    return len(marcas) > _LIMIT


def _origin_allowed(origin: str) -> bool:
    return (
        origin in ALLOWED_ORIGINS
        or origin.endswith(".onrender.com")
        or bool(LOCAL_ORIGIN.match(origin))
        or origin == "null"
    )


@app.after_request
def _cors(resp):
    origin = request.headers.get("Origin", "")
    if origin and _origin_allowed(origin):
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
    resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Cache-Control"] = "no-store"
    return resp


# --- health check do Render. --- #
@app.get("/healthz")
def health():
    return jsonify({"servico": "SearchName", "status": "online"})


@app.get("/regions")
def regions():
    return jsonify({"regions": sorted(CLIENT_HOSTS)})


@app.get("/search")
def handle_search():
    apelido = (request.args.get("name") or request.args.get("nickname") or "").strip()
    regiao = (request.args.get("server_name") or request.args.get("region") or "BR").strip().upper()

    if not apelido:
        return jsonify({"error": "Parâmetro 'name' é obrigatório."}), 400
    if len(apelido) < 3:
        return jsonify({"error": "Digite pelo menos 3 caracteres."}), 400
    if regiao not in CLIENT_HOSTS:
        return jsonify({"error": "Região inválida. Use: %s" % ", ".join(sorted(CLIENT_HOSTS))}), 400

    if _rate_limited(_client_ip()):
        return jsonify({"error": "Muitas buscas. Tente em um minuto."}), 429

    chave = (apelido.lower(), regiao)
    agora = time.time()
    em_cache = _CACHE.get(chave)
    if em_cache and em_cache[0] > agora:
        return jsonify({**em_cache[1], "cached": True})

    try:
        resultado = search_by_nickname(apelido, regiao)
    except GarenaError as exc:
        return jsonify({"error": str(exc)}), 502

    _CACHE[chave] = (agora + _CACHE_TTL, resultado)
    return jsonify(resultado)


# --- site estático: qualquer caminho que não seja API cai aqui. --- #
@app.get("/", defaults={"path": ""})
@app.get("/<path:path>")
def serve_site(path: str):
    if path:
        alvo = PUBLIC_DIR / path
        # --- pasta (ex.: /search/): entrega o index.html de dentro. --- #
        if alvo.is_dir():
            interno = alvo / "index.html"
            if interno.is_file():
                return send_from_directory(PUBLIC_DIR, path.rstrip("/") + "/index.html")
        elif alvo.is_file():
            return send_from_directory(PUBLIC_DIR, path)
    return send_from_directory(PUBLIC_DIR, "index.html")


@app.errorhandler(404)
def _404(_):
    return jsonify({"error": "não encontrado"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
