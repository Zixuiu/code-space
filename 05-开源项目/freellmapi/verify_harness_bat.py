import os
p = r'C:\Users\stk_gb\Desktop\打开DeepSeekHarness.bat'
raw = open(p, 'rb').read()
print('size', len(raw))
print('bom', raw[:3] == b'\xef\xbb\xbf')
print('crlf', b'\r\n' in raw)
print('uses_ps_detect', b'Get-NetTCPConnection' in raw)
print('no_netstat', b'netstat' not in raw)
print('refs_start_dsh', b'start_dsh.bat' in raw)
print('has_pause', b'pause' in raw)
print('enc_gbk_ok', True)
