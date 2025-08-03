# 多平台库存监控器

一个支持同时监控多个平台的Discord库存监控机器人，目前支持AliExpress和PopMart官网。

## 🎯 功能特性

- ✅ **多平台同时监控** - 支持AliExpress和PopMart官网并发监控
- ✅ **模块化设计** - 每个平台独立的监控模块，易于扩展
- ✅ **环境变量配置** - 敏感信息安全存储在.env文件中
- ✅ **灵活的命令行参数** - 可选择监控单个或多个平台
- ✅ **智能通知策略** - 库存变化时立即通知，无库存时定期心跳
- ✅ **高质量图片显示** - 自动获取产品的高清图片（支持.avif格式）
- ✅ **增强反爬虫机制** - 内置多种反检测措施
- ✅ **智能价格获取** - 多层级价格检测策略，支持多种货币

## 🚀 快速开始

### 1. 创建Discord机器人

#### 步骤1：创建Discord应用程序
1. 访问 [Discord Developer Portal](https://discord.com/developers/applications)
2. 点击 **"New Application"** 创建新应用
3. 输入应用名称（如：`PopMart Monitor`）
4. 点击 **"Create"** 创建应用

#### 步骤2：创建机器人
1. 在左侧导航栏点击 **"Bot"**
2. 点击 **"Add Bot"** 按钮
3. 确认创建机器人

#### 步骤3：获取BOT_TOKEN
1. 在Bot页面找到 **"Token"** 部分  
2. 点击 **"Reset Token"** 按钮
3. **复制并保存Token**（这就是你的`BOT_TOKEN`）
4. ⚠️ **重要**：Token只显示一次，请妥善保存！

#### 步骤4：设置机器人权限
在Bot页面确保启用以下权限：
- ✅ **Send Messages** - 发送消息
- ✅ **Use Slash Commands** - 使用斜杠命令  
- ✅ **Embed Links** - 嵌入链接
- ✅ **Attach Files** - 附加文件
- ✅ **Use External Emojis** - 使用外部表情
- ✅ **Mention Everyone** - @everyone和@here通知

#### 步骤5：邀请机器人到服务器
1. 在左侧导航栏点击 **"OAuth2"** → **"URL Generator"**
2. 在 **"Scopes"** 部分选择：
   - ✅ `bot`
   - ✅ `applications.commands`
3. 在 **"Bot Permissions"** 部分选择：
   - ✅ Send Messages
   - ✅ Use Slash Commands
   - ✅ Embed Links
   - ✅ Attach Files
   - ✅ Use External Emojis
   - ✅ Mention Everyone
4. 复制生成的URL并在浏览器中打开
5. 选择你的服务器并点击 **"Authorize"**

#### 步骤6：获取频道ID
1. 在Discord中，进入 **用户设置** → **高级** → 启用 **"开发者模式"**
2. 右键点击你要监控的频道
3. 点击 **"复制频道ID"**
4. 这个ID就是你的 `CHANNEL_ID`

### 2. 环境要求

- Python 3.8+
- Chrome浏览器（用于Selenium）  
- Discord服务器管理员权限（用于添加机器人）
- 稳定的网络连接

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

创建 `.env` 文件并配置以下变量（可以复制 `.env.example` 文件作为模板）：

```bash
# 复制模板文件
cp .env.example .env
# 然后编辑 .env 文件，填入你的真实配置
```

```env
# Discord Bot Configuration
BOT_TOKEN=MTIzNDU2Nzg5MDEyMzQ1Njc4OS5GaWN0aW9uYWwuVG9rZW5Gb3JFeGFtcGxl

# Channel IDs for different platforms
ALIEXPRESS_CHANNEL_ID=1234567890123456789
OFFICIAL_CHANNEL_ID=9876543210987654321

# Product URLs to monitor
ALIEXPRESS_PRODUCT_URL=https://www.aliexpress.com/item/1005007198494636.html
OFFICIAL_PRODUCT_URL=https://www.popmart.com/your-product-url

# Monitoring intervals (seconds)
ALIEXPRESS_MIN_INTERVAL=3
ALIEXPRESS_MAX_INTERVAL=8
OFFICIAL_MIN_INTERVAL=2
OFFICIAL_MAX_INTERVAL=5

# Heartbeat intervals (seconds)
ALIEXPRESS_HEARTBEAT_INTERVAL=180
OFFICIAL_HEARTBEAT_INTERVAL=120

# Notification intervals (seconds)
ALIEXPRESS_NOTIFICATION_INTERVAL=3
OFFICIAL_NOTIFICATION_INTERVAL=2
```

> 💡 **配置提示**：
> - `BOT_TOKEN`：从Discord Developer Portal获取的机器人Token
> - `CHANNEL_ID`：右键Discord频道获取的数字ID
> - `PRODUCT_URL`：要监控的商品完整URL地址
> - 确保机器人已邀请到服务器并有正确权限

### 5. 运行监控器

```bash
# 仅监控AliExpress
python monitor.py --ali

# 仅监控PopMart官网
python monitor.py --pop

# 同时监控两个平台
python monitor.py --ali --pop

# 启用详细模式（每次检查都通知）
python monitor.py --ali --pop --verbose

# 查看帮助信息
python monitor.py --help
```

## 📋 命令行参数

| 参数 | 别名 | 描述 |
|------|------|------|
| `--ali` | `--aliexpress` | 启用AliExpress库存监控 |
| `--pop` | `--popmart` | 启用PopMart官网库存监控 |
| `--verbose` | `-v` | 启用详细通知模式 |
| `--help` | `-h` | 显示帮助信息 |

## 🔧 项目结构

```
FK_Popmart/
├── monitor.py              # 🚀 主监控脚本
├── .env                    # 🔐 环境变量配置（需要手动创建）
├── requirements.txt        # 📦 Python依赖
├── README.md              # 📖 项目说明文档
├── .gitignore             # 🚫 Git忽略文件
├── monitors/              # 📁 监控模块目录
│   ├── __init__.py        # 📦 Python包初始化
│   ├── base_monitor.py    # 🏗️ 基础监控抽象类
│   ├── aliexpress_monitor.py  # 🛒 AliExpress监控器
│   └── official_monitor.py    # 🎯 PopMart官网监控器
```

## 📊 通知策略

### 正常模式
- **有库存时**：持续通知（每2-3秒一次）
- **无库存时**：仅在状态变化时通知（售罄时通知一次）

### Verbose模式
- **所有情况**：每次检查都发送通知，包含详细调试信息
- **适合调试**：可以看到详细的检查过程和技术细节

## 🔍 监控功能

### AliExpress监控
- ✅ 智能按钮状态检测（支持多种按钮类型）
- ✅ 多层级价格获取策略（CSS选择器 + XPath + JavaScript）
- ✅ 高质量产品图片获取（优先.avif格式，960x960分辨率）
- ✅ 新加坡地区价格支持（SG$）
- ✅ 页面错误检测与处理
- ✅ 增强反检测机制

### PopMart官网监控
- ✅ 多种购买按钮检测
- ✅ Cloudflare绕过机制
- ✅ 快速结算链接生成
- ✅ PopMart CDN图片优先选择
- ✅ 产品ID和SKU智能提取

## 🎨 Discord通知示例

每个平台的通知包含：
- 📦 **产品信息** - 完整的产品标题和描述
- 💰 **价格** - 实时价格信息（支持多种货币）
- 📊 **状态** - 库存状态（有货/售罄/检查出错）
- 🛒 **链接** - 产品页面直达链接
- 🔔 **提醒** - 库存变化提醒信息
- 📸 **图片** - 高清产品图片（优先高质量格式）
- ⏰ **时间** - 检查时间戳

## ⚠️ 注意事项

1. **环境变量**：确保 `.env` 文件配置正确且包含所有必需参数
2. **Discord权限**：机器人需要发送消息、embed和@here通知的权限
3. **频道ID**：使用正确的Discord频道ID（开启开发者模式获取）
4. **网络环境**：确保能正常访问目标网站，建议使用稳定网络
5. **资源使用**：多平台监控会占用更多CPU和内存资源
6. **Chrome浏览器**：确保系统已安装Chrome浏览器（用于Selenium）

## 🔧 故障排除

### 常见问题

1. **环境配置错误**
   ```bash
   ❌ 错误: 未找到BOT_TOKEN，请检查.env文件
   ```
   **解决**：创建 `.env` 文件并配置正确的BOT_TOKEN

2. **Discord机器人Token无效**
   ```bash
   ❌ Discord登录失败，请检查BOT_TOKEN是否正确
   ```
   **解决**：
   - 检查Token是否复制正确（无额外空格）
   - 确认Token没有过期或被重置
   - 在Discord Developer Portal重新生成Token

3. **Discord权限问题**
   ```bash
   ❌ 找不到Discord频道: XXXXXX
   ```
   **解决**：
   - 检查频道ID是否正确（纯数字，无其他字符）
   - 确保机器人已被邀请到服务器
   - 确认机器人有查看频道和发送消息的权限
   - 检查频道是否为私有频道（机器人需要特殊权限）

4. **机器人无法发送消息**
   ```bash
   ❌ 403 Forbidden: Missing Permissions  
   ```
   **解决**：
   - 确保机器人有"发送消息"权限
   - 确保机器人有"嵌入链接"权限
   - 确保机器人有"使用外部表情符号"权限
   - 检查频道权限设置，确保机器人角色有必要权限

5. **页面加载问题**
   ```bash
   ⏰ 页面加载超时
   ```
   **解决**：检查网络连接，可能需要重启程序或更换网络

6. **价格获取失败**
   ```bash
   💰 价格暂不可用
   ```
   **解决**：可能是页面结构变化或地区限制，检查产品URL是否有效

7. **图片显示问题**
   ```bash
   📸 没有找到有效的图片URL
   ```
   **解决**：页面图片组件可能更新，或图片被CDN缓存

## 📈 性能优化

- **随机间隔**：使用随机检查间隔避免被反爬虫检测
- **并发监控**：多个平台同时独立运行，互不影响
- **智能图片选择**：优先选择高质量图片，过滤小尺寸缩略图
- **内存管理**：定期清理浏览器驱动和临时文件
- **错误恢复**：自动重试机制，故障时自动恢复

## 🆕 更新日志

### v3.0 (2025-08-03)
- 🧹 **项目结构优化**：删除重复的原始脚本，保持项目简洁
- 🔧 **模块化完成**：完全基于模块化架构运行
- 📸 **图片修复**：修复.avif格式图片支持
- 💰 **价格增强**：新增用户指定的价格选择器支持
- 🚀 **性能提升**：移除冗余代码，提升运行效率
- 🎯 **参数优化**：将PopMart参数从容易误解的`--off`改为更清晰的`--pop`
- 📖 **文档完善**：新增详细的Discord机器人设置指南和故障排除

### v2.0 (2025-07-15)
- 🎯 多平台监控支持
- 📦 模块化架构设计
- 🔐 环境变量配置
- 📱 Discord通知优化

## 🚀 未来计划

- [ ] 支持更多电商平台（Amazon、eBay等）
- [ ] 添加价格变动监控和历史记录
- [ ] 支持多商品同时监控
- [ ] 添加Web管理界面
- [ ] 支持自定义通知模板
- [ ] 添加监控数据统计和可视化

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

1. Fork 这个仓库
2. 创建你的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建一个Pull Request

---

**开发者**: FK_popmart  
**版本**: v3.0  
**最后更新**: 2025-08-03

> 💡 **提示**: 如果遇到问题，请首先检查网络连接和配置文件，大多数问题都与环境配置相关。