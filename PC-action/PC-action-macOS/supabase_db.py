"""
Supabase数据库管理模块
用于替代SQLite，实现多设备共享用户数据
"""
import os
import json
import time
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class SupabaseManager:
    def __init__(self):
        self.client = None
        self._connection_status = None
        self._last_check_time = 0
        self._check_interval = 30  # 缓存连接状态30秒
        self._retry_count = 0
        self._max_retries = 3
        self._retry_delay = 1  # 秒
        
        # 添加数据缓存
        self._user_cache = {}  # 用户数据缓存 {username: {data, timestamp}}
        self._cache_duration = 300  # 用户数据缓存5分钟
        self._total_user_count_cached = None  # 总用户数缓存
        self._total_count_cache_time = 0  # 总数缓存时间
    
    def connect(self):
        """连接到Supabase"""
        try:
            # 从环境变量或配置文件读取URL和密钥
            SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://your-project.supabase.co')
            SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'your-anon-key')
            
            # 创建Supabase客户端
            self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("Supabase连接已建立")
            self._connection_status = True
            self._last_check_time = time.time()
            self._retry_count = 0
            return True
        except Exception as e:
            self._connection_status = False
            self._last_check_time = time.time()
            return False
    
    def is_connected(self):
        """检查是否已连接，使用缓存减少频繁检查"""
        current_time = time.time()
        
        # 如果距离上次检查时间不足缓存间隔，返回缓存的状态
        if self._connection_status is not None and (current_time - self._last_check_time) < self._check_interval:
            return self._connection_status
            
        # 更新检查时间
        self._last_check_time = current_time
        
        # 如果客户端不存在，尝试连接
        if self.client is None:
            return self.connect()
            
        # 尝试执行简单查询验证连接
        try:
            # 使用轻量级查询代替获取用户数据
            response = self.client.table('users').select('id', count='exact').limit(1).execute()
            self._connection_status = True
            self._retry_count = 0
            return True
        except Exception as e:
            print(f"检查连接状态失败: {e}")
            self._connection_status = False
            
            # 如果连接失败且重试次数未达上限，尝试重新连接
            if self._retry_count < self._max_retries:
                self._retry_count += 1
                print(f"尝试重新连接 ({self._retry_count}/{self._max_retries})...")
                time.sleep(self._retry_delay)
                return self.connect()
                
            return False
    

    
    def _verify_connection(self):
        """验证连接是否有效 - 仅在必要时调用"""
        try:
            # 使用轻量级查询验证连接
            self.client.table('users').select('id').limit(1).execute()
            return True
        except:
            # 连接失效，尝试重新连接
            self.connect()
            return self.is_connected()
    
    def open(self):
        """打开数据库连接（兼容SQLite接口）"""
        return self.is_connected()
    
    def close(self):
        """关闭数据库连接（兼容SQLite接口）"""
        # Supabase客户端不需要显式关闭连接
        pass
    
    def create_tables(self):
        """创建所需的表结构"""
        if not self.is_connected():
            return False
        
        try:
            # 创建用户表
            # 注意：Supabase中表通常通过界面或SQL创建，这里只是示例
            # 实际使用时需要在Supabase控制台手动创建表
            
            # 用户表结构示例SQL:
            # CREATE TABLE users (
            #   id SERIAL PRIMARY KEY,
            #   username TEXT UNIQUE NOT NULL,
            #   email TEXT,
            #   password_hash TEXT NOT NULL,
            #   is_active INTEGER DEFAULT 1,
            #   is_admin INTEGER DEFAULT 0,
            #   replay_count INTEGER DEFAULT 0,
            #   created_at TEXT NOT NULL
            # );
            
            # 充值记录表结构示例SQL:
            # CREATE TABLE recharge_records (
            #   id SERIAL PRIMARY KEY,
            #   username TEXT NOT NULL,
            #   amount REAL NOT NULL,
            #   payment_method TEXT,
            #   created_at TEXT NOT NULL,
            #   FOREIGN KEY (username) REFERENCES users (username)
            # );
            
            return True
        except Exception as e:
            print(f"创建表失败: {e}")
            return False
    
    def get_user(self, username):
        """根据用户名获取用户信息 - 使用缓存优化"""
        if not self.is_connected():
            return None
        
        # 检查缓存
        current_time = time.time()
        if username in self._user_cache:
            cached_data = self._user_cache[username]
            # 如果缓存未过期，直接返回缓存数据
            if current_time - cached_data['timestamp'] < self._cache_duration:
                return cached_data['data']
        
        try:
            # 仅在必要时验证连接
            if self._connection_status is None:
                self._verify_connection()
                
            response = self.client.table('users').select('*').eq('username', username).execute()
            if response.data:
                user_data = response.data[0]
                # 更新缓存
                self._user_cache[username] = {
                    'data': user_data,
                    'timestamp': current_time
                }
                return user_data
            return None
        except Exception as e:
            print(f"获取用户失败: {e}")
            # 尝试重新连接
            self.connect()
            return None
    
    def create_user(self, username, email, password_hash, is_admin=False):
        """创建新用户 - 创建后清除总数缓存"""
        if not self.is_connected():
            return None
        
        try:
            user_data = {
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'is_active': 1,
                'is_admin': 1 if is_admin else 0,
                'is_vip': 0,
                'vip_end_date': None,
                'can_replay': 1,
                'replay_count': 0,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            response = self.client.table('users').insert(user_data).execute()
            if response.data:
                # 清除总数缓存，因为用户数量已改变
                self._total_user_count_cached = None
                self._total_count_cache_time = 0
                return response.data[0]
            return None
        except Exception as e:
            print(f"创建用户失败: {e}")
            return None
    
    def update_user(self, username, updates):
        """更新用户信息 - 更新后清除缓存"""
        if not self.is_connected():
            return False
        
        try:
            response = self.client.table('users').update(updates).eq('username', username).execute()
            success = len(response.data) > 0 if response.data else False
            
            # 如果更新成功，清除该用户的缓存
            if success and username in self._user_cache:
                del self._user_cache[username]
                
            return success
        except Exception as e:
            print(f"更新用户失败: {e}")
            return False
    
    def clear_cache(self, username=None):
        """清除缓存数据
        
        Args:
            username: 如果提供，只清除该用户的缓存；否则清除所有缓存
        """
        if username:
            if username in self._user_cache:
                del self._user_cache[username]
        else:
            self._user_cache.clear()
            self._total_user_count_cached = None
            self._total_count_cache_time = 0
    
    def delete_user(self, username):
        """删除用户 - 删除后清除缓存"""
        if not self.is_connected():
            return False
        
        try:
            response = self.client.table('users').delete().eq('username', username).execute()
            success = len(response.data) > 0 if response.data else False
            
            # 如果删除成功，清除该用户的缓存和总数缓存
            if success:
                if username in self._user_cache:
                    del self._user_cache[username]
                # 清除总数缓存，因为用户数量已改变
                self._total_user_count_cached = None
                self._total_count_cache_time = 0
                
            return success
        except Exception as e:
            print(f"删除用户失败: {e}")
            return False
    
    def get_all_users(self):
        """获取所有用户"""
        if not self.is_connected():
            return []
        
        try:
            response = self.client.table('users').select('*').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"获取所有用户失败: {e}")
            return []
    
    def get_users_paginated(self, page=1, page_size=50, order_by='created_at', ascending=False):
        """分页获取用户列表 - 优化版本，使用缓存减少网络请求次数
        
        Args:
            page: 页码，从1开始
            page_size: 每页记录数
            order_by: 排序字段
            ascending: 是否升序排列
            
        Returns:
            dict: 包含用户数据和分页信息的字典
        """
        if not self.is_connected():
            return {'data': [], 'count': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
        
        try:
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 先只获取分页数据，避免第一次查询总数的网络开销
            query = self.client.table('users').select('*')
            
            # 添加排序
            if ascending:
                query = query.order(order_by, asc=True)
            else:
                query = query.order(order_by, desc=True)
                
            # 添加分页 - 只获取一页数据
            query = query.range(offset, offset + page_size - 1)
            
            response = query.execute()
            users_data = response.data if response.data else []
            
            # 检查总数缓存是否有效（缓存5分钟）
            current_time = time.time()
            if (self._total_user_count_cached is not None and 
                current_time - self._total_count_cache_time < self._cache_duration):
                total_count = self._total_user_count_cached
            else:
                # 只在第一页或缓存过期时获取总数
                if page == 1 or self._total_user_count_cached is None:
                    try:
                        count_response = self.client.table('users').select('id', count='exact').execute()
                        total_count = count_response.count if count_response.count else len(users_data)
                        # 缓存总数，避免重复查询
                        self._total_user_count_cached = total_count
                        self._total_count_cache_time = current_time
                    except:
                        total_count = len(users_data)
                else:
                    # 使用缓存的总数或估算总数
                    total_count = self._total_user_count_cached
            
            # 计算总页数
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
    
    def add_recharge_record(self, username, amount, payment_method=None):
        """添加充值记录"""
        if not self.is_connected():
            return None
        
        try:
            record_data = {
                'username': username,
                'amount': amount,
                'payment_method': payment_method,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            response = self.client.table('recharge_records').insert(record_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"添加充值记录失败: {e}")
            return None
    
    def get_recharge_records(self, username=None):
        """获取充值记录"""
        if not self.is_connected():
            return []
        
        try:
            if username:
                response = self.client.table('recharge_records').select('*').eq('username', username).execute()
            else:
                response = self.client.table('recharge_records').select('*').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"获取充值记录失败: {e}")
            return []
    
    def verify_password(self, username, password):
        """验证用户密码"""
        user = self.get_user(username)
        if not user:
            return False
        
        # 这里应该使用与注册时相同的哈希算法
        import hashlib
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        return password_hash == user.get('password_hash', '')
    
    def authenticate_user(self, username, password_hash):
        """验证用户登录"""
        user = self.get_user(username)
        if not user:
            return False
        
        # 检查密码哈希是否匹配
        if password_hash == user.get('password_hash', ''):
            return user
        return False
    
    def create_login_record(self, login_data):
        """创建登录记录"""
        if not self.is_connected():
            return False
        
        try:
            response = self.client.table('login_records').insert(login_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"创建登录记录失败: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """根据ID获取用户信息"""
        if not self.is_connected():
            return None
        
        try:
            response = self.client.table('users').select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"根据ID获取用户失败: {e}")
            return None
    
    def update_user_by_id(self, user_id, updates):
        """根据ID更新用户信息"""
        if not self.is_connected():
            print("错误: Supabase未连接")
            return False
        
        try:
            print(f"尝试更新用户ID {user_id}，更新内容: {updates}")
            response = self.client.table('users').update(updates).eq('id', user_id).execute()
            print(f"更新响应: {response}")
            
            if response.data and len(response.data) > 0:
                print(f"成功更新用户 {user_id}")
                return True
            else:
                print(f"更新用户 {user_id} 失败: 未找到匹配的记录或更新未生效")
                return False
        except Exception as e:
            print(f"根据ID更新用户失败: {e}")
            return False
    
    def delete_user_by_id(self, user_id):
        """根据ID删除用户"""
        if not self.is_connected():
            return False
        
        try:
            response = self.client.table('users').delete().eq('id', user_id).execute()
            return len(response.data) > 0 if response.data else False
        except Exception as e:
            print(f"根据ID删除用户失败: {e}")
            return False
    
    def create_recharge_record(self, record_data):
        """创建充值记录（兼容性方法）"""
        if not self.is_connected():
            return None
        
        try:
            # 如果record_data包含user_id而不是username，需要转换
            if 'user_id' in record_data and 'username' not in record_data:
                user = self.get_user_by_id(record_data['user_id'])
                if user:
                    record_data['username'] = user['username']
            
            response = self.client.table('recharge_records').insert(record_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"创建充值记录失败: {e}")
            return None
    
    def create_feedback(self, feedback_data):
        """创建反馈记录"""
        if not self.is_connected():
            return None
        
        try:
            response = self.client.table('feedback').insert(feedback_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"创建反馈记录失败: {e}")
            return None
    
    def get_user_by_username(self, username):
        """根据用户名获取用户信息"""
        return self.get_user(username)

# 全局Supabase管理器实例 - 使用单例模式
_supabase_manager = None

def get_supabase_manager():
    """获取全局Supabase管理器实例 - 单例模式"""
    global _supabase_manager
    if _supabase_manager is None:
        _supabase_manager = SupabaseManager()
        print("创建新的Supabase管理器实例")
    else:
        print("使用已存在的Supabase管理器实例")
    return _supabase_manager

# 为了兼容性，延迟创建全局实例（只在真正需要时才创建）
# supabase_manager = get_supabase_manager()

# 添加缺少的方法
def get_user_by_username(username):
    """根据用户名获取用户信息（兼容性方法）"""
    return get_supabase_manager().get_user(username)

def get_user_licenses(user_id):
    """获取用户的许可证列表"""
    supabase_manager = get_supabase_manager()
    if not supabase_manager.is_connected():
        return []
    
    try:
        response = supabase_manager.client.table('licenses').select('*').eq('user_id', user_id).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"获取用户许可证失败: {e}")
        return []

def update_license(license_id, updates):
    """更新许可证信息"""
    supabase_manager = get_supabase_manager()
    if not supabase_manager.is_connected():
        return False
    
    try:
        response = supabase_manager.client.table('licenses').update(updates).eq('id', license_id).execute()
        return len(response.data) > 0 if response.data else False
    except Exception as e:
        print(f"更新许可证失败: {e}")
        return False

def create_license(license_data):
    """创建新许可证"""
    supabase_manager = get_supabase_manager()
    if not supabase_manager.is_connected():
        return None
    
    try:
        response = supabase_manager.client.table('licenses').insert(license_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"创建许可证失败: {e}")
        return None

def get_user_by_email(email):
    """根据邮箱获取用户信息"""
    supabase_manager = get_supabase_manager()
    if not supabase_manager.is_connected():
        return None
    
    try:
        response = supabase_manager.client.table('users').select('*').eq('email', email).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"根据邮箱获取用户失败: {e}")
        return None

def update_user_password(user_id, password_hash):
    """更新用户密码"""
    supabase_manager = get_supabase_manager()
    if not supabase_manager.is_connected():
        return False
    
    try:
        response = supabase_manager.client.table('users').update({'password_hash': password_hash}).eq('id', user_id).execute()
        return len(response.data) > 0 if response.data else False
    except Exception as e:
        print(f"更新用户密码失败: {e}")
        return False

def create_login_record(login_data):
    """创建登录记录"""
    supabase_manager = get_supabase_manager()
    if not supabase_manager.is_connected():
        return False
    
    try:
        response = supabase_manager.client.table('login_records').insert(login_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"创建登录记录失败: {e}")
        return None

def get_user_by_id(user_id):
    """根据ID获取用户信息"""
    supabase_manager = get_supabase_manager()
    if not supabase_manager.is_connected():
        return None
    
    try:
        response = supabase_manager.client.table('users').select('*').eq('id', user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"根据ID获取用户失败: {e}")
        return None