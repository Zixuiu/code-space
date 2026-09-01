# -*- coding: utf-8 -*-
"""纯标准库生成中文 PDF 简历样例。
方案：从系统 .ttc 抽取 font0 成独立 TTF 内嵌（FontFile2），文本用 GID（Identity-H）编码，
并提供 ToUnicode CMap(GID->Unicode) 让 pypdf 正确提取中文。
用法：python gen_samples.py  -> 在 简历/ 下生成 张三.pdf / 李四.pdf / 王五.pdf
"""
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = r"C:/Windows/Fonts/msyh.ttc"
OUT_DIR = os.path.join(HERE, "简历")


def _read_table(data, off, length):
    return data[off:off + length]


def build_standalone_ttf(data, f0):
    """从 TTC 的 font0 抽取成独立 TTF（字节）。"""
    num = struct.unpack(">H", data[f0 + 4:f0 + 6])[0]
    head16 = data[f0:f0 + 12]
    o = f0 + 12
    tables = []
    for _ in range(num):
        tag = data[o:o + 4]
        length = struct.unpack(">I", data[o + 12:o + 16])[0]
        toff = struct.unpack(">I", data[o + 8:o + 12])[0]
        tables.append((tag, toff, length))
        o += 16
    body = bytearray()
    dir_entries = []
    cursor = 12 + num * 16
    for tag, toff, length in tables:
        raw = bytearray(data[toff:toff + length])
        while len(raw) % 4:
            raw.append(0)
        dir_entries.append((tag, cursor, length))
        body += raw
        cursor += len(raw)
    out = bytearray(head16)
    for tag, noff, length in dir_entries:
        out += tag + struct.pack(">III", 0, noff, length)
    out += body
    return bytes(out)


def parse_cmap(ttf):
    """返回 (gid_of: {unicode: gid}, metrics)。优先 (3,10)fmt12 / (3,1)fmt4 / (0,*) 。"""
    num = struct.unpack(">H", ttf[4:6])[0]
    o = 12
    tabs = {}
    for _ in range(num):
        tag = ttf[o:o + 4]
        toff = struct.unpack(">I", ttf[o + 8:o + 12])[0]
        tlen = struct.unpack(">I", ttf[o + 12:o + 16])[0]
        tabs[tag] = (toff, tlen)
        o += 16
    cmap_off, _ = tabs[b"cmap"]
    nsub = struct.unpack(">H", ttf[cmap_off + 2:cmap_off + 4])[0]
    p = cmap_off + 4
    subs = []
    for _ in range(nsub):
        plat, enc, soff = struct.unpack(">HHI", ttf[p:p + 8])
        subs.append((plat, enc, cmap_off + soff))
        p += 8

    def parse4(s):
        g = {}
        sc = struct.unpack(">H", ttf[s + 6:s + 8])[0] // 2
        base = s + 14
        end = struct.unpack(">%dh" % sc, ttf[base:base + sc * 2]); base += sc * 2 + 2
        start = struct.unpack(">%dh" % sc, ttf[base:base + sc * 2]); base += sc * 2
        idelta = struct.unpack(">%dh" % sc, ttf[base:base + sc * 2]); base += sc * 2
        idroff = struct.unpack(">%dH" % sc, ttf[base:base + sc * 2]); base += sc * 2
        gb = base
        for i in range(sc):
            if start[i] == 0xFFFF:
                continue
            for c in range(start[i], end[i] + 1):
                if idroff[i] == 0:
                    g[c] = (c + idelta[i]) & 0xFFFF
                else:
                    idx = idroff[i] // 2 + (c - start[i]) - (sc - i)
                    arr = struct.unpack(">H", ttf[gb + idx * 2:gb + idx * 2 + 2])[0]
                    g[c] = (arr + idelta[i]) & 0xFFFF if arr != 0 else 0
        return g

    def parse12(s):
        g = {}
        ng = struct.unpack(">I", ttf[s + 12:s + 16])[0]
        q = s + 16
        for _ in range(ng):
            lo, hi, sg = struct.unpack(">III", ttf[q:q + 12])
            for c in range(lo, hi + 1):
                g[c] = sg + (c - lo)
            q += 12
        return g

    # 选择优先级：(3,10)fmt12 > (3,1)fmt4 > (0,*)fmt4/12（保证 CJK 用 format12）
    cands = []
    for plat, enc, s in subs:
        fmt = struct.unpack(">H", ttf[s:s + 2])[0]
        if (plat, enc) == (3, 10) and fmt == 12:
            cands.append(("a", s))
        elif (plat, enc) == (3, 1) and fmt == 4:
            cands.append(("b", s))
        elif plat == 0 and fmt == 4:
            cands.append(("c", s))
        elif plat == 0 and fmt == 12:
            cands.append(("d", s))
    cands.sort()
    gid_of = None
    if cands:
        pri, s = cands[0]
        gid_of = parse12(s) if pri in ("a", "d") else parse4(s)
    if gid_of is None:
        raise ValueError("未找到可用的 Unicode cmap 子表")
    # 度量
    hoff, _ = tabs[b"head"]
    units = struct.unpack(">H", ttf[hoff + 18:hoff + 20])[0]
    bbox = struct.unpack(">hhhh", ttf[hoff + 36:hoff + 44])
    heoff, _ = tabs[b"hhea"]
    ascent = struct.unpack(">h", ttf[heoff + 4:heoff + 6])[0]
    descent = struct.unpack(">h", ttf[heoff + 6:heoff + 8])[0]
    return gid_of, {"units": units, "bbox": bbox, "ascent": ascent, "descent": descent}


