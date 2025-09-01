import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import select
from werkzeug.security import generate_password_hash, check_password_hash
from db import Base, engine, SessionLocal
from models import User
from middleware import request_logger

app = Flask(__name__)
CORS(app)
request_logger(app)

Base.metadata.create_all(bind=engine)

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
ADMIN_NAME = os.environ.get("ADMIN_NAME", "Admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

def ensure_admin():
    with SessionLocal() as db:
        existing = db.execute(select(User).where(User.email == ADMIN_EMAIL)).scalar_one_or_none()
        if not existing:
            u = User(
                email=ADMIN_EMAIL,
                name=ADMIN_NAME,
                password_hash=generate_password_hash(ADMIN_PASSWORD),
                role="admin"
            )
            db.add(u)
            db.commit()
ensure_admin()

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/users")
def list_users():
    with SessionLocal() as db:
        items = db.execute(select(User)).scalars().all()
        return jsonify([{"id":u.id,"email":u.email,"name":u.name,"role":u.role} for u in items])

@app.post("/auth/register")
def register():
    data = request.get_json() or {}
    email = data.get("email")
    name = data.get("name")
    password = data.get("password")
    if not email or not name or not password:
        return {"error":"email, name, password required"}, 400
    with SessionLocal() as db:
        exists = db.execute(select(User).where(User.email==email)).scalar_one_or_none()
        if exists:
            return {"error":"email already registered"}, 409
        u = User(email=email, name=name, password_hash=generate_password_hash(password), role="user")
        db.add(u)
        db.commit()
        db.refresh(u)
        return {"id":u.id,"email":u.email,"name":u.name,"role":u.role}, 201

@app.post("/auth/login")
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return {"error":"email and password required"}, 400
    with SessionLocal() as db:
        u = db.execute(select(User).where(User.email==email)).scalar_one_or_none()
        if not u or not check_password_hash(u.password_hash, password):
            return {"error":"invalid credentials"}, 401
        return {
            "user": {"id":u.id,"email":u.email,"name":u.name,"role":u.role}
        }

@app.get("/users/<int:uid>")
def get_user(uid):
    with SessionLocal() as db:
        u = db.get(User, uid)
        if not u: return {"error":"not found"}, 404
        return {"id":u.id,"email":u.email,"name":u.name,"role":u.role}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
