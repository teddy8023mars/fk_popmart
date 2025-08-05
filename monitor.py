#!/usr/bin/env python3
"""
PopMart官网库存监控器
专注监控PopMart官网商品库存状态
"""

from monitors.official_monitor import OfficialMonitor
import os
import sys
import asyncio
import argparse
import logging
import time
import discord
from dotenv import load_dotenv

# 添加monitors目录到路径
sys.path.append(os.path.dirname(__file__))


class PopMartMonitor:
    """PopMart官网库存监控器"""

    def __init__(self, bot_token, verbose_mode=False):
        self.bot_token = bot_token
        self.verbose_mode = verbose_mode
        self.monitors = []

        # 设置Discord客户端
        intents = discord.Intents.default()
        self.client = discord.Client(intents=intents)

        # 配置日志
        self.setup_logging()

    def setup_logging(self):
        """设置日志配置"""
        # 禁用discord.py内部日志以减少混乱
        logging.getLogger('discord').setLevel(logging.WARNING)
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('WDM').setLevel(logging.WARNING)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )

    def get_unified_config(self):
        """获取统一的配置参数"""
        return {
            # 检查间隔（秒）
            'min_interval': int(os.getenv('MONITOR_MIN_INTERVAL', 3)),
            'max_interval': int(os.getenv('MONITOR_MAX_INTERVAL', 6)),

            # 通知间隔（秒）
            'notification_interval': int(os.getenv('MONITOR_NOTIFICATION_INTERVAL', 3)),

            # 心跳间隔（秒）- 目前未使用，但保留配置
            'heartbeat_interval': int(os.getenv('MONITOR_HEARTBEAT_INTERVAL', 300)),

            # 页面加载超时（秒）
            'page_load_timeout': int(os.getenv('MONITOR_PAGE_LOAD_TIMEOUT', 25)),

            # 页面加载后等待时间（秒）
            'page_load_wait': int(os.getenv('MONITOR_PAGE_LOAD_WAIT', 3)),

            # JavaScript渲染等待时间（秒）
            'js_render_wait': int(os.getenv('MONITOR_JS_RENDER_WAIT', 5)),

            # Cloudflare验证等待时间（秒）
            'cloudflare_wait': int(os.getenv('MONITOR_CLOUDFLARE_WAIT', 10)),
        }

    def add_official_monitor(self):
        """添加PopMart官网监控器"""
        try:
            channel_id = int(os.getenv('OFFICIAL_CHANNEL_ID'))
            product_url = os.getenv('OFFICIAL_PRODUCT_URL')
            config = self.get_unified_config()

            monitor = OfficialMonitor(
                channel_id=channel_id,
                product_url=product_url,
                min_interval=config['min_interval'],
                max_interval=config['max_interval'],
                heartbeat_interval=config['heartbeat_interval'],
                notification_interval=config['notification_interval'],
                page_load_timeout=config['page_load_timeout'],
                page_load_wait=config['page_load_wait'],
                js_render_wait=config['js_render_wait'],
                cloudflare_wait=config['cloudflare_wait'],
                verbose_mode=self.verbose_mode
            )

            self.monitors.append(monitor)
            print(f"✅ PopMart官网监控器已添加 - 频道ID: {channel_id}")

        except Exception as e:
            print(f"❌ 添加PopMart官网监控器失败: {e}")

    async def send_startup_notifications(self):
        """发送启动通知"""
        mode_text = "Verbose模式" if self.verbose_mode else "正常模式"

        for monitor in self.monitors:
            try:
                channel = self.client.get_channel(monitor.channel_id)
                if channel:
                    product_name = monitor.extract_product_name_from_url(
                        monitor.product_url)
                    await channel.send(f"🤖 {monitor.platform_name}监控启动 | {product_name} | {mode_text}")
                    print(f"✅ {monitor.platform_name}启动通知已发送")
            except Exception as e:
                print(f"❌ {monitor.platform_name}启动通知发送失败: {e}")

    async def run_monitors(self):
        """运行所有监控器"""
        if not self.monitors:
            print("❌ 没有配置任何监控器")
            return

        print("=" * 80)
        print(f"🤖 PopMart官网监控机器人已启动")
        print("=" * 80)

        # 发送启动通知
        await self.send_startup_notifications()

        # 为每个监控器设置浏览器驱动
        for monitor in self.monitors:
            if not monitor.setup_driver():
                print(f"❌ {monitor.platform_name}浏览器驱动初始化失败")
                continue

        print(f"🔄 开始并发监控...")
        print("=" * 80)

        # 并发运行所有监控器
        tasks = []
        for monitor in self.monitors:
            task = asyncio.create_task(monitor.monitor_loop(self.client))
            tasks.append(task)

        try:
            # 等待所有任务完成（通常不会完成，除非出错）
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"❌ 监控出错: {e}")
        finally:
            # 清理所有驱动
            for monitor in self.monitors:
                monitor.cleanup_driver()
            await self.client.close()

    async def start(self):
        """启动监控器"""
        @self.client.event
        async def on_ready():
            """Discord客户端准备就绪"""
            await self.run_monitors()

        # 启动Discord客户端
        try:
            await self.client.start(self.bot_token)
        except discord.errors.LoginFailure:
            print("❌ Discord登录失败，请检查BOT_TOKEN是否正确")
        except Exception as e:
            print(f"❌ 程序运行出错: {e}")
        finally:
            # 清理所有驱动
            for monitor in self.monitors:
                monitor.cleanup_driver()
            print("👋 PopMart监控程序已退出")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='PopMart官网库存监控器 - Discord Bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
通知策略:
  正常模式: 检测到库存时持续通知，售罄时仅通知一次
  Verbose模式: 每次检查都发送通知，无论是否有库存

示例:
  python monitor.py                    # 正常模式监控
  python monitor.py --verbose          # 详细模式监控
        """)

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='启用详细通知模式 - 每次检查都发送Discord通知（无论是否有库存）'
    )

    return parser.parse_args()


def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()

    # 解析命令行参数
    args = parse_arguments()

    # 检查BOT_TOKEN
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        print("❌ 错误: 未找到BOT_TOKEN，请检查.env文件")
        return

    # 创建PopMart监控器
    monitor = PopMartMonitor(bot_token, verbose_mode=args.verbose)

    # 添加PopMart官网监控器
    monitor.add_official_monitor()

    # 显示启动信息
    mode_info = "🔍 Verbose模式 (每次检查都通知)" if args.verbose else "🎯 正常模式 (有库存时持续通知)"
    print(f"🚀 正在启动PopMart官网监控... | {mode_info}")

    # 启动监控
    try:
        asyncio.run(monitor.start())
    except KeyboardInterrupt:
        print("\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")


if __name__ == "__main__":
    main()
