"""Coze 工作流调用 + 本地 LLM 直连 + 本地兜底打分。"""
import os
import json
import re
import urllib.request
import urllib.error

_STOP = set(
    "的 和 与 及 或 在 有 中 对 等 并 能 会 熟悉 了解 掌握 以上 优先 学历 本科 硕士 博士 "
    "年 工作经验 职责 要求 岗位 负责 使用 进行 相关 能力 良好 一定 至少 以及 具备 具有 "
    "我们 公司 需要 可以 能够 希望 加分 熟悉使用".split()
)


def coze_configured(cfg):
    token = (cfg.get("coze_api_token") or "").strip()
    wid = (cfg.get("workflow_id") or "").strip()
    if not token or not wid:
        return False
    if "在此粘贴" in token or "在此粘贴" in wid:
        return False
    if not token.startswith("pat_"):
        return False
    return True


def call_coze_workflow(job, resume_text, cfg):
    """返回 (dict_result, error)。成功时 error=None。"""
    url = (cfg.get("coze_api_base") or "https://api.coze.cn").rstrip("/") + "/v1/workflow/run"
    token = cfg["coze_api_token"].strip()
    wid = cfg["workflow_id"].strip()
    payload = {
        "workflow_id": wid,
        "parameters": {
            "job_requirements": job,
            "resume_text": resume_text,
        },
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": "Bearer %s" % token,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=int(cfg.get("request_timeout", 120))) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return None, "Coze HTTP 错误 %s: %s" % (e.code, e.read().decode("utf-8", "ignore")[:300])
    except Exception as e:  # noqa: BLE001
        return None, "调用 Coze 失败：%s" % e
    try:
        obj = json.loads(body)
    except Exception:
        return None, "Coze 返回非 JSON：%s" % body[:300]
    if obj.get("code", 0) != 0:
        return None, "Coze 业务错误 code=%s msg=%s" % (obj.get("code"), obj.get("msg"))
    data_field = obj.get("data")
    try:
        result = json.loads(data_field) if isinstance(data_field, str) else data_field
    except Exception:
        return None, "工作流输出非 JSON：%s" % str(data_field)[:300]
    if not isinstance(result, dict):
        return None, "工作流输出结构异常：%s" % str(result)[:300]
    return result, None


# ---- 本地启发式打分（未配置 Coze 时使用） ----
# 从岗位要求中识别「已知技能项」；命中则以一组别名在简历里查找。
# 这样打分能读懂"FastAPI/Flask 都算 Python Web 框架"之类的语义，强匹配候选人会得高分。
_SKILL_RULES = [
    ("Python", ["python"], ["python"]),
    ("Python Web 框架(FastAPI/Flask)", ["fastapi", "flask", "django", "tornado", "sanic"], ["fastapi", "flask", "django", "tornado", "sanic", "web 框架", "微服务"]),
    ("MySQL/SQL", ["mysql", "sql"], ["mysql", "sql"]),
    ("Redis/缓存", ["redis", "缓存", "cache"], ["redis", "缓存", "cache"]),
    ("Docker", ["docker", "容器"], ["docker", "容器"]),
    ("Kubernetes", ["kubernetes", "k8s"], ["kubernetes", "k8s", "编排"]),
    ("客户交付/售前", ["售前", "客户现场", "交付", "现场"], ["售前", "客户现场", "现场交付", "交付"]),
]
_NEG = ["未", "无", "不", "没", "否", "缺乏", "缺少", "没有"]
_EDU_ORDER = {"大专": 1, "本科": 2, "硕士": 3, "博士": 4}


def _hit_without_negation(text, variant, window=12):
    """简历里出现 variant 且『前方 window 字内』不含否定词，才算命中。
    否定词只在关键词之前才算（'未使用过 Python' 的'未'在前=未命中；'了解 Docker，无 K8s' 的'无'在后，不误伤 Docker）。"""
    i = text.find(variant)
    while i != -1:
        before = text[max(0, i - window): i]
        if not any(n in before for n in _NEG):
            return True
        i = text.find(variant, i + 1)
    return False


def _req_years(text):
    ms = re.findall(r"(\d+)\s*年", text)
    return max(int(x) for x in ms) if ms else None


def _edu_level(text):
    lvl = 0
    for k, v in _EDU_ORDER.items():
        if k in text:
            lvl = max(lvl, v)
    return lvl


def _is_priority(job, anchor):
    """岗位要求里 anchor 附近出现『优先/加分』则视为软性要求，权重降低。"""
    i = job.find(anchor)
    if i < 0:
        return False
    window = job[max(0, i - 12): i + 12]
    return ("优先" in window) or ("加分" in window)


def local_fallback_score(job, resume_text):
    """未配置 Coze 时的本地启发式评估。结果含 _fallback=True 标记。"""
    jl = job.lower()
    rl = resume_text.lower()

    # 1) 从岗位要求中提取结构化要求项
    items = []  # (name, weight, hit, note)
    for name, triggers, variants in _SKILL_RULES:
        if any(t in jl for t in triggers):
            weight = 0.6 if any(_is_priority(jl, t) for t in triggers) else 1.0
            hit = any(_hit_without_negation(rl, v) for v in variants)
            items.append((name, weight, hit, None))

    # 学历
    req_edu = _edu_level(jl)
    if req_edu:
        res_edu = _edu_level(rl)
        res_name = [k for k, v in _EDU_ORDER.items() if v == res_edu]
        hit = res_edu >= req_edu
        note = None if hit else ("简历学历：%s（要求 %s 及以上）" % (res_name[0] if res_name else "未提及", list(_EDU_ORDER)[req_edu - 1]))
        items.append(("学历(%s及以上)" % list(_EDU_ORDER)[req_edu - 1], 1.0, hit, note))

    # 工作年限
    req_y = _req_years(jl)
    if req_y:
        res_y = _req_years(rl)
        if res_y is None:
            hit, note = False, "简历未提及工作年限（要求 %d 年以上）" % req_y
        else:
            hit, note = res_y >= req_y, ("简历 %d 年 < 要求 %d 年" % (res_y, req_y) if res_y < req_y else None)
        items.append(("工作年限(≥%d年)" % req_y, 1.0, hit, note))

    if not items:
        return {
            "score": 0, "level": "无法评估",
            "summary": "未能从岗位要求中识别到可评估项（技能/学历/年限），请写得更具体，例如列出技能名与年限。",
            "matched_points": [],
            "gap_points": ["岗位要求信息不足，无法评估"],
            "suggestions": ["在岗位要求中列出具体技能（如 Python、MySQL）、学历与年限要求。"],
            "_fallback": True,
        }

    # 2) 加权计分
    w_sum = sum(w for _, w, _, _ in items)
    w_hit = sum(w for _, w, h, _ in items if h)
    score = round(w_hit / w_sum * 100)
    score = min(score, 100)

    matched, gaps, sugg = [], [], []
    for name, w, hit, note in items:
        if hit:
            matched.append("具备：%s" % name)
        else:
            gaps.append("缺少：%s" % (note or name))
            sugg.append("建议补充 %s 相关经验" % name)

    level = "高度匹配" if score >= 80 else "较好匹配" if score >= 60 else "一般匹配" if score >= 40 else "不匹配"
    return {
        "score": score,
        "level": level,
        "summary": "本地启发式评估（未配置大模型）：%d/%d 项核心要求满足，匹配度 %d%%。配置大模型（本地直连 LLM）后可获得语义级专业分析与更细的差距诊断。" % (
            sum(1 for _, _, h, _ in items if h), len(items), score),
        "matched_points": matched,
        "gap_points": gaps,
        "suggestions": sugg or ["配置大模型（本地直连 LLM）后可获得专业匹配度分析与差距诊断（当前为本地启发式兜底）。"],
        "_fallback": True,
    }


# ---- 本地直连 LLM（OpenAI 兼容协议，不依赖 Coze 云） ----
def local_llm_configured(cfg):
    llm = cfg.get("llm") or {}
    if not llm.get("enabled", False):
        return False
    key = (llm.get("api_key") or "").strip()
    base = (llm.get("base_url") or "").strip()
    model = (llm.get("model") or "").strip()
    if not key or not base or not model:
        return False
    if "在此粘贴" in key:
        return False
    return True


def _friendly_llm_error(code, raw, llm):
    """把 FreeLLMAPI / OpenAI 兼容网关的常见报错翻译成人话 + 下一步。"""
    base = llm.get("base_url", "")
    is_freellmapi = "3001" in base or "freellmapi" in base.lower()
    if "no usable key configured" in raw or "Add more API keys" in raw:
        if is_freellmapi:
            return ("FreeLLMAPI 还没配置任何模型密钥 → 无法调用真 LLM。\n"
                    "  下一步（一次性）：打开 http://localhost:5173 → 左侧 Providers →\n"
                    "  添加至少一家免费 key（推荐 Google AI Studio 的 Gemini，免绑卡）→ 保存。\n"
                    "  配好后再双击「简历助手-免费LLM.bat」即可，无需改任何配置。")
        return "模型网关返回：未配置可用的模型密钥（%s）。请检查 %s 背后的 provider key。" % (raw[:200], base)
    if "prompt too large" in raw or "context" in raw.lower() or code == 413:
        if is_freellmapi:
            return ("FreeLLMAPI 当前可用的免费模型上下文窗口太小，装不下这份简历+岗位要求。\n"
                    "  通常是还没添加大上下文的 provider（如 Gemini，支持超长上下文）。\n"
                    "  下一步：打开 http://localhost:5173 → Providers → 添加 Gemini 等免费 key 后重试。")
        return "请求超出模型上下文窗口（%s）。可减少简历/岗位文本长度，或换用更大上下文的模型。" % raw[:200]
    if code == 401:
        return "鉴权失败（401）：统一密钥无效。请确认 config.json 的 llm.api_key 与 FreeLLMAPI 后台 Keys 页一致。"
    if code == 429:
        return "触发限流（429）：免费额度瞬时用尽，稍等片刻或降低并发后重试。"
    return "LLM HTTP 错误 %s: %s" % (code, raw[:300])


def _load_prompt_template():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coze_workflow_prompt.txt")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return (
            "你是一位资深的技术招聘筛选专家。请根据【岗位要求】对【简历内容】做匹配度评估，\n"
            "只输出如下 JSON（不要任何额外说明）：\n"
            '{"score":0,"level":"","matched_points":[],"gap_points":[],"suggestions":[],"summary":""}'
        )


