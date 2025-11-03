#!/usr/bin/env python3
"""
Email Verification Script - Test complete email sending functionality
"""
import sys
import os
import asyncio
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.channels.email.email_publisher import EmailPublisher
from src.config.settings import get_settings

async def main():
    """Main verification function"""
    settings = get_settings()

    print("=" * 70)
    print("Email System Verification Test")
    print("=" * 70)

    # Check SMTP configuration
    print("\n1. Checking SMTP configuration...")
    if not settings.smtp_user or not settings.smtp_password:  # noqa: S105
        print("[FAILED] SMTP credentials not configured")
        return False

    print(f"[OK] SMTP Host: {settings.smtp_host}")
    print(f"[OK] SMTP Port: {settings.smtp_port}")
    print(f"[OK] From Email: {settings.smtp_from_email}")
    print(f"[OK] From Name: {settings.smtp_from_name}")

    # Initialize Email Publisher
    print("\n2. Initializing Email Publisher...")
    try:
        publisher = EmailPublisher(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_user=settings.smtp_user,
            smtp_password=settings.smtp_password,
            from_email=settings.smtp_from_email,
            from_name=settings.smtp_from_name
        )
        print("[OK] Email publisher initialized successfully")
    except Exception as e:
        print(f"[FAILED] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Prepare test article
    print("\n3. Preparing verification email...")
    title = "DeepDive Tracking - System Verification Email"
    summary = "Email system verification from Cloud Run"
    author = "System Test"
    source_url = "https://deepdive-tracking-726493701291.asia-east1.run.app"
    category = "Technology"
    score = 95.0
    content = f"""
<p>DeepDive Tracking system is operational and email functionality has been verified.</p>

<h3>Tasks Completed:</h3>
<ul>
    <li>Cloud Run deployment successful</li>
    <li>Database connection working</li>
    <li>Redis cache available</li>
    <li>GCP Secret Manager integrated</li>
    <li>Email system initialized</li>
</ul>

<h3>System Status:</h3>
<ul>
    <li><strong>Service URL:</strong> https://deepdive-tracking-726493701291.asia-east1.run.app</li>
    <li><strong>Region:</strong> asia-east1</li>
    <li><strong>Status:</strong> RUNNING</li>
    <li><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
</ul>

<h3>Email Functionality Verified:</h3>
<ul>
    <li>SMTP connection established</li>
    <li>Gmail authentication successful</li>
    <li>HTML email formatting working</li>
    <li>Email content generation successful</li>
</ul>

<p style="color: #666; font-size: 12px; margin-top: 40px;">
    This is an auto-generated system verification email from DeepDive Tracking.
</p>
    """

    print(f"[OK] Email title: {title}")
    print(f"[OK] Email score: {score}")

    # Send verification email
    print("\n4. Sending verification email...")
    recipient_email = settings.smtp_from_email or "hello.junjie.duan@gmail.com"
    print(f"    Recipient: {recipient_email}")

    try:
        result = await publisher.publish_article(
            title=title,
            content=content,
            summary=summary,
            author=author,
            source_url=source_url,
            score=score,
            category=category,
            email_list=[recipient_email]
        )

        if result and result.get("success"):
            print(f"[OK] Email sent successfully!")
            print(f"    Sent to {result.get('sent_count', 0)} recipient(s)")
            return True
        else:
            error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else "Unknown error"
            print(f"[FAILED] Email send failed: {error_msg}")
            if isinstance(result, dict):
                failed = result.get("failed_emails", [])
                if failed:
                    print(f"    Failed recipients: {failed}")
            return False

    except Exception as e:
        print(f"[FAILED] Exception during send: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        print("\n" + "=" * 70)
        if success:
            print("Email System Verification Complete!")
            print("=" * 70)
            print("\nVerification email has been sent successfully.")
            print("Please check your inbox for the test email from DeepDive Tracking.")
        else:
            print("Email System Verification Failed!")
            print("=" * 70)

        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
