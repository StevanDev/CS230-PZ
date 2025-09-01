import os, json, threading, time
from redis import Redis
from db import SessionLocal
from models import Product
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

def _handle_event(msg, logger):
    try:
        data = json.loads(msg.get("data"))
        if data.get("type") == "order_created":
            product_id = data.get("product_id"); qty = int(data.get("quantity",0))
            with SessionLocal() as db:
                p = db.get(Product, product_id)
                if p and p.stock >= qty:
                    p.stock -= qty; db.commit()
                    logger.info({"event":"stock_decremented","product_id":product_id,"quantity":qty,"new_stock":p.stock})
                else:
                    logger.warning({"event":"stock_not_decremented","product_id":product_id,"quantity":qty})
    except Exception as e:
        logger.exception(e)

def start_events_listener(logger):
    def _run():
        time.sleep(1.5)
        r = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        p = r.pubsub(); p.subscribe("events"); logger.info("Subscribed to events")
        for m in p.listen():
            if m["type"] == "message": _handle_event(m, logger)
    threading.Thread(target=_run, daemon=True).start()
