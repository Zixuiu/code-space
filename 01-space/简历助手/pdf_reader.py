"""PDF 文本抽取。优先使用 pypdf；未安装时给出明确错误。"""
import os


def extract_pdf_text(path, max_chars=16000):
    """返回 (text, error)。成功时 error=None。"""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None, "未安装 pypdf，请先运行「简历助手.bat」自动安装依赖（或执行 pip install pypdf）"
    try:
        reader = PdfReader(path)
        parts = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                parts.append("")
        text = "\n".join(parts).strip()
        if not text:
            return None, "未能从 PDF 提取到文本（可能是扫描件/图片型 PDF，建议转成可复制文本）"
        if len(text) > max_chars:
            text = text[:max_chars] + "\n...（内容过长已截断）"
        return text, None
    except Exception as e:
        return None, "读取 PDF 失败：%s" % e
