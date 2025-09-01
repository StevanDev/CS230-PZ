import os
from urllib.parse import urljoin
from flask import Flask, request, Response
from flask_cors import CORS
import requests
from middleware import request_logger
from itsdangerous import URLSafeSerializer, BadSignature

app = Flask(__name__)
CORS(
    app,
    resources={r"/api/*": {"origins": os.environ.get("FRONTEND_ORIGIN", "*")}},
    supports_credentials=False,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-Request-ID"],
)

request_logger(app)

PRODUCTS = os.environ.get("DOWNSTREAM_PRODUCTS_URL", "http://product_service:5001")
ORDERS   = os.environ.get("DOWNSTREAM_ORDERS_URL",   "http://order_service:5002")
USERS    = os.environ.get("DOWNSTREAM_USERS_URL",    "http://user_service:5003")

AUTH_SECRET = os.environ.get("AUTH_SECRET", "devsecret")
signer = URLSafeSerializer(AUTH_SECRET, salt="auth")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/auth/register")
def api_register():
    r = requests.post(urljoin(USERS + "/", "auth/register"), json=request.get_json(silent=True) or {})
    return Response(r.content, r.status_code, r.headers.items())

@app.post("/api/auth/login")
def api_login():
    r = requests.post(urljoin(USERS + "/", "auth/login"), json=request.get_json(silent=True) or {})
    if r.status_code != 200:
        return Response(r.content, r.status_code, r.headers.items())
    data = r.json()
    user = data.get("user")
    if not user:
        return {"error": "login failed"}, 401
    token = signer.dumps({
        "id": user["id"], "role": user["role"],
        "name": user["name"], "email": user["email"]
    })
    return {"token": token, "user": user}

def require_token():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = signer.loads(token)
        return payload 
    except BadSignature:
        return None

def is_admin(user):
    return user and user.get("role") == "admin"

def _proxy(base_url, subpath=""):
    url = urljoin(base_url + "/", subpath)
    method = request.method
    headers = dict(request.headers)
    headers["X-Request-ID"] = request.headers.get("X-Request-ID", headers.get("x-request-id", ""))

    json_body = request.get_json(silent=True) if request.is_json else None
    data = None if json_body is not None else request.get_data()
    resp = requests.request(method, url, headers=headers, params=request.args, json=json_body, data=data)
    excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    resp_headers = [(name, value) for (name, value) in resp.headers.items() if name.lower() not in excluded]
    return Response(resp.content, resp.status_code, resp_headers)

@app.route("/api/products", methods=["GET"])
def products_list():
    return _proxy(PRODUCTS, "products")

@app.route("/api/products", methods=["POST"])
def products_create():
    user = require_token()
    if not is_admin(user):
        return {"error": "admin required"}, 403
    return _proxy(PRODUCTS, "products")

@app.route("/api/products/<path:subpath>", methods=["GET"])
def products_get(subpath=""):
    return _proxy(PRODUCTS, f"products/{subpath}")

@app.route("/api/products/<path:subpath>", methods=["PUT", "DELETE"])
def products_modify(subpath=""):
    user = require_token()
    if not is_admin(user):
        return {"error": "admin required"}, 403
    return _proxy(PRODUCTS, f"products/{subpath}")

@app.route("/api/orders", methods=["GET"])
def orders_list():
    user = require_token()
    args = dict(request.args)
    if not is_admin(user):
        if not user:
            return {"error": "auth required"}, 401
        args["user_id"] = str(user["id"])
    url = urljoin(ORDERS + "/", "orders")
    r = requests.get(url, params=args, headers={"X-Request-ID": request.headers.get("X-Request-ID", "")})
    return Response(r.content, r.status_code, r.headers.items())

@app.route("/api/orders", methods=["POST"])
def orders_create():
    user = require_token()
    if not user:
        return {"error": "auth required"}, 401
    body = request.get_json(silent=True) or {}
    body["user_id"] = user["id"]
    url = urljoin(ORDERS + "/", "orders")
    r = requests.post(url, json=body, headers={"X-Request-ID": request.headers.get("X-Request-ID", "")})
    return Response(r.content, r.status_code, r.headers.items())

@app.route("/api/orders/<path:subpath>", methods=["DELETE"])
def orders_delete(subpath=""):
    user = require_token()
    if not is_admin(user):
        return {"error": "admin required"}, 403
    return _proxy(ORDERS, f"orders/{subpath}")

@app.get("/api/users")
def proxy_users():
    user = require_token()
    if not is_admin(user):
        return {"error": "admin required"}, 403
    return _proxy(USERS, "users")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
