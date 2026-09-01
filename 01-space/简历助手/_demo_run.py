# -*- coding: utf-8 -*-
"""演示：造 3 份示例简历 PDF -> 跑匹配打分 -> 生成报告（本地兜底路径，不依赖 Coze）。"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
FONT = "STSong-Light"

def make_pdf(path, lines):
    c = canvas.Canvas(path, pagesize=A4)
    c.setFont(FONT, 12)
    y = 800
    for ln in lines:
        c.drawString(50, y, ln)
        y -= 22
    c.save()

job = ("【Python 后端工程师 / FDE 方向】\n"
       "要求：熟练掌握 Python，3 年以上开发经验；熟悉 FastAPI / Flask；\n"
       "熟悉 MySQL、Redis；熟悉 Docker、Kubernetes；本科及以上学历；\n"
       "有客户现场交付 / 售前支持经验者优先。")

r1 = ["张三 ｜ Python 后端工程师",
      "本科，计算机科学，5 年经验",
      "精通 Python，主导 FastAPI 微服务，使用 MySQL + Redis 做缓存",
      "熟练 Docker、Kubernetes 容器化部署，负责客户现场交付与售前支持",
      "项目：为某金融客户搭建实时风控 API，部署于 K8s 集群"]

r2 = ["李四 ｜ 后端开发",
      "本科，软件工程，2 年经验",
      "使用 Python + Flask 开发业务系统，熟悉 MySQL",
      "了解 Docker，无 Kubernetes 实操经验",
      "无客户现场交付经验"]

r3 = ["王五 ｜ Java 开发工程师",
      "大专，4 年经验",
      "精通 Java / Spring Boot，使用 Oracle 数据库",
      "了解 Docker，未使用过 Python 与 K8s",
      "无售前 / 客户交付背景"]

folder = os.path.join(HERE, "简历")
os.makedirs(folder, exist_ok=True)
make_pdf(os.path.join(folder, "示例-张三.pdf"), r1)
make_pdf(os.path.join(folder, "示例-李四.pdf"), r2)
make_pdf(os.path.join(folder, "示例-王五.pdf"), r3)
print("已生成 3 份示例 PDF 到 简历/ 文件夹")

import run, pdf_reader
from coze_api import local_fallback_score

results = []
for name, _ in [("示例-张三", r1), ("示例-李四", r2), ("示例-王五", r3)]:
    pdf = os.path.join(folder, name + ".pdf")
    text, e = pdf_reader.extract_pdf_text(pdf)
    assert e is None, e
    res = local_fallback_score(job, text)
    res["name"] = name
    results.append(res)
    print("  %s -> 得分 %s ｜ %s" % (name, res["score"], res["level"]))

results.sort(key=lambda r: r["score"], reverse=True)
report = run.build_report(job, results, use_coze=False)
out = os.path.join(HERE, "演示-简历匹配报告.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(report)
print("\n报告已生成：", out)
