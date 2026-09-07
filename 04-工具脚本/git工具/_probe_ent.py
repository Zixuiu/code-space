import sys
sys.path.insert(0, r"D:\codespace\01-space\PC-action\PC-action-macOS")
try:
    from entitlement import get_entitlement
    u = "ink"
    ent = get_entitlement(u)
    keys = ("has_access", "is_vip", "is_trial", "plan", "expires_at", "trial_end", "reason", "offline", "local_valid")
    print("ENT =", {k: ent.get(k) for k in keys})
except Exception:
    import traceback
    traceback.print_exc()