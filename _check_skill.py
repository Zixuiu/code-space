"""检查 combo_skills.json 数据"""
import json
d = json.load(open('01-开发项目/PC-action/PC-action-macOS/data/combo_skills.json', encoding='utf-8'))
skills = d if isinstance(d, list) else [d]
s = [x for x in skills if x.get('name') == '看客户有无招聘']
if not s:
    print("❌ 找不到 '看客户有无招聘' 技能")
    print("现有技能:", [x.get('name') for x in skills])
else:
    s = s[0]
    print(f"step_interval: {s.get('step_interval', '__default__')}")
    print(f"flows 数量: {len(s.get('flows', []))}")
    for i, f in enumerate(s['flows']):
        print(f"  [{i}] cond={f['condition']}, action={f['action']}, delay={f.get('delay_after',0)}")
        if f.get('else_branch'):
            print(f"       else: cond={f['else_branch']['condition']}, action={f['else_branch']['action']}")
print("✅ 数据完整")