# 数据库设计规范

**版本：** 1.0
**强制级别：** 🔴 MUST
**更新日期：** 2025-11-02

---

## 核心原则

```
✅ 数据完整性第一
✅ 性能和可维护性平衡
✅ 清晰的表结构和关系
✅ 充分的索引和约束
✅ 自动化的版本管理（migrations）
```

---

## 表设计规范

### 🔴 MUST - 严格遵守

1. **表名使用 snake_case，复数形式**
   ```sql
   ✅ CREATE TABLE users (...)
   ✅ CREATE TABLE content_items (...)
   ✅ CREATE TABLE data_sources (...)
   ✅ CREATE TABLE raw_news (...)
   ❌ CREATE TABLE User (...)
   ❌ CREATE TABLE user (...)
   ❌ CREATE TABLE UserTable (...)
   ```

2. **主键使用 id，类型为 BIGINT**
   ```sql
   ✅ CREATE TABLE users (
       id BIGINT PRIMARY KEY AUTO_INCREMENT,
       ...
   )

   ❌ CREATE TABLE users (
       user_id BIGINT PRIMARY KEY,
       ...
   )

   ❌ CREATE TABLE users (
       id INT PRIMARY KEY,  (INT容量不足)
       ...
   )
   ```

3. **外键命名规范**
   ```sql
   ✅ CREATE TABLE content_items (
       id BIGINT PRIMARY KEY,
       user_id BIGINT NOT NULL REFERENCES users(id),
       source_id BIGINT NOT NULL REFERENCES data_sources(id),
       ...
   )

   ❌ CREATE TABLE content_items (
       id BIGINT PRIMARY KEY,
       uid BIGINT,  (缩写不清晰)
       user BIGINT,  (没有_id后缀)
       ...
   )
   ```

4. **时间戳字段规范**
   ```sql
   ✅ CREATE TABLE users (
       id BIGINT PRIMARY KEY,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
       deleted_at TIMESTAMP NULL,
       ...
   )

   ❌ CREATE TABLE users (
       id BIGINT PRIMARY KEY,
       create_date DATE,  (应该是TIMESTAMP)
       update_time TIMESTAMP,  (字段名不一致)
       ...
   )
   ```

5. **列名使用 snake_case**
   ```sql
   ✅ CREATE TABLE users (
       id BIGINT,
       user_name VARCHAR(255),
       email_address VARCHAR(255),
       is_active BOOLEAN DEFAULT TRUE,
       created_at TIMESTAMP
   )

   ❌ CREATE TABLE users (
       ID,
       userName,
       emailAddress,
       IsActive,
       CreatedAt
   )
   ```

6. **布尔字段使用 BOOLEAN，前缀 is_/has_/can_**
   ```sql
   ✅ is_active BOOLEAN DEFAULT TRUE
   ✅ has_permission BOOLEAN DEFAULT FALSE
   ✅ can_publish BOOLEAN DEFAULT FALSE

   ❌ active BOOLEAN
   ❌ ADMIN INT (0/1表示)
   ```

7. **VARCHAR 长度明确指定**
   ```sql
   ✅ user_name VARCHAR(100)
   ✅ email_address VARCHAR(255)
   ✅ title VARCHAR(500)

   ❌ user_name VARCHAR  (没有长度)
   ❌ user_name VARCHAR(65535)  (太大)
   ```

8. **使用 TEXT 存储长文本，不用 VARCHAR**
   ```sql
   ✅ content_body TEXT
   ✅ description TEXT

   ❌ content_body VARCHAR(10000)
   ```

9. **数值字段指定精度**
   ```sql
   ✅ price DECIMAL(10, 2)  (最多10位，2位小数)
   ✅ score INT  (整数0-100)
   ✅ rating FLOAT  (单精度浮点数)

   ❌ price FLOAT  (精度不足)
   ❌ score INT  (不明确范围)
   ```

10. **约束规范**
    ```sql
    ✅ CREATE TABLE users (
        id BIGINT PRIMARY KEY,
        email_address VARCHAR(255) NOT NULL UNIQUE,
        user_name VARCHAR(100) NOT NULL,
        age INT CHECK (age >= 0 AND age <= 150),
        status VARCHAR(50) DEFAULT 'active'
    )

    ❌ CREATE TABLE users (
        id BIGINT,
        email_address VARCHAR(255),  (可为NULL，不合理)
        age INT,  (没有范围检查)
        ...
    )
    ```

### 🟡 SHOULD - 强烈建议

1. **避免使用保留字**
   ```sql
   ❌ SELECT `order`, `user`, `date` FROM ...

   ✅ SELECT placed_order, user_account, created_date FROM ...
   ```

