# -*- coding: utf-8 -*-
"""
LangChain 智能客服 · 真实联网版（Web 后端）
==========================================
真正调用你在 .env 里配置的 OpenRouter API Key，
前端 langchain_web.html 发来的每条消息都会走真实大模型生成回复。

运行（需本地联网）：
    pip install -r requirements.txt
    python langchain_server.py
然后浏览器打开 http://127.0.0.1:5000
"""
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage

load_dotenv()

app = Flask(__name__)
CORS(app)

# ---------- 读取配置 ----------
API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

if not API_KEY:
    print("⚠️  警告：未检测到 OPENROUTER_API_KEY，请在 .env 中填写你的 Key。")

# ---------- 系统提示词（产品知识库）----------
SYSTEM_PROMPT = """你是一个智能硬件电商的在线客服助手，名字叫「小链」。
请用友好、简洁的中文回答用户问题。

我们目前正在售的 4 款智能硬件产品如下：
1. 智能水杯 —— 售价 ¥299。内置温度传感器与蓝牙模块，可手机 APP 管理饮水数据；功能：实时温度显示、智能饮水提醒、APP 数据同步、长效续航。
2. 无线耳机 —— 售价 ¥499。主打主动降噪与长续航，适合通勤与运动；功能：主动降噪、30 小时续航、低延迟游戏模式、双设备连接。
3. 运动手环 —— 售价 ¥199。轻巧防水，入门级健康追踪；功能：心率监测、睡眠分析、50 米防水、14 天超长续航。
4. 智能手表 —— 售价 ¥899。旗舰款，支持独立通话与精准定位；功能：AMOLED 高清屏、GPS 定位、血氧检测、独立通话。

回答要求：
- 用户问「卖什么/有哪些产品」时，主动列出以上全部产品与价格。
- 用户问某款价格时，直接给出对应价格。
- 用户对比两款时，算出差价并说明。
- 如果用户问的是与产品无关的问题（如闲聊），礼貌回应并引导回产品话题。
- 不要编造不存在的产品或价格。
"""

# ---------- 初始化 LangChain 的 ChatOpenAI（真实模型）----------
llm = ChatOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    model=MODEL,
    temperature=0.7,
    max_tokens=800,
)

# ---------- 对话记忆（服务端保存历史）----------
# 说明：这里用最简单的全局列表演示。多用户场景应改为按 session 隔离。
_history = []

MAX_HISTORY = 12  # 最多保留最近 12 条（6 轮），避免 token 膨胀


@app.route("/")
def index():
    return send_from_directory(".", "langchain_web.html")


@app.route("/chat", methods=["POST"])
def chat():
    global _history
    data = request.get_json(silent=True) or {}
    user_msg = (data.get("message") or "").strip()
    if not user_msg:
        return jsonify({"reply": "（消息为空）"}), 400

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + _history + [HumanMessage(content=user_msg)]
    try:
        ai_msg = llm.invoke(messages)
        reply = ai_msg.content if hasattr(ai_msg, "content") else str(ai_msg)
    except Exception as e:
        # 出错时返回明确信息，方便排查（常见：Key 无效 / 模型不支持 / 网络问题）
        err = str(e)
        print("❌ 调用模型失败：", err)
        return jsonify({"reply": f"调用模型出错：{err}"}), 500

    _history.append(HumanMessage(content=user_msg))
    _history.append(AIMessage(content=reply))
    if len(_history) > MAX_HISTORY:
        _history = _history[-MAX_HISTORY:]

    return jsonify({"reply": reply})


@app.route("/reset", methods=["POST"])
def reset():
    global _history
    _history = []
    return jsonify({"ok": True})


if __name__ == "__main__":
    print(f"🚀 LangChain 客服已启动：http://127.0.0.1:5000  （模型：{MODEL}）")
    app.run(host="127.0.0.1", port=5000, debug=False)
