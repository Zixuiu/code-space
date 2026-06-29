# combo_skill_manager.py
import os
import json

class ComboSkillManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.combo_skills = []
        self.load_combo_skills()
    
    def get_combo_skills_path(self):
        app_data_dir = os.path.join(os.path.expanduser('~'), 'PC-action', 'data')
        os.makedirs(app_data_dir, exist_ok=True)
        return os.path.join(app_data_dir, 'combo_skills.json')
    
    def load_combo_skills(self):
        try:
            path = self.get_combo_skills_path()
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self.combo_skills = json.load(f)
            else:
                self.combo_skills = []
        except:
            self.combo_skills = []
    
    def save_combo_skills(self):
        try:
            path = self.get_combo_skills_path()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.combo_skills, f, ensure_ascii=False, indent=2)
        except:
            pass
