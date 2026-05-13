"""
混合数据库管理模块
仅支持Supabase云端数据库
"""
import os
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("警告: Supabase模块未安装")

class HybridDatabaseManager:
    def __init__(self):
        """初始化混合数据库管理器"""
        self.supabase_url = os.getenv('SUPABASE_URL', 'YOUR_SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY', 'YOUR_SUPABASE_ANON_KEY')
        self.supabase_client = None
        self.use_supabase = False
        
        # 尝试连接Supabase
        self._try_connect_supabase()
    
    def _try_connect_supabase(self):
        """尝试连接到Supabase"""
        if not SUPABASE_AVAILABLE:
            print("Supabase模块不可用")
            return False
            
        try:
            print(f"尝试连接到Supabase: {self.supabase_url}")
            self.supabase_client = create_client(self.supabase_url, self.supabase_key)
            # 测试连接
            test_response = self.supabase_client.table('users').select('id').limit(1).execute()
            print("成功连接到Supabase数据库")
            self.use_supabase = True
            return True
        except Exception as e:
            print(f"连接Supabase失败: {e}")
            print(f"请检查网络连接和Supabase配置: URL={self.supabase_url}")
            self.supabase_client = None
            self.use_supabase = False
            return False
    
    def is_connected(self):
        """检查是否已连接"""
        return self.supabase_client is not None
    
    def get_users_paginated(self, page=1, page_size=50, order_by='created_at', ascending=False):
        """分页获取用户列表"""
        if not self.is_connected():
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
        if not self.is_connected():
            return None
        
        try:
            response = self.supabase_client.table('users').select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"根据ID获取用户失败: {e}")
            return None
    
    def update_user(self, user_id, updates):
        """更新用户信息"""
        if not self.is_connected():
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
        if not self.is_connected():
            return False
        
        try:
            response = self.supabase_client.table('users').delete().eq('id', user_id).execute()
            return len(response.data) > 0 if response.data else False
        except Exception as e:
            print(f"删除用户失败: {e}")
            return False
    
    def create_user(self, username, email, password_hash, is_admin=False):
        """创建新用户"""
        if not self.is_connected():
            return None
        
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
        if not self.is_connected():
            return None
        
        try:
            response = self.supabase_client.table('users').select('*').eq('username', username).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"根据用户名获取用户失败: {e}")
            return None
    
    def get_all_users(self):
        """获取所有用户"""
        if not self.is_connected():
            return []
        
        try:
            response = self.supabase_client.table('users').select('*').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"获取所有用户失败: {e}")
            return []
    
    def get_all_feedback(self):
        """获取所有反馈信息"""
        if not self.is_connected():
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