import os, json, requests
from redis import Redis
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import select
from db import Base, engine, SessionLocal
from models import Order
from middleware import request_logger

app = Flask(__name__)
CORS(app)
request_logger(app)

Base.metadata.create_all(bind=engine)

PRODUCT_BASE_URL = os.environ.get("PRODUCT_BASE_URL", "http://product_service:5001")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/orders")
def list_orders():
    user_id = request.args.get("user_id", type=int)
    with SessionLocal() as db:
        q = select(Order)
        if user_id is not None:
            q = q.where(Order.user_id == user_id)
        items = db.execute(q).scalars().all()
        return jsonify([
            {
                "id": o.id,
                "product_id": o.product_id,
                "quantity": o.quantity,
                "user_id": o.user_id,
                "status": o.status
            } for o in items
        ])

@app.post("/orders")
def create_order():
    d = request.get_json() or {}
    pid = d.get("product_id")
    qty = int(d.get("quantity", 1))
    user_id = d.get("user_id")
    if not pid or qty <= 0:
        return {"error": "product_id and quantity>0 required"}, 400

    try:
        r = requests.get(f"{PRODUCT_BASE_URL}/products/{pid}", timeout=5)
        if r.status_code != 200:
            return {"error": "product not found"}, 404
        if (r.json().get("stock", 0) < qty):
            return {"error": "insufficient stock"}, 409
    except Exception as e:
        return {"error": f"product service error: {str(e)}"}, 502

    with SessionLocal() as db:
        o = Order(product_id=pid, quantity=qty, user_id=user_id, status="CREATED")
        db.add(o)
        db.commit()
        db.refresh(o)
        redis_client.publish("events", json.dumps({
            "type": "order_created",
            "order_id": o.id,
            "product_id": pid,
            "quantity": qty
        }))
        return {
            "id": o.id, "product_id": o.product_id, "quantity": o.quantity,
            "user_id": o.user_id, "status": o.status
        }, 201

@app.get("/orders/<int:oid>")
def get_order(oid):
    with SessionLocal() as db:
        o = db.get(Order, oid)
        if not o:
            return {"error": "not found"}, 404
        return {
            "id": o.id, "product_id": o.product_id, "quantity": o.quantity,
            "user_id": o.user_id, "status": o.status
        }

@app.route("/orders/<int:oid>", methods=["DELETE"])
def delete_order(oid):
    with SessionLocal() as db:
        o = db.get(Order, oid)
        if not o:
            return {"error": "not found"}, 404
        db.delete(o)
        db.commit()
        return {"status": "deleted"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)