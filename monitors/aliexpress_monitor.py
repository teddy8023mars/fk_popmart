import asyncio
import time
import discord
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException
from .base_monitor import BaseMonitor


class AliExpressMonitor(BaseMonitor):
    """AliExpress库存监控器"""

    def __init__(self, channel_id, product_url, min_interval, max_interval,
                 heartbeat_interval, notification_interval, verbose_mode=False):
        super().__init__(
            platform_name="AliExpress",
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
        """从AliExpress URL中提取商品名称"""
        try:
            import urllib.parse

            # AliExpress URL通常包含商品ID
            parts = url.split('/')
            if 'item' in parts:
                item_index = parts.index('item')
                if item_index + 1 < len(parts):
                    item_part = parts[item_index + 1].split('.')[0]  # 移除.html
                    return f"AliExpress Item {item_part}"

            return "AliExpress Product"
        except:
            return "AliExpress Product"

    async def check_stock_and_notify(self, client):
        """检查AliExpress库存状态"""
        try:
            if self.driver is None:
                if not self.setup_driver():
                    return False

            # 访问AliExpress产品页面
            print("🌐 正在访问AliExpress产品页面...", end="", flush=True)
            self.driver.get(self.product_url)
            await asyncio.sleep(4)  # AliExpress需要更多时间加载

            # 等待页面准备就绪
            WebDriverWait(self.driver, 30).until(
                lambda d: d.execute_script(
                    "return document.readyState") == "complete"
            )

            # 检查各种阻塞场景
            title = self.driver.title.lower()
            if any(keyword in title for keyword in ["robot", "captcha", "blocked", "access denied"]):
                print(" ⛔ 页面被阻止，刷新中...", end="", flush=True)
                self.driver.refresh()
                await asyncio.sleep(8)

            print(" ✅ 页面OK，检查库存中...", end="", flush=True)

            # 初始化变量
            stock_available = False
            button_text = ""
            product_price = "价格获取失败"
            product_image_url = None
            product_title = self.extract_product_name_from_url(
                self.product_url)

            # 获取页面产品标题
            try:
                title_selectors = [
                    "h1[data-pl='product-title']",
                    "h1.product-title",
                    ".product-title-text",
                    "h1[class*='title']",
                    ".pdp-product-name",
                    "h1"
                ]

                for selector in title_selectors:
                    try:
                        title_elements = self.driver.find_elements(
                            By.CSS_SELECTOR, selector)
                        for element in title_elements:
                            text = element.text.strip()
                            if text and len(text) > 10 and len(text) < 200:
                                product_title = text
                                break
                        if product_title != self.extract_product_name_from_url(self.product_url):
                            break
                    except:
                        continue
            except:
                pass

            # 等待页面完全加载 - 特别是JavaScript内容
            try:
                # 额外等待JavaScript内容加载
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script(
                        "return document.readyState") == "complete"
                )
                time.sleep(3)  # 额外等待JavaScript渲染

                # 验证页面是否正确加载
                page_title = self.driver.title
                current_url = self.driver.current_url
                if self.verbose_mode:
                    print(f" 📄 标题: '{page_title[:30]}'", end="")
                    print(f" 🌐 URL: {current_url[-30:]}...", end="")

                # 检查页面是否正确加载了产品内容
                body_text = self.driver.find_element(By.TAG_NAME, "body").text

                # 检查页面长度和内容质量
                if len(body_text) < 2000:
                    print(f" ⚠️ 页面内容过少({len(body_text)}字符)", end="")

                # 检查是否包含产品相关内容
                product_indicators = ["add to cart", "buy now", "price",
                                      "description", "seller", "reviews", "立即购买", "加入购物车"]
                has_product_content = any(
                    indicator in body_text.lower() for indicator in product_indicators)

                if not has_product_content:
                    print(f" ❌ 页面缺少产品内容，可能产品已下架或URL失效", end="")

                # 检查是否遇到明确的错误页面
                body_lower = body_text.lower()
                if any(error in body_lower for error in ["not found", "404", "error", "无法找到", "页面不存在"]):
                    print(f" ❌ 页面错误：产品不存在", end="")

                # 等待JavaScript渲染价格信息
                time.sleep(5)  # 额外等待JavaScript加载价格

                # 检查页面上是否有任何价格相关的文本 (排除script标签)
                if self.verbose_mode:
                    # 搜索页面上任何包含SG$或$的可见文本 (排除script和style标签)
                    sgd_elements = self.driver.find_elements(
                        By.XPATH, "//*[not(self::script) and not(self::style) and (contains(text(), 'SG$') or contains(text(), '$'))]")
                    print(f" 💲 可见SG$/USD元素: {len(sgd_elements)}个", end="")

                    if sgd_elements:
                        # 显示前5个找到的价格元素
                        for i, elem in enumerate(sgd_elements[:5]):
                            try:
                                text = elem.text.strip()
                                inner_html = elem.get_attribute('innerHTML')
                                tag_name = elem.tag_name
                                class_name = elem.get_attribute('class')

                                if text:
                                    print(
                                        f" 💰{i+1}[{tag_name}]: '{text}'", end="")
                                elif inner_html and len(inner_html) < 100:
                                    print(
                                        f" 🏷️{i+1}[{tag_name}]: {inner_html[:30]}...", end="")
                                else:
                                    print(
                                        f" 📝{i+1}[{tag_name}.{class_name[:20]}]: 无文本", end="")
                            except Exception as e:
                                print(f" ❌{i+1}: {e}", end="")
                                continue

            except Exception as e:
                if self.verbose_mode:
                    print(f" ⚠️ 页面加载验证失败: {e}", end="")

            # 获取产品价格 - 使用完整的多层级策略
            try:
                # Priority 1: 主要价格选择器
                price_selectors = [
                    # 用户提供的具体价格选择器 - 最高优先级
                    ".price-default--current--F8OlYIo",
                    "[class*='price-default--current']",
                    ".price-default--wrap--uwQneeq .price-default--current--F8OlYIo",
                    "[class*='price-default--wrap'] [class*='price-default--current']",

                    # 通用价格选择器
                    ".pdp-price_color_orange",
                    ".product-price-current",
                    "[class*='price-current']",
                    ".price-now",
                    "[data-pl='price']",
                    ".notranslate[dir='ltr']",

                    # 新增的AliExpress价格选择器
                    "[class*='pdp-price']",
                    "[class*='product-price']",
                    "[class*='price-default']",
                    ".price-sale",
                    ".price-discount",
                    ".sku-price",
                    "[class*='price-info']",
                    "[class*='sale-price']",
                    ".comet-v2-price",
                    "[class*='comet-v2-price']"
                ]

                for i, selector in enumerate(price_selectors):
                    try:
                        price_elements = self.driver.find_elements(
                            By.CSS_SELECTOR, selector)
                        if self.verbose_mode and price_elements:
                            print(
                                f" 🔍 选择器{i+1}({selector[:15]}): 找到{len(price_elements)}个元素", end="")

                        for element in price_elements:
                            try:
                                text = element.text.strip()
                                if self.verbose_mode and text:
                                    print(f" 📝 文本: '{text[:20]}'", end="")

                                if text and any(currency in text for currency in ["$", "€", "£", "¥", "₽", "¢", "CA$", "US$", "AUD", "SGD"]) and any(char.isdigit() for char in text):
                                    product_price = text
                                    if self.verbose_mode:
                                        print(f" ✅ 价格匹配: {text}", end="")
                                    break
                            except Exception as e:
                                if self.verbose_mode:
                                    print(f" ⚠️ 元素文本获取失败: {e}", end="")
                                continue

                        if product_price != "价格获取失败":
                            break
                    except Exception as e:
                        if self.verbose_mode:
                            print(f" ❌ 选择器{i+1}失败: {e}", end="")
                        continue

                # Priority 2: XPath备用方案
                if product_price == "价格获取失败":
                    try:
                        price_elements = self.driver.find_elements(
                            By.XPATH, "//*[contains(text(), '$') or contains(text(), '€') or contains(text(), '£') or contains(text(), '¥') or contains(text(), 'CA$') or contains(text(), 'US$')]")
                        for element in price_elements:
                            text = element.text.strip()
                            if text and any(currency in text for currency in ["$", "€", "£", "¥", "₽", "CA$", "US$"]) and any(char.isdigit() for char in text) and len(text) < 30:
                                # 过滤掉明显不是价格的文本
                                if not any(skip in text.lower() for skip in ['shipping', 'delivery', 'save', 'off', 'discount', 'coupon', 'code']):
                                    product_price = text
                                    if self.verbose_mode:
                                        print(f" 🏷️ XPath价格: {text}", end="")
                                    break
                    except Exception as e:
                        if self.verbose_mode:
                            print(f" ⚠️ XPath价格查找失败: {e}", end="")
                        pass

                # Priority 3: 通用货币符号查找
                if product_price == "价格获取失败":
                    try:
                        # 查找所有包含货币符号的可见元素
                        all_elements = self.driver.find_elements(
                            By.XPATH, "//*[text()]")
                        currency_elements = []

                        for element in all_elements:
                            try:
                                text = element.text.strip()
                                if (text and
                                    any(currency in text for currency in ["$", "€", "£", "¥", "₽", "SGD", "USD"]) and
                                    any(char.isdigit() for char in text) and
                                    len(text) < 50 and  # 限制长度
                                        element.is_displayed()):  # 确保元素可见

                                    # 进一步过滤
                                    text_lower = text.lower()
                                    if not any(skip in text_lower for skip in [
                                        'shipping', 'delivery', 'save', 'off', 'discount',
                                        'coupon', 'code', 'total', 'subtotal', 'tax', 'fee',
                                        'minimum', 'maximum', 'range', 'from', 'to'
                                    ]):
                                        currency_elements.append(
                                            (text, element))

                            except:
                                continue

                        if self.verbose_mode:
                            print(
                                f" 💰 找到{len(currency_elements)}个货币元素", end="")

                        # 选择最可能的价格元素（较短的文本优先）
                        if currency_elements:
                            currency_elements.sort(key=lambda x: len(x[0]))
                            product_price = currency_elements[0][0]
                            if self.verbose_mode:
                                print(f" ✅ 通用价格: {product_price}", end="")

                    except Exception as e:
                        if self.verbose_mode:
                            print(f" ⚠️ 通用价格查找失败: {e}", end="")
                        pass

                # Priority 4: JavaScript价格获取
                if product_price == "价格获取失败":
                    try:
                        js_scripts = [
                            # AliExpress价格模块数据
                            "return window.runParams && window.runParams.data && window.runParams.data.priceModule && window.runParams.data.priceModule.formatedPrice;",
                            "return window.runParams && window.runParams.data && window.runParams.data.priceModule && window.runParams.data.priceModule.currentPrice;",
                            "return window.runParams && window.runParams.data && window.runParams.data.priceModule && window.runParams.data.priceModule.minActivityAmount && window.runParams.data.priceModule.minActivityAmount.formatedAmount;",

                            # 查找具体的价格default选择器
                            "return document.querySelector('.price-default--current--F8OlYIo') && document.querySelector('.price-default--current--F8OlYIo').textContent;",
                            "return document.querySelector('[class*=\"price-default--current\"]') && document.querySelector('[class*=\"price-default--current\"]').textContent;",

                            # 通用价格查找
                            "return Array.from(document.querySelectorAll('*:not(script):not(style)')).find(el => el.textContent && /SG\\$\\d/.test(el.textContent)) && Array.from(document.querySelectorAll('*:not(script):not(style)')).find(el => el.textContent && /SG\\$\\d/.test(el.textContent)).textContent.trim();",
                            "return Array.from(document.querySelectorAll('span, div')).find(el => el.textContent && /\\$\\d+\\.\\d+/.test(el.textContent) && el.offsetParent !== null) && Array.from(document.querySelectorAll('span, div')).find(el => el.textContent && /\\$\\d+\\.\\d+/.test(el.textContent) && el.offsetParent !== null).textContent.trim();"
                        ]

                        for i, script in enumerate(js_scripts):
                            try:
                                result = self.driver.execute_script(script)
                                if result and isinstance(result, str) and any(currency in result for currency in ["$", "€", "£", "¥", "₽"]):
                                    product_price = result.strip()
                                    if self.verbose_mode:
                                        print(
                                            f" 🔧 JS价格{i+1}: {product_price}", end="")
                                    break
                            except Exception as e:
                                if self.verbose_mode:
                                    print(f" ⚠️ JS脚本{i+1}失败: {e}", end="")
                                continue
                    except:
                        pass

            except Exception as e:
                if self.verbose_mode:
                    print(f" ❌ 价格获取整体错误: {e}", end="")
                pass

            # 获取产品图片 - 使用完整的多层级策略
            try:
                # Priority 1: 指定的图片组件结构
                magnifier_selectors = [
                    # 完整的选择器路径
                    ".image-view-v2--previewBox--yPlyD6F .magnifier--wrap--qjbuwmt img.magnifier--image--RM17RL2",
                    ".image-view-v2--previewBox--yPlyD6F img.magnifier--image--RM17RL2",
                    "img.magnifier--image--RM17RL2.magnifier--zoom--zzDgZB8",
                    "img.magnifier--image--RM17RL2",

                    # 通用的magnifier图片选择器
                    ".magnifier--wrap--qjbuwmt img",
                    ".image-view-v2--previewBox--yPlyD6F img",
                    "div[class*='magnifier--wrap'] img",
                    "div[class*='image-view-v2--previewBox'] img"
                ]

                for selector in magnifier_selectors:
                    try:
                        img_elements = self.driver.find_elements(
                            By.CSS_SELECTOR, selector)
                        for img in img_elements:
                            src = img.get_attribute('src')
                            if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.avif']):
                                # 确保是完整的URL
                                if src.startswith('//'):
                                    src = 'https:' + src
                                elif src.startswith('/'):
                                    src = 'https://www.aliexpress.com' + src

                                # 过滤掉小尺寸图片
                                if any(size in src.lower() for size in ['72x72', '50x50', '100x100', '24x24', '154x64', '_mini', '_thumb']):
                                    if self.verbose_mode:
                                        print(
                                            f" 🚫 跳过小图: {src.split('/')[-1]}", end="")
                                    continue

                                # 验证图片URL的有效性 - 支持新的aliexpress-media.com域名
                                if 'alicdn.com' in src or 'aliexpress.com' in src or 'aliexpress-media.com' in src:
                                    # 优先选择.avif格式和高质量图片
                                    is_high_quality = (
                                        '.avif' in src.lower() or
                                        '_960x960' in src.lower() or
                                        '_220x220' in src.lower() or
                                        'q75' in src.lower() or
                                        'q80' in src.lower() or
                                        'q90' in src.lower()
                                    )

                                    # 如果当前没有图片或找到了更高质量的图片，则更新
                                    if not product_image_url or is_high_quality:
                                        product_image_url = src
                                        print(
                                            f" 📸 找到{'高质量' if is_high_quality else ''}magnifier图片", end="")
                                        if is_high_quality:
                                            break  # 找到高质量图片就停止

                        if product_image_url:
                            break
                    except Exception as e:
                        if self.verbose_mode:
                            print(
                                f" ⚠️ magnifier选择器 {selector[:30]} 失败: {e}", end="")
                        continue

                # Priority 2: 备用图片选择器（如果magnifier没找到）
                if not product_image_url:
                    fallback_selectors = [
                        "img[class*='magnifier-image']",
                        ".pdp-main-image img",
                        ".gallery-main-image img",
                        "img[data-pl='gallery-image']",
                        ".product-image img",
                        # 通用的产品图片选择器
                        "img[src*='alicdn.com']",
                        "img[alt*='product']",
                        "img[alt*='item']"
                    ]

                    for selector in fallback_selectors:
                        try:
                            img_elements = self.driver.find_elements(
                                By.CSS_SELECTOR, selector)
                            for img in img_elements:
                                src = img.get_attribute('src')
                                if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.avif']):
                                    # 确保是完整的URL
                                    if src.startswith('//'):
                                        src = 'https:' + src
                                    elif src.startswith('/'):
                                        src = 'https://www.aliexpress.com' + src

                                    # 过滤掉小尺寸图片
                                    if any(size in src.lower() for size in ['72x72', '50x50', '100x100', '24x24', '_mini', '_thumb']):
                                        if self.verbose_mode:
                                            print(
                                                f" 🚫 跳过备用小图: {src.split('/')[-1]}", end="")
                                        continue

                                    # 过滤掉明显的非产品图片
                                    if any(skip in src.lower() for skip in ['icon', 'logo', 'avatar', 'banner']):
                                        continue

                                    product_image_url = src
                                    print(f" 📸 备用图片", end="")
                                    break

                            if product_image_url:
                                break
                        except:
                            continue

                # Priority 3: JavaScript获取图片（最后手段）
                if not product_image_url:
                    try:
                        # 尝试从页面的JavaScript变量中获取图片URL
                        js_scripts = [
                            "return window.runParams && window.runParams.data && window.runParams.data.imageModule && window.runParams.data.imageModule.imagePathList && window.runParams.data.imageModule.imagePathList[0];",
                            "return document.querySelector('img[src*=\"alicdn.com\"]') && document.querySelector('img[src*=\"alicdn.com\"]').src;",
                            "return Array.from(document.querySelectorAll('img')).find(img => img.src && img.src.includes('alicdn.com') && img.width > 100 && img.height > 100) && Array.from(document.querySelectorAll('img')).find(img => img.src && img.src.includes('alicdn.com') && img.width > 100 && img.height > 100).src;"
                        ]

                        for script in js_scripts:
                            try:
                                result = self.driver.execute_script(script)
                                if result and isinstance(result, str) and any(ext in result.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.avif']):
                                    if result.startswith('//'):
                                        result = 'https:' + result
                                    product_image_url = result
                                    print(f" 📸 JS获取图片", end="")
                                    break
                            except:
                                continue
                    except:
                        pass

            except Exception as e:
                print(f" ❌ 图片获取错误: {e}", end="")
                pass

            # 检查库存状态
            try:
                # 查找特定的Buy Now按钮
                buy_button_selectors = [
                    "button.comet-v2-btn.comet-v2-btn-primary.comet-v2-btn-large.buy-now--buynow--OH44OI8",
                    "button[class*='buy-now--buynow']",
                    "button.comet-v2-btn-primary[class*='buy-now']",
                    "button.comet-v2-btn.comet-v2-btn-primary.comet-v2-btn-large",
                    "button[class*='comet-v2-btn-primary']",
                    "button[class*='buy-now']"
                ]

                button_found = False
                for selector in buy_button_selectors:
                    try:
                        buttons = self.driver.find_elements(
                            By.CSS_SELECTOR, selector)
                        for button in buttons:
                            if button.is_displayed():
                                button_inner_text = button.text.strip().upper()
                                button_html = button.get_attribute(
                                    'innerHTML').upper()

                                buy_keywords = [
                                    'BUY NOW', 'BUY', 'ADD TO CART', 'CART', '立即购买', '加入购物车']

                                if any(keyword in button_inner_text for keyword in buy_keywords) or \
                                   any(keyword in button_html for keyword in buy_keywords):

                                    is_disabled = button.get_attribute(
                                        'disabled')
                                    is_clickable = button.is_enabled()

                                    if not is_disabled and is_clickable:
                                        stock_available = True
                                        button_text = button_inner_text if button_inner_text else "BUY NOW"
                                        button_found = True
                                        print(f" 🎯 找到可用按钮", end="")
                                        break

                        if button_found:
                            break
                    except:
                        continue

                # 如果没找到按钮，检查缺货标识
                if not button_found:
                    page_source = self.driver.page_source
                    if any(phrase in page_source for phrase in [
                        "out of stock", "sold out", "unavailable", "缺货", "售罄"
                    ]):
                        stock_available = False
                        button_text = "SOLD OUT"
                        print(" 📄 页面文本显示缺货", end="")
                    else:
                        stock_available = False
                        button_text = "状态未知"
                        print(" ❓ 无法确定库存状态", end="")

            except Exception as e:
                print(f" ❌ 库存检查出错: {e}", end="")
                stock_available = False
                button_text = f"检查出错"

            # 最后检查：智能图片替换逻辑
            try:
                specific_imgs = self.driver.find_elements(
                    By.CSS_SELECTOR, "img.magnifier--image--RM17RL2")
                if specific_imgs and specific_imgs[0].get_attribute('src'):
                    magnifier_src = specific_imgs[0].get_attribute('src')

                    # 如果当前图片是小尺寸或者没有找到图片，使用magnifier中的大图
                    if (not product_image_url or
                        any(size in product_image_url.lower() for size in ['20x20', '24x24', '72x72', '50x50', '100x100', '_mini', '_thumb']) and
                        magnifier_src and
                            not any(size in magnifier_src.lower() for size in ['20x20', '24x24', '72x72', '50x50', '100x100', '_mini', '_thumb'])):

                        if self.verbose_mode:
                            old_url = product_image_url[:50] if product_image_url else "无"
                            new_url = magnifier_src[:50]
                            print(f" 🔄 替换图片: {old_url} -> {new_url}", end="")

                        product_image_url = magnifier_src

                    elif self.verbose_mode and product_image_url:
                        print(f" ✅ 图片质量OK: {product_image_url[:50]}", end="")
            except:
                pass

            # 更新当前库存状态
            self.current_stock_status = stock_available

            # 显示附加信息
            if product_price == "价格获取失败":
                price_short = "⚠️N/A"
            else:
                price_short = product_price

            # 在verbose模式下添加图片组件调试信息
            if self.verbose_mode:
                try:
                    # 检查主容器
                    preview_boxes = self.driver.find_elements(
                        By.CSS_SELECTOR, ".image-view-v2--previewBox--yPlyD6F")
                    print(f" | 📦 previewBox: {len(preview_boxes)}个", end="")

                    # 检查magnifier wrapper
                    magnifier_wraps = self.driver.find_elements(
                        By.CSS_SELECTOR, ".magnifier--wrap--qjbuwmt")
                    print(
                        f" | 🔧 magnifierWrap: {len(magnifier_wraps)}个", end="")

                    # 检查实际的图片元素
                    specific_imgs = self.driver.find_elements(
                        By.CSS_SELECTOR, "img.magnifier--image--RM17RL2")
                    if specific_imgs:
                        print(f" | 🎯 指定图片: 找到({len(specific_imgs)}张)", end="")
                        # 显示第一张图片的src前50个字符
                        if specific_imgs[0].get_attribute('src'):
                            magnifier_src = specific_imgs[0].get_attribute(
                                'src')
                            src_preview = magnifier_src[:50]
                            print(f" | src:{src_preview}...", end="")

                            # 如果当前找到的图片比magnifier中的图片小，替换它
                            if product_image_url and any(size in product_image_url.lower() for size in ['24x24', '72x72', '50x50', '100x100']):
                                print(f" | 🔄 替换小图为magnifier大图", end="")
                                # 注意：这里只是显示调试信息，实际替换在所有模式下都应该进行
                    else:
                        print(f" | ❌ 指定图片: 未找到", end="")

                    # 检查覆盖层元素
                    behiver_divs = self.driver.find_elements(
                        By.CSS_SELECTOR, "div.magnifier--behiver--cY4D2TR")
                    print(f" | 🎭 覆盖层: {len(behiver_divs)}个", end="")
                except:
                    pass

            print(f" | 💰{price_short}")

            # 判断是否需要通知
            should_notify, notification_title = self.should_notify()

            if stock_available:
                print(" 🎉 AliExpress有库存！", end="")
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
                    description=f"**Store:** AliExpress",
                    color=0xff4747  # AliExpress红色
                )

                embed.add_field(
                    name="📦 Product",
                    value=product_title[:1000] if len(
                        product_title) > 1000 else product_title,
                    inline=False
                )

                # 价格字段 - 根据页面状态提供具体的失败提示
                if product_price == "价格获取失败":
                    # 检查页面内容来确定具体问题
                    try:
                        body_text = self.driver.find_element(
                            By.TAG_NAME, "body").text
                        if len(body_text) < 2000:
                            price_display = "❌ **产品页面异常**\n*页面内容过少，产品可能已下架*"
                        else:
                            price_display = "⚠️ 价格暂不可用\n*可能原因：地区限制、页面更新或反爬虫*"
                    except:
                        price_display = "⚠️ 价格暂不可用\n*页面访问异常*"
                else:
                    price_display = product_price

                embed.add_field(
                    name="💰 Price",
                    value=price_display,
                    inline=True
                )

                embed.add_field(
                    name="📊 Status",
                    value=button_text,
                    inline=True
                )

                embed.add_field(
                    name="🛒 Product Link",
                    value=f"[View on AliExpress]({self.product_url})",
                    inline=False
                )

                embed.add_field(
                    name="🔔 Alert",
                    value="**Limited time offer!** Check AliExpress for details.",
                    inline=False
                )

                # 添加产品图片 - 增强调试和验证
                if product_image_url:
                    # 详细的图片URL调试
                    if self.verbose_mode:
                        print(f"\n🖼️ 完整图片URL: {product_image_url}")

                    # 验证图片URL格式
                    if product_image_url.startswith('https://'):
                        embed.set_thumbnail(url=product_image_url)
                        if self.verbose_mode:
                            print(f"✅ 图片已设置到Discord embed")
                    else:
                        print(f"❌ 图片URL格式不正确: {product_image_url}")
                else:
                    print(f"\n❌ 没有找到有效的图片URL")

                # 添加时间戳和页脚
                embed.set_footer(
                    text=f"AliExpress Monitor by FK_popmart | {time.strftime('%Y-%m-%d %H:%M:%S')}")

                # 发送通知
                mention_message = "@here"
                await channel.send(content=mention_message, embed=embed)
                return True
            else:
                print(f"❌ 找不到Discord频道: {self.channel_id}")
                return False

        except TimeoutException:
            print("⏰ AliExpress页面加载超时")
            return False
        except WebDriverException as e:
            print(f"🔧 浏览器错误: {e}")
            self.cleanup_driver()
            return False
        except Exception as e:
            print(f"❌ AliExpress检查出错: {e}")
            return False
