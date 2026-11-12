import sys
import logging

from config import Config
from automation import CheckInAutomation

logger = logging.getLogger(__name__)


def main() -> bool:
    """主函数，返回签到是否成功（供 GitHub Actions 判定退出码）"""
    try:
        config = Config.from_env()
        logger.info(f"使用账户: {config.sakurafrp_user}")

        automation = CheckInAutomation(config)
        return bool(automation.run())

    except ValueError as e:
        logger.error(f"配置错误: {e}")
        return False
    except Exception as e:
        logger.error(f"程序执行失败: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
