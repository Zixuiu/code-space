#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复预设和重置：兼容数字式布局"""

with open('hz.py', 'r', encoding='utf-8') as f:
    c = f.read()

# ─── 1) 修复 _apply ───
old_apply = """    def _apply(self, gains, bass):
        for i,v in enumerate(gains):
            if i<len(self._all_sls):
                self._all_sls[i].set(v)
                self._all_vls[i].config(text=f"{v:+.1f}")
                self.eq.sg(i,v)
        self._bv.set(bass); self._bvl.config(text=f"{bass}%"); self.eq.sb(bass)"""

new_apply = """    def _apply(self, gains, bass):
        for i,v in enumerate(gains):
            if i<len(self._all_sls):
                try: self._all_sls[i].set(v)
                except: pass
            if i<len(self._all_vls):
                self._all_vls[i].config(text=f"{v:+.1f}")
            if hasattr(self, '_dig_values') and i < len(self._dig_values):
                self._dig_values[i] = v
            self.eq.sg(i,v)
        self._bv.set(bass); self._bvl.config(text=f"{bass}%"); self.eq.sb(bass)"""

if old_apply in c:
    c = c.replace(old_apply, new_apply)
    print("✅ _apply: 兼容数字式布局")
else:
    print("⚠️ _apply 未匹配")

# ─── 2) 修复 _reset ───
old_reset = """    def _reset(self):
        self.eq.reset()
        for i,s in enumerate(self._all_sls):
            s.set(0)
            if i<len(self._all_vls): self._all_vls[i].config(text="0.0")
        self._bv.set(30); self._bvl.config(text="30%")
        self._sbl.config(text="已重置")"""

new_reset = """    def _reset(self):
        self.eq.reset()
        if hasattr(self, '_dig_values'):
            self._dig_values = [0.0] * 10
        for s in self._all_sls:
            try: s.set(0)
            except: pass
        for vl in self._all_vls:
            try: vl.config(text="0.0")
            except: pass
        self._bv.set(30); self._bvl.config(text="30%")
        self._sbl.config(text="已重置")"""

if old_reset in c:
    c = c.replace(old_reset, new_reset)
    print("✅ _reset: 兼容数字式布局")
else:
    print("⚠️ _reset 未匹配")

# ─── 3) 修复 _scb：没有滑块时也兼容 ───
old_scb = """    def _scb(self, i):
        v = self._all_sls[i].get()
        self._all_vls[i].config(text=f"{v:+.1f}")
        self.eq.sg(i, v)"""

new_scb = """    def _scb(self, i):
        if hasattr(self, '_dig_values') and i < len(self._dig_values):
            v = self._dig_values[i]
        else:
            v = self._all_sls[i].get()
        if i < len(self._all_vls):
            self._all_vls[i].config(text=f"{v:+.1f}")
        self.eq.sg(i, v)"""

if old_scb in c:
    c = c.replace(old_scb, new_scb)
    print("✅ _scb: 兼容数字式")
else:
    print("⚠️ _scb 未匹配")

with open('hz.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
print('✅ 完成！')
print('  • 点击预设方案 → 数字值跟着变了 ✓')
print('  • 点击重置 → 数字值归零 ✓')
print()
print('运行命令: python hz.py')