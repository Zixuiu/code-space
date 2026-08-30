# -*- coding: utf-8 -*-
"""简历助手：读岗位要求 + 扫描 PDF 简历 -> 调用 Coze 工作流打分 -> 生成 HTML 报告。"""
import os
import json
import glob
import html
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    with open(os.path.join(HERE, "config.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def read_job(cfg):
    p = os.path.join(HERE, cfg.get("job_file", "岗位要求.txt"))
    if not os.path.exists(p):
        return None, "未找到岗位要求文件：%s\n请在该文件内粘贴岗位要求后重新运行。" % p
    with open(p, "r", encoding="utf-8") as f:
        t = f.read().strip()
    if not t:
        return None, "岗位要求文件为空，请先填入岗位要求。"
    return t, None


def find_pdfs(folder):
    folder = os.path.join(HERE, folder)
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    return sorted(glob.glob(os.path.join(folder, "*.pdf")))


def score_color(s):
    if s >= 80:
        return "#1a7f37"
    if s >= 60:
        return "#0969da"
    if s >= 40:
        return "#bc4c00"
    return "#cf222e"


def build_report(job, results, engine_label):
    cards = []
    for idx, r in enumerate(results, 1):
        sc = score_color(r.get("score", 0))
        matched = "".join("<li>%s</li>" % html.escape(str(m)) for m in r.get("matched_points", [])) or "<li>—</li>"
        gaps = "".join("<li>%s</li>" % html.escape(str(g)) for g in r.get("gap_points", [])) or "<li>—</li>"
        sugg = "".join("<li>%s</li>" % html.escape(str(s)) for s in r.get("suggestions", [])) or "<li>—</li>"
        err = r.get("error")
        card = (
            '<div class="card">'
            '<div class="card-head">'
            '<span class="rank">#%d</span>'
            '<span class="cname">%s</span>'
            '<span class="score" style="color:%s">%s</span>'
            '<span class="level" style="border-color:%s;color:%s">%s</span>'
            "</div>"
            '<div class="summary">%s</div>'
            '<div class="cols">'
            '<div class="col"><h4>✅ 匹配点</h4><ul>%s</ul></div>'
            '<div class="col gap"><h4>⚠️ 不匹配 / 不足点</h4><ul>%s</ul></div>'
            '<div class="col"><h4>💡 建议</h4><ul>%s</ul></div>'
            "</div>"
            '%s'
            "</div>"
        ) % (
            idx,
            html.escape(r.get("name", "")),
            sc,
            r.get("score", 0),
            sc,
            sc,
            html.escape(r.get("level", "")),
            html.escape(r.get("summary", "")),
            matched,
            gaps,
            sugg,
            ('<div class="err">⚠ %s</div>' % html.escape(err)) if err else "",
        )
        cards.append(card)
    cards_html = "".join(cards)
    engine = engine_label if isinstance(engine_label, str) else ("Coze 工作流（专业 LLM 评估）" if engine_label else "本地兜底（启发式粗评，未配置任何 LLM）")
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        "<title>简历匹配报告</title><style>"
        "body{font-family:-apple-system,'Segoe UI',Roboto,'Microsoft YaHei',sans-serif;"
        "background:#f6f8fa;color:#1f2328;margin:0;padding:24px;}"
        "h1{font-size:22px;margin:0 0 4px;}"
        ".meta{color:#656d76;font-size:13px;margin-bottom:16px;}"
        ".job{background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:14px 16px;"
        "white-space:pre-wrap;font-size:13px;color:#24292f;margin-bottom:20px;"
        "max-height:220px;overflow:auto;}"
        ".card{background:#fff;border:1px solid #d0d7de;border-radius:10px;padding:16px;"
        "margin-bottom:14px;box-shadow:0 1px 2px rgba(0,0,0,.04);}"
        ".card-head{display:flex;align-items:center;gap:10px;}"
        ".rank{color:#656d76;font-weight:600;}"
        ".cname{font-weight:700;font-size:16px;flex:1;}"
        ".score{font-size:26px;font-weight:800;}"
        ".level{border:1px solid;border-radius:999px;padding:2px 10px;font-size:12px;font-weight:600;}"
        ".summary{color:#424a53;font-size:13px;margin:10px 0;}"
        ".cols{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;}"
        ".col h4{margin:0 0 6px;font-size:13px;}"
        ".col.gap h4{color:#cf222e;}"
        ".col ul{margin:0;padding-left:18px;font-size:13px;line-height:1.7;}"
        ".err{margin-top:10px;color:#cf222e;font-size:13px;}"
        "</style></head><body>"
        "<h1>简历匹配报告</h1>"
        '<div class="meta">评估引擎：%s ｜ 简历数量：%d ｜ 已按匹配度从高到低排序</div>'
        '<div class="job">岗位要求：\n%s</div>'
        "%s"
        "</body></html>"
    ) % (engine, len(results), html.escape(job), cards_html)


def main():
    cfg = load_config()
    job, err = read_job(cfg)
    if err:
        print(err)
        input("按回车退出")
        return
    pdfs = find_pdfs(cfg.get("resume_folder", "简历"))
    if not pdfs:
        print("在「%s」文件夹未找到 PDF 简历。请把简历 PDF 放进去再运行。" % cfg.get("resume_folder", "简历"))
        input("按回车退出")
        return

    from pdf_reader import extract_pdf_text
    from coze_api import coze_configured, call_coze_workflow, local_fallback_score, local_llm_configured, call_local_llm

    use_coze = coze_configured(cfg)
    use_llm = local_llm_configured(cfg)
    if use_coze:
        engine_label = "Coze 工作流（专业 LLM 评估）"
    elif use_llm:
        base = cfg["llm"].get("base_url", "")
        if "3001" in base or "freellmapi" in base:
            engine_label = "免费 LLM（FreeLLMAPI 网关，auto 路由多家免费模型）"
        else:
            engine_label = "本地 LLM（%s，OpenAI 兼容）" % cfg["llm"].get("model", "")
    else:
        engine_label = "本地启发式兜底（未配置任何 LLM）"
    print("共发现 %d 份简历，使用：%s。\n" % (len(pdfs), engine_label))

    results = []
    for i, pdf in enumerate(pdfs, 1):
        name = os.path.splitext(os.path.basename(pdf))[0]
        print("[%d/%d] 处理：%s" % (i, len(pdfs), name))
        text, e = extract_pdf_text(pdf)
        if e:
            print("   ⚠ %s" % e)
            results.append({
                "name": name, "error": e, "score": 0, "level": "读取失败",
                "summary": e, "matched_points": [], "gap_points": [], "suggestions": [],
            })
            continue
        if use_coze:
            res, e = call_coze_workflow(job, text, cfg)
            if e:
                print("   ⚠ %s（回退本地兜底）" % e)
                res = local_fallback_score(job, text)
        elif use_llm:
            res, e = call_local_llm(job, text, cfg)
            if e:
                hint = ""
                if "localhost:3001" in cfg["llm"].get("base_url", ""):
                    hint = ("\n   → FreeLLMAPI 未就绪：先运行『启动freellmapi.bat』启动网关，"
                            "打开 http://localhost:5173 后台填好至少一家 provider 的免费 key，"
                            "并把 Keys 页生成的统一密钥粘贴到 config.json 的 llm.api_key。")
                print("   ⚠ %s（回退本地启发式）%s" % (e, hint))
                res = local_fallback_score(job, text)
        else:
            res = local_fallback_score(job, text)
        res["name"] = name
        for k in ("score", "level", "summary", "matched_points", "gap_points", "suggestions"):
            res.setdefault(k, [] if k.endswith("s") or k.endswith("points") else "")
        results.append(res)
        print("   得分：%s  等级：%s" % (res.get("score", 0), res.get("level", "")))

    results.sort(key=lambda r: r.get("score", 0), reverse=True)
    report = build_report(job, results, engine_label)
    out = os.path.join(HERE, cfg.get("report_file", "简历匹配报告.html"))
    with open(out, "w", encoding="utf-8") as f:
        f.write(report)
    print("\n报告已生成：%s" % out)
    try:
        os.startfile(out)
    except Exception:
        webbrowser.open(out)
    input("按回车退出")


if __name__ == "__main__":
    main()
