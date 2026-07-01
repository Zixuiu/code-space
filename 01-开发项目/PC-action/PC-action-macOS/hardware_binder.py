"""
硬件绑定 + 离线激活码 + 试用期管理 + EULA 许可协议
==================================================
商业化核心模块
"""
import os
import json
import sys
import uuid
import hashlib
import hmac
import platform
from datetime import datetime, timedelta

# ─── 常量 ─────────────────────────────────────────
_ACTIVATION_SECRET = "PcAction2024Secret!"  # 服务端和客户端共用的密钥
_TRIAL_DAYS = 7                              # 试用天数
_USER_DATA_DIR = None                        # 延迟初始化


def _get_data_dir():
    global _USER_DATA_DIR
    if _USER_DATA_DIR is None:
        # 使用用户可写的标准配置目录，而非 exe 所在目录
        if sys.platform == "win32":
            base = os.environ.get("APPDATA", os.path.expanduser("~"))
        else:
            base = os.path.expanduser("~/.config")
        _USER_DATA_DIR = os.path.join(base, "PC-Action", "user_data")
        try:
            os.makedirs(_USER_DATA_DIR, exist_ok=True)
        except PermissionError:
            # 终极 fallback：使用 temp 目录
            import tempfile
            _USER_DATA_DIR = os.path.join(tempfile.gettempdir(), "PC-Action", "user_data")
            os.makedirs(_USER_DATA_DIR, exist_ok=True)
    return _USER_DATA_DIR


