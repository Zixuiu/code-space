# -*- coding: utf-8 -*-
"""批量生成 PC-Action 激活码：
1. 写入 Supabase licenses 表（license_key 未绑定 -> 用户激活时绑定）
2. 写入 PayPro 码池文件 config/cards/product-1.txt（PayPro pass() 自动取码发邮件）
"""
import json
import secrets
import urllib.request
from pathlib import Path

SUPABASE_URL = "https://loifmrvoignxlifizogv.supabase.co"
ANON_KEY = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6"
            "ImxvaWZtcnZvaWdueGxpZml6b2d2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA5NTA3ODksImV4cCI6MjA3NjUyNjc4OX0"
            ".EtuSOO6pms-kkHiR4g1lLU8As-J0mWR0WIO8TiwselQ")

# 去掉易混淆字符 0/O/1/I/L
ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
N_CODES = 50


def gen_code():
    seg = lambda: "".join(secrets.choice(ALPHABET) for _ in range(4))
    return f"PCA-{seg()}-{seg()}-{seg()}"


def supabase_insert(rows):
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/activation_codes",
        data=json.dumps(rows).encode("utf-8"),
        method="POST",
        headers={
            "apikey": ANON_KEY,
            "Authorization": f"Bearer {ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status


def supabase_cleanup_licenses():
    """删除误写入 licenses 表的码（user_id 为空的 PCA- 行）"""
    import time as _t
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/licenses?license_key=like.PCA-*&user_id=is.null",
        method="DELETE",
        headers={
            "apikey": ANON_KEY,
            "Authorization": f"Bearer {ANON_KEY}",
            "Prefer": "return=representation",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8") or "[]")
            return len(data)
    except Exception as e:
        print(f"[WARN] licenses 清理失败(不影响主流程): {e}")
        return -1


def supabase_cleanup_stale_codes():
    """删除上一批激活码（本次批次 note + PCA- 前缀 + 未使用）"""
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/activation_codes?code=like.PCA-*&used=eq.0&note=eq.PayPro发码批次-20260903",
        method="DELETE",
        headers={
            "apikey": ANON_KEY,
            "Authorization": f"Bearer {ANON_KEY}",
            "Prefer": "return=representation",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8") or "[]")
            return len(data)
    except Exception as e:
        print(f"[WARN] activation_codes 清理失败(不影响主流程): {e}")
        return -1


def main():
    # 清理上一批误形态码
    n = supabase_cleanup_stale_codes()
    if n >= 0:
        print(f"[OK] activation_codes 清理上一批: {n} 条")

    codes = [gen_code() for _ in range(N_CODES)]
    assert len(set(codes)) == N_CODES, "码重复，重跑"

    now = _now_str()
    # 关键：activate_code 会把用户输入清洗为纯字母数字大写后查询，
    # 库里存「无连字符」形态；码池文件存「带连字符」形态供邮件展示。
    rows = [
        {
            "code": c.replace("-", ""),
            "plan": "plan_1",
            "months": 1,
            "used": 0,
            "note": "PayPro发码批次-20260903",
            "created_at": now,
        }
        for c in codes
    ]
    try:
        status = supabase_insert(rows)
        print(f"[OK] Supabase activation_codes 写入 {len(rows)} 条(无连字符形态), HTTP {status}")
    except Exception as e:
        print(f"[FAIL] Supabase 写入失败: {e}")
        print("码仍写入本地码池文件，可在修复后重跑入库。")

    pool = Path(__file__).resolve().parent.parent / "PayPro-master" / "config" / "cards" / "product-1.txt"
    pool.parent.mkdir(parents=True, exist_ok=True)
    pool.write_text("\n".join(codes) + "\n", encoding="utf-8")
    print(f"[OK] 码池文件(带连字符展示形态): {pool}")
    print(f"样例: 库={codes[0].replace('-', '')} / 展示={codes[0]}")


def _now_str():
    import time
    return time.strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    main()
