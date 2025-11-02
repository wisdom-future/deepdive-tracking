# 安全规范

**版本：** 1.0
**强制级别：** 🔴 MUST
**更新日期：** 2025-11-02

---

## 核心原则

```
✅ 安全第一，性能其次
✅ 最小权限原则
✅ 深度防御
✅ 定期审计和更新
✅ 透明的安全流程
```

---

## 密钥和凭证管理

### 🔴 MUST - 严格遵守

1. **绝不在代码中硬编码密钥**
   ```python
   ❌ API_KEY = 'sk-1234567890'
   ❌ DATABASE_PASSWORD = 'admin123'
   ❌ SECRET_KEY = 'my-secret-key'

   ✅ API_KEY = getenv('OPENAI_API_KEY')
   ✅ DATABASE_PASSWORD = getenv('DATABASE_PASSWORD')
   ✅ SECRET_KEY = getenv('SECRET_KEY')
   ```

2. **使用环境变量存储敏感信息**
   ```python
   import os

   # ✅ 从环境变量读取
   openai_api_key = os.getenv('OPENAI_API_KEY')
   database_url = os.getenv('DATABASE_URL')
   jwt_secret = os.getenv('JWT_SECRET_KEY')

   # ✅ 提供默认值仅用于开发环境
   debug = os.getenv('DEBUG', 'false').lower() == 'true'
   log_level = os.getenv('LOG_LEVEL', 'INFO')

   # ❌ 为敏感信息提供默认值
   api_key = os.getenv('API_KEY', 'default-key')  (不允许)
   ```

3. **.env 文件管理**
   ```
   .env (不上传到版本控制系统)
   .env.example (示例文件，上传到版本控制系统)
   .gitignore 包含: .env, .env.local, *.key, *.pem
   ```

4. **.env.example 示例**
   ```
   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/deepdive_dev
   DATABASE_POOL_SIZE=10

   # API Keys
   OPENAI_API_KEY=your-key-here
   CLAUDE_API_KEY=your-key-here

   # JWT
   JWT_SECRET_KEY=your-secret-key
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_HOURS=24

   # Redis
   REDIS_URL=redis://localhost:6379/0

   # Environment
   ENVIRONMENT=development
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```

5. **密钥轮换**
   ```
   - 定期轮换API密钥（每90天）
   - 定期轮换数据库密码（每30天）
   - 发生泄露事件时立即轮换
   ```

6. **密钥的访问权限控制**
   ```
   - 生产环境密钥仅在CI/CD中存储
   - 使用密钥管理服务（AWS Secrets Manager, HashiCorp Vault等）
   - 限制只有必要的服务可以访问密钥
   - 记录所有密钥访问日志
   ```

### 🟡 SHOULD - 强烈建议

1. **使用 python-dotenv 加载环境变量**
   ```python
   from dotenv import load_dotenv
   import os

   # 加载.env文件
   load_dotenv()

   api_key = os.getenv('OPENAI_API_KEY')
   ```

2. **配置管理使用 Pydantic**
   ```python
   from pydantic import BaseSettings, SecretStr

   class Settings(BaseSettings):
       openai_api_key: SecretStr
       database_url: str
       debug: bool = False

       class Config:
           env_file = ".env"
           case_sensitive = True

   settings = Settings()
   ```

---

## 认证和授权

### 🔴 MUST - 严格遵守

1. **使用 JWT 进行认证**
   ```python
   from fastapi import HTTPException, Depends
   from jose import JWTError, jwt
   from datetime import datetime, timedelta

   SECRET_KEY = getenv('JWT_SECRET_KEY')
   ALGORITHM = "HS256"

   def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
       to_encode = data.copy()
       if expires_delta:
           expire = datetime.utcnow() + expires_delta
       else:
           expire = datetime.utcnow() + timedelta(hours=1)
       to_encode.update({"exp": expire})
       encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
       return encoded_jwt

   async def get_current_user(token: str = Depends(oauth2_scheme)):
       try:
           payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
           user_id: int = payload.get("sub")
           if user_id is None:
               raise HTTPException(status_code=401)
       except JWTError:
           raise HTTPException(status_code=401)
       return user_id
   ```

