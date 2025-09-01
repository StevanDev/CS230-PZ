from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import select
from db import Base, engine, SessionLocal
from models import Product
from middleware import request_logger
from events import start_events_listener
app = Flask(__name__); CORS(app); request_logger(app)
Base.metadata.create_all(bind=engine)
start_events_listener(app.logger)

@app.get("/health")
def health(): return {"status":"ok"}

@app.get("/products")
def list_products():
    with SessionLocal() as db:
        items = db.execute(select(Product)).scalars().all()
        return jsonify([{"id":p.id,"name":p.name,"price":p.price,"currency":p.currency,"stock":p.stock} for p in items])

@app.post("/products")
def create_product():
    d = request.get_json() or {}
    name, price = d.get("name"), d.get("price")
    currency = d.get("currency","USD"); stock = d.get("stock",0)
    if not name or price is None: return {"error":"name and price required"}, 400
    with SessionLocal() as db:
        p = Product(name=name, price=price, currency=currency, stock=stock)
        db.add(p); db.commit(); db.refresh(p)
        return {"id":p.id,"name":p.name,"price":p.price,"currency":p.currency,"stock":p.stock}, 201

@app.get("/products/<int:pid>")
def get_product(pid):
    with SessionLocal() as db:
        p = db.get(Product, pid)
        if not p: return {"error":"not found"}, 404
        return {"id":p.id,"name":p.name,"price":p.price,"currency":p.currency,"stock":p.stock}

@app.put("/products/<int:pid>")
def update_product(pid):
    d = request.get_json() or {}
    with SessionLocal() as db:
        p = db.get(Product, pid)
        if not p: return {"error":"not found"}, 404
        p.name = d.get("name", p.name); p.price = d.get("price", p.price)
        p.currency = d.get("currency", p.currency); p.stock = d.get("stock", p.stock)
        db.commit(); return {"id":p.id,"name":p.name,"price":p.price,"currency":p.currency,"stock":p.stock}

@app.delete("/products/<int:pid>")
def delete_product(pid):
    with SessionLocal() as db:
        p = db.get(Product, pid)
        if not p: return {"error":"not found"}, 404
        db.delete(p); db.commit(); return {"status":"deleted"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