# ========================================================================
#  1. 硬件 ID 生成器
# ========================================================================
class HardwareBinder:
    """生成并管理设备唯一硬件指纹"""

    @staticmethod
    def get_hardware_id() -> str:
        """
        生成 32 位硬件指纹，组合多个硬件特征:
          Windows: 硬盘序列号 + CPU ID + MAC 地址
          macOS:   IO 注册表条目 + 机器序列号
        """
        parts = []

        try:
            if sys.platform == "win32":
                parts.extend(HardwareBinder._win_ids())
            elif sys.platform == "darwin":
                parts.extend(HardwareBinder._mac_ids())
            else:
                parts.append(platform.node())
                parts.append(str(uuid.getnode()))
        except Exception:
            parts.append(platform.node())
            parts.append(os.environ.get("COMPUTERNAME", "unknown"))

        raw = "|".join(filter(None, parts)) or str(uuid.uuid4())
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

    @staticmethod
    def _win_ids():
        """Windows 专用：获取硬盘、CPU、MAC"""
        out = []
        try:
            import wmi
            c = wmi.WMI()
            for disk in c.Win32_DiskDrive()[:1]:
                out.append(disk.SerialNumber or "")
            for cpu in c.Win32_Processor()[:1]:
                out.append(cpu.ProcessorId or "")
            for nic in c.Win32_NetworkAdapterConfiguration():
                if nic.MACAddress and nic.IPEnabled:
                    out.append(nic.MACAddress)
                    break
        except ImportError:
            # wmi 未安装 -> fallback
            out.append(platform.node())
            out.append(os.environ.get("COMPUTERNAME", ""))
        return out

    @staticmethod
    def _mac_ids():
        """macOS 专用"""
        out = []
        try:
            import subprocess
            # 机器序列号
            r = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True, text=True, timeout=5
            )
            for line in r.stdout.splitlines():
                if "IOPlatformSerialNumber" in line:
                    out.append(line.split('"')[1])
                    break
            # MAC 地址
            r2 = subprocess.run(
                ["ifconfig", "en0", "ether"],
                capture_output=True, text=True, timeout=5
            )
            if r2.stdout:
                out.append(r2.stdout.strip().split()[-1])
        except Exception:
            out.append(platform.node())
        return out

    # ─── 激活码生成（服务端使用） ────────────────────
    @staticmethod
    def generate_key(hardware_id: str = None, days: int = 365) -> str:
        """
        生成离线激活码（此方法通常只在你的管理后台调用）
        格式: YYYYMMDD-HMAC签名(16位)-硬件ID前8位
        """
        hid = hardware_id or HardwareBinder.get_hardware_id()
        expiry = (datetime.now() + timedelta(days=days)).strftime("%Y%m%d")
        msg = f"{hid}|{expiry}"
        sig = hmac.new(_ACTIVATION_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()[:16]
        return f"{expiry}-{sig}-{hid[:8]}"

    # ─── 激活码验证（客户端使用） ────────────────────
    @staticmethod
    def verify_key(activation_key: str) -> tuple:
        """
        验证激活码是否有效
        返回: (is_valid: bool, message: str)
        """
        try:
            parts = activation_key.strip().split("-")
            if len(parts) < 3:
                return False, "激活码格式错误"

            expiry_str, sig, hid_prefix = parts[0], parts[1], parts[2]
            current_hid = HardwareBinder.get_hardware_id()

            # 1. 硬件 ID 匹配
            if hid_prefix != current_hid[:8]:
                return False, "激活码与当前设备不匹配"

            # 2. 检查过期
            expiry_date = datetime.strptime(expiry_str, "%Y%m%d")
            if expiry_date < datetime.now():
                return False, f"激活码已于 {expiry_str} 过期"

            # 3. 验证 HMAC 签名
            expected_sig = hmac.new(
                _ACTIVATION_SECRET.encode(),
                f"{current_hid}|{expiry_str}".encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            if sig != expected_sig:
                return False, "激活码无效（签名不匹配）"

            return True, f"激活成功，有效期至 {expiry_str}"

        except (ValueError, IndexError):
            return False, "激活码格式错误"

    # ─── 持久化 ─────────────────────────────────────
    @staticmethod
    def save_activation(key: str):
        """保存激活信息到本地"""
        path = os.path.join(_get_data_dir(), "activation.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"key": key, "activated_at": datetime.now().isoformat()}, f)

    @staticmethod
    def load_activation() -> dict:
        """读取本地激活信息"""
        path = os.path.join(_get_data_dir(), "activation.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    @staticmethod
    def clear_activation():
        """清除激活信息（重置）"""
        path = os.path.join(_get_data_dir(), "activation.json")
        if os.path.exists(path):
            os.remove(path)

    @staticmethod
    def is_activated() -> bool:
        """快捷方法：检查是否已激活"""
        data = HardwareBinder.load_activation()
        if not data:
            return False
        ok, _ = HardwareBinder.verify_key(data.get("key", ""))
        return ok


# ========================================================================
#  2. 试用期管理器
# ========================================================================
class TrialManager:
    """管理首次使用的试用期"""

    @staticmethod
    def get_trial_file() -> dict:
        path = os.path.join(_get_data_dir(), "trial.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    @staticmethod
    def _save_trial(data: dict):
        path = os.path.join(_get_data_dir(), "trial.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    @staticmethod
    def start_trial() -> dict:
        """开始试用（记录首次使用时间）"""
        data = TrialManager.get_trial_file()
        if "first_use" not in data:
            data["first_use"] = datetime.now().isoformat()
            data["trial_days"] = _TRIAL_DAYS
            TrialManager._save_trial(data)
        return data

    @staticmethod
    def get_trial_info() -> dict:
        """
        获取试用信息
        返回: {
            "in_trial": bool,      # 是否在试用期内
            "days_used": int,      # 已用天数
            "days_remaining": int,  # 剩余天数
            "first_use": str,      # 首次使用日期
            "expired": bool        # 是否已过期
        }
        """
        data = TrialManager.get_trial_file()
        if "first_use" not in data:
            # 还没开始试用
            return {"in_trial": True, "days_used": 0, "days_remaining": _TRIAL_DAYS,
                    "first_use": None, "expired": False}

        first_use = datetime.fromisoformat(data["first_use"])
        days_used = (datetime.now() - first_use).days
        days_remaining = max(0, _TRIAL_DAYS - days_used)

        return {
            "in_trial": days_remaining > 0,
            "days_used": days_used,
            "days_remaining": days_remaining,
            "first_use": data["first_use"],
            "expired": days_remaining <= 0
        }

    @staticmethod
    def is_trial_valid() -> bool:
        """快捷方法：试用是否仍有效"""
        info = TrialManager.get_trial_info()
        # 如果已激活，试用期状态不重要
        if HardwareBinder.is_activated():
            return True
        return info["in_trial"]


# ========================================================================
#  3. EULA 许可协议
# ========================================================================
EULA_TEXT = """
PC-action 最终用户许可协议（EULA）

版本 1.0，生效日期：2025-01-01

重要提示：请仔细阅读本协议。安装、复制或以其他方式使用本
软件，即表示您同意受本协议条款的约束。

1. 许可授予
   本软件按"现状"授予您非独占的、不可转让的许可，仅限
   于您个人的商业或非商业用途。

2. 限制
   您不得：
   a) 对本软件进行反向工程、反编译、反汇编或试图获取
      其源代码（除非适用法律明确允许）；
   b) 将本软件分发给任何第三方；
   c) 绕过本软件的任何技术保护措施（包括但不限于激活
      码验证、硬件绑定）。

3. 知识产权
   本软件的所有权利、所有权和知识产权均归开发者所有。

4. 免责声明
   本软件按"现状"提供，不提供任何明示或默示的担保。
   在任何情况下，开发者均不对因使用或无法使用本软件而
   产生的任何损害承担责任。

5. 终止
   如果您违反本协议的任何条款，开发者有权立即终止本许可。
   终止后，您必须销毁本软件的所有副本。

6. 适用法律
   本协议受中华人民共和国法律管辖。

────────────────────────────────────
如您同意上述条款，请点击"同意"继续。
""".strip()


class EULAManager:
    """管理用户对 EULA 的接受状态"""

    @staticmethod
    def is_accepted() -> bool:
        path = os.path.join(_get_data_dir(), "eula_accepted.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("accepted", False)
        return False

    @staticmethod
    def accept():
        path = os.path.join(_get_data_dir(), "eula_accepted.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "accepted": True,
                "accepted_at": datetime.now().isoformat(),
                "version": "1.0"
            }, f)

    @staticmethod
    def reject():
        """拒绝 EULA 则记录但不影响再次提示"""
        path = os.path.join(_get_data_dir(), "eula_accepted.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"accepted": False}, f)


# ========================================================================
#  4. 一站式授权检查
# ========================================================================
def check_authorization() -> dict:
    """
    全面检查当前授权状态（给 UI 层使用）
    返回: {
        "ok": bool,              # 是否可以继续使用
        "activated": bool,       # 是否已激活
        "in_trial": bool,        # 是否在试用期
        "trial_info": dict,      # 试用详情
        "message": str,          # 给用户看的提示信息
    }
    """
    activated = HardwareBinder.is_activated()
    trial_info = TrialManager.get_trial_info()

    if activated:
        return {
            "ok": True,
            "activated": True,
            "in_trial": False,
            "trial_info": trial_info,
            "message": "已激活"
        }

    if trial_info["in_trial"]:
        return {
            "ok": True,
            "activated": False,
            "in_trial": True,
            "trial_info": trial_info,
            "message": f"试用期剩余 {trial_info['days_remaining']} 天"
        }

    # 试用已过期且未激活
    return {
        "ok": False,
        "activated": False,
        "in_trial": False,
        "trial_info": trial_info,
        "message": f"试用已过期（共 {trial_info['days_used']} 天），请购买激活码"
    }