2. **使用 HTTPS 传输**
   ```
   生产环境必须使用 HTTPS
   所有HTTP请求重定向到HTTPS
   ```

3. **密码必须加密存储**
   ```python
   from passlib.context import CryptContext

   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

   # ✅ 密码哈希存储
   hashed_password = pwd_context.hash("user_password")
   db.user.password = hashed_password

   # ✅ 验证密码
   is_correct = pwd_context.verify("input_password", user.password)

   ❌ # 不允许明文存储
      user.password = input_password
   ```

4. **实现权限检查**
   ```python
   from enum import Enum

   class UserRole(Enum):
       ADMIN = "admin"
       REVIEWER = "reviewer"
       USER = "user"

   async def check_admin(current_user: User = Depends(get_current_user)):
       if current_user.role != UserRole.ADMIN:
           raise HTTPException(status_code=403, detail="Insufficient permissions")
       return current_user

   @app.post("/api/v1/admin/delete-content/{id}")
   async def delete_content(id: int, admin: User = Depends(check_admin)):
       # 仅管理员可执行
       pass
   ```

5. **实施会话超时**
   ```python
   # Token 设置短期过期时间
   TOKEN_EXPIRE_MINUTES = 60  # 1小时

   # 使用 refresh token 获取新 access token
   ```

### 🟡 SHOULD - 强烈建议

1. **实现多因素认证（MFA）**
   ```python
   # 可选的额外安全层
   # - TOTP (Time-based One-Time Password)
   # - SMS验证码
   # - 硬件密钥
   ```

2. **登记和审计用户操作**
   ```python
   logger.info(f"User {user_id} logged in from {ip_address}")
   logger.info(f"User {user_id} accessed content {content_id}")
   ```

---

## 输入验证和防护

### 🔴 MUST - 严格遵守

1. **验证所有用户输入**
   ```python
   from pydantic import BaseModel, Field, validator

   class ContentCreateRequest(BaseModel):
       title: str = Field(..., min_length=1, max_length=200)
       body: str = Field(..., min_length=10, max_length=10000)
       category: str = Field(..., regex="^(AI|ML|DL|NLP|CV|RL|NLG|AGI)$")

       @validator('title')
       def title_no_script(cls, v):
           if '<script>' in v.lower():
               raise ValueError('Script tags not allowed')
           return v
   ```

2. **防止 SQL 注入**
   ```python
   ❌ # SQL注入风险
      query = f"SELECT * FROM users WHERE email = '{email}'"

   ✅ # 使用参数化查询
      from sqlalchemy import text
      query = text("SELECT * FROM users WHERE email = :email")
      result = db.execute(query, {"email": email})

   ✅ # 或使用ORM
      user = db.query(User).filter_by(email=email).first()
   ```

3. **防止 XSS 攻击**
   ```python
   from html import escape

   # ✅ 转义HTML
   safe_content = escape(user_input)

   # ✅ 在模板中自动转义
   # Jinja2默认转义，FastAPI返回的JSON也安全
   ```

4. **防止 CSRF 攻击**
   ```python
   from fastapi_csrf_protect import CsrfProtect

   @app.post("/api/v1/contents")
   async def create_content(
       request: Request,
       csrf_protect: CsrfProtect = Depends()
   ):
       await csrf_protect.validate_csrf(request)
       # 处理请求
   ```

5. **限制请求大小**
   ```python
   from fastapi import FastAPI

   app = FastAPI()

   # 限制请求体大小为10MB
   MAX_BODY_SIZE = 10 * 1024 * 1024

   # FastAPI配置

   @app.middleware("http")
   async def limit_request_size(request: Request, call_next):
       if request.method == "POST" and request.headers.get("content-length"):
           content_length = int(request.headers["content-length"])
           if content_length > MAX_BODY_SIZE:
               return JSONResponse(status_code=413)
       return await call_next(request)
   ```

### 🟡 SHOULD - 强烈建议