def _fill_prompt(template, job, resume):
    return template.replace("{{job_requirements}}", job).replace("{{resume_text}}", resume)


def _extract_json(text):
    """从模型输出里抠出第一个 JSON 对象（兼容 ```json 代码块包裹）。"""
    t = text.strip()
    if t.startswith("```"):
        # 去掉 ```json ... ```
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
    s, e = t.find("{"), t.rfind("}")
    if s != -1 and e != -1 and e > s:
        try:
            return json.loads(t[s:e + 1])
        except Exception:
            return None
    return None


def call_local_llm(job, resume_text, cfg):
    """本地直连 OpenAI 兼容 LLM。返回 (dict_result, error)。"""
    llm = cfg["llm"]
    url = (llm["base_url"].rstrip("/") + "/chat/completions")
    key = llm["api_key"].strip()
    model = llm["model"].strip()
    template = _load_prompt_template()
    user_content = _fill_prompt(template, job, resume_text)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一位严谨的技术招聘评估助手，严格按用户要求的 JSON 格式输出，不要输出任何额外说明文字。"},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.2,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": "Bearer %s" % key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=int(llm.get("timeout", 120))) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "ignore")[:400]
        return None, _friendly_llm_error(e.code, raw, llm)
    except Exception as e:  # noqa: BLE001
        return None, "调用 LLM 失败：%s" % e
    try:
        obj = json.loads(body)
        content = obj["choices"][0]["message"]["content"]
    except Exception:
        return None, "LLM 返回结构异常：%s" % body[:300]
    result = _extract_json(content)
    if not isinstance(result, dict):
        return None, "LLM 输出非预期 JSON：%s" % content[:300]
    result["_fallback"] = False
    return result, None
