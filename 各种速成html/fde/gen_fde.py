# -*- coding: utf-8 -*-
"""生成 FDE 各知识点速成文件夹：每个知识点一个子文件夹，含 index.html 教程 + 案例代码。"""
import os, html

BASE = "D:/codespace/各种速成html/fde"

# 统一教程页模板（浅色清爽，匹配 langchain 原教程风），用 __占位__ 替换，避免 f-string 花括号冲突
TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;color:#1f2937;background:#f7f8fa;line-height:1.7}
  header{background:linear-gradient(120deg,#4f46e5,#7c3aed);color:#fff;padding:2.2rem 1.5rem}
  header h1{margin:0;font-size:1.6rem}
  header p{margin:.4rem 0 0;opacity:.92;font-size:.95rem}
  main{max-width:860px;margin:0 auto;padding:1.8rem 1.5rem 4rem}
  h2{margin-top:2.2rem;font-size:1.2rem;color:#4f46e5;border-left:4px solid #4f46e5;padding-left:.6rem}
  ul{padding-left:1.4rem}
  li{margin:.35rem 0}
  .lead{font-size:1.05rem;color:#374151;background:#eef2ff;padding:1rem 1.2rem;border-radius:10px}
  pre{background:#0f172a;color:#e2e8f0;padding:1rem 1.1rem;border-radius:10px;overflow:auto;font-size:.84rem;line-height:1.55}
  code{font-family:"JetBrains Mono",Consolas,monospace}
  .tag{display:inline-block;background:#4f46e5;color:#fff;font-size:.72rem;padding:.15rem .6rem;border-radius:20px;margin-right:.4rem;vertical-align:middle}
  .nav{margin-top:3rem;padding-top:1rem;border-top:1px solid #e5e7eb;font-size:.9rem}
  .nav a{color:#4f46e5;text-decoration:none}
  .warn{background:#fff7ed;border:1px solid #fdba74;color:#9a3412;padding:.8rem 1rem;border-radius:10px;font-size:.9rem}
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <p>FDE 速成知识点 · 实战向</p>
</header>
<main>
  <p class="lead">__LEAD__</p>

  <h2>你会学到</h2>
  <ul>__LEARN__</ul>

  <h2>核心概念</h2>
  __CONCEPTS__

  <h2><span class="tag">案例</span>可直接参考的代码</h2>
  <pre><code>__CODE__</code></pre>

  <h2>动手练习</h2>
  <p>__EXERCISE__</p>

  <div class="nav">
    返回 <a href="../index.html">FDE 总导航</a> ｜ 看 <a href="../fde_skills.html">FDE 能力地图</a> ｜ 单屏版 <a href="../fde_saas.html">fde_saas.html</a>
  </div>
</main>
</body>
</html>
"""

topics = {
  "01-大模型接入": {
    "title": "FDE 速成 · 大模型接入",
    "lead": "把任意大模型（OpenAI / DeepSeek / 通义 / 本地）接进应用，是 FDE 的地基。统一用 LangChain 的 ChatOpenAI 接口，换个 base_url 和 model 就能切厂商。",
    "learn": ["用 ChatOpenAI 统一接各家模型", "OpenRouter 聚合网关的用法（一个 Key 调多家）", "API Key 与 .env 安全管理", "模型选型与成本意识"],
    "concepts": '<p><b>统一接口</b>：LangChain 的 <code>ChatOpenAI</code> 本质是个 OpenAI 兼容客户端，只要目标服务暴露 OpenAI 格式接口，改 <code>base_url</code> 即可，不用换代码。</p>\n<p><b>OpenRouter</b>：一个 Key 聚合几百个模型（含免费档），适合 FDE 多模型对比、快速验证。</p>\n<p><b>安全</b>：Key 永远放 <code>.env</code>，别写进前端/提交仓库；免费模型质量弱，生产换付费档。</p>\n<p class="warn">注意：给 OpenRouter 传自定义 HTTP 头（如 X-Title）必须 ASCII，中文会触发 ascii 编码错误导致调用失败。</p>',
    "code": 'import os\nfrom dotenv import load_dotenv\nfrom langchain_openai import ChatOpenAI\n\nload_dotenv()\nllm = ChatOpenAI(\n    base_url="https://openrouter.ai/api/v1",\n    api_key=os.getenv("OPENROUTER_API_KEY"),\n    model=os.getenv("OPENROUTER_MODEL", "openrouter/free"),\n    temperature=0.7,\n)\nprint(llm.invoke("用一句话介绍你自己").content)',
    "exercise": "把 model 改成 DeepSeek（deepseek/deepseek-chat），对比回复质量与速度，体会「换模型不换代码」。",
  },
  "02-Agent与工具调用": {
    "title": "FDE 速成 · Agent 与工具调用",
    "lead": "Agent = 会自己决定「调哪个工具」的 LLM。FDE 落地 AI 的核心就是把业务系统封装成 tool，让模型在对话中自主调用。",
    "learn": ["@tool 把函数暴露给模型", "create_tool_calling_agent + AgentExecutor 跑决策循环", "用 verbose 看思考链", "工具调用失败时的兜底降级"],
    "concepts": '<p><b>工具即能力</b>：<code>@tool</code> 装饰的函数就是 Agent 的「手」，能查库存、算差价、调订单 API。</p>\n<p><b>决策循环</b>：模型分析用户问题 → 选工具 → 拿结果 → 再思考 → 直到能回答。verbose=True 能看到全过程。</p>\n<p class="warn">弱模型（如 openrouter/free）未必支持工具调用，会触发异常；生产务必加 try/except 降级为纯 LLM 客服。</p>',
    "code": 'from langchain.agents import create_tool_calling_agent, AgentExecutor\nfrom langchain.tools import tool\nfrom langchain_core.prompts import ChatPromptTemplate\n\nPRICES = {"智能水杯":299, "无线耳机":499, "运动手环":199, "智能手表":899}\n\n@tool\ndef get_product_price(name: str) -> int:\n    # 返回指定产品的价格（元）\n    return PRICES.get(name, -1)\n\nprompt = ChatPromptTemplate.from_messages([\n    ("system", "你是智能客服，能用工具查价格并算差价。"),\n    ("human", "{input}"),\n    ("placeholder", "{agent_scratchpad}"),\n])\nagent = create_tool_calling_agent(llm, [get_product_price], prompt)\nexe = AgentExecutor(agent=agent, tools=[get_product_price], verbose=True)\nprint(exe.invoke({"input": "智能手表比运动手环贵多少？"})["output"])',
    "exercise": "再加一个 @tool get_stock(name) 返回库存，问「智能水杯还有货吗」看 Agent 是否自动调新工具。",
    "extra": {"name": "agent_demo.py", "content": '"""FDE 实战：带工具调用的 LangChain Agent（可直接跑，需 pip install langchain langchain-openai python-dotenv）"""\nimport os\nfrom dotenv import load_dotenv\nfrom langchain_openai import ChatOpenAI\nfrom langchain.agents import create_tool_calling_agent, AgentExecutor\nfrom langchain.tools import tool\nfrom langchain_core.prompts import ChatPromptTemplate\n\nload_dotenv()\nllm = ChatOpenAI(base_url="https://openrouter.ai/api/v1",\n                 api_key=os.getenv("OPENROUTER_API_KEY"),\n                 model=os.getenv("OPENROUTER_MODEL", "openrouter/free"))\n\nPRICES = {"智能水杯": 299, "无线耳机": 499, "运动手环": 199, "智能手表": 899}\n\n@tool\ndef get_product_price(name: str) -> int:\n    """返回指定产品的价格（元）"""\n    return PRICES.get(name, -1)\n\nprompt = ChatPromptTemplate.from_messages([\n    ("system", "你是智能客服，能用工具查价格并算差价。"),\n    ("human", "{input}"),\n    ("placeholder", "{agent_scratchpad}"),\n])\nagent = create_tool_calling_agent(llm, [get_product_price], prompt)\nexe = AgentExecutor(agent=agent, tools=[get_product_price], verbose=True)\nprint(exe.invoke({"input": "智能手表比运动手环贵多少？"})["output"])\n'},
  },
  "03-RAG知识工程": {
    "title": "FDE 速成 · RAG 知识工程",
    "lead": "RAG = 先把文档切块 → 向量化 → 入库 → 用户提问时检索最相关片段 → 拼进 prompt 让 LLM 只基于检索内容回答。知识量大/频繁更新时的标配。",
    "learn": ["什么时候该用 RAG（vs 直接写进 prompt）", "文本切分策略", "Embedding 与向量库（Chroma）", "检索质量决定上限"],
    "concepts": '<p><b>何时用</b>：商品/文档几百上千条、天天变、要可溯源时，写进 prompt 装不下也不好维护，上 RAG。</p>\n<p><b>链路</b>：切分 → 嵌入 → 存向量库 → 相似度检索 → 拼 context → 生成。</p>\n<p class="warn">RAG 难在「检索准不准」，retriever 没召回对的片段，LLM 再强也答歪。别只盯着生成。</p>',
    "code": 'from langchain_community.vectorstores import Chroma\nfrom langchain_community.embeddings import SentenceTransformerEmbeddings\nfrom langchain.text_splitter import RecursiveCharacterTextSplitter\n\ndocs = open("产品手册.txt", encoding="utf-8").read()\nchunks = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50).split_text(docs)\nemb = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")\nvs = Chroma.from_texts(chunks, emb, persist_directory="./chroma")\n\nhits = vs.similarity_search("智能水杯怎么用", k=3)\ncontext = "\\n".join(h.page_content for h in hits)\n# 把 context 拼进 prompt 交给 LLM 生成答案',
    "exercise": "把 4 个产品介绍写进 产品手册.txt，检索「最便宜的是哪款」验证检索命中。",
  },
  "04-微信接入实战": {
    "title": "FDE 速成 · 微信接入实战",
    "lead": "客户要接公众号/企业微信？核心是「被动回调」：微信推消息到你服务器 → 你调大模型 → 回给微信。三个硬门槛必须讲清。",
    "learn": ["微信回调校验（SHA1 签名）", "消息加解密", "5 秒响应限制 → 客服消息异步回", "公网服务器 + 域名 + HTTPS 前置条件"],
    "concepts": '<p><b>被动回调</b>：微信服务器主动 POST 用户消息到你的回调 URL，你必须在 5 秒内响应，否则用户收不到回复。</p>\n<p><b>异步回包</b>：大模型常超 5 秒，标准做法是先立刻回「正在查询…」，后台算完用「客服消息接口」主动推第二条。</p>\n<p><b>前置条件</b>：你的服务必须公网可达（本地 127.0.0.1 不行），配 token 校验 + 消息加解密。</p>',
    "code": 'from flask import Flask, request\nimport hashlib\n\napp = Flask(__name__)\nTOKEN = "你的公众号Token"\n\n@app.route("/wechat", methods=["GET"])\ndef verify():\n    sig = request.args.get("signature")\n    ts, nonce, echostr = request.args.get("timestamp"), request.args.get("nonce"), request.args.get("echostr")\n    tmp = sorted([TOKEN, ts, nonce])\n    if hashlib.sha1("".join(tmp).encode()).hexdigest() == sig:\n        return echostr\n    return "fail", 403\n\n# POST 分支：接收用户消息 -> 调大模型 -> 异步回（此处省略消息体解析与客服消息接口）\nif __name__ == "__main__":\n    app.run(port=80)',
    "exercise": "把服务部署到云服务器 + 域名，在公众号后台填回调 URL 与 Token，跑通 GET 校验。",
    "extra": {"name": "wechat_server.py", "content": '"""FDE 实战：微信公众号回调骨架（Flask）。\n前置：云服务器 + 公网域名 + HTTPS + 公众号后台配置 Token 与回调 URL。\n完整生产还需：消息体 XML 解析、AES 加解密、客服消息异步回包（突破 5 秒限制）。\n"""\nfrom flask import Flask, request\nimport hashlib\n\napp = Flask(__name__)\nTOKEN = "你的公众号Token"\n\n@app.route("/wechat", methods=["GET"])\ndef verify():\n    sig = request.args.get("signature")\n    ts, nonce, echostr = (request.args.get("timestamp"),\n                          request.args.get("nonce"),\n                          request.args.get("echostr"))\n    tmp = sorted([TOKEN, ts, nonce])\n    if hashlib.sha1("".join(tmp).encode()).hexdigest() == sig:\n        return echostr\n    return "fail", 403\n\n@app.route("/wechat", methods=["POST"])\ndef receive():\n    # 1) 解析微信推送的 XML 消息体，取出用户 openid 与文本内容\n    # 2) 调你的大模型服务拿到回复\n    # 3) 若预计 >5 秒：先回空/success，再用「客服消息接口」主动推送\n    return "success"\n\nif __name__ == "__main__":\n    app.run(port=80)\n'},
  },
  "05-多租户会话隔离": {
    "title": "FDE 速成 · 多租户会话隔离",
    "lead": "Demo 能跑 ≠ 敢给客户用。每个客户/用户必须各有独立会话记忆，否则 A 的客户看到 B 的对话就是事故。这是接入任何系统的硬门槛。",
    "learn": ["为什么全局一份 Memory 会串台", "用 user_id 分桶管理会话", "内存字典 vs Redis 持久化", "会话过期与清理"],
    "concepts": '<p><b>串台是事故</b>：当前 langchain_server.py 是全局一份 history，多用户共用会互相看到对话。</p>\n<p><b>分桶</b>：以 user_id（微信 openid / CRM customer_id）为 key 隔离各自的 history 与 memory。</p>\n<p><b>持久化</b>：内存字典重启即丢，生产用 Redis 存会话，并设置 TTL 过期。</p>',
    "code": 'SESSIONS = {}  # user_id -> 各自的历史\n\ndef get_session(uid):\n    if uid not in SESSIONS:\n        SESSIONS[uid] = {"history": [{"role": "system", "content": SYSTEM_PROMPT}]}\n    return SESSIONS[uid]\n\ndef chat(uid, msg):\n    s = get_session(uid)\n    s["history"].append({"role": "user", "content": msg})\n    reply = call_llm(s["history"])          # 调你的大模型\n    s["history"].append({"role": "assistant", "content": reply})\n    return reply\n\n# 调用示例：chat("openid_abc", "智能水杯多少钱？")',
    "exercise": "把 SESSIONS 换成 Redis（redis-py），设 30 分钟 TTL，模拟两个用户互不影响。",
    "extra": {"name": "multi_tenant.py", "content": '"""FDE 实战：多租户会话隔离（按 user_id 分桶）。\n生产建议用 Redis 替代内存 dict，并设 TTL 自动过期。\n"""\nSESSIONS = {}  # user_id -> {"history": [...]}\n\nSYSTEM_PROMPT = "你是智能客服。"\n\ndef get_session(uid):\n    if uid not in SESSIONS:\n        SESSIONS[uid] = {"history": [{"role": "system", "content": SYSTEM_PROMPT}]}\n    return SESSIONS[uid]\n\ndef chat(uid, msg, call_llm):\n    s = get_session(uid)\n    s["history"].append({"role": "user", "content": msg})\n    reply = call_llm(s["history"])\n    s["history"].append({"role": "assistant", "content": reply})\n    return reply\n\n# 两个用户各自独立，互不串台：\n# chat("openid_A", "水杯多少钱", llm_fn)\n# chat("openid_B", "耳机多少钱", llm_fn)\n'},
  },
  "06-私有化部署": {
    "title": "FDE 速成 · 私有化部署",
    "lead": "金融/政企/医疗客户数据不能出内网。FDE 得把整套（含大模型）部署到客户机房，用 Ollama/vLLM 跑私有模型，数据不出厂。",
    "learn": ["什么时候必须私有化（数据合规）", "Ollama 跑本地模型", "vLLM 高并发推理", "Docker 封装整个服务"],
    "concepts": '<p><b>触发条件</b>：客户要求数据不出网、等保/合规、或对公有云 LLM 不信任。</p>\n<p><b>Ollama</b>：单机本地跑模型，最简单；<b>vLLM</b>：高吞吐、多卡，适合并发大的场景。</p>\n<p><b>接口一致</b>：本地模型同样暴露 OpenAI 格式，LangChain 改 base_url 即可，业务代码不动。</p>',
    "code": '# docker-compose.yml 起一个本地 Ollama\n# services:\n#   ollama:\n#     image: ollama/ollama\n#     ports: ["11434:11434"]\n#     volumes: ["ollama:/root/.ollama"]\n# volumes:\n#   ollama:\n\n# Python 侧：base_url 指向本地，api_key 随便填\nfrom langchain_openai import ChatOpenAI\nllm = ChatOpenAI(\n    base_url="http://localhost:11434/v1",\n    api_key="ollama",\n    model="qwen2.5:7b",   # 本地已 pull 的模型\n)',
    "exercise": "本地装 Ollama，pull qwen2.5:7b，跑通上面这段，验证私有模型回复（完全不联网）。",
    "extra": {"name": "docker-compose.yml", "content": '# FDE 实战：私有化部署最小骨架\n# 1) 起 Ollama 提供本地模型（OpenAI 兼容接口）\n# 2) 你的 LangChain 服务把 base_url 指向 http://ollama:11434/v1\nservices:\n  ollama:\n    image: ollama/ollama\n    ports:\n      - "11434:11434"\n    volumes:\n      - ollama:/root/.ollama\n    # 进入容器执行: ollama pull qwen2.5:7b\n\n  app:\n    build: .\n    ports:\n      - "5000:5000"\n    environment:\n      - OPENAI_BASE_URL=http://ollama:11434/v1\n      - OPENAI_API_KEY=ollama\n      - OPENAI_MODEL=qwen2.5:7b\n    depends_on:\n      - ollama\n\nvolumes:\n  ollama:\n'},
  },
  "07-渠道与系统集成": {
    "title": "FDE 速成 · 渠道与系统集成",
    "lead": "接客户系统本质就是「调 API」。官网挂件最简单（fetch 你的 /chat），CRM/ERP 用 Webhook 推事件，后端统一处理。",
    "learn": ["官网聊天挂件（iframe）怎么嵌", "CRM Webhook 接收与回包", "后端统一 /chat 接口的价值", "把客户业务 API 封装成 Agent 工具"],
    "concepts": '<p><b>官网挂件</b>：前端嵌个 iframe 直接 fetch 你的 /chat，和 langchain_web.html 一样。</p>\n<p><b>CRM 集成</b>：客户系统用 Webhook/OpenAPI 推对话事件，你回 JSON，客户再渲染到自己 UI。</p>\n<p><b>统一后端</b>：所有渠道都调同一个 /chat，多租户隔离在后端做，前端只管展示。</p>',
    "code": '<!-- 前端：官网聊天挂件 -->\n<iframe src="https://你的服务/chat-widget"\n        style="position:fixed;right:20px;bottom:20px;width:380px;height:600px;border:0">\n</iframe>\n\n# 后端：CRM Webhook 接收并回包\nfrom flask import Flask, request, jsonify\napp = Flask(__name__)\n\n@app.route("/webhook/crm", methods=["POST"])\ndef crm_webhook():\n    data = request.json\n    uid = data["customer_id"]\n    msg = data["message"]\n    return jsonify({"reply": chat(uid, msg)})  # chat 见多租户章节',
    "exercise": "做一个静态页嵌入上面 iframe，本地起服务看挂件能否对话；再写个 /webhook/crm 用 Postman 模拟 CRM 调用。",
  },
  "08-鉴权限流与安全": {
    "title": "FDE 速成 · 鉴权限流与安全",
    "lead": "对外暴露的 /chat 必须鉴权 + 限流 + 成本熔断，否则被刷爆账单。数据合规（PII 脱敏）在敏感行业是红线。",
    "learn": ["API Key / JWT 鉴权", "限流防刷（按 IP/用户）", "成本熔断（单次/每日上限）", "PII 脱敏与数据合规"],
    "concepts": '<p><b>鉴权</b>：每个调用方带 Key 或 JWT，非法直接 401。</p>\n<p><b>限流</b>：按 IP/用户限制单位时间请求数，防刷、控并发。</p>\n<p><b>成本熔断</b>：大模型按 token 计费，设每日/单次上限，超了降级或拒绝。</p>\n<p class="warn">金融/医疗场景还要做 PII 脱敏、对话留痕（会话存档），这是合规硬要求。</p>',
    "code": 'from flask import Flask, request, jsonify\nfrom functools import wraps\nimport time\n\napp = Flask(__name__)\nAPI_KEY = "你的服务端Key"\nRATE = {}  # ip -> [时间戳]\n\ndef rate_limit(f):\n    @wraps(f)\n    def w():\n        ip = request.remote_addr\n        now = time.time()\n        RATE[ip] = [t for t in RATE.get(ip, []) if now - t < 60]\n        if len(RATE[ip]) >= 20:        # 每 IP 每分钟上限 20 次\n            return jsonify({"err": "限流"}), 429\n        RATE[ip].append(now)\n        return f()\n    return w\n\n@app.route("/chat")\n@rate_limit\ndef chat():\n    if request.headers.get("X-API-Key") != API_KEY:\n        return jsonify({"err": "未授权"}), 401\n    # ... 调大模型并返回\n    return jsonify({"reply": "hi"})',
    "exercise": "把内存 RATE 换成 Redis 限流，并加 JWT 校验，模拟 20 次后第 21 次被限流。",
    "extra": {"name": "auth_limiter.py", "content": '"""FDE 实战：API 鉴权 + 限流中间件（Flask）。\n生产用 Redis 做分布式限流，并改用 JWT 替代静态 Key。\n"""\nfrom flask import Flask, request, jsonify\nfrom functools import wraps\nimport time\n\napp = Flask(__name__)\nAPI_KEY = "你的服务端Key"\nRATE = {}  # ip -> [时间戳]\n\ndef rate_limit(f):\n    @wraps(f)\n    def w():\n        ip = request.remote_addr\n        now = time.time()\n        RATE[ip] = [t for t in RATE.get(ip, []) if now - t < 60]\n        if len(RATE[ip]) >= 20:\n            return jsonify({"err": "限流"}), 429\n        RATE[ip].append(now)\n        return f()\n    return w\n\n@app.route("/chat")\n@rate_limit\ndef chat():\n    if request.headers.get("X-API-Key") != API_KEY:\n        return jsonify({"err": "未授权"}), 401\n    return jsonify({"reply": "hi"})\n\nif __name__ == "__main__":\n    app.run()\n'},
  },
}

# ---- 生成各知识点文件夹 ----
for folder, t in topics.items():
    d = os.path.join(BASE, folder)
    os.makedirs(d, exist_ok=True)
    learn_li = "".join("<li>%s</li>" % x for x in t["learn"])
    page = (TPL
            .replace("__TITLE__", t["title"])
            .replace("__LEAD__", t["lead"])
            .replace("__LEARN__", learn_li)
            .replace("__CONCEPTS__", t["concepts"])
            .replace("__CODE__", html.escape(t["code"]))
            .replace("__EXERCISE__", t["exercise"]))
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    if "extra" in t:
        with open(os.path.join(d, t["extra"]["name"]), "w", encoding="utf-8") as f:
            f.write(t["extra"]["content"])
    print("生成:", folder)

# ---- 总导航 index.html ----
cards = ""
for folder, t in topics.items():
    lead = t["lead"][:42] + "…"
    cards += ('    <a class="card" href="%s/index.html">\n'
              '      <h3>%s</h3>\n'
              '      <p>%s</p>\n'
              '      <span class="go">查看教程 →</span>\n'
              '    </a>\n') % (folder, folder, lead)

nav_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FDE 速成 · 总导航</title>
<style>
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;background:#f7f8fa;color:#1f2937}
  header{background:linear-gradient(120deg,#4f46e5,#7c3aed);color:#fff;padding:2.4rem 1.5rem}
  header h1{margin:0;font-size:1.7rem}
  header p{margin:.5rem 0 0;opacity:.92}
  main{max-width:980px;margin:0 auto;padding:2rem 1.5rem 4rem}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1.1rem;margin-top:1.5rem}
  .card{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:1.2rem;text-decoration:none;color:inherit;transition:.15s;display:flex;flex-direction:column}
  .card:hover{transform:translateY(-3px);box-shadow:0 8px 24px rgba(79,70,229,.15);border-color:#4f46e5}
  .card h3{margin:0 0 .4rem;color:#4f46e5;font-size:1.05rem}
  .card p{margin:0 0 1rem;font-size:.86rem;color:#6b7280;flex:1}
  .go{color:#7c3aed;font-size:.85rem;font-weight:600}
  .top{margin-top:2rem;font-size:.92rem}
  .top a{color:#4f46e5;text-decoration:none;margin-right:1.2rem}
</style>
</head>
<body>
<header>
  <h1>FDE 速成 · 知识点总导航</h1>
  <p>前端部署工程师（Forward Deployed Engineer）核心技能，按知识点拆分，逐个击破</p>
</header>
<main>
  <div class="grid">
__CARDS__  </div>
  <div class="top">
    概况：<a href="fde_saas.html">单屏速成课</a> ｜ <a href="fde_skills.html">能力地图</a>
  </div>
</main>
</body>
</html>
"""
nav_html = nav_html.replace("__CARDS__", cards)
with open(os.path.join(BASE, "index.html"), "w", encoding="utf-8") as f:
    f.write(nav_html)
print("生成: index.html (总导航)")
print("完成，共", len(topics), "个知识点")