1. **使用速率限制**
   ```python
   from fastapi_limiter import FastAPILimiter
   from fastapi_limiter.depends import RateLimiter

   @app.get("/api/v1/contents")
   @limiter.limit("100/minute")
   async def list_contents(request: Request):
       pass
   ```

2. **日志记录敏感操作**
   ```python
   logger.warning(f"User {user_id} attempted unauthorized access to {resource}")
   logger.error(f"Failed login attempt for user {username}")
   ```

---

## 依赖管理和更新

### 🔴 MUST - 严格遵守

1. **定期更新依赖**
   ```bash
   # 检查过时的依赖
   pip list --outdated

   # 更新依赖
   pip install --upgrade package-name

   # 更新所有依赖
   pip install --upgrade -r requirements.txt
   ```

2. **检查依赖安全漏洞**
   ```bash
   # 使用 safety 检查已知漏洞
   pip install safety
   safety check

   # 使用 bandit 检查代码安全
   pip install bandit
   bandit -r src/

   # 使用 pip-audit
   pip install pip-audit
   pip-audit
   ```

3. **锁定依赖版本**
   ```
   使用 requirements.txt 或 poetry.lock 锁定版本
   避免使用 >= 的宽泛版本指定
   ```

4. **requirements.txt 示例**
   ```
   fastapi==0.104.1
   sqlalchemy==2.0.23
   pydantic==2.5.0
   jose[cryptography]==3.3.0
   bcrypt==4.1.0
   python-dotenv==1.0.0
   ```

### 🟡 SHOULD - 强烈建议

1. **使用 Poetry 管理依赖**
   ```bash
   poetry add package-name
   poetry update
   poetry lock
   ```

2. **定期审计依赖安全**
   ```bash
   # 每月运行依赖安全检查
   safety check
   pip-audit
   ```

---

## 日志和监控

### 🔴 MUST - 严格遵守

1. **记录安全事件**
   ```python
   import logging

   logger = logging.getLogger(__name__)

   # ✅ 记录认证失败
   logger.warning(f"Failed login attempt for user {username} from {ip}")

   # ✅ 记录权限违反
   logger.error(f"User {user_id} attempted unauthorized access to {resource}")

   # ✅ 记录异常
   logger.exception("Unexpected error occurred")

   # ❌ 不记录敏感信息
   # logger.info(f"User login with password: {password}")
   ```

2. **不记录敏感信息**
   ```python
   ✅ logger.info(f"Processing user {user_id}")
   ✅ logger.info(f"API call took {duration}ms")

   ❌ logger.info(f"User credentials: {username}:{password}")
   ❌ logger.info(f"API key: {api_key}")
   ❌ logger.info(f"JWT token: {token}")
   ```

3. **错误处理不要泄露系统信息**
   ```python
   ❌ # 返回详细的错误信息
      except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))

   ✅ # 返回通用错误信息，记录详细错误
      except Exception as e:
          logger.exception("Database error")
          raise HTTPException(status_code=500, detail="Internal server error")
   ```

### 🟡 SHOULD - 强烈建议

1. **监控异常访问**
   ```
   - 多次失败的登录尝试
   - 来自异常IP的访问
   - 批量数据导出请求
   - 权限升级操作
   ```

2. **设置告警**
   ```
   - 认证失败超过阈值
   - 异常数据库查询
   - 服务宕机
   - 异常的API流量
   ```

---

## 安全检查清单

提交代码前检查：

- [ ] 没有硬编码的密钥或密码
- [ ] 所有敏感信息从环境变量读取
- [ ] 使用参数化查询防止SQL注入
- [ ] 验证和清理所有用户输入
- [ ] 使用HTTPS传输敏感数据
- [ ] 密码使用bcrypt加密存储
- [ ] 实现了适当的认证和授权
- [ ] 记录了安全相关的日志
- [ ] 没有记录敏感信息
- [ ] 运行了安全检查工具（bandit, safety）
- [ ] 更新了依赖并检查了漏洞

---

**记住：** 安全是持续的过程，不是一次性的工作。定期审计、更新和监控是维护系统安全的关键。

