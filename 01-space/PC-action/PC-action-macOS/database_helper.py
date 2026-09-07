"""
数据库助手模块
作为Supabase数据库操作的包装器，提供简化的接口
"""
import uuid
from datetime import datetime
from supabase_db import get_supabase_manager

class DatabaseHelper:
    """数据库助手类，封装Supabase操作"""

    @classmethod
    def manage_vip_license(cls, username, months):
        """
        管理 VIP 许可证（开通/续费）。
        双写策略：licenses 表记录交易（审计真源），
        users.is_vip / vip_end_date 作为判定口径（entitlement.get_entitlement 读取）。
        :param username: 用户名
        :param months: VIP月数
        :return: (success, message) 元组
        """
        try:
            supabase_manager = get_supabase_manager()
            user = supabase_manager.get_user(username)
            if not user:
                return False, "用户不存在"

            from datetime import timedelta
            current_date = datetime.now()
            new_expiry = current_date + timedelta(days=int(months) * 30)

            # 1) 写 licenses 表：已有未过期 license 则叠加时长，否则新建
            try:
                r = supabase_manager.client.table('licenses').select('*').eq('user_id', user['id']).execute()
                if r.data:
                    existing = r.data[0]
                    try:
                        existing_expiry = datetime.strptime(str(existing.get('expiry_date'))[:10], '%Y-%m-%d')
                        if existing_expiry > current_date:
                            new_expiry = existing_expiry + timedelta(days=int(months) * 30)
                    except Exception:
                        pass  # 旧到期日解析失败则按当前时间起算
                    supabase_manager.client.table('licenses').update({
                        'expiry_date': new_expiry.strftime('%Y-%m-%d'),
                    }).eq('id', existing['id']).execute()
                else:
                    supabase_manager.client.table('licenses').insert({
                        'user_id': user['id'],
                        'license_key': f"VIP-{uuid.uuid4().hex[:8].upper()}",
                        'product_name': 'VIP会员',
                        'expiry_date': new_expiry.strftime('%Y-%m-%d'),
                        'created_at': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                    }).execute()
            except Exception as e:
                return False, f"写入许可证失败: {e}"

            # 2) 同步 users 表（entitlement 判定口径），失败视为整体失败，保证两表一致
            try:
                supabase_manager.client.table('users').update({
                    'is_vip': 1,
                    'vip_end_date': new_expiry.strftime('%Y-%m-%d'),
                }).eq('id', user['id']).execute()
            except Exception as e:
                return False, f"会员状态同步失败: {e}"

            # 3) 失效该用户的进程内缓存，避免 entitlement 读到写库前的旧数据（缓存5分钟）
            try:
                supabase_manager._user_cache.pop(username, None)
            except Exception:
                pass

            return True, f"会员已开通至 {new_expiry.strftime('%Y-%m-%d')}"
        except Exception as e:
            print(f"管理VIP许可证失败: {e}")
            return False, f"操作失败: {str(e)}"
    
    @classmethod
    def add_recharge_record(cls, username, amount, months, payment_method='微信支付', status='pending'):
        """
        添加充值记录
        :param username: 用户名
        :param amount: 充值金额
        :param months: VIP月数
        :param payment_method: 支付 / 备注说明
        :param status: 审核状态，默认 pending（待审核）
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
                'payment_method': payment_method,
                'status': status,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            response = supabase_manager.client.table('recharge_records').insert(record_data).execute()
            return response.data[0] if response.data else None
        
        except Exception as e:
            print(f"添加充值记录失败: {e}")
            return None
    
    @classmethod
    def get_recharge_records(cls, username=None, status=None):
        """获取充值记录（可按用户名 / 状态过滤）"""
        try:
            supabase_manager = get_supabase_manager()
            return supabase_manager.get_recharge_records(username, status)
        except Exception as e:
            print(f"获取充值记录失败: {e}")
            return []
    
    @classmethod
    def update_recharge_status(cls, record_id, status):
        """更新充值记录审核状态：pending / approved / rejected"""
        try:
            supabase_manager = get_supabase_manager()
            return supabase_manager.update_recharge_status(record_id, status)
        except Exception as e:
            print(f"更新充值记录状态失败: {e}")
            return False
    
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