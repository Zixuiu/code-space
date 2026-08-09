"""FDE 实战：多租户会话隔离（按 user_id 分桶）。
生产建议用 Redis 替代内存 dict，并设 TTL 自动过期。
"""
SESSIONS = {}  # user_id -> {"history": [...]}

SYSTEM_PROMPT = "你是智能客服。"

def get_session(uid):
    if uid not in SESSIONS:
        SESSIONS[uid] = {"history": [{"role": "system", "content": SYSTEM_PROMPT}]}
    return SESSIONS[uid]

def chat(uid, msg, call_llm):
    s = get_session(uid)
    s["history"].append({"role": "user", "content": msg})
    reply = call_llm(s["history"])
    s["history"].append({"role": "assistant", "content": reply})
    return reply

# 两个用户各自独立，互不串台：
# chat("openid_A", "水杯多少钱", llm_fn)
# chat("openid_B", "耳机多少钱", llm_fn)
