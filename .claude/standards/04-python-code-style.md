# Python代码风格规范

**版本：** 1.0
**强制级别：** 🔴 MUST
**更新日期：** 2025-11-02

---

## 核心原则

```
✅ 可读性 > 聪明代码
✅ 显式 > 隐式
✅ 简单 > 复杂
✅ 实用 > 纯粹
```

遵循 **PEP 8** 和 **PEP 20 (Zen of Python)**

---

## 代码格式化

### 🔴 MUST - 严格遵守

1. **使用 Black 格式化**
   ```bash
   # 所有代码必须通过black格式化
   black src/ tests/

   # 配置：max-line-length = 88 (Black默认)
   ```

2. **行长度限制 88字符**
   ```python
   ✅ def process_content(content_id: int, include_metadata: bool = False) -> Dict:

   ❌ def process_content_with_metadata_and_validation(content_id: int, include_metadata: bool = False, validate: bool = True) -> Dict:
   ```

3. **缩进使用4个空格**
   ```python
   ✅ def function():
           if condition:
               do_something()

   ❌ def function():
     if condition:
       do_something()  (2个空格不允许)

   ❌ def function():
   \t\tif condition:  (制表符不允许)
   ```

4. **空行规范**
   ```python
   # 顶级定义间使用2个空行
   class FirstClass:
       pass


   class SecondClass:
       pass


   def top_level_function():
       pass

   # 方法间使用1个空行
   class MyClass:
       def method1(self):
           pass

       def method2(self):
           pass

   # 函数体内逻辑块间使用1个空行
   def complex_function():
       # 初始化
       result = []

       # 处理逻辑
       for item in items:
           result.append(process(item))

       # 返回结果
       return result
   ```

5. **导入排列规范**
   ```python
   # 按照以下顺序排列
   # 1. 标准库
   import os
   import sys
   from typing import Dict, List, Optional

   # 2. 第三方库
   import fastapi
   from sqlalchemy import Column, String

   # 3. 本地应用
   from src.models.content import Content
   from src.services.collection import Collector

   # 每个分组间一个空行
   # 同一分组内按字母顺序排列
   ```

6. **避免尾随空格和混合空白**
   ```python
   ✅ def function():
           pass

   ❌ def function():
           pass          (行末有空格)
   ```

### 🟡 SHOULD - 强烈建议

1. **每个文件一个逻辑单位**
   ```
   ✅ src/services/content/manager.py (ContentManager类)
   ✅ src/services/content/validator.py (ContentValidator类)
   ❌ src/services/content.py (包含10个不相关的类)
   ```

2. **文件不超过500行**
   ```
   如果超过500行，考虑拆分成多个文件
   ```

---

## 类型注解

### 🔴 MUST - 严格遵守

1. **所有函数必须有参数和返回值类型注解**
   ```python
   ✅ def get_content(content_id: int) -> Optional[Content]:
           return db.query(Content).filter_by(id=content_id).first()

   ✅ def process_batch(items: List[str], batch_size: int = 100) -> Dict[str, Any]:
           pass

   ❌ def get_content(content_id):
           pass

   ❌ def process_batch(items, batch_size=100):
           pass
   ```

2. **使用 typing 模块进行复杂类型**
   ```python
   from typing import Dict, List, Optional, Tuple, Union, Any

   ✅ def fetch_data() -> Dict[str, Any]:
           pass

   ✅ def validate_items(items: List[Dict[str, str]]) -> Tuple[bool, str]:
           pass

   ✅ def get_config(key: str) -> Optional[str]:
           pass

   ✅ def process(value: Union[int, str]) -> bool:
           pass
   ```

3. **变量类型注解**
   ```python
   ✅ user_id: int = 123
   ✅ items: List[str] = []
   ✅ config: Dict[str, Any] = {}
   ✅ status: Optional[str] = None

   ❌ user_id = 123  (本地变量可选，但建议有)
   ```

