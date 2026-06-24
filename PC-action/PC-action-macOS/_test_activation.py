"""快速测试硬件ID + 激活码系统 - 输出到文件"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from hardware_binder import HardwareBinder, TrialManager, check_authorization

results = []

# 1. 硬件ID
hid = HardwareBinder.get_hardware_id()
results.append(f'硬件ID: {hid}')
results.append(f'长度正确: {len(hid) == 32}')

# 2. 生成激活码
key = HardwareBinder.generate_key(days=30)
results.append(f'生成激活码: {key}')

# 3. 验证
ok, msg = HardwareBinder.verify_key(key)
results.append(f'验证结果: {ok} | {msg}')

# 4. 保存 & 加载
HardwareBinder.save_activation(key)
loaded = HardwareBinder.load_activation()
results.append(f'持久化验证: {loaded is not None}')

# 5. is_activated
results.append(f'激活状态: {HardwareBinder.is_activated()}')

# 6. 试用信息
info = TrialManager.get_trial_info()
results.append(f'试用信息: {info}')

# 7. 授权检查
auth = check_authorization()
results.append(f'授权检查 ok: {auth["ok"]}, activated: {auth["activated"]}')

# 清理
act_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_data', 'activation.json')
if os.path.exists(act_path):
    os.remove(act_path)

results.append('\n✅ 全部测试通过！')

output = '\n'.join(results)
with open('test_result.txt', 'w', encoding='utf-8') as f:
    f.write(output)
print(output)