import asyncio
import time
import discord
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from .base_monitor import BaseMonitor


class OfficialMonitor(BaseMonitor):
    """PopMart官网库存监控器"""

    def __init__(self, channel_id, product_url, min_interval, max_interval,
                 heartbeat_interval, notification_interval, verbose_mode=False):
        super().__init__(
            platform_name="PopMart Official",
            channel_id=channel_id,
            product_url=product_url,
            min_interval=min_interval,
            max_interval=max_interval,
            heartbeat_interval=heartbeat_interval,
            notification_interval=notification_interval,
            verbose_mode=verbose_mode
        )
        self.current_stock_status = False

    def extract_product_name_from_url(self, url):
        """从PopMart URL中提取商品名称"""
        try:
            import urllib.parse

            # PopMart URL格式处理
            parts = url.split('/')
            if len(parts) >= 5:
                product_part = parts[-1]
                product_name = urllib.parse.unquote(product_part)
                product_name = product_name.replace(
                    '-', ' ').replace('%20', ' ').replace('_', ' ')

                if '.' in product_name:
                    product_name = product_name.split('.')[0]

                # 首字母大写处理
                words = product_name.split()
                formatted_words = []
                for word in words:
                    if word.upper() == word and len(word) > 1:
                        formatted_words.append(word)
                    else:
                        formatted_words.append(word.capitalize())

                product_name = ' '.join(formatted_words)

                if len(product_name) > 60:
                    product_name = product_name[:60] + "..."

                return product_name if product_name.strip() else "PopMart Product"
            return "PopMart Product"
        except:
            return "PopMart Product"

    def extract_product_id_from_url(self, url):
        """从URL中提取产品ID (spuId)"""
        try:
            parts = url.split('/')
            if len(parts) >= 5 and 'products' in parts:
                products_index = parts.index('products')
                if products_index + 1 < len(parts):
                    product_id = parts[products_index + 1]
                    if product_id.isdigit():
                        return product_id
            return None
        except:
            return None

    def create_quick_checkout_url(self, spu_id, sku_id, product_title):
        """创建快速结算链接"""
        try:
            if not spu_id or not sku_id:
                return None

            import urllib.parse

            # 使用自定义的商品标题映射
            custom_titles = {
                '1149': 'Merbubu | Hide and Seek | 🐟',
            }

            display_title = custom_titles.get(spu_id, product_title)
            encoded_title = urllib.parse.quote(display_title)

            checkout_url = f"https://www.popmart.com/sg/order-confirmation?spuId={spu_id}&skuId={sku_id}&count=2&spuTitle={encoded_title}"
            return checkout_url
        except:
            return None

    async def check_stock_and_notify(self, client):
        """检查PopMart官网库存状态"""
        try:
            if self.driver is None:
                if not self.setup_driver():
                    return False

            # 访问PopMart产品页面
            print("🌐 正在访问PopMart产品页面...", end="", flush=True)
            self.driver.get(self.product_url)
            await asyncio.sleep(2)

            # 等待页面准备就绪
            WebDriverWait(self.driver, 20).until(
                lambda d: d.execute_script(
                    "return document.readyState") == "complete"
            )

            # 检查Cloudflare阻塞
            title = self.driver.title
            if "Just a moment" in title or "Access denied" in title:
                print(" ⛔ Cloudflare验证，刷新中...", end="", flush=True)
                self.driver.refresh()
                await asyncio.sleep(10)

            # 验证页面内容
            page_source = self.driver.page_source
            url_product_name = self.extract_product_name_from_url(
                self.product_url)
            key_words = url_product_name.split()[:2]

            page_valid = any(len(word) > 3 and word.upper()
                             in page_source.upper() for word in key_words)

            if not page_valid:
                print(f" ❌ 页面异常，未找到关键词: {key_words}")
                return False

            print(" ✅ 页面OK，检查库存中...", end="", flush=True)

            # 初始化变量
            stock_available = False
            button_text = ""
            product_price = "价格获取失败"
            product_image_url = None
            product_sku_id = None
            product_title = self.extract_product_name_from_url(
                self.product_url)
            product_spu_id = self.extract_product_id_from_url(self.product_url)

            # 获取产品价格
            try:
                price_selectors = [
                    "[class*='price']",
                    "[class*='Price']",
                    ".price-current",
                    ".price-now",
                    "[data-testid*='price']"
                ]

                for selector in price_selectors:
                    try:
                        price_elements = self.driver.find_elements(
                            By.CSS_SELECTOR, selector)
                        for element in price_elements:
                            text = element.text.strip()
                            if "S$" in text and any(char.isdigit() for char in text):
                                product_price = text
                                break
                        if "S$" in product_price:
                            break
                    except:
                        continue
            except:
                pass

            # 获取更准确的产品标题
            try:
                url_keywords = url_product_name.split()[:2]
                title_selectors = [
                    "h1",
                    "[class*='title']",
                    "[class*='Title']",
                    "[class*='name']",
                    "[class*='Name']"
                ]

                original_title = product_title
                for selector in title_selectors:
                    try:
                        title_elements = self.driver.find_elements(
                            By.CSS_SELECTOR, selector)
                        for element in title_elements:
                            text = element.text.strip()
                            if text and len(text) > 10:
                                text_upper = text.upper()
                                for keyword in url_keywords:
                                    if len(keyword) > 3 and keyword.upper() in text_upper:
                                        product_title = text
                                        break
                                if product_title != original_title:
                                    break
                        if product_title != original_title:
                            break
                    except:
                        continue
            except:
                pass

            # 获取SKU ID（仅支持LABUBU 1149）
            if product_spu_id == '1149':
                product_sku_id = '1755'

            # 获取产品图片
            try:
                # 优先使用PopMart CDN图片
                img_elements = self.driver.find_elements(By.TAG_NAME, "img")
                for img in img_elements:
                    src = img.get_attribute('src')
                    if src and 'prod-eurasian-res.popmart.com' in src:
                        product_image_url = src
                        break

                # 备用图片选择器
                if not product_image_url:
                    selectors = [
                        "img[style*='cursor: crosshair']",
                        "img[style*='display: block']",
                        "img[class*='product']"
                    ]
                    for selector in selectors:
                        try:
                            elements = self.driver.find_elements(
                                By.CSS_SELECTOR, selector)
                            if elements:
                                src = elements[0].get_attribute('src')
                                if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                                    if src.startswith('//'):
                                        src = 'https:' + src
                                    elif src.startswith('/'):
                                        src = 'https://www.popmart.com' + src
                                    product_image_url = src
                                    break
                        except:
                            continue
            except:
                pass

            # 检查库存状态
            try:
                # 查找购买按钮
                buy_elements = []
                try:
                    buy_elements = self.driver.find_elements(
                        By.XPATH, "//*[contains(text(), 'BUY NOW') or contains(text(), 'Buy Now') or contains(text(), 'ADD TO CART') or contains(text(), 'Add to Cart')]")

                    if buy_elements:
                        button_text = buy_elements[0].text.strip()

                        unavailable_keywords = [
                            "SOLD OUT", "OUT OF STOCK", "NOTIFY ME", "COMING SOON"]
                        if any(keyword in button_text.upper() for keyword in unavailable_keywords):
                            stock_available = False
                        else:
                            stock_available = True

                except:
                    pass

                # CSS选择器备用方案
                if not buy_elements:
                    button_selectors = [
                        "button[class*='buy']", "div[class*='buy']", "[class*='add-to-cart']",
                        "[class*='purchase']", ".btn-primary", ".btn-buy"
                    ]

                    for selector in button_selectors:
                        try:
                            elements = self.driver.find_elements(
                                By.CSS_SELECTOR, selector)
                            for element in elements:
                                text = element.text.strip().upper()
                                if any(keyword in text for keyword in ["BUY", "CART", "PURCHASE"]):
                                    button_text = text
                                    stock_available = not any(keyword in text for keyword in [
                                                              "SOLD OUT", "OUT OF STOCK"])
                                    break
                            if button_text:
                                break
                        except:
                            continue

                # 页面文本分析
                if not button_text:
                    page_text = page_source.upper()
                    if "SOLD OUT" in page_text or "OUT OF STOCK" in page_text:
                        stock_available = False
                        button_text = "SOLD OUT"
                    elif "BUY NOW" in page_text or "ADD TO CART" in page_text:
                        stock_available = True
                        button_text = "BUY NOW"
                    else:
                        stock_available = False
                        button_text = "未知状态"

            except Exception as e:
                print(f" ❌ 库存检查出错: {e}", end="")
                stock_available = False
                button_text = "检查出错"

            # 更新当前库存状态
            self.current_stock_status = stock_available

            # 显示附加信息
            price_short = product_price.replace("价格获取失败", "价格失败")
            print(f" | 💰{price_short}")

            # 判断是否需要通知
            should_notify, notification_title = self.should_notify()

            if stock_available:
                print(" 🎉 PopMart有库存！", end="")
                if should_notify:
                    print(" [库存通知]", end="")
            else:
                print(f" ❌ {button_text}", end="")
                if should_notify:
                    if self.last_stock_status != stock_available:
                        print(" [售罄通知]", end="")
                    elif self.verbose_mode:
                        print(" [Verbose通知]", end="")
                    else:
                        print(" [心跳通知]", end="")

            self.last_stock_status = stock_available

            if not should_notify:
                return False

            # 发送Discord通知
            channel = client.get_channel(self.channel_id)
            if channel:
                # 创建Discord embed
                embed = discord.Embed(
                    title=notification_title,
                    description=f"**Store:** popmart.com/SG",
                    color=0xff6b6b  # 红色
                )

                embed.add_field(
                    name="📦 In-Stock Item",
                    value=product_title,
                    inline=False
                )

                embed.add_field(
                    name="💰 Price",
                    value=product_price,
                    inline=True
                )

                embed.add_field(
                    name="📊 Status",
                    value=button_text,
                    inline=True
                )

                # 创建快速结算URL
                quick_checkout_url = None
                if product_spu_id and product_sku_id:
                    quick_checkout_url = self.create_quick_checkout_url(
                        product_spu_id, product_sku_id, product_title)

                # 构建链接文本
                links_text = f"[Product Link]({self.product_url})"
                if quick_checkout_url:
                    links_text += f"\n[Checkout Page]({quick_checkout_url})"

                embed.add_field(
                    name="🛒 Quick Links",
                    value=links_text,
                    inline=False
                )

                embed.add_field(
                    name="🔔 Alert",
                    value="**Go Go Go!** Limited stock available.",
                    inline=False
                )

                # 添加产品图片
                if product_image_url:
                    embed.set_thumbnail(url=product_image_url)

                # 添加时间戳和页脚
                embed.set_footer(
                    text=f"PopMart Monitor by FK_popmart | {time.strftime('%Y-%m-%d %H:%M:%S')}")

                # 发送通知
                mention_message = "@here"
                await channel.send(content=mention_message, embed=embed)
                return True
            else:
                print(f"❌ 找不到Discord频道: {self.channel_id}")
                return False

        except TimeoutException:
            print("⏰ PopMart页面加载超时")
            return False
        except WebDriverException as e:
            print(f"🔧 浏览器错误: {e}")
            self.cleanup_driver()
            return False
        except Exception as e:
            print(f"❌ PopMart检查出错: {e}")
            return False
