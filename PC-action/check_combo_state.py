# -*- coding: utf-8 -*-
import os
import json

# Check combo_skills.json for any state fields
paths = [
    'PC-action-macOS/user_data/combo_skills.json',
    'PC-action-macOS/combo_skills.json',
]

for p in paths:
    if os.path.exists(p):
        print(f'\n=== {p} ===')
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            for i, skill in enumerate(data):
                print(f'\nSkill {i}: name={skill.get("name", "无")}')
                print(f'  Keys: {list(skill.keys())}')
                # Check for any state-related fields
                for k, v in skill.items():
                    if k in ['current_step', 'current_flow', 'step_index', 'flow_index', 'state', 'status', 'paused', 'last_step']:
                        print(f'  STATE FIELD: {k} = {v}')
    else:
        print(f'{p}: NOT FOUND')
