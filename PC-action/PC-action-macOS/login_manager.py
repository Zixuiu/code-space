import os
import json
import hashlib
import random
import string
import smtplib
import sys
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 尝试导入数据库管理器
try:
    from hybrid_db import hybrid_db_manager
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("警告: 混合数据库模块未找到，注册将只保存到本地文件")

class LoginManager:
    """简单的登录管理器，用于处理用户认证"""
    
    def __init__(self):
        self.current_user = None
        self.verification_codes = {}  # 存储验证码 {email: (code, expire_time)}
        
        # 获取数据目录 - 在打包环境中使用用户数据目录
        self.data_dir = self._get_data_directory()
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.credentials_file = os.path.join(self.data_dir, "login_credentials.json")
        self.saved_login_file = os.path.join(self.data_dir, "saved_login.json")
        
        # 加载环境变量，支持多种位置
        self._load_env()
        
        self._ensure_data_files()
        
        # 同步本地用户到Supabase数据库
        self._sync_local_users_to_db()
    
    def _get_data_directory(self):
        """
        获取数据存储目录
        在单文件exe模式下，从临时目录读取初始数据，但写入到用户目录
        """
        # 检查是否在打包环境中运行
        if getattr(sys, 'frozen', False):
            # 在PyInstaller单文件打包环境中
            # 数据写入到exe所在目录下的user_data文件夹
            app_dir = os.path.dirname(sys.executable)
            data_dir = os.path.join(app_dir, "user_data")
            
            # 获取PyInstaller解压的临时目录（包含嵌入的数据文件）
            # sys._MEIPASS 是PyInstaller解压资源文件的临时目录
            if hasattr(sys, '_MEIPASS'):
                self._meipass_dir = sys._MEIPASS
                self._embedded_user_data_dir = os.path.join(sys._MEIPASS, "user_data")
            else:
                self._meipass_dir = None
                self._embedded_user_data_dir = None
        else:
            # 在开发环境中，使用脚本所在目录
            data_dir = os.path.dirname(os.path.abspath(__file__))
            self._meipass_dir = None
            self._embedded_user_data_dir = None
        
        # 确保数据目录存在
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
            except Exception as e:
                print(f"创建数据目录失败: {e}")
        
        return data_dir
        
    def _load_env(self):
        """
        加载环境变量，支持多种位置
        解决PyInstaller打包后.env文件位置问题
        """
        # 定义可能的.env文件位置列表
        env_locations = []
        
        # 1. 当前工作目录
        env_locations.append('.env')
        
        # 2. 程序所在目录（适用于PyInstaller目录模式）
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
            env_locations.append(os.path.join(app_dir, '.env'))
            # 3. _internal目录（PyInstaller打包后的内部目录）
            internal_dir = os.path.join(app_dir, '_internal')
            env_locations.append(os.path.join(internal_dir, '.env'))
        else:
            # 开发环境：脚本所在目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            env_locations.append(os.path.join(script_dir, '.env'))
        
        # 4. user_data目录
        env_locations.append(os.path.join(self.data_dir, '.env'))
        
        # 5. 尝试从所有位置加载.env文件
        env_loaded = False
        for env_path in env_locations:
            if os.path.exists(env_path):
                print(f"从 {env_path} 加载环境变量")
                load_dotenv(dotenv_path=env_path, override=True)  # override=True确保后面的配置会覆盖前面的
                env_loaded = True
        
        # 调试信息
        sender_email = os.getenv('SENDER_EMAIL', '')
        print(f"SMTP配置加载结果: SENDER_EMAIL={'已配置' if sender_email else '未配置'}")
        if sender_email:
            # 隐藏密码中间部分，只显示首尾
            sender_password = os.getenv('SENDER_PASSWORD', '')
            if sender_password:
                masked_password = sender_password[0] + '*' * (len(sender_password) - 2) + sender_password[-1] if len(sender_password) > 2 else '***'
                print(f"SMTP_PASSWORD: {masked_password}")
        
        # 如果仍未加载到SMTP配置，尝试从.env.example复制一份到当前目录
        if not sender_email or not sender_password:
            print("未找到有效的SMTP配置")
            # 查找.env.example文件
            example_locations = []
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
                example_locations.append(os.path.join(app_dir, '.env.example'))
                example_locations.append(os.path.join(app_dir, '_internal', '.env.example'))
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                example_locations.append(os.path.join(script_dir, '.env.example'))
            
            for example_path in example_locations:
                if os.path.exists(example_path):
                    print(f"找到.env.example文件: {example_path}")
                    # 可以选择自动复制或提示用户配置
                    break
    
    def _sync_local_users_to_db(self):
        """
        同步本地JSON文件中的用户到Supabase数据库
        解决不同电脑注册的用户在管理界面看不到的问题
        """
        try:
            # 检查数据库是否可用
            if not DB_AVAILABLE or not hybrid_db_manager.is_connected():
                print("数据库不可用，跳过本地用户同步")
                return
            
            # 读取本地JSON文件中的所有用户
            local_users = self._load_users()
            if not local_users:
                print("本地用户列表为空，跳过同步")
                return
            
            print(f"开始同步本地用户到数据库，共 {len(local_users)} 个用户")
            
            # 获取数据库中的所有用户
            db_users = hybrid_db_manager.get_all_users()
            db_username_set = {user['username'] for user in db_users} if db_users else set()
            db_email_set = {user['email'] for user in db_users if user.get('email')} if db_users else set()
            
            # 逐个检查本地用户
            for username, user_data in local_users.items():
                if username not in db_username_set:
                    # 用户不在数据库中，需要添加
                    try:
                        # 提取必要的用户信息
                        email = user_data.get('email', '')
                        password_hash = user_data.get('password', '')
                        is_admin = user_data.get('is_admin', False)
                        
                        # 检查邮箱是否已被使用
                        if email and email in db_email_set:
                            # 邮箱已被使用，生成一个唯一的邮箱
                            # 使用用户名+随机数组合成唯一邮箱
                            unique_email = f"{username}_{random.randint(1000, 9999)}@example.com"
                            print(f"用户 {username} 的邮箱 {email} 已被使用，使用唯一邮箱: {unique_email}")
                            email = unique_email
                        
                        # 添加到数据库
                        result = hybrid_db_manager.create_user(username, email, password_hash, is_admin)
                        if result:
                            print(f"成功将用户 {username} 同步到数据库")
                            # 更新数据库中的用户名和邮箱集合，避免后续检查重复
                            db_username_set.add(username)
                            if email:
                                db_email_set.add(email)
                        else:
                            print(f"同步用户 {username} 到数据库失败")
                    except Exception as e:
                        print(f"同步用户 {username} 出错: {e}")
                else:
                    print(f"用户 {username} 已存在于数据库，跳过同步")
            
            # 2. 删除本地存在但数据库中不存在的用户（双向同步）
            print("开始清理本地存在但数据库中不存在的用户")
            users_to_remove = []
            for username in local_users:
                if username not in db_username_set:
                    users_to_remove.append(username)
            
            if users_to_remove:
                print(f"需要清理的本地用户: {users_to_remove}")
                # 从本地JSON文件中删除这些用户
                updated_users = {k: v for k, v in local_users.items() if k not in users_to_remove}
                if updated_users != local_users:
                    self._save_users(updated_users)
                    print(f"成功清理 {len(users_to_remove)} 个本地用户")
            
            print("本地用户同步完成")
        except Exception as e:
            print(f"本地用户同步过程中发生错误: {e}")
        
    def _ensure_data_files(self):
        """确保数据文件存在，如果是第一次运行则从嵌入的数据文件复制"""
        # 检查是否需要从嵌入的数据文件初始化
        if not os.path.exists(self.users_file) or os.path.getsize(self.users_file) < 10:
            # 尝试从嵌入的数据文件复制
            if self._embedded_user_data_dir and os.path.exists(self._embedded_user_data_dir):
                embedded_users_file = os.path.join(self._embedded_user_data_dir, "users.json")
                if os.path.exists(embedded_users_file):
                    try:
                        with open(embedded_users_file, 'r', encoding='utf-8') as src:
                            data = src.read()
                        with open(self.users_file, 'w', encoding='utf-8') as dst:
                            dst.write(data)
                        print(f"已从嵌入文件初始化 users.json")
                    except Exception as e:
                        print(f"复制 users.json 失败: {e}")
            
            # 如果仍然没有数据，创建空文件
            if not os.path.exists(self.users_file):
                with open(self.users_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
        
        # 同样的处理 credentials_file
        if not os.path.exists(self.credentials_file) or os.path.getsize(self.credentials_file) < 10:
            if self._embedded_user_data_dir and os.path.exists(self._embedded_user_data_dir):
                embedded_creds_file = os.path.join(self._embedded_user_data_dir, "login_credentials.json")
                if os.path.exists(embedded_creds_file):
                    try:
                        with open(embedded_creds_file, 'r', encoding='utf-8') as src:
                            data = src.read()
                        with open(self.credentials_file, 'w', encoding='utf-8') as dst:
                            dst.write(data)
                        print(f"已从嵌入文件初始化 login_credentials.json")
                    except Exception as e:
                        print(f"复制 login_credentials.json 失败: {e}")
            
            if not os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
        
        # 处理 saved_login_file
        if not os.path.exists(self.saved_login_file) or os.path.getsize(self.saved_login_file) < 10:
            if self._embedded_user_data_dir and os.path.exists(self._embedded_user_data_dir):
                embedded_saved_file = os.path.join(self._embedded_user_data_dir, "saved_login.json")
                if os.path.exists(embedded_saved_file):
                    try:
                        with open(embedded_saved_file, 'r', encoding='utf-8') as src:
                            data = src.read()
                        with open(self.saved_login_file, 'w', encoding='utf-8') as dst:
                            dst.write(data)
                        print(f"已从嵌入文件初始化 saved_login.json")
                    except Exception as e:
                        print(f"复制 saved_login.json 失败: {e}")
            
            if not os.path.exists(self.saved_login_file):
                with open(self.saved_login_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
    
    def _load_users(self):
        """加载用户数据"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_users(self, users):
        """保存用户数据"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    
    def _hash_password(self, password):
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def login(self, username, password):
        """用户登录"""
        users = self._load_users()
        
        if username in users and users[username]['password'] == self._hash_password(password):
            self.current_user = username
            return True, username
        else:
            return False, "用户名或密码错误"
    
    def register(self, username, password, email, verification_code=None):
        """用户注册"""
        # 如果提供了验证码，则进行验证
        if verification_code is not None:
            success, message = self.verify_code(email, verification_code)
            if not success:
                return False, message
        
        users = self._load_users()
        
        if username in users:
            return False, "用户名已存在"
            
        # 密码哈希
        password_hash = self._hash_password(password)
        
        # 添加新用户到JSON文件
        users[username] = {
            'password': password_hash,
            'email': email,
            'created_at': datetime.now().isoformat()
        }
        
        self._save_users(users)
        
        # 同时保存到数据库
        if DB_AVAILABLE and hybrid_db_manager.is_connected():
            try:
                hybrid_db_manager.create_user(username, email, password_hash)
                print(f"用户 {username} 已保存到数据库")
            except Exception as e:
                print(f"保存用户到数据库失败: {e}")
        
        return True, "注册成功"
    
    def send_verification_code(self, email):
        """发送验证码"""
        # 生成6位随机验证码
        code = ''.join(random.choices(string.digits, k=6))
        expire_time = datetime.now() + timedelta(minutes=10)
        
        # 存储验证码
        self.verification_codes[email] = (code, expire_time)
        
        # 尝试发送邮件
        try:
            # 从环境变量获取邮件服务器配置
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.qq.com')  # 默认使用QQ邮箱
            smtp_port = int(os.getenv('SMTP_PORT', '587'))  # 默认587端口
            sender_email = os.getenv('SENDER_EMAIL', '')
            sender_password = os.getenv('SENDER_PASSWORD', '')
            
            # 调试信息
            print(f"SMTP配置: 服务器={smtp_server}, 端口={smtp_port}, 发件人={sender_email}")
            
            # 如果没有配置邮件服务器信息，则回退到UI显示
            if not sender_email or not sender_password:
                print("===== 验证码信息 =====")
                print(f"邮箱: {email}")
                print(f"验证码: {code}")
                print(f"过期时间: {expire_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print("=======================")
                return True, f"验证码已生成", code
            
            # 创建邮件内容
            body = f"""您好！

您的验证码是：{code}

验证码有效期为10分钟，请及时使用。

如果这不是您本人的操作，请忽略此邮件。

---
此邮件由 PC-action 系统自动发送，请勿回复。"""
            
            message = MIMEText(body, 'plain', 'utf-8')
            message['From'] = sender_email
            message['To'] = email
            message['Subject'] = 'PC-action 验证码'
            
            # 发送邮件
            if smtp_port == 465:
                # 使用SSL连接
                print("使用SSL连接发送邮件...")
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
                try:
                    print(f"已连接到 {smtp_server}:{smtp_port}")
                    server.login(sender_email, sender_password)
                    print("登录成功，正在发送邮件...")
                    server.sendmail(sender_email, [email], message.as_string())
                    print("邮件发送成功!")
                    return True, f"验证码已发送至 {email}", None
                except Exception as e:
                    print(f"发送邮件时出错: {e}")
                    raise
                finally:
                    try:
                        server.quit()
                    except:
                        pass
            else:
                # 使用STARTTLS连接
                print("使用STARTTLS连接发送邮件...")
                server = smtplib.SMTP(smtp_server, smtp_port)
                try:
                    server.starttls()  # 启用安全传输
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, [email], message.as_string())
                    return True, f"验证码已发送至 {email}", None
                except Exception as e:
                    print(f"发送邮件时出错: {e}")
                    raise
                finally:
                    try:
                        server.quit()
                    except:
                        pass
            
            return True, f"验证码已发送至 {email}", None
            
        except Exception as e:
            # 邮件发送失败，回退到UI显示
            print(f"邮件发送失败: {str(e)}")
            print("===== 验证码信息 =====")
            print(f"邮箱: {email}")
            print(f"验证码: {code}")
            print(f"过期时间: {expire_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=======================")
            return True, f"验证码已生成 (邮件发送失败)", code
    
    def verify_code(self, email, code):
        """验证验证码"""
        if email not in self.verification_codes:
            return False, "验证码不存在或已过期"
            
        stored_code, expire_time = self.verification_codes[email]
        
        if datetime.now() > expire_time:
            del self.verification_codes[email]
            return False, "验证码已过期"
            
        if stored_code != code:
            return False, "验证码错误"
            
        # 验证成功，删除验证码
        del self.verification_codes[email]
        return True, "验证成功"
    
    def get_latest_verification_code(self, email):
        """获取最新的验证码（用于自动填充）"""
        if email in self.verification_codes:
            code, expire_time = self.verification_codes[email]
            if datetime.now() <= expire_time:
                return code
        return None
    
    def reset_password(self, email, new_password, verification_code):
        """重置密码"""
        # 验证验证码
        success, message = self.verify_code(email, verification_code)
        if not success:
            return False, message
            
        # 查找使用该邮箱的用户
        users = self._load_users()
        username = None
        
        for user, data in users.items():
            if data.get('email') == email:
                username = user
                break
                
        if not username:
            return False, "未找到使用该邮箱的用户"
            
        # 更新密码
        users[username]['password'] = self._hash_password(new_password)
        self._save_users(users)
        
        return True, "密码重置成功"
    
    def save_login_credentials(self, username, password):
        """保存登录凭据（用于记住我功能）"""
        credentials = self._load_credentials()
        credentials[username] = {
            'password': password,  # 注意：实际应用中不应明文存储
            'saved_at': datetime.now().isoformat()
        }
        
        with open(self.credentials_file, 'w', encoding='utf-8') as f:
            json.dump(credentials, f, ensure_ascii=False, indent=2)
            
        # 同时保存到saved_login.json，用于自动填充
        saved_login = {
            'username': username,
            'password': password,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(self.saved_login_file, 'w', encoding='utf-8') as f:
            json.dump(saved_login, f, ensure_ascii=False, indent=2)
    
    def _load_credentials(self):
        """加载登录凭据"""
        try:
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def get_saved_credentials(self, username):
        """获取保存的登录凭据"""
        credentials = self._load_credentials()
        if username in credentials:
            return credentials[username].get('password')
        return None
    
    def logout(self):
        """用户登出"""
        self.current_user = None
    
    def is_admin(self, username=None):
        """检查用户是否为管理员"""
        if username is None:
            username = self.current_user
        
        if not username:
            return False
            
        # 加载用户数据
        users = self._load_users()
        
        # 检查用户是否存在且为管理员
        if username in users:
            return users[username].get('is_admin', False)
        
        return False
    
    def load_saved_login(self):
        """加载保存的登录信息"""
        try:
            if os.path.exists(self.saved_login_file):
                with open(self.saved_login_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('username', ''), data.get('password', '')
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # 如果没有保存的登录信息，返回空字符串
        return '', ''