4. **类属性类型注解**
   ```python
   ✅ class User:
           id: int
           name: str
           email: Optional[str] = None

           def __init__(self, id: int, name: str):
               self.id = id
               self.name = name
   ```

5. **避免使用 Any，尽量具体**
   ```python
   ✅ def parse_json(data: str) -> Dict[str, Any]:
           pass

   ❌ def parse_json(data: Any) -> Any:
           pass
   ```

6. **使用 Protocol 定义接口**
   ```python
   from typing import Protocol

   ✅ class DataSource(Protocol):
           def fetch(self) -> List[str]:
               ...

           def validate(self, data: str) -> bool:
               ...
   ```

### 🟡 SHOULD - 强烈建议

1. **复杂类型使用类型别名**
   ```python
   JSONData = Dict[str, Any]
   ContentList = List[Dict[str, Any]]

   def process_data(data: JSONData) -> ContentList:
       pass
   ```

2. **在Python 3.10+中使用新型注解**
   ```python
   # Python 3.10+
   ✅ def get_items() -> list[str]:
           pass

   ✅ def get_mapping() -> dict[str, int]:
           pass

   # Python 3.9及以下
   ✅ from typing import List, Dict
      def get_items() -> List[str]:
          pass
   ```

---

## 文档字符串（Docstring）

### 🔴 MUST - 严格遵守

1. **所有公开函数必须有 docstring**
   ```python
   ✅ def get_content(content_id: int) -> Optional[Content]:
           """获取内容详情。

           根据内容ID查询数据库获取完整的内容信息。

           Args:
               content_id: 内容ID，必须存在于数据库

           Returns:
               Content对象或None（如果不存在）

           Raises:
               ValueError: 如果content_id为负数

           Example:
               >>> content = get_content(123)
               >>> print(content.title)
               'OpenAI发布GPT-4'
           """
           pass

   ❌ def get_content(content_id: int) -> Optional[Content]:
           pass
   ```

2. **所有公开类必须有 docstring**
   ```python
   ✅ class ContentManager:
           """内容管理服务。

           负责内容的创建、更新、删除和查询操作。
           包括内容验证、格式化和发布管理。

           Attributes:
               db_session: 数据库会话
               cache: 缓存客户端
               logger: 日志对象
           """

           def __init__(self, db_session, cache, logger):
               pass
   ```

3. **Docstring 格式：Google风格**
   ```python
   def create_content(
       news_id: int,
       override_category: Optional[str] = None,
   ) -> Content:
       """从新闻创建内容。

       将原始新闻转换为可发布的内容，包括AI评分和分类。

       Args:
           news_id: 新闻ID，必须存在
           override_category: 可选，覆盖AI预测的分类

       Returns:
           创建的Content对象

       Raises:
           NewsNotFoundError: 如果新闻不存在
           AIProcessingError: 如果AI处理失败
           CategoryValidationError: 如果override_category无效

       Example:
           >>> content = create_content(123, override_category="AI")
           >>> print(content.score)
           85
       """
       pass
   ```

4. **Docstring 部分详解**
   ```
   1. 一行简介（必须）
   2. 详细说明（可选，多行）
   3. Args: 参数说明（如有参数则必须）
   4. Returns: 返回值说明（如有返回值则必须）
   5. Raises: 异常说明（如抛出异常则必须）
   6. Example: 使用示例（可选但推荐）
   ```

5. **模块级 docstring**
   ```python
   """内容管理模块。

   负责内容的生命周期管理，包括创建、验证、编辑和发布。

   Key Classes:
       ContentManager: 主要的内容管理服务
       ContentValidator: 内容验证器
       ContentFormatter: 内容格式化器

   Example:
       >>> from src.services.content import ContentManager
       >>> manager = ContentManager(db_session)
       >>> content = manager.create(news_id=123)
   """
   ```

