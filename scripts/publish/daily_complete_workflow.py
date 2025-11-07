#!/usr/bin/env python3
"""
DeepDive Daily Complete Workflow - 每日完整工作流

功能：
  1. 采集新闻 (Collect News)
  2. AI 评分 (Score News with OpenAI)
  3. 发送邮件 (Send Email with card layout)
  4. 发布 GitHub (Publish to GitHub with batch summary)

使用方式：
  python scripts/publish/daily_complete_workflow.py

说明：
  - 自动执行完整的每日流程
  - 从采集→评分→发布，一条龙完成
  - 支持邮件和 GitHub 两个渠道
  - 包含完整的日志和错误处理
  - 支持 Cron 和 Cloud Scheduler 调度
"""

import sys
import io
import subprocess
from pathlib import Path
from datetime import datetime
import json
import logging

# 修复 Windows 编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class DailyWorkflow:
    """每日工作流管理器"""

    def __init__(self):
        self.start_time = datetime.now()
        self.results = {
            "status": "pending",
            "start_time": self.start_time.isoformat(),
            "steps": {},
            "errors": []
        }

    def run_command(self, cmd, step_name, description):
        """执行命令并记录结果"""
        print(f"\n{'='*80}")
        print(f"[{step_name}] {description}")
        print(f"{'='*80}")
        print(f"执行命令: {cmd}\n")

        try:
            # Import os to access environment variables
            import os

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=1200,  # 20 分钟超时 (评分200篇需要更多时间)
                env=os.environ.copy()  # Pass environment variables to subprocess
            )

            if result.returncode == 0:
                print(f"[OK] {step_name} 成功")
                self.results["steps"][step_name] = {
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                }
                if result.stdout:
                    print(f"输出:\n{result.stdout}")
                return True
            else:
                error_msg = f"{step_name} 失败: {result.stderr}"
                print(f"[FAILED] {error_msg}")
                self.results["steps"][step_name] = {
                    "status": "failed",
                    "error": result.stderr,
                    "timestamp": datetime.now().isoformat()
                }
                self.results["errors"].append(error_msg)
                return False

        except subprocess.TimeoutExpired:
            error_msg = f"{step_name} 超时（20 分钟）"
            print(f"[FAILED] {error_msg}")
            self.results["errors"].append(error_msg)
            return False
        except Exception as e:
            error_msg = f"{step_name} 异常: {str(e)}"
            print(f"[FAILED] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def print_banner(self):
        """打印欢迎横幅"""
        print("\n" + "=" * 80)
        print("DeepDive Tracking - 每日完整工作流")
        print("=" * 80)
        print()
        print("流程：采集新闻 -> AI 评分 -> 发送邮件 -> 发布 GitHub")
        print()
        print(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def print_summary(self):
        """打印总结"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        print("\n" + "=" * 80)
        print("每日工作流完成总结")
        print("=" * 80)
        print()

        # 统计成功和失败
        successful_steps = sum(1 for step in self.results["steps"].values() if step["status"] == "success")
        total_steps = len(self.results["steps"])

        print(f"总耗时: {duration:.1f} 秒")
        print(f"完成步骤: {successful_steps}/{total_steps}")
        print()

        # 详细结果
        print("步骤结果:")
        for step_name, step_result in self.results["steps"].items():
            status_icon = "[OK]" if step_result["status"] == "success" else "[FAILED]"
            print(f"  {status_icon} {step_name}: {step_result['status']}")

        if self.results["errors"]:
            print()
            print("错误信息:")
            for error in self.results["errors"]:
                print(f"  {error}")

        self.results["status"] = "success" if successful_steps == total_steps else "partial"
        self.results["end_time"] = end_time.isoformat()
        self.results["duration_seconds"] = duration

        # 保存结果到文件
        self.save_results()

        # 最终状态
        print()
        if self.results["status"] == "success":
            print("[SUCCESS] 所有步骤完成！")
            return 0
        else:
            print("[WARNING] 部分步骤失败")
            return 1

    def save_results(self):
        """保存工作流结果"""
        results_file = project_root / "logs" / f"workflow_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"[OK] 工作流日志已保存: {results_file}")
        except Exception as e:
            print(f"[WARN] 保存日志失败: {e}")

    def run(self):
        """执行完整工作流"""
        self.print_banner()

        # Step 1: 采集新闻
        if not self.run_command(
            "python scripts/collection/collect_news.py",
            "采集",
            "采集最新的AI新闻"
        ):
            print("\n[WARN] 采集失败，但继续处理已有的新闻...")

        # Step 2: AI 评分 (评分200篇以确保多样性)
        if not self.run_command(
            "python scripts/evaluation/score_collected_news.py 200",
            "评分",
            "对采集的新闻进行 AI 智能评分 (200篇，确保来源多样性)"
        ):
            print("\n[FAILED] 评分失败，无法继续")
            return self.print_summary()

        # Step 3: 发送邮件
        if not self.run_command(
            "python scripts/publish/send_top_news_email.py",
            "邮件",
            "发送每日精选邮件（批量发送，卡片布局）"
        ):
            print("\n[WARN] 邮件发送失败，继续发布到 GitHub...")

        # Step 4: 发布到 GitHub
        if not self.run_command(
            "python scripts/publish/send_top_ai_news_to_github.py",
            "GitHub",
            "发布到 GitHub 仓库（批量汇总页面）"
        ):
            print("\n[WARN] GitHub 发布失败")

        # 打印总结
        return self.print_summary()


def main():
    """主函数"""
    workflow = DailyWorkflow()
    exit_code = workflow.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
