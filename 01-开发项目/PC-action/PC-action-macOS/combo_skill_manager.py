# combo_skill_manager.py
import os
import json
from utils import get_app_base_dir

class ComboSkillManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.combo_skills = []
        self.load_combo_skills()
    
    def get_combo_skills_path(self):
        """获取组合技数据路径（与录制数据目录保持一致）"""
        base_dir = get_app_base_dir()
        app_data_dir = os.path.join(base_dir, 'data')
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