### 🟡 SHOULD - 强烈建议

1. **私有方法的简短 docstring**
   ```python
   def _validate_score(self, score: int) -> bool:
       """检查score是否在有效范围内（0-100）。"""
       return 0 <= score <= 100
   ```

2. **复杂逻辑前的注释说明**
   ```python
   def _calculate_similarity(text1: str, text2: str) -> float:
       """计算两个文本的相似度。

       使用SimHash算法用于快速去重，精度约95%。
       """
       # 使用64位SimHash算法
       hash1 = simhash.SimHash(text1).value
       hash2 = simhash.SimHash(text2).value

       # 计算汉明距离作为相似度
       distance = bin(hash1 ^ hash2).count('1')
       return 1 - (distance / 64)
   ```

---

## 注释规范

### 🔴 MUST - 严格遵守

1. **只注释"为什么"，不注释"是什么"**
   ```python
   ✅ # 使用Simhash算法用于快速去重，性能优于TF-IDF
      is_duplicate = check_simhash_duplicate(content)

   ✅ # 重试3次是为了应对AI服务的偶发超时
      for attempt in range(3):
           try:
               result = ai_service.process(content)
               break
           except TimeoutError:
               if attempt == 2:
                   raise

   ❌ # 设置x为1
      x = 1

   ❌ # 循环遍历items列表
      for item in items:
           process(item)
   ```

2. **复杂算法前的注释**
   ```python
   # 使用余弦相似度计算文本相似度
   # 阈值0.8为判重标准，>0.8认为是重复
   if cosine_similarity(text1, text2) > 0.8:
       is_duplicate = True
   ```

3. **TODO/FIXME/HACK 注释**
   ```python
   # TODO: 后续优化数据库查询性能
   # FIXME: 需要处理边界情况
   # HACK: 临时解决方案，后续重构
   ```

4. **不要注释掉代码**
   ```python
   ❌ # result = old_function()
      result = new_function()

   ✅ # 使用新版本的函数
      result = new_function()
   ```

### 🟡 SHOULD - 强烈建议

1. **在复杂逻辑处添加说明**
   ```python
   # 必须在这里执行，因为之后的逻辑会修改state
   state.mark_processing()
   ```

2. **关键业务规则的注释**
   ```python
   # 根据业务规则，score >= 80分的内容才能自动发布
   if content.score >= 80:
       publish_content(content)
   ```

---

## 代码结构

### 🔴 MUST - 严格遵守

1. **类中方法的顺序**
   ```python
   class MyClass:
       # 1. 类变量
       class_var = "value"

       # 2. __init__方法
       def __init__(self):
           self.instance_var = "value"

       # 3. 公开方法
       def public_method(self):
           pass

       # 4. 私有方法
       def _private_method(self):
           pass

       # 5. 特殊方法（__str__, __repr等）
       def __str__(self) -> str:
           return f"MyClass({self.instance_var})"

       def __repr__(self) -> str:
           return f"MyClass({self.instance_var!r})"
   ```

2. **避免过度嵌套**
   ```python
   ✅ def process_items(items: List[str]) -> List[str]:
           result = []
           for item in items:
               processed = process(item)
               if processed:
                   result.append(processed)
           return result

   ❌ def process_items(items: List[str]) -> List[str]:
           result = []
           for item in items:
               if item:
                   processed = process(item)
                   if processed:
                       if validated(processed):
                           result.append(processed)  # 过度嵌套
           return result

   # 改进：使用早返回或提取方法
   ✅ def process_items(items: List[str]) -> List[str]:
           result = []
           for item in items:
               processed = _safe_process(item)
               if processed:
                   result.append(processed)
           return result

       def _safe_process(item: str) -> Optional[str]:
           if not item:
               return None
           processed = process(item)
           if not processed:
               return None
           if not validated(processed):
               return None
           return processed
   ```

