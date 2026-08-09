"""FDE 实战：API 鉴权 + 限流中间件（Flask）。
生产用 Redis 做分布式限流，并改用 JWT 替代静态 Key。
"""
from flask import Flask, request, jsonify
from functools import wraps
import time

app = Flask(__name__)
API_KEY = "你的服务端Key"
RATE = {}  # ip -> [时间戳]

def rate_limit(f):
    @wraps(f)
    def w():
        ip = request.remote_addr
        now = time.time()
        RATE[ip] = [t for t in RATE.get(ip, []) if now - t < 60]
        if len(RATE[ip]) >= 20:
            return jsonify({"err": "限流"}), 429
        RATE[ip].append(now)
        return f()
    return w

@app.route("/chat")
@rate_limit
def chat():
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"err": "未授权"}), 401
    return jsonify({"reply": "hi"})

if __name__ == "__main__":
    app.run()