2. **使用 ENUM 而不是整数表示枚举**
   ```sql
   ✅ status ENUM('draft', 'reviewing', 'published', 'archived')

   ❌ status INT  (0=draft, 1=reviewing, ...)
   ```

---

## 索引设计规范

### 🔴 MUST - 严格遵守

1. **索引命名规范**
   ```sql
   ✅ CREATE INDEX idx_users_email ON users(email_address)
   ✅ CREATE INDEX idx_content_items_source_id ON content_items(source_id)
   ✅ CREATE UNIQUE INDEX uq_users_email ON users(email_address)
   ✅ CREATE INDEX idx_content_items_created_at_status ON content_items(created_at, status)

   ❌ CREATE INDEX index1 ON users(email_address)
   ❌ CREATE INDEX users_email ON users(email_address)
   ❌ CREATE INDEX idx_user_email_address (字段名多余)
   ```

2. **在常见查询字段上建立索引**
   ```sql
   -- 查询常用的字段需要索引
   ✅ CREATE INDEX idx_users_id ON users(id)  (自动)
   ✅ CREATE INDEX idx_content_items_user_id ON content_items(user_id)
   ✅ CREATE INDEX idx_raw_news_source_id ON raw_news(source_id)
   ✅ CREATE INDEX idx_content_items_status ON content_items(status)
   ✅ CREATE INDEX idx_raw_news_created_at ON raw_news(created_at)
   ```

3. **外键字段必须有索引**
   ```sql
   ✅ CREATE TABLE content_items (
       id BIGINT PRIMARY KEY,
       user_id BIGINT NOT NULL,  -- 需要索引
       source_id BIGINT NOT NULL,  -- 需要索引
       ...
   )

   CREATE INDEX idx_content_items_user_id ON content_items(user_id)
   CREATE INDEX idx_content_items_source_id ON content_items(source_id)
   ```

4. **复合索引规范**
   ```sql
   -- 查询条件：WHERE created_at > ? AND status = 'published'
   ✅ CREATE INDEX idx_content_status_created ON content_items(status, created_at)

   -- 复合索引的列顺序很重要
   -- 选择性强的列放前面（如status）
   ```

5. **避免过度索引**
   ```sql
   -- 不是所有列都需要索引
   ❌ CREATE INDEX idx_title ON content_items(title)  (全文搜索列不适合普通索引)
   ❌ CREATE INDEX idx_body ON content_items(body)    (文本列不适合普通索引)

   ✅ -- 使用全文索引
      CREATE FULLTEXT INDEX ft_content ON content_items(title, body)
   ```

### 🟡 SHOULD - 强烈建议

1. **定期分析索引效率**
   ```sql
   -- MySQL
   ANALYZE TABLE table_name;
   ```

2. **避免冗余索引**
   ```sql
   ❌ CREATE INDEX idx_user_id ON content_items(user_id)
      CREATE INDEX idx_user_id_created ON content_items(user_id, created_at)
      (第一个索引是多余的)
   ```

---

## 约束规范

### 🔴 MUST - 严格遵守

1. **命名约束**
   ```sql
   ✅ CONSTRAINT fk_content_user FOREIGN KEY (user_id) REFERENCES users(id)
   ✅ CONSTRAINT ck_score_range CHECK (score >= 0 AND score <= 100)
   ✅ CONSTRAINT uq_users_email UNIQUE (email_address)

   ❌ CONSTRAINT fk1 FOREIGN KEY
   ❌ CONSTRAINT check1 CHECK
   ```

2. **外键约束应指定删除策略**
   ```sql
   ✅ FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
   ✅ FOREIGN KEY (source_id) REFERENCES data_sources(id) ON DELETE RESTRICT

   ❌ FOREIGN KEY (user_id) REFERENCES users(id)  (没有策略)
   ```

3. **唯一约束规范**
   ```sql
   ✅ CREATE TABLE users (
       id BIGINT PRIMARY KEY,
       email_address VARCHAR(255) NOT NULL UNIQUE,
       username VARCHAR(100) NOT NULL UNIQUE,
       ...
   )

   ❌ CREATE TABLE users (
       id BIGINT PRIMARY KEY,
       email_address VARCHAR(255),  (可为NULL，UNIQUE无效)
       ...
   )
   ```

---

## 数据库迁移规范

### 🔴 MUST - 严格遵守

1. **使用迁移框架（Alembic）**
   ```python
   # src/database/migrations/versions/xxx_add_column.py
   from alembic import op
   import sqlalchemy as sa

   def upgrade():
       """向users表添加新列。"""
       op.add_column('users', sa.Column('phone', sa.String(20)))

   def downgrade():
       """删除添加的列。"""
       op.drop_column('users', 'phone')
   ```

2. **迁移文件命名**
   ```
   ✅ versions/001_create_users_table.py
   ✅ versions/002_add_email_to_users.py
   ✅ versions/003_create_content_items_table.py

   ❌ versions/migration.py
   ❌ versions/update.py
   ❌ versions/fix_db.py
   ```

