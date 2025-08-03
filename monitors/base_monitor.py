import asyncio
import random
import time
import logging
from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class BaseMonitor(ABC):
    """基础监控类，定义所有监控器的通用接口和功能"""

    def __init__(self, platform_name, channel_id, product_url, min_interval, max_interval,
                 heartbeat_interval, notification_interval, page_load_timeout=25,
                 page_load_wait=3, js_render_wait=5, cloudflare_wait=10, verbose_mode=False):
        self.platform_name = platform_name
        self.channel_id = channel_id
        self.product_url = product_url
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.heartbeat_interval = heartbeat_interval
        self.notification_interval = notification_interval
        self.page_load_timeout = page_load_timeout
        self.page_load_wait = page_load_wait
        self.js_render_wait = js_render_wait
        self.cloudflare_wait = cloudflare_wait
        self.verbose_mode = verbose_mode

        # 状态跟踪
        self.last_stock_status = None
        self.last_heartbeat_time = 0
        self.last_stock_notification_time = 0
        self.driver = None

        # 配置日志
        self.setup_logging()

    def setup_logging(self):
        """设置日志配置"""
        # 禁用外部日志以减少干扰
        logging.getLogger('discord').setLevel(logging.WARNING)
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('WDM').setLevel(logging.WARNING)

    def setup_driver(self):
        """设置Chrome驱动"""
        try:
            options = Options()

            # 基础无头操作选项
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')

            # 反检测选项
            options.add_argument(
                '--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-images')  # 更快加载
            options.add_experimental_option(
                'excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)

            # 随机用户代理
            user_agents = [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            ]
            selected_ua = random.choice(user_agents)
            options.add_argument(f'--user-agent={selected_ua}')

            # 设置服务
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

            # 执行反检测脚本
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logging.info(f"{self.platform_name}浏览器驱动设置成功")
            return True

        except Exception as e:
            logging.error(f"{self.platform_name}浏览器驱动设置失败: {e}")
            return False

    def cleanup_driver(self):
        """清理驱动"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            logging.info(f"{self.platform_name}浏览器驱动已清理")

    @abstractmethod
    async def check_stock_and_notify(self, client):
        """检查库存并通知 - 子类必须实现"""
        pass

    @abstractmethod
    def extract_product_name_from_url(self, url):
        """从URL提取产品名称 - 子类必须实现"""
        pass

    async def monitor_loop(self, client):
        """主监控循环"""
        check_count = 0

        try:
            while not client.is_closed():
                check_count += 1
                current_time = time.strftime('%H:%M:%S')
                print(
                    f"\n📊 [{self.platform_name}] #{check_count} [{current_time}]", end="")

                await self.check_stock_and_notify(client)

                # 随机等待时间
                wait_time = random.uniform(
                    self.min_interval, self.max_interval)
                print(f" ⏰ 等待{wait_time:.1f}s...")
                await asyncio.sleep(wait_time)

        except Exception as e:
            logging.error(f"{self.platform_name}监控循环出错: {e}")
        finally:
            self.cleanup_driver()

    def should_notify(self):
        """判断是否应该发送通知"""
        current_time = time.time()

        # 检查库存状态是否改变
        stock_status_changed = (
            self.last_stock_status is not None and
            self.last_stock_status != self.current_stock_status
        )

        if self.current_stock_status:
            # 有库存时的通知策略
            if (stock_status_changed or
                    current_time - self.last_stock_notification_time > self.notification_interval):
                self.last_stock_notification_time = current_time
                return True, "🚨 Restock Detected 🚨" if stock_status_changed else "⚡ Stock Still Available ⚡"
        else:
            # 无库存时的通知策略
            if stock_status_changed:
                return True, "📉 Stock Sold Out 📉"
            elif self.verbose_mode:
                return True, f"📊 {self.platform_name} Stock Check"
            # 移除心跳通知，只在状态变化时通知

        return False, ""
