"""移除多余的调试日志"""
import sys

filepath = sys.argv[1]
basename = filepath.lower()

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

changed = False

if 'app_macos' in basename:
    old = '''        print("[MACOS DEBUG] macOS initUI called, stylesheet cleared", flush=True)\n        body_layout'''
    new = '''        body_layout'''
    if old in content:
        content = content.replace(old, new, 1)
        changed = True
        print("✅ 已移除 [MACOS DEBUG] macOS initUI called")

elif 'hybrid_db' in basename:
    old1 = '''            print(f"尝试连接到Supabase: {self.supabase_url}")
            self.supabase_client = create_client(self.supabase_url, self.supabase_key)'''
    new1 = '''            self.supabase_client = create_client(self.supabase_url, self.supabase_key)'''
    if old1 in content:
        content = content.replace(old1, new1, 1)
        changed = True
        print("✅ 已移除 '尝试连接到Supabase' 日志")

    old2 = '''        except Exception as e:
            print(f"连接Supabase失败: {e}")
            print(f"请检查网络连接和Supabase配置: URL={self.supabase_url}")
            self.supabase_client = None'''
    new2 = '''        except Exception as e:
            self.supabase_client = None'''
    if old2 in content:
        content = content.replace(old2, new2, 1)
        changed = True
        print("✅ 已移除 '连接Supabase失败' 日志")

elif 'login_manager' in basename:
    old1 = '''        sender_email = os.getenv('SENDER_EMAIL', '')
        print(f"SMTP配置加载结果: SENDER_EMAIL={'已配置' if sender_email else '未配置'}")
        if sender_email:'''
    new1 = '''        sender_email = os.getenv('SENDER_EMAIL', '')
        if sender_email:'''
    if old1 in content:
        content = content.replace(old1, new1, 1)
        changed = True
        print("✅ 已移除 'SMTP配置加载结果' 日志")

    old2 = '''        # 如果仍未加载到SMTP配置，尝试从.env.example复制一份到当前目录
        if not sender_email or not sender_password:
            print("未找到有效的SMTP配置")'''
    new2 = '''        # 如果仍未加载到SMTP配置，尝试从.env.example复制一份到当前目录
        if not sender_email or not sender_password:'''
    if old2 in content:
        content = content.replace(old2, new2, 1)
        changed = True
        print("✅ 已移除 '未找到有效的SMTP配置' 日志")

    old3 = '''            if not DB_AVAILABLE or not hybrid_db_manager.is_connected():
                print("数据库不可用，跳过本地用户同步")
                return'''
    new3 = '''            if not DB_AVAILABLE or not hybrid_db_manager.is_connected():
                return'''
    if old3 in content:
        content = content.replace(old3, new3, 1)
        changed = True
        print("✅ 已移除 '数据库不可用' 日志")

elif 'supabase_db' in basename:
    old = '''        except Exception as e:
            print(f"连接Supabase失败: {e}")
            self._connection_status = False'''
    new = '''        except Exception as e:
            self._connection_status = False'''
    if old in content:
        content = content.replace(old, new, 1)
        changed = True
        print("✅ 已移除 supabase_db 连接失败日志")

elif 'app.py' in basename and 'macos' in basename:
    old1 = '''            self.debug_print("成功注册F12键作为停止回放的快捷键")
        except Exception as e:'''
    new1 = '''        except Exception as e:'''
    if old1 in content:
        content = content.replace(old1, new1, 1)
        changed = True
        print("✅ 已移除 '注册F12' 日志")

    # 移除快捷键注册日志（但仍保留失败日志）
    old2 = '''                    hotkey_id = keyboard.add_hotkey(shortcut_str, make_handler())
                    self.shortcut_objects.append(hotkey_id)
                    self.debug_print(f"[快捷键] 成功注册快捷键: {shortcut_str} -> {folder_paths}")
                except Exception as e:'''
    new2 = '''                    hotkey_id = keyboard.add_hotkey(shortcut_str, make_handler())
                    self.shortcut_objects.append(hotkey_id)
                except Exception as e:'''
    if old2 in content:
        content = content.replace(old2, new2, 1)
        changed = True
        print("✅ 已移除 '成功注册快捷键' 日志")

else:
    print("⚠️  未知文件类型，跳过")

if changed:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n🎉 已保存修改到 {filepath}")
else:
    print("⚠️  未匹配到任何日志，文件未修改")