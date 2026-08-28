import ctypes, os
files = [
    r'D:\codespace\05-开源项目\freellmapi\server\inspect_users.js',
    r'D:\codespace\05-开源项目\freellmapi\server\inspect_users.cjs',
    r'D:\codespace\05-开源项目\freellmapi\server\reset_password.cjs',
    r'D:\codespace\05-开源项目\freellmapi\server\verify.cjs',
]
k = ctypes.WinDLL('kernel32', use_last_error=True)
for f in files:
    if os.path.exists(f):
        r = k.DeleteFileW(ctypes.c_wchar_p(f))
        print(f.split('\\')[-1], '=> deleted' if r else ('=> FAIL ' + str(ctypes.get_last_error())))
    else:
        print(f.split('\\')[-1], '=> absent')
