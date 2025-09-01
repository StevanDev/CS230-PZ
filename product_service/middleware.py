import time, uuid, json
from flask import request, g
def request_logger(app):

    @app.before_request
    def _start():
        g.start_time = time.time()
        g.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    
    @app.after_request
    def _log(resp):
        duration = int((time.time() - g.get("start_time", time.time())) * 1000)
        try: body = request.get_json(silent=True)
        except Exception: body = None
        app.logger.info(json.dumps({
            "request_id": g.get("request_id"), "method": request.method,
            "path": request.path, "status": resp.status_code,
            "duration_ms": duration, "ip": request.remote_addr, "body": body
        }))
        resp.headers["X-Request-ID"] = g.get("request_id")
        return resp
