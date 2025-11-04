#!/usr/bin/env python3
"""
直接通过数据库连接重置用户密码
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ["CLOUDSQL_USER"] = "deepdive_user"
os.environ["CLOUDSQL_PASSWORD"] = "deepdive_user123"  # 使用当前Secret里的密码尝试连接
os.environ["CLOUDSQL_DATABASE"] = "deepdive_db"
os.environ["CLOUD_RUN"] = "true"

try:
    from sqlalchemy import text, create_engine
    from google.cloud.sql.connector import Connector, IPTypes

    print("[INFO] 初始化Cloud SQL Connector...")
    connector = Connector()

    def getconn():
        return connector.connect(
            "deepdive-engine:asia-east1:deepdive-db",
            "pg8000",
            user="deepdive_user",
            password="deepdive_user123",  # 尝试当前密码
            db="deepdive_db",
            ip_type=IPTypes.PUBLIC,
        )

    print("[INFO] 创建数据库引擎...")
    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        echo=False,
    )

    print("[INFO] 尝试连接数据库...")
    with engine.connect() as conn:
        print("[OK] 成功连接！当前密码是正确的")
        sys.exit(0)

except Exception as e:
    print(f"[ERROR] 连接失败: {e}")
    print(f"[INFO] 这意味着Secret里的密码 'deepdive_user123' 不匹配数据库用户密码")
    print(f"[INFO] 需要通过以下方式重置:")
    print(f"     1. Cloud Console手动重置数据库用户密码")
    print(f"     2. 或者给拥有cloudsql.admin权限的人运行:")
    print(f"        gcloud sql users set-password deepdive_user \\")
    print(f"          --instance=deepdive-engine \\")
    print(f"          --password=deepdive_user123")
    sys.exit(1)
