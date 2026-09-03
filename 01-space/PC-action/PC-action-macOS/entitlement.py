"""
PC-action 商业化权限与激活模块
- 定价配置：pricing.json（作者可在后台 admin_manager 修改）
- 权限判定：has_full_access = VIP 有效期内 或 试用期内（限时全功能试用策略）
- 激活码：卡密激活模式（用户在第三方平台付款拿码 -> 程序内输码自动开通 VIP）
"""
import os
import json
import uuid
from datetime import datetime, timedelta

try:
    from supabase_db import get_supabase_manager
    SUPABASE_OK = True
except ImportError:
    SUPABASE_OK = False

PRICING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pricing.json')

DEFAULT_PRICING = {
    "plan_1": {"name": "基础会员", "price": 9.9, "months": 1, "desc": "包月"},
    "plan_2": {"name": "高级会员", "price": 100.0, "months": 12, "desc": "包年（约合8.3/月，立省19%）"},
    "trial_days": 7,
    "channel_name": "爱发电",
    "channel_url": "https://afdian.com/a/your_id",
}


# ------------------------- 定价配置 -------------------------
def get_pricing():
    """读取定价配置，缺字段则用默认值兜底"""
    try:
        if os.path.exists(PRICING_FILE):
            with open(PRICING_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            merged = dict(DEFAULT_PRICING)
            merged.update(data)
            # 保证 plan 子字段完整
            for k in ('plan_1', 'plan_2'):
                if k in merged and isinstance(merged[k], dict):
                    base = dict(DEFAULT_PRICING[k])
                    base.update(merged[k])
                    merged[k] = base
            return merged
    except Exception as e:
        print(f"读取定价失败，使用默认: {e}")
    return dict(DEFAULT_PRICING)


def save_pricing(pricing):
    """保存定价配置（后台 admin_manager 调用）"""
    try:
        with open(PRICING_FILE, 'w', encoding='utf-8') as f:
            json.dump(pricing, f, ensure_ascii=False, indent=2)
        return True, "定价已保存"
    except Exception as e:
        return False, f"保存失败: {e}"


# ------------------------- 权限判定 -------------------------
def get_entitlement(username):
    """
    返回用户权益状态字典。
    策略：限时全功能试用。试用期内全功能开放；过期且非 VIP 则锁定。
    离线（Supabase 未连）时放行，避免本地无网时把用户锁死。
    """
    fallback = {
        "is_vip": False, "vip_end": None, "trial_end": None,
        "trial_valid": False, "has_access": True, "reason": "offline_or_no_user"
    }
    if not SUPABASE_OK:
        return fallback
    try:
        supabase_manager = get_supabase_manager()
        if not supabase_manager.is_connected():
            return fallback
        user = supabase_manager.get_user(username)
        if not user:
            return fallback

        now = datetime.now()
        pricing = get_pricing()
        trial_days = int(pricing.get('trial_days', 7))

        # VIP 状态
        is_vip = bool(user.get('is_vip', 0))
        vip_end = user.get('vip_end_date')
        vip_valid = False
        if is_vip and vip_end:
            try:
                vip_valid = datetime.strptime(str(vip_end)[:10], '%Y-%m-%d') > now
            except Exception:
                vip_valid = False

        # 试用状态（基于注册时间）
        trial_end = None
        created = user.get('created_at')
        if created:
            try:
                ct = datetime.strptime(str(created)[:19], '%Y-%m-%d %H:%M:%S')
                trial_end = ct + timedelta(days=trial_days)
            except Exception:
                trial_end = None
        trial_valid = bool(trial_end and trial_end > now)

        has_access = bool(vip_valid or trial_valid)
        return {
            "is_vip": vip_valid,
            "vip_end": vip_end if vip_valid else None,
            "trial_end": trial_end.strftime('%Y-%m-%d') if trial_end else None,
            "trial_valid": trial_valid,
            "has_access": has_access,
        }
    except Exception as e:
        print(f"获取权益失败: {e}")
        return fallback


def has_full_access(username):
    """核心 gate 调用：当前用户是否拥有全功能权限"""
    if not username:
        return True  # 未登录态由调用方决定，此处不擅自锁
    return get_entitlement(username).get('has_access', True)


def trial_remaining_days(username):
    """返回试用剩余天数（用于 UI 展示），无试用期返回 None"""
    ent = get_entitlement(username)
    if not ent.get('trial_end'):
        return None
    try:
        te = datetime.strptime(ent['trial_end'], '%Y-%m-%d')
        return max(0, (te - datetime.now()).days)
    except Exception:
        return None


# ------------------------- 激活码 -------------------------
def generate_activation_codes(count, months, plan='plan_1', note=''):
    """
    后台批量生成激活码，写入 Supabase activation_codes 表。
    :return: 成功生成的码列表
    """
    if not SUPABASE_OK:
        return []
    try:
        supabase_manager = get_supabase_manager()
        if not supabase_manager.is_connected():
            return []
        codes = []
        for _ in range(int(count)):
            code = uuid.uuid4().hex[:12].upper()
            row = {
                'code': code,
                'plan': plan,
                'months': int(months),
                'used': 0,
                'used_by': None,
                'note': note or '',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            try:
                r = supabase_manager.client.table('activation_codes').insert(row).execute()
                if r.data:
                    codes.append(code)
            except Exception as e:
                print(f"生成激活码失败: {e}")
        return codes
    except Exception as e:
        print(f"批量生成激活码异常: {e}")
        return []


def activate_code(code, username):
    """
    用户输码激活：校验码 -> 开通对应 months 的 VIP（复用 manage_vip_license）。
    :return: (success, message)
    """
    if not SUPABASE_OK:
        return False, "服务未连接"
    code = ''.join(ch for ch in (code or '') if ch.isalnum()).upper()
    if not code:
        return False, "请输入激活码"
    try:
        supabase_manager = get_supabase_manager()
        if not supabase_manager.is_connected():
            return False, "服务未连接"
        r = supabase_manager.client.table('activation_codes').select('*').eq('code', code).execute()
        if not r.data:
            return False, "激活码无效"
        row = r.data[0]
        if row.get('used'):
            return False, "激活码已被使用"
        months = int(row.get('months', 1))

        from database_helper import db_helper
        ok, msg = db_helper.manage_vip_license(username, months)
        if not ok:
            return False, f"开通失败: {msg}"

        # 标记激活码已使用
        try:
            supabase_manager.client.table('activation_codes').update({
                'used': 1,
                'used_by': username,
                'used_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }).eq('id', row['id']).execute()
        except Exception as e:
            print(f"标记激活码已用失败(不影响开通): {e}")

        return True, f"激活成功，已开通 {months} 个月会员"
    except Exception as e:
        return False, f"激活异常: {e}"


def list_activation_codes(only_unused=False):
    """后台列出激活码（可选仅未使用）"""
    if not SUPABASE_OK:
        return []
    try:
        supabase_manager = get_supabase_manager()
        if not supabase_manager.is_connected():
            return []
        q = supabase_manager.client.table('activation_codes').select('*')
        if only_unused:
            q = q.eq('used', 0)
        r = q.execute()
        return r.data if r.data else []
    except Exception as e:
        print(f"列出激活码失败: {e}")
        return []
