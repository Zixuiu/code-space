import json, os
with open(r'd:\code空间\PC-action\PC-action-家用电脑\resent\combo_skills.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
for s in data:
    name = s.get('name', '')
    flows = s.get('flows', [])
    print('=== %s ===' % name)
    for i, flow in enumerate(flows):
        fp = flow.get('folder_path', '') or flow.get('recording_path', '')
        print('  流程%d: action=%s, condition=%s, path=%s' % (i, flow.get('action',''), flow.get('condition',''), fp))
        if fp:
            if os.path.exists(fp):
                print('    -> OK')
            else:
                print('    -> 路径不存在!')