3. **函数长度限制**
   ```
   ✅ 函数长度 < 50行（一屏可见）
   ❌ 函数长度 > 100行

   如果函数超过50行，考虑拆分成多个函数
   ```

4. **避免全局变量**
   ```python
   ❌ GLOBAL_CONFIG = {}  # 不允许全局状态

   ✅ class Config:  # 使用类或对象管理配置
           def __init__(self):
               self.data = {}
   ```

### 🟡 SHOULD - 强烈建议

1. **使用context managers处理资源**
   ```python
   ✅ with open('file.txt') as f:
           data = f.read()

   ✅ with db.session() as session:
           items = session.query(Item).all()

   ❌ f = open('file.txt')
      data = f.read()
      f.close()  # 容易遗漏
   ```

2. **使用生成器处理大数据**
   ```python
   ✅ def fetch_large_dataset() -> Generator[Item, None, None]:
           for batch in fetch_batches():
               for item in batch:
                   yield item

   ❌ def fetch_large_dataset() -> List[Item]:
           all_items = []
           for batch in fetch_batches():
               for item in batch:
                   all_items.append(item)  # 内存占用大
           return all_items
   ```

---

## 异常处理

### 🔴 MUST - 严格遵守

1. **定义自己的异常类**
   ```python
   ✅ class ContentNotFoundError(Exception):
           """内容不存在。"""
           pass

   ✅ class InvalidContentError(ValueError):
           """内容数据无效。"""
           pass

   ❌ raise Exception("Content not found")  (不允许通用Exception)
   ```

2. **具体捕获异常**
   ```python
   ✅ try:
           content = get_content(id)
       except ContentNotFoundError:
           logger.error(f"Content {id} not found")
           raise

   ❌ try:
           content = get_content(id)
       except:  # 太泛了
           pass

   ❌ try:
           content = get_content(id)
       except Exception:  # 太泛了
           pass
   ```

3. **异常链保留原始错误**
   ```python
   ✅ try:
           result = ai_service.process(content)
       except AIServiceError as e:
           raise ContentProcessingError(f"Failed to process {content.id}") from e

   ❌ try:
           result = ai_service.process(content)
       except AIServiceError:
           raise ContentProcessingError(f"Failed to process {content.id}")
           # 丢失了原始错误信息
   ```

4. **不要使用异常控制流**
   ```python
   ✅ def get_value(key: str) -> Optional[Any]:
           return self.data.get(key)

   ❌ def get_value(key: str) -> Any:
           try:
               return self.data[key]
           except KeyError:
               return None
   ```

5. **在 finally 块中清理资源**
   ```python
   ✅ try:
           connection = create_connection()
           result = connection.query()
       except ConnectionError:
           logger.error("Connection failed")
           raise
       finally:
           connection.close()  # 保证关闭
   ```

### 🟡 SHOULD - 强烈建议

1. **异常信息要清晰有用**
   ```python
   ✅ raise ValueError(f"Score must be 0-100, got {score}")
   ✅ raise ContentNotFoundError(f"Content with id={content_id} not found in database")

   ❌ raise ValueError("Invalid value")
   ❌ raise Exception("Error")
   ```

2. **自定义异常添加上下文**
   ```python
   class ContentValidationError(ValueError):
       def __init__(self, content_id: int, field: str, message: str):
           self.content_id = content_id
           self.field = field
           super().__init__(f"Content {content_id}.{field}: {message}")
   ```

---

## 代码示例

### 完整示例：规范的Python模块

