import os, shutil, stat
def on_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        if os.path.isfile(path): os.remove(path)
        else: os.rmdir(path)
    except:
        pass
shutil.rmtree(r'D:\code空间\PC-action\PC-action-macOS\code空间', onerror=on_error)
print('删除完成')
