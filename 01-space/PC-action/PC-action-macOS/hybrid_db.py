"""
混合数据库管理模块
仅支持Supabase云端数据库
"""
import os
import re
from datetime import datetime

# 与 supabase_db.py 共用同一套默认 anon key（打包发布态无 .env 时自动可用）。
# 这是 Supabase 公开 anon key，随客户端分发是标准做法；写库权限由表的 RLS 策略控制。
# 直接写在这里（不依赖运行时 import supabase_db），避免冻结包里 import 失败导致连不上。
SUPABASE_URL_DEFAULT = 'https://loifmrvoignxlifizogv.supabase.co'
SUPABASE_KEY_DEFAULT = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvaWZtcnZvaWdueGxpZml6b2d2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA5NTA3ODksImV4cCI6MjA3NjUyNjc4OX0.EtuSOO6pms-kkHiR4g1lLU8As-J0mWR0WIO8TiwselQ'

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("警告: Supabase模块未安装")

class HybridDatabaseManager:
    def __init__(self):
        """初始化混合数据库管理器"""
        self.supabase_url = None
        self.supabase_key = None
        self.supabase_client = None
        self.use_supabase = False
        # 连接延迟到首次使用时建立，不再在 __init__ 中连接
    
    def _try_connect_supabase(self):
        """尝试连接到Supabase"""
        if not SUPABASE_AVAILABLE:
            print("Supabase模块不可用")
            return False
            
        try:
            self.supabase_client = create_client(self.supabase_url, self.supabase_key)
            # 测试连接
            test_response = self.supabase_client.table('users').select('id').limit(1).execute()
            try:
                from utils import log_info
                log_info("成功连接到Supabase数据库")
            except Exception:
                print("成功连接到Supabase数据库")
            self.use_supabase = True
            return True
        except Exception as e:
            self.supabase_client = None
            self.use_supabase = False
            # 窗口化 exe 无 stdout，把连接失败原因写进 app.log 便于排查
            try:
                from utils import log_error
                log_error("Supabase 连接失败: %r" % (e,))
            except Exception:
                print("Supabase 连接失败:", e)
            return False
    
    def is_connected(self):
        """检查是否已连接（惰性连接，首次检查时尝试连接）"""
        return self._ensure_connected()
    
    def _ensure_connected(self):
        """确保已连接，未连接则尝试连接（惰性加载）"""
        if self.use_supabase and self.supabase_client is not None:
            return True
        if self.supabase_client is not None:
            return True
        # 首次使用：读取配置并尝试连接
        # 用 or 让环境变量覆盖默认值；即使环境只给了 URL 没给 KEY（很常见），
        # KEY 也会回退到内置 anon 默认，保证连接尝试一定会发起。
        if not self.supabase_url:
            self.supabase_url = os.getenv('SUPABASE_URL') or SUPABASE_URL_DEFAULT
        if not self.supabase_key:
            self.supabase_key = os.getenv('SUPABASE_KEY') or SUPABASE_KEY_DEFAULT
        if self.supabase_url and self.supabase_key:
            return self._try_connect_supabase()
        return False
    
    def get_users_paginated(self, page=1, page_size=50, order_by='created_at', ascending=False):
        """分页获取用户列表"""
        if not self._ensure_connected():
            return {'data': [], 'count': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
        
        try:
            # 使用Supabase获取数据
            offset = (page - 1) * page_size
            query = self.supabase_client.table('users').select('*')
            
            # 添加排序
            if ascending:
                query = query.order(order_by, asc=True)
            else:
                query = query.order(order_by, desc=True)
                
            # 添加分页
            query = query.range(offset, offset + page_size - 1)
            
            response = query.execute()
            users_data = response.data if response.data else []
            
            # 获取总数
            if page == 1 and not hasattr(self, '_total_user_count_cached'):
                try:
                    count_response = self.supabase_client.table('users').select('id', count='exact').execute()
                    total_count = count_response.count if count_response.count else len(users_data)
                    self._total_user_count_cached = total_count
                except:
                    total_count = len(users_data)
            else:
                total_count = getattr(self, '_total_user_count_cached', len(users_data) * page)
            
            total_pages = max(1, (total_count + page_size - 1) // page_size)
            
            return {
                'data': users_data,
                'count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            }
        except Exception as e:
            print(f"分页获取用户失败: {e}")
            return {'data': [], 'count': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
    
    def get_user_by_id(self, user_id):
        """根据ID获取用户信息"""
        if not self._ensure_connected():
            return None
        
        try:
            response = self.supabase_client.table('users').select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"根据ID获取用户失败: {e}")
            return None
    
    def update_user(self, user_id, updates):
        """更新用户信息"""
        if not self._ensure_connected():
            print("数据库未连接")
            return False
        
        try:
            print(f"尝试更新用户 {user_id}, 更新内容: {updates}")
            print("使用Supabase更新用户")
            
            # 先检查用户表结构，确保字段存在
            try:
                table_info_response = self.supabase_client.table('users').select('*').limit(1).execute()
                if table_info_response.data:
                    existing_fields = set(table_info_response.data[0].keys())
                    update_fields = set(updates.keys())
                    missing_fields = update_fields - existing_fields
                    if missing_fields:
                        print(f"警告: 以下字段在Supabase表中不存在: {missing_fields}")
                        # 尝试将is_active映射为active
                        if 'is_active' in missing_fields and 'active' in existing_fields:
                            print("尝试将is_active字段映射为active字段")
                            updates = {'active': updates['is_active']}
                        elif 'is_active' in missing_fields and 'status' in existing_fields:
                            print("尝试将is_active字段映射为status字段")
                            updates = {'status': 'active' if updates['is_active'] else 'inactive'}
                        else:
                            print(f"无法找到合适的字段映射，跳过更新: {missing_fields}")
                            return False
            except Exception as e:
                print(f"检查表结构失败: {e}")
            
            response = self.supabase_client.table('users').update(updates).eq('id', user_id).execute()
            print(f"Supabase响应: {response}")
            result = len(response.data) > 0 if response.data else False
            print(f"更新结果: {result}")
            return result
        except Exception as e:
            print(f"更新用户失败: {e}")
            return False
    
    def update_user_by_id(self, user_id, updates):
        """根据ID更新用户信息（别名方法）"""
        return self.update_user(user_id, updates)
    
    def delete_user(self, user_id):
        """删除用户"""
        if not self._ensure_connected():
            return False
        
        try:
            response = self.supabase_client.table('users').delete().eq('id', user_id).execute()
            return len(response.data) > 0 if response.data else False
        except Exception as e:
            print(f"删除用户失败: {e}")
            return False
    
    def create_user(self, username, email, password_hash, is_admin=False):
        """创建新用户"""
        if not self._ensure_connected():
            return None
        # 邮箱必填（无邮箱不允许创建成功，保证后端可按邮箱开通VIP）
        if not email or not str(email).strip():
            print("创建用户失败: 邮箱不能为空")
            return None
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', str(email).strip()):
            print("创建用户失败: 邮箱格式不正确")
            return None
        email = str(email).strip()

        try:
            # 进一步简化，只保留最基本的必填字段
            # 移除不存在的is_vip和vip_end_date字段
            user_data = {
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'is_active': 1,
                'is_admin': 1 if is_admin else 0,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            response = self.supabase_client.table('users').insert(user_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"创建用户失败: {e}")
            return None
    
    def get_user(self, username):
        """根据用户名获取用户信息"""
        if not self._ensure_connected():
            return None
        
        try:
            response = self.supabase_client.table('users').select('*').eq('username', username).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"根据用户名获取用户失败: {e}")
            return None
    
    def get_all_users(self):
        """获取所有用户"""
        if not self._ensure_connected():
            return []
        
        try:
            response = self.supabase_client.table('users').select('*').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"获取所有用户失败: {e}")
            return []
    
    def get_all_feedback(self):
        """获取所有反馈信息"""
        if not self._ensure_connected():
            return []
        
        try:
            response = self.supabase_client.table('feedback').select('*').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"获取所有反馈失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        # Supabase客户端不需要显式关闭连接
        pass

# 创建全局实例
hybrid_db_manager = HybridDatabaseManager()