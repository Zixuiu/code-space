"""
PC-action 商业化权限与激活模块
- 定价配置：pricing.json（作者可在后台 admin_manager 修改）
- 权限判定：has_full_access = VIP 有效期内 或 试用期内（限时全功能试用策略）
- 激活码：卡密激活模式（用户在第三方平台付款拿码 -> 程序内输码自动开通 VIP）
"""
import os
import json
import time
import uuid
import hmac
import hashlib
import base64
from datetime import datetime, timedelta

try:
    from supabase_db import get_supabase_manager
    SUPABASE_OK = True
except ImportError:
    SUPABASE_OK = False

PRICING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pricing.json')
REMOTE_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pricing_remote.json')

# 远程配置源：URL 永不变（GitCode 仓库），内容动态更新当前充值页域名。
# 充值页域名动态获取优先级：本地 cpolar 实时隧道地址(自动跟漂移) > 本地兜底 > 远程配置源(动态更新)。
# cpolar 免费域名会漂移，本地实时地址最高优先，app 自启即自动跟上，无需改配置或推远程。
CONFIG_SOURCES = [
    "https://gitcode.com/api/v5/repos/weixin_58844486/pc-action-config/raw/paypro-config.json?ref=main",
    "https://gitcode.com/api/v5/repos/weixin_58844486/pc-action-config/contents/paypro-config.json?ref=main",
]

DEFAULT_PRICING = {
    "plan_1": {"name": "VIP会员", "price": 9.9, "months": 1, "desc": "包月（全功能）"},
    "trial_days": 7,
    "channel_name": "PC-Action",
    "channel_url": "https://3e22a5a4.r8.cpolar.top/recharge.html",
}


# ------------------------- 防破解：离线回退与本地状态签名 -------------------------
# 背景：早期策略「离线/异常一律放行」是为了不误伤正版，但客观上让破解者靠
# 断网/hosts 屏蔽 Supabase 就能白嫖全功能。整改为 -> 联网判定权威，仅当网络
# 不可达时按「已签名的最近一次成功授权」给一个离线宽限期，超期即锁定。
OFFLINE_GRACE_DAYS = 7          # 离线宽限期（天）：到期需联网验证一次
ENT_CACHE_VERSION = 1

# 本地授权状态 HMAC 签名密钥。目的：让普通用户手工改 user_data 里的缓存 JSON
# 会因签名不匹配而失效。它提高篡改门槛，非绝对安全（本地无法绝对防逆向）。
_ENT_SIGN_SECRET = b"PCa@ction#SignedEnt!2026$c7f2-9b41-ea3d8c7f2aa1"

# _ent_store_path 惰性计算一次（避免每次判定都拼路径）
_ENT_STORE_PATH = None


def _ent_store_path():
    global _ENT_STORE_PATH
    if _ENT_STORE_PATH:
        return _ENT_STORE_PATH
    try:
        from utils import get_user_data_path
        _ENT_STORE_PATH = os.path.join(get_user_data_path(), "entitlement_cache.json")
    except Exception:
        d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data")
        os.makedirs(d, exist_ok=True)
        _ENT_STORE_PATH = os.path.join(d, "entitlement_cache.json")
    return _ENT_STORE_PATH


def _ent_sign(payload):
    return hmac.new(_ENT_SIGN_SECRET, payload, hashlib.sha256).hexdigest()


