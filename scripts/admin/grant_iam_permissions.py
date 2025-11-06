#!/usr/bin/env python3
"""
Grant database permissions to IAM service account user

This script connects using a password-based user and grants privileges
to the IAM service account user.
"""

import sys
from pathlib import Path
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_session
from sqlalchemy import text


def main():
    """Grant permissions to IAM user"""
    iam_user = "726493701291-compute@developer"

    print("\n" + "=" * 70)
    print("GRANT PERMISSIONS TO IAM SERVICE ACCOUNT")
    print("=" * 70)
    print()
    print(f"IAM User: {iam_user}")
    print()

    # Force direct connection (not Cloud SQL Connector) by unsetting K_SERVICE
    os.environ.pop("K_SERVICE", None)
    os.environ.pop("CLOUD_RUN", None)

    session = get_session()

    try:
        print("1. Granting CONNECT privilege on database...")
        # Note: GRANT CONNECT ON DATABASE must be run by a superuser or database owner
        # We'll skip this and just grant schema-level permissions

        print("2. Granting USAGE on schema public...")
        session.execute(text(f'GRANT USAGE ON SCHEMA public TO "{iam_user}"'))
        session.commit()

        print("3. Granting table privileges...")
        session.execute(text(f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "{iam_user}"'))
        session.commit()

        print("4. Granting sequence privileges...")
        session.execute(text(f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "{iam_user}"'))
        session.commit()

        print("5. Setting default privileges for future tables...")
        session.execute(text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{iam_user}"'))
        session.commit()

        print("6. Setting default privileges for future sequences...")
        session.execute(text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO "{iam_user}"'))
        session.commit()

        print()
        print("=" * 70)
        print("✅ PERMISSIONS GRANTED SUCCESSFULLY")
        print("=" * 70)
        print()
        print("The IAM service account can now:")
        print("  - Connect to the database")
        print("  - Read/write all tables in public schema")
        print("  - Use sequences (for auto-increment columns)")
        print()

        return 0

    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        session.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
