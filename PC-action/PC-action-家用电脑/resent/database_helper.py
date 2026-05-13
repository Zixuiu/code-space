"""
数据库助手模块
作为Supabase数据库操作的包装器，提供简化的接口
"""
from datetime import datetime
from supabase_db import get_supabase_manager

class DatabaseHelper:
    """数据库助手类，封装Supabase操作"""
    
    @classmethod
    def manage_vip_license(cls, username, months):
        """
        管理VIP许可证
        :param username: 用户名
        :param months: VIP月数
        :return: (success, message) 元组
        """
        try:
            supabase_manager = get_supabase_manager()
            # 获取用户信息
            user = supabase_manager.get_user(username)
            if not user:
                return False, "用户不存在"
            
            print(f"获取到用户: {username}, ID: {user['id']}, 类型: {type(user['id'])}")
            
            # 计算新的到期时间
            from datetime import datetime, timedelta
            import uuid
            current_date = datetime.now()
            
            # 检查是否已有VIP许可证
            try:
                licenses = supabase_manager.client.table('licenses').select('*').eq('user_id', user['id']).execute()
                print(f"查询到 {len(licenses.data) if licenses.data else 0} 个现有许可证")
            except Exception as e:
                print(f"查询现有许可证失败: {e}")
                licenses = None
            
            if licenses and licenses.data and len(licenses.data) > 0:
                # 更新现有许可证
                license_data = licenses.data[0]
                existing_expiry = datetime.strptime(license_data['expiry_date'], '%Y-%m-%d')
                
                # 如果现有许可证未过期，则延长时间；否则从当前时间开始计算
                if existing_expiry > current_date:
                    new_expiry = existing_expiry + timedelta(days=months * 30)
                else:
                    new_expiry = current_date + timedelta(days=months * 30)
                
                try:
                    supabase_manager.client.table('licenses').update({
                        'expiry_date': new_expiry.strftime('%Y-%m-%d')
                    }).eq('id', license_data['id']).execute()
                    return True, f"VIP已延长{months}个月"
                except Exception as e:
                    print(f"更新许可证失败: {e}")
                    return False, f"更新许可证失败: {str(e)}"
            else:
                # 创建新的VIP许可证
                new_expiry = current_date + timedelta(days=months * 30)
                license_data = {
                    'user_id': user['id'],
                    'license_key': f"VIP-{uuid.uuid4().hex[:8].upper()}",
                    'product_name': 'VIP会员',
                    'expiry_date': new_expiry.strftime('%Y-%m-%d'),
                    'created_at': current_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                print(f"尝试插入许可证: {license_data}")
                
                # 尝试多种方法插入许可证
                methods = [
                    ("标准插入", lambda: supabase_manager.client.table('licenses').insert(license_data).execute()),
                    ("不带created_at", lambda: supabase_manager.client.table('licenses').insert({
                        'user_id': user['id'],
                        'license_key': license_data['license_key'],
                        'product_name': 'VIP会员',
                        'expiry_date': license_data['expiry_date']
                    }).execute()),
                    ("仅必要字段", lambda: supabase_manager.client.table('licenses').insert({
                        'user_id': user['id'],
                        'license_key': license_data['license_key'],
                        'product_name': 'VIP会员',
                        'expiry_date': license_data['expiry_date'],
                        'created_at': '2025-11-22 13:48:30'
                    }).execute()),
                    ("使用字符串ID", lambda: supabase_manager.client.table('licenses').insert({
                        'user_id': str(user['id']),
                        'license_key': license_data['license_key'],
                        'product_name': 'VIP会员',
                        'expiry_date': license_data['expiry_date'],
                        'created_at': '2025-11-22 13:48:30'
                    }).execute()),
                ]
                
                for method_name, method_func in methods:
                    try:
                        print(f"尝试方法: {method_name}")
                        result = method_func()
                        print(f"{method_name}成功")
                        return True, f"已成功开通VIP，有效期{months}个月"
                    except Exception as e:
                        print(f"{method_name}失败: {e}")
                        continue
                
                # 如果所有方法都失败，返回错误
                return False, f"无法创建VIP许可证，所有方法都失败了"
        
        except Exception as e:
            print(f"管理VIP许可证失败: {e}")
            return False, f"操作失败: {str(e)}"
    
    @classmethod
    def add_recharge_record(cls, username, amount, months):
        """
        添加充值记录
        :param username: 用户名
        :param amount: 充值金额
        :param months: VIP月数
        """
        try:
            supabase_manager = get_supabase_manager()
            # 获取用户信息
            user = supabase_manager.get_user(username)
            if not user:
                print(f"用户不存在: {username}")
                return None
            
            # 创建充值记录
            record_data = {
                'username': username,
                'amount': amount,
                'months': months,
                'payment_method': '微信支付',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            response = supabase_manager.client.table('recharge_records').insert(record_data).execute()
            return response.data[0] if response.data else None
        
        except Exception as e:
            print(f"添加充值记录失败: {e}")
            return None
    
    def get_user_list(self):
        """获取用户列表"""
        try:
            supabase_manager = get_supabase_manager()
            users = supabase_manager.get_all_users()
            return users if users else []
        except Exception as e:
            print(f"获取用户列表失败: {e}")
            return []
    
    def get_all_users(self):
        """获取所有用户（别名方法）"""
        return self.get_user_list()
    
    def get_users_paginated(self, page=1, page_size=50, order_by='created_at', ascending=False):
        """分页获取用户列表
        
        Args:
            page: 页码，从1开始
            page_size: 每页记录数
            order_by: 排序字段
            ascending: 是否升序排列
            
        Returns:
            dict: 包含用户数据和分页信息的字典
        """
        try:
            supabase_manager = get_supabase_manager()
            return supabase_manager.get_users_paginated(page, page_size, order_by, ascending)
        except Exception as e:
            print(f"分页获取用户失败: {e}")
            return {'data': [], 'count': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
    
    def get_user_by_id(self, user_id):
        """根据ID获取用户信息"""
        try:
            supabase_manager = get_supabase_manager()
            return supabase_manager.get_user_by_id(user_id)
        except Exception as e:
            print(f"根据ID获取用户失败: {e}")
            return None
    
    def get_user_by_username(self, username):
        """根据用户名获取用户信息"""
        try:
            supabase_manager = get_supabase_manager()
            return supabase_manager.get_user(username)
        except Exception as e:
            print(f"根据用户名获取用户失败: {e}")
            return None
    
    def update_user(self, user_id, updates):
        """更新用户信息"""
        try:
            supabase_manager = get_supabase_manager()
            return supabase_manager.update_user_by_id(user_id, updates)
        except Exception as e:
            print(f"更新用户失败: {e}")
            return False
    
    def update_user_by_id(self, user_id, updates):
        """根据ID更新用户信息"""
        try:
            supabase_manager = get_supabase_manager()
            return supabase_manager.update_user_by_id(user_id, updates)
        except Exception as e:
            print(f"根据ID更新用户失败: {e}")
            return False
    
    def delete_user(self, user_id):
        """删除用户"""
        try:
            supabase_manager = get_supabase_manager()
            return supabase_manager.delete_user_by_id(user_id)
        except Exception as e:
            print(f"删除用户失败: {e}")
            return False
    
    def get_all_feedback(self):
        """获取所有反馈"""
        try:
            return self.get_feedback_list()
        except Exception as e:
            print(f"获取所有反馈失败: {e}")
            return []
    
    def update_feedback(self, feedback_id, updates):
        """更新反馈"""
        try:
            supabase_manager = get_supabase_manager()
            response = supabase_manager.client.table('feedback').update(updates).eq('id', feedback_id).execute()
            return len(response.data) > 0 if response.data else False
        except Exception as e:
            print(f"更新反馈失败: {e}")
            return False
    
    def delete_feedback(self, feedback_id):
        """删除反馈"""
        try:
            supabase_manager = get_supabase_manager()
            response = supabase_manager.client.table('feedback').delete().eq('id', feedback_id).execute()
            return len(response.data) > 0 if response.data else False
        except Exception as e:
            print(f"删除反馈失败: {e}")
            return False
    
    def get_feedback_list(self):
        """获取反馈列表"""
        try:
            supabase_manager = get_supabase_manager()
            response = supabase_manager.client.table('feedback').select('*').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"获取反馈列表失败: {e}")
            return []
    
    def create_user(self, username, email, password_hash, is_admin=False):
        """
        创建新用户
        :param username: 用户名
        :param email: 邮箱
        :param password_hash: 密码哈希
        :param is_admin: 是否为管理员
        :return: 用户对象或None
        """
        try:
            supabase_manager = get_supabase_manager()
            return supabase_manager.create_user(username, email, password_hash, is_admin)
        except Exception as e:
            print(f"创建用户失败: {e}")
            return None
    
    def submit_feedback(self, username, content, contact_info=""):
        """
        提交反馈
        :param username: 用户名
        :param content: 反馈内容
        :param contact_info: 联系方式
        :return: 反馈记录ID或None
        """
        try:
            supabase_manager = get_supabase_manager()
            feedback_data = {
                'username': username,
                'content': content,
                'contact_info': contact_info,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            response = supabase_manager.client.table('feedback').insert(feedback_data).execute()
            return response.data[0]['id'] if response.data else None
        except Exception as e:
            print(f"提交反馈失败: {e}")
            return None
    
    def try_supabase_then_local(self, supabase_func, local_func):
        """
        尝试先执行Supabase操作，失败则执行本地SQLite操作
        :param supabase_func: Supabase操作函数
        :param local_func: 本地SQLite操作函数
        :return: 操作是否成功
        """
        try:
            # 尝试执行Supabase操作
            supabase_func()
            return True
        except Exception as e:
            print(f"Supabase操作失败: {e}，尝试使用本地SQLite数据库")
            try:
                # 如果Supabase操作失败，尝试本地SQLite操作
                local_func()
                return True
            except Exception as e2:
                print(f"本地SQLite操作也失败: {e2}")
                return False
    
    def check_vip_status(self, username):
        """
        检查用户VIP状态
        :param username: 用户名
        :return: (is_vip, expiry_date) 元组
        """
        try:
            supabase_manager = get_supabase_manager()
            user = supabase_manager.get_user(username)
            if not user:
                return False, None
            
            # 检查VIP许可证
            licenses = supabase_manager.client.table('licenses').select('*').eq('user_id', user['id']).execute()
            
            if licenses.data and len(licenses.data) > 0:
                license_data = licenses.data[0]
                expiry_date = datetime.strptime(license_data['expiry_date'], '%Y-%m-%d')
                current_date = datetime.now()
                
                if expiry_date > current_date:
                    return True, license_data['expiry_date']
            
            return False, None
        except Exception as e:
            print(f"检查VIP状态失败: {e}")
            return False, None

# 创建全局实例
db_helper = DatabaseHelper()