import socket, time
log = r'D:\codespace\05-开源项目\freellmapi\dsh_web.log'
for i in range(180):
    s=socket.socket(); s.settimeout(0.5); up=False
    try:
        s.connect(('127.0.0.1',3080)); up=True
    except: pass
    finally:
        try: s.close()
        except: pass
    if up:
        print(f"[{i*3}s] 3080 UP", flush=True); break
    if i % 10 == 0:
        try:
            lines=open(log,encoding='utf-8',errors='replace').read().splitlines()
            tail=' | '.join(lines[-2:]) if lines else '(empty)'
        except Exception as e:
            tail='log err '+str(e)
        print(f"[{i*3}s] 3080 down | {tail[:140]}", flush=True)
    time.sleep(3)
else:
    print("TIMEOUT: 3080 never came up", flush=True)
