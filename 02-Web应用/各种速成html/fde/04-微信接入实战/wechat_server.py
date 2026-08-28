"""FDE 实战：微信公众号回调骨架（Flask）。
前置：云服务器 + 公网域名 + HTTPS + 公众号后台配置 Token 与回调 URL。
完整生产还需：消息体 XML 解析、AES 加解密、客服消息异步回包（突破 5 秒限制）。
"""
from flask import Flask, request
import hashlib

app = Flask(__name__)
TOKEN = "你的公众号Token"

@app.route("/wechat", methods=["GET"])
def verify():
    sig = request.args.get("signature")
    ts, nonce, echostr = (request.args.get("timestamp"),
                          request.args.get("nonce"),
                          request.args.get("echostr"))
    tmp = sorted([TOKEN, ts, nonce])
    if hashlib.sha1("".join(tmp).encode()).hexdigest() == sig:
        return echostr
    return "fail", 403

@app.route("/wechat", methods=["POST"])
def receive():
    # 1) 解析微信推送的 XML 消息体，取出用户 openid 与文本内容
    # 2) 调你的大模型服务拿到回复
    # 3) 若预计 >5 秒：先回空/success，再用「客服消息接口」主动推送
    return "success"

if __name__ == "__main__":
    app.run(port=80)