def _ent_save(cache):
    """把 {username: {ent..., 'ts': epoch}} 整个编码 + HMAC 签名落盘。
    ts 用"最近一次联网验证成功"的时间戳，破解者改 ts 会让签名失效。"""
    try:
        payload = base64.b64encode(
            json.dumps(cache, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        ).decode('ascii')
        store = {"ver": ENT_CACHE_VERSION, "payload": payload, "sig": _ent_sign(payload.encode('ascii'))}
        with open(_ent_store_path(), 'w', encoding='utf-8') as f:
            json.dump(store, f, ensure_ascii=False)
    except Exception:
        pass


def _ent_load():
    """读取并校验签名的本地状态缓存；签名不符视为被篡改，返回空。"""
    try:
        with open(_ent_store_path(), 'r', encoding='utf-8') as f:
            store = json.load(f)
        if store.get('ver') != ENT_CACHE_VERSION:
            return {}
        payload = store.get('payload') or ''
        if not hmac.compare_digest(store.get('sig') or '', _ent_sign(payload.encode('ascii'))):
            return {}
        cache = json.loads(base64.b64decode(payload.encode('ascii')).decode('utf-8'))
        return cache if isinstance(cache, dict) else {}
    except Exception:
        return {}


def _ent_read_signed(username):
    """返回该用户最近一次联网验证成功的 (ent, ts)，无或无效返回 None。"""
    cache = _ent_load()
    rec = cache.get(username)
    if not isinstance(rec, dict) or not isinstance(rec.get('ts'), (int, float)) or not isinstance(rec.get('ent'), dict):
        return None
    return rec['ent'], float(rec['ts'])


# ------------------------- 渠道地址可用性校验 -------------------------
# cpolar 免费域名漂移后旧域名会被回收给别人（曾出现过陌生人网站），
# HTTP 200 也可能是别人的站，校验必须带页面指纹，不能只看状态码。
CHANNEL_FINGERPRINTS = ("PC-Action", "会员充值")
_URL_VERIFY_CACHE = {}   # url -> (ts, ok)
_URL_VERIFY_TTL = 300    # 秒


# ------------------------- 本地 cpolar 实时隧道地址 -------------------------
# cpolar 免费版域名会漂移；与其依赖写死的候选或远程配置滞后，
# 不如直接读本地 cpolar 当前隧道地址（来自其运行日志里最新的 StartProxy Url），
# 作为最高优先级候选，漂移后 app 自启即自动跟上，无需改配置/推远程。
import os as _os
import re as _re
import glob as _glob

_CPOLAR_LOG_DIR = _os.path.join(_os.path.expanduser("~"), ".cpolar", "logs")
# 只取 https 隧道地址（bind_tls: both 时日志里 http/https 都有，优先 https）
_CPOLAR_URL_RE = _re.compile(r'https://[a-z0-9.\-]+\.cpolar\.(?:io|com|cn|top)')
_LOCAL_CPOLAR_CACHE = {"ts": 0.0, "url": None}
_LOCAL_CPOLAR_TTL = 60  # 秒，避免每次解析都读日志


def _probe_cpolar_url():
    """从 cpolar 本地日志尾部提取当前 website 隧道公网地址（不含路径）。
    免费版 /api/tunnels 不返回 JSON（实测空响应），故读日志里最新的 StartProxy Url。失败返回 None。"""
    try:
        logs = sorted(_glob.glob(_os.path.join(_CPOLAR_LOG_DIR, "cpolar_service.log*")),
                      key=_os.path.getmtime, reverse=True)
        for lf in logs[:3]:
            try:
                with open(lf, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(0, size - 300000))  # 只读尾部 300KB，避免整文件
                    tail = f.read()
                urls = _CPOLAR_URL_RE.findall(tail)
                if urls:
                    return urls[-1]  # 最后一条 https 隧道地址
            except Exception:
                continue
    except Exception:
        pass
    return None


def _local_cpolar_url():
    """带短缓存的本地 cpolar 当前隧道地址（https://xxxx.cpolar.cn，不含路径）。"""
    import time as _t
    now = _t.time()
    if now - _LOCAL_CPOLAR_CACHE["ts"] < _LOCAL_CPOLAR_TTL:
        return _LOCAL_CPOLAR_CACHE["url"]
    url = _probe_cpolar_url()
    _LOCAL_CPOLAR_CACHE["ts"] = now
    _LOCAL_CPOLAR_CACHE["url"] = url
    return url


def verify_channel_url(url, timeout=3):
    """校验充值页地址是否真的是我们的页面（200 且含品牌指纹）。结果缓存 300s。"""
    if not url or not isinstance(url, str):
        return False
    import time as _t
    try:
        cached = _URL_VERIFY_CACHE.get(url)
        if cached and _t.time() - cached[0] < _URL_VERIFY_TTL:
            return cached[1]
    except Exception:
        pass
    ok = False
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "PC-Action"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if getattr(r, 'status', 200) == 200:
                body = r.read(4096).decode('utf-8', 'ignore')
                ok = any(fp in body for fp in CHANNEL_FINGERPRINTS)
    except Exception:
        ok = False
    _URL_VERIFY_CACHE[url] = (_t.time(), ok)
    return ok


def _candidate_channel_urls(local_url, remote):
    """去重汇总所有候选充值地址：本地 cpolar 实时地址(优先) -> 本地 -> 远程主地址 -> 远程 mirror 列表"""
    candidates = []
    # 真·自动：本地 cpolar 当前隧道地址排第一，免费域名漂移时自启即跟上
    live = _local_cpolar_url()
    if live:
        live_u = live.rstrip('/') + '/recharge.html'
        if live_u not in candidates:
            candidates.append(live_u)
    if isinstance(remote, dict):
        for u in [local_url, remote.get('channel_url')] + list(remote.get('mirror_urls') or []):
            if u and isinstance(u, str) and u not in candidates:
                candidates.append(u)
    elif local_url:
        if local_url not in candidates:
            candidates.append(local_url)
    return candidates


def resolve_channel_url(local_url=None, timeout=3, deep=False):
    """返回当前真实可用的充值地址。
    deep=True 完整逐个探测（适合后台线程/预热）；False 时若本地地址缓存判定可用则直接返回。"""
    try:
        pricing = get_pricing(refresh_remote=False)
        if local_url is None:
            local_url = pricing.get('channel_url')
        remote = _fetch_remote_config() or {}
    except Exception:
        remote = {}
    candidates = _candidate_channel_urls(local_url, remote)
    if not candidates:
        return local_url
    if not deep:
        # 浅模式：本地地址缓存判定可用（或与最佳候选一致）就直接用，零网络等待
        best = candidates[0]
        cached = _URL_VERIFY_CACHE.get(best)
        import time as _t
        if cached and cached[1] and _t.time() - cached[0] < _URL_VERIFY_TTL:
            return best
    for u in candidates:
        if verify_channel_url(u, timeout=timeout):
            return u
    # 全部探测失败：仍返回第一个候选（可能是本机网络问题），不返回空
    return candidates[0]


def warmup_channel_url():
    """启动时后台预热：探测并缓存可用充值地址，避免用户点购买按钮时卡顿。"""
    import threading

    def _run():
        try:
            resolve_channel_url(deep=True)
        except Exception:
            pass
    try:
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t
    except Exception:
        return None


def _fetch_remote_config(timeout=3):
    """从固定配置源拉最新配置（channel_url 等）。
    顺序：CONFIG_SOURCES 在线拉 -> 上次成功缓存 -> None（用本地默认）。"""
    import urllib.request
    for u in CONFIG_SOURCES:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "PC-Action"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode('utf-8'))
            # 兼容 contents 端点：{"encoding":"base64","content":"..."}
            if isinstance(data, dict) and data.get('content') and not data.get('channel_url'):
                import base64
                data = json.loads(base64.b64decode(str(data['content']).strip()).decode('utf-8'))
            if isinstance(data, dict) and data.get('channel_url'):
                try:
                    with open(REMOTE_CACHE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                return data
        except Exception:
            continue
    try:
        with open(REMOTE_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


# ------------------------- 定价配置 -------------------------
# 远程配置缓存：TTL 内直接用缓存，避免点击录制/回放时在 UI 线程同步发 HTTP 造成卡顿
_REMOTE_CFG_CACHE = {"ts": 0.0, "data": None}
_REMOTE_CFG_TTL = 600  # 秒


def get_pricing(refresh_remote=True):
    """读取定价配置：本地 pricing.json -> 远程配置源覆盖（channel_url 等）-> 默认兜底
    远程拉取带 10 分钟 TTL 缓存；refresh_remote=False 时完全用本地/缓存值（零网络）"""
    try:
        if os.path.exists(PRICING_FILE):
            with open(PRICING_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}
    except Exception as e:
        print(f"读取定价失败，使用默认: {e}")
        data = {}
    merged = dict(DEFAULT_PRICING)
    merged.update(data)
    # 保证 plan 子字段完整
    for k in ('plan_1',):
        if k in merged and isinstance(merged[k], dict):
            base = dict(DEFAULT_PRICING[k])
            base.update(merged[k])
            merged[k] = base
    # 远程配置源覆盖（域名动态下发；失败静默用本地值）
    # TTL 缓存：TTL 内直接复用上次结果，UI 线程点击不再每次都发 3s 超时的 HTTP
    if refresh_remote:
        import time as _time
        try:
            now_ts = _time.time()
            if now_ts - _REMOTE_CFG_CACHE["ts"] < _REMOTE_CFG_TTL and _REMOTE_CFG_CACHE["data"] is not None:
                remote = _REMOTE_CFG_CACHE["data"]
            else:
                remote = _fetch_remote_config()
                if remote is not None:
                    _REMOTE_CFG_CACHE["ts"] = now_ts
                    _REMOTE_CFG_CACHE["data"] = remote
            if remote:
                # 先记下本地（pricing.json/上次可用）地址，再让远程覆盖
                _local_channel_url = merged.get('channel_url')
                for k in ('channel_url', 'channel_name', 'trial_days',
                          'plan_1', 'plan_2', 'plan_3'):
                    if k in remote:
                        merged[k] = remote[k]
                # 渠道地址防污染：远程配置源滞后时（旧域名已被回收/404），
                # 不能让过期远程值覆盖掉本地可用的新地址。
                # 仅依据已缓存的校验结果判断（零网络，不阻塞 UI 线程）；
                # 无缓存时不拦截，由 warmup/点击时的 resolve_channel_url 兜底。
                try:
                    import time as _t2
                    remote_u = remote.get('channel_url')
                    if _local_channel_url and remote_u and _local_channel_url != remote_u:
                        lc = _URL_VERIFY_CACHE.get(_local_channel_url)
                        if lc and lc[1] and _t2.time() - lc[0] < _URL_VERIFY_TTL:
                            merged['channel_url'] = _local_channel_url  # 本地已验证可用，保住它
                except Exception:
                    pass
        except Exception:
            pass
    return merged


def save_pricing(pricing):
    """保存定价配置（后台 admin_manager 调用）"""
    try:
        with open(PRICING_FILE, 'w', encoding='utf-8') as f:
            json.dump(pricing, f, ensure_ascii=False, indent=2)
        return True, "定价已保存"
    except Exception as e:
        return False, f"保存失败: {e}"


# ------------------------- 权限判定 -------------------------
# 权益缓存：TTL 内直接返回上次查询结果（用户开通/过期后最长 2 分钟生效）
_ENT_CACHE = {}
_ENT_TTL = 120  # 秒


def get_entitlement(username):
    """
    返回用户权益状态字典。
    策略：限时全功能试用。试用期内全功能开放；过期且非 VIP 则锁定。
    联网判定权威；仅网络不可达时按「最近一次联网成功的签名状态」给离线宽限期。
    reason 取值：online / no_user / offline_grace / offline_expired / no_backend / error。
    """
    import time as _time
    global _ENT_CACHE
    # 用户级 TTL 缓存：录制/回放点击闸会高频调本函数，
    # 不缓存的话每次都在 UI 线程同步跑 Supabase HTTP（网络一慢就卡死界面）
    try:
        _c = _ENT_CACHE.get(username)
        if _c and _time.time() - _c["ts"] < _ENT_TTL:
            return dict(_c["ent"])
    except Exception:
        pass
    if not SUPABASE_OK:
        return _offline_grace(username, "no_backend")
    try:
        supabase_manager = get_supabase_manager()
        if not supabase_manager.is_connected():
            return _offline_grace(username, "offline")

        user = supabase_manager.get_user(username)
        if not user:
            # 联网但查无该用户：修正旧漏洞（原为放行=未注册也能白嫖）-> 锁定
            return _locked("no_user")

        now = datetime.now()
        # trial_days 只是个配置数字，用缓存即可，无需在这里触发远程拉取
        pricing = get_pricing(refresh_remote=False)
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
        result = {
            "is_vip": vip_valid,
            "vip_end": vip_end if vip_valid else None,
            "trial_end": trial_end.strftime('%Y-%m-%d') if trial_end else None,
            "trial_valid": trial_valid,
            "has_access": has_access,
            "reason": "online",
        }
        try:
            _ENT_CACHE[username] = {"ts": _time.time(), "ent": dict(result)}
        except Exception:
            pass
        # 联网验证成功 -> 落盘签名状态，作为后续离线宽限期依据
        try:
            cache = _ent_load()
            cache[username] = {"ent": result, "ts": _time.time()}
            _ent_save(cache)
        except Exception:
            pass
        return result
    except Exception as e:
        print(f"获取权益失败: {e}")
        # 联网过程抛异常（网络抖动/后端异常）：走离线宽限/锁定，而非无条件放行
        return _offline_grace(username, "error")


def _locked(reason):
    return {
        "is_vip": False, "vip_end": None, "trial_end": None,
        "trial_valid": False, "has_access": False, "reason": reason,
    }


def _offline_grace(username, reason):
    """网络不可达/查询异常时的回退：读签名缓存，宽限期内沿用上次联网状态，超期锁定。"""
    import time as _time
    current = _time.time()
    # 先看内存缓存是否在 TTL 内（瞬时抖动保护）
    try:
        _c = _ENT_CACHE.get(username)
        if _c and current - _c["ts"] < _ENT_TTL:
            out = dict(_c["ent"]); out.setdefault("reason", reason)
            return out
    except Exception:
        pass
    signed = _ent_read_signed(username)
    if signed:
        ent, ts = signed
        if current - ts <= OFFLINE_GRACE_DAYS * 86400:
            out = dict(ent); out.setdefault("reason", reason)
            try:
                _ENT_CACHE[username] = {"ts": current, "ent": dict(out)}
            except Exception:
                pass
            return out
        return _locked("offline_expired")
    return _locked(f"{reason}_expired" if reason == "offline_grace" else reason)


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

        # 激活后立刻清权益缓存，下次闸检查拉到最新 VIP 状态
        try:
            _ENT_CACHE.pop(username, None)
        except Exception:
            pass

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