```python
"""内容管理模块。

负责内容的生命周期管理，包括创建、验证、编辑和发布。

Key Classes:
    ContentManager: 主要的内容管理服务

Example:
    >>> from src.services.content import ContentManager
    >>> manager = ContentManager(db_session)
    >>> content = manager.create(news_id=123)
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.models.content import Content
from src.utils.logger import get_logger
from src.utils.exceptions import ContentNotFoundError, ValidationError


logger = get_logger(__name__)


class ContentStatus(Enum):
    """内容状态枚举。"""
    DRAFT = "draft"
    REVIEWING = "reviewing"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class ContentData:
    """内容数据容器。"""
    title: str
    body: str
    category: str
    score: int
    source_id: int


class ContentManager:
    """内容管理服务。

    负责内容的创建、更新、删除和查询操作。
    包括内容验证、格式化和发布管理。

    Attributes:
        db_session: 数据库会话
        validator: 内容验证器
        logger: 日志对象
    """

    def __init__(self, db_session, validator=None):
        """初始化ContentManager。

        Args:
            db_session: 数据库会话对象
            validator: 可选的验证器，默认使用ContentValidator
        """
        self.db_session = db_session
        self.validator = validator or self._default_validator
        self.logger = logger

    def create(self, content_data: ContentData) -> Content:
        """创建新内容。

        验证内容数据，然后保存到数据库。

        Args:
            content_data: 内容数据对象

        Returns:
            创建的Content对象

        Raises:
            ValidationError: 如果内容数据无效
            DatabaseError: 如果保存失败
        """
        # 验证内容
        if not self.validator.validate(content_data):
            raise ValidationError("Invalid content data")

        # 创建数据库对象
        content = Content(
            title=content_data.title,
            body=content_data.body,
            category=content_data.category,
            score=content_data.score,
            source_id=content_data.source_id,
            status=ContentStatus.DRAFT.value,
            created_at=datetime.now(),
        )

        # 保存到数据库
        self.db_session.add(content)
        try:
            self.db_session.commit()
            self.logger.info(f"Content created: {content.id}")
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"Failed to create content: {str(e)}")
            raise

        return content

    def get(self, content_id: int) -> Optional[Content]:
        """获取内容。

        Args:
            content_id: 内容ID

        Returns:
            Content对象或None

        Raises:
            ValueError: 如果content_id无效
        """
        if content_id <= 0:
            raise ValueError(f"Invalid content_id: {content_id}")

        return self.db_session.query(Content).filter_by(id=content_id).first()

    def list(self, limit: int = 10, offset: int = 0) -> List[Content]:
        """列表查询内容。

        Args:
            limit: 限制条数
            offset: 偏移量

        Returns:
            Content对象列表
        """
        return (
            self.db_session.query(Content)
            .order_by(Content.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def update(self, content_id: int, data: Dict[str, Any]) -> Content:
        """更新内容。

        Args:
            content_id: 内容ID
            data: 更新数据字典

        Returns:
            更新后的Content对象

        Raises:
            ContentNotFoundError: 如果内容不存在
        """
        content = self.get(content_id)
        if not content:
            raise ContentNotFoundError(f"Content {content_id} not found")

        for key, value in data.items():
            if hasattr(content, key):
                setattr(content, key, value)

        content.updated_at = datetime.now()
        self.db_session.commit()

        return content

    def _default_validator(self, data: ContentData) -> bool:
        """默认验证器。"""
        return (
            data.title
            and data.body
            and 0 <= data.score <= 100
            and data.category
        )
```

---

## 代码风格检查清单

提交代码前检查：

- [ ] 代码通过 `black src/ tests/` 格式化
- [ ] 代码通过 `flake8 src/ tests/` 检查
- [ ] 代码通过 `mypy src/` 类型检查
- [ ] 所有函数都有类型注解（参数和返回值）
- [ ] 所有公开函数都有docstring
- [ ] 没有 TODO/FIXME 注释未解决
- [ ] 异常处理具体且有意义
- [ ] 没有未使用的导入
- [ ] 没有全局变量
- [ ] 没有过度嵌套的代码
- [ ] 函数长度 < 50行
- [ ] 注释只解释"为什么"

---

**记住：** 代码是写给人看的，顺便让电脑执行。好的代码应该易于理解、易于维护、易于测试。