def load_font(path):
    data = open(path, "rb").read()
    if data[:4] == b"ttcf":
        num = struct.unpack(">I", data[8:12])[0]
        offs = struct.unpack(">%dI" % num, data[12:12 + num * 4])
        f0 = offs[0]
        ttf = build_standalone_ttf(data, f0)
    else:
        ttf = data
    gid_of, m = parse_cmap(ttf)
    return {"ttf": ttf, "gid_of": gid_of, **m}


def make_pdf(font, lines):
    gid_of = font["gid_of"]
    ttf = font["ttf"]
    used = {}

    def gid(ch):
        return gid_of.get(ord(ch), 0)

    parts = []
    y = 800
    first = True
    for ln in lines:
        if first:
            first = False
        else:
            parts.append(b"\nET\nBT\n/F1 11 Tf")
        parts.append(b"\n1 0 0 1 50 %d Tm\n" % y)
        hexchars = []
        for ch in ln:
            g = gid(ch)
            used.setdefault(g, ord(ch))
            hexchars.append(b"%04X" % g)
        parts.append(b"<" + b"".join(hexchars) + b"> Tj")
        y -= 18
        if y < 60:
            y = 800
    content = b"BT\n/F1 11 Tf" + b"".join(parts) + b"\nET"

    tu = [b"/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n"
          b"/CMapType 2 def\n/CMapName /MsyhToUni def\n"
          b"1 begincodespacerange\n<0000> <FFFF>\nendcodespacerange\n"]
    items = sorted(used.items())
    for i in range(0, len(items), 100):
        batch = items[i:i + 100]
        tu.append(b"%d beginbfchar\n" % len(batch))
        for g, u in batch:
            tu.append(b"<%04X> <%04X>\n" % (g, u))
        tu.append(b"endbfchar\n")
    tu.append(b"endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend")
    tu = b"".join(tu)

    bbox = font["bbox"]
    ascent, descent = font["ascent"], font["descent"]
    units = font["units"]
    maxcid = max(used) if used else 0

    # 显式对象编号，杜绝 insert 错位导致 FontFile2 指空
    obj_catalog = b"<< /Type /Catalog /Pages 2 0 R >>"
    obj_pages = b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
    obj_page = (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>")
    obj_type0 = (b"<< /Type /Font /Subtype /Type0 /BaseFont /MSYH "
                 b"/Encoding /Identity-H /ToUnicode 8 0 R /DescendantFonts [9 0 R] >>")
    obj_contents = b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream"
    obj_fontdesc = (b"<< /Type /FontDescriptor /FontName /MSYH /Flags 4 "
                    b"/FontBBox [%d %d %d %d] /ItalicAngle 0 /Ascent %d /Descent %d "
                    b"/CapHeight %d /StemV 80 /FontFile2 7 0 R >>"
                    % (bbox[0], bbox[1], bbox[2], bbox[3], ascent, descent, ascent))
    obj_fontfile = b"<< /Length %d >>\nstream\n" % len(ttf) + ttf + b"\nendstream"
    obj_tounicode = b"<< /Length %d >>\nstream\n" % len(tu) + tu + b"\nendstream"
    obj_cidfont = (b"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /MSYH "
                   b"/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> "
                   b"/FontDescriptor 6 0 R /W [ 0 %d %d ] >>" % (maxcid, units))

    objects = [obj_catalog, obj_pages, obj_page, obj_type0,
               obj_contents, obj_fontdesc, obj_fontfile, obj_tounicode, obj_cidfont]

    out = [b"%PDF-1.5\n%\xe2\xe3\xcf\xd3\n"]
    offsets = []
    for i, body in enumerate(objects, 1):
        offsets.append((i, len(b"".join(out))))
        out.append(b"%d 0 obj\n" % i + body + b"\nendobj\n")
    xref_pos = len(b"".join(out))
    n = max(num for num, _ in offsets) + 1
    xref = [b"xref\n0 %d\n" % n, b"0000000000 65535 f \n"]
    for num, off in offsets:
        xref.append(b"%010d 00000 n \n" % off)
    out.append(b"".join(xref))
    out.append(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (n, xref_pos))
    return b"".join(out)


RESUMES = {
    "张三": [
        "张三  后端开发工程师",
        "手机：138-0000-0001  邮箱：zhangsan@example.com",
        "学历：本科 计算机科学与技术（某211高校）",
        "",
        "【专业技能】",
        "- 熟练掌握 Python，6 年后端开发经验",
        "- 精通 FastAPI 与 Flask，主导多个 Web 服务从 0 到 1",
        "- 熟悉 MySQL / PostgreSQL，掌握索引优化与 SQL 调优",
        "- 熟悉 Redis 缓存与 Kafka 消息队列，落地过高并发架构",
        "- 微服务架构经验丰富，熟练 Docker / Kubernetes 容器编排",
        "- 熟悉 Linux 开发与部署，搭建过 GitLab CI/CD 流水线",
        "- 熟悉 Golang，有 AI 应用落地经验（RAG 问答系统）",
        "",
        "【工作经历】",
        "2020-至今  某互联网公司  高级后端工程师",
        "  - 负责核心交易系统，QPS 峰值 5 万，稳定性 99.99%",
        "  - 主导服务拆分与 K8s 化，资源成本下降 30%",
        "2017-2020  某科技公司  后端工程师",
        "  - 使用 FastAPI 搭建开放平台 API，日调用千万级",
    ],
    "李四": [
        "李四  软件开发工程师",
        "手机：139-0000-0002  邮箱：lisi@example.com",
        "学历：本科 软件工程",
        "",
        "【专业技能】",
        "- 了解 Python，1 年脚本开发经验（非主力语言）",
        "- 熟悉 JavaScript / Vue，前端开发为主",
        "- 用过 Flask 写过简单接口，未接触 FastAPI / Django",
        "- 了解 MySQL 基础查询，未做过索引优化",
        "- 听说过 Redis 与 Kafka，无实际项目经验",
        "- 无微服务与 K8s 经验，仅本地 Docker 跑过 demo",
        "- 熟悉 Windows 开发，Linux 部署经验较少",
        "",
        "【工作经历】",
        "2024-至今  某创业公司  全栈开发（以前端为主）",
        "  - 负责后台管理系统前端，偶有 Node 接口编写",
    ],
    "王五": [
        "王五  数据分析师",
        "手机：137-0000-0003  邮箱：wangwu@example.com",
        "学历：硕士 统计学",
        "",
        "【专业技能】",
        "- 熟练 SQL（Hive / Spark SQL）做数据清洗与报表",
        "- 熟练 Python（pandas / numpy）做数据分析与可视化",
        "- 熟练 Tableau / PowerBI 业务看板搭建",
        "- 熟悉 Excel 高级函数与宏",
        "- 无 Web 框架、无后端服务、无微服务经验",
        "- 无 Redis / Kafka / Docker / K8s 相关经验",
        "",
        "【工作经历】",
        "2021-至今  某零售企业  数据分析师",
        "  - 搭建销售主题看板，支撑运营决策",
        "  - 输出周/月报，无系统开发职责",
    ],
}


def main():
    font = load_font(FONT_PATH)
    print("字体加载完成：CID 映射 %d 项，TTF %d 字节" % (len(font["gid_of"]), len(font["ttf"])))
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, lines in RESUMES.items():
        pdf = make_pdf(font, lines)
        outp = os.path.join(OUT_DIR, name + ".pdf")
        with open(outp, "wb") as f:
            f.write(pdf)
        print("生成：%s  (%d 字节)" % (outp, len(pdf)))


if __name__ == "__main__":
    main()