3. **每个迁移应该原子化**
   ```python
   ✅ # 只做一件事
      def upgrade():
          op.add_column('users', sa.Column('phone', sa.String(20)))

   ❌ # 多个不相关的改动
      def upgrade():
          op.add_column('users', sa.Column('phone', sa.String(20)))
          op.add_column('posts', sa.Column('category', sa.String(50)))
          op.drop_column('comments', 'spam_count')
   ```

4. **迁移必须是可逆的**
   ```python
   ✅ def upgrade():
          op.add_column('users', sa.Column('age', sa.Integer))

      def downgrade():
          op.drop_column('users', 'age')

   ❌ def upgrade():
          op.execute("DELETE FROM users WHERE age < 18")

      def downgrade():
          pass  # 数据已删除，无法恢复
   ```

5. **迁移包含完整的SQL，可独立运行**
   ```python
   ✅ def upgrade():
          op.create_table(
              'users',
              sa.Column('id', sa.BIGINT, primary_key=True),
              sa.Column('email', sa.String(255), unique=True),
              sa.Column('created_at', sa.TIMESTAMP, default=sa.func.now())
          )

   ❌ def upgrade():
          # 假设表已存在？
          op.add_column('users', sa.Column('email', sa.String(255)))
   ```

### 🟡 SHOULD - 强烈建议

1. **在生产环境前在测试环境验证迁移**
   ```bash
   # 在测试数据库上运行迁移
   alembic upgrade head --sql
   ```

2. **保持迁移历史完整**
   ```
   不允许修改已执行的迁移文件
   ```

---

## 数据一致性规范

### 🔴 MUST - 严格遵守

1. **使用事务确保一致性**
   ```python
   from sqlalchemy import begin

   ✅ with db.begin():
          # 多个操作要么都成功，要么都失败
          user = create_user(data)
          profile = create_profile(user.id)
          notification = send_notification(user)

   ❌ user = create_user(data)
      profile = create_profile(user.id)  # 如果这里失败，user已创建
      notification = send_notification(user)
   ```

2. **关键数据必须有备份和恢复策略**
   ```sql
   -- 使用软删除
   ✅ ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL;

   -- 查询时排除已删除的记录
   ✅ SELECT * FROM users WHERE deleted_at IS NULL;

   -- 恢复删除的记录
   ✅ UPDATE users SET deleted_at = NULL WHERE id = 123;
   ```

3. **避免数据孤立**
   ```sql
   ✅ -- 使用外键约束
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE

   ❌ -- 手动维护外键关系容易出错
   ```

---

## 查询性能规范

### 🔴 MUST - 严格遵守

1. **避免 N+1 查询**
   ```python
   ❌ # N+1问题
      users = db.query(User).all()
      for user in users:
          posts = db.query(Post).filter_by(user_id=user.id).all()  # N次查询

   ✅ # 使用JOIN或eager loading
      users = db.query(User).options(joinedload(User.posts)).all()

   ✅ # 或使用单个查询
      users_with_posts = (
          db.query(User)
          .join(Post)
          .options(contains_eager(User.posts))
          .all()
      )
   ```

2. **使用分页避免一次加载大量数据**
   ```python
   ✅ items = db.query(Item).limit(10).offset(0).all()

   ❌ items = db.query(Item).all()  # 可能加载数百万条记录
   ```

3. **选择需要的列，不要 SELECT \***
   ```python
   ✅ db.query(User.id, User.email).filter_by(active=True).all()

   ❌ db.query(User).filter_by(active=True).all()  # 加载所有列，包括大TEXT字段
   ```

### 🟡 SHOULD - 强烈建议

1. **定期检查慢查询日志**
   ```sql
   -- MySQL
   SET GLOBAL slow_query_log = 'ON';
   SET GLOBAL long_query_time = 2;
   ```

2. **使用 EXPLAIN 分析查询**
   ```sql
   EXPLAIN SELECT * FROM content_items WHERE status = 'published' AND created_at > '2025-11-01';
   ```

---

## 数据库设计检查清单

创建新表前检查：

- [ ] 表名使用 snake_case 复数形式
- [ ] 主键使用 id (BIGINT)
- [ ] 有 created_at 和 updated_at 时间戳
- [ ] 外键有索引和约束
- [ ] 所有列都有明确的类型和默认值
- [ ] NOT NULL 约束正确指定
- [ ] 关键查询字段有索引
- [ ] 避免过度索引
- [ ] 迁移文件编写完整
- [ ] 迁移可逆，包含 downgrade

---

**记住：** 好的数据库设计是系统性能和数据完整性的基础。花时间设计好表结构，避免后期大量重构。

