# PopMart官网库存监控器

一个专注于PopMart官网的Discord库存监控机器人，实时监控商品库存状态并发送通知。

## 🎯 功能特性

- ✅ **PopMart官网专业监控** - 专注于PopMart官网商品库存监控
- ✅ **智能库存检测** - 准确识别商品库存状态变化
- ✅ **实时Discord通知** - 库存变化时立即发送Discord消息
- ✅ **高质量商品展示** - 自动获取商品图片和详细信息
- ✅ **灵活通知策略** - 支持正常模式和详细模式
- ✅ **增强反检测机制** - 内置多种反爬虫检测措施
- ✅ **环境变量配置** - 敏感信息安全存储
- ✅ **错误处理机制** - 网络异常自动重试

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
3. 在 **"Bot Permissions"** 部分选择：
   - ✅ `Send Messages`
   - ✅ `Embed Links`
   - ✅ `Attach Files`
   - ✅ `Use External Emojis`
4. 复制生成的URL并在浏览器中打开
5. 选择要添加机器人的服务器
6. 确认权限并完成邀请

### 2. 获取Discord频道ID

1. 在Discord中启用开发者模式：
   - 用户设置 → 高级 → 开发者模式 ✅
2. 右键点击要接收通知的频道
3. 选择 **"复制频道ID"**
4. 保存这个ID（这就是你的`OFFICIAL_CHANNEL_ID`）

### 3. 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-username/fk_popmart.git
cd fk_popmart

# 安装Python依赖
pip install -r requirements.txt
```

### 4. 配置环境变量

1. 复制环境变量模板：
```bash
cp env.example .env
```

2. 编辑 `.env` 文件，填入你的配置：
```bash
# Discord Bot Configuration
BOT_TOKEN=你的机器人Token

# PopMart官网监控配置
OFFICIAL_CHANNEL_ID=你的频道ID
OFFICIAL_PRODUCT_URL=要监控的PopMart商品URL

# 监控配置参数（可选，使用默认值即可）
MONITOR_MIN_INTERVAL=3
MONITOR_MAX_INTERVAL=6
MONITOR_NOTIFICATION_INTERVAL=3
MONITOR_PAGE_LOAD_TIMEOUT=25
MONITOR_PAGE_LOAD_WAIT=3
MONITOR_JS_RENDER_WAIT=5
MONITOR_CLOUDFLARE_WAIT=10
```

### 5. 运行监控器

```bash
# 正常模式运行
python monitor.py

# 详细模式运行（每次检查都通知）
python monitor.py --verbose
```

## 📋 使用说明

### 命令行参数

```bash
python monitor.py [选项]

选项:
  --verbose, -v    启用详细通知模式
  --help, -h       显示帮助信息
```

### 通知策略

#### 正常模式
- **有库存**: 持续通知（每3秒一次）
- **无库存**: 仅在状态变化时通知一次
- **售罄**: 通知一次

#### 详细模式 (`--verbose`)
- **每次检查**: 无论是否有库存都发送通知
- **调试用途**: 用于测试和监控状态确认

### 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `BOT_TOKEN` | Discord机器人Token | 必填 |
| `OFFICIAL_CHANNEL_ID` | Discord频道ID | 必填 |
| `OFFICIAL_PRODUCT_URL` | PopMart商品URL | 必填 |
| `MONITOR_MIN_INTERVAL` | 最小检查间隔（秒） | 3 |
| `MONITOR_MAX_INTERVAL` | 最大检查间隔（秒） | 6 |
| `MONITOR_NOTIFICATION_INTERVAL` | 通知间隔（秒） | 3 |
| `MONITOR_PAGE_LOAD_TIMEOUT` | 页面加载超时（秒） | 25 |
| `MONITOR_PAGE_LOAD_WAIT` | 页面加载等待（秒） | 3 |
| `MONITOR_JS_RENDER_WAIT` | JS渲染等待（秒） | 5 |
| `MONITOR_CLOUDFLARE_WAIT` | Cloudflare等待（秒） | 10 |

## 🔧 技术架构

### 核心组件

1. **PopMartMonitor** - 主控制器
   - 管理Discord客户端连接
   - 协调监控任务
   - 处理配置管理

2. **OfficialMonitor** - PopMart官网监控器
   - 专门处理PopMart官网的库存检测
   - 商品信息提取
   - 库存状态判断

3. **BaseMonitor** - 基础监控类
   - 浏览器驱动管理
   - 通用监控逻辑
   - 反检测机制

### 工作流程

```
启动程序 → 加载配置 → 初始化Discord → 设置浏览器 → 开始监控循环
    ↓
访问商品页面 → 等待加载 → 提取信息 → 判断库存 → 发送通知 → 等待间隔
    ↑                                                        ↓
    ←←←←←←←←←←←←← 循环继续 ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
```

### 反检测机制

- **无头浏览器**: 使用Chrome无头模式
- **随机用户代理**: 从多个真实UA中随机选择
- **随机等待时间**: 避免规律性访问
- **反自动化检测**: 隐藏webdriver特征
- **Cloudflare处理**: 智能处理验证页面

## 🛠️ 开发指南

### 项目结构

```
fk_popmart/
├── monitor.py              # 主程序入口
├── monitors/               # 监控器模块
│   ├── __init__.py
│   ├── base_monitor.py     # 基础监控类
│   └── official_monitor.py # PopMart官网监控器
├── .env                    # 环境变量配置（需要创建）
├── env.example             # 环境变量模板
├── requirements.txt        # Python依赖
├── README.md              # 项目文档
└── .gitignore             # Git忽略文件
```

### 依赖说明

- `discord.py` - Discord API客户端
- `selenium` - 网页自动化工具
- `webdriver-manager` - 浏览器驱动管理
- `python-dotenv` - 环境变量加载

## 🐛 故障排除

### 常见问题

1. **Discord连接失败**
   - 检查BOT_TOKEN是否正确
   - 确认机器人已添加到服务器
   - 验证频道ID是否正确

2. **浏览器驱动问题**
   - 确保Chrome浏览器已安装
   - 检查网络连接
   - 尝试重新安装webdriver-manager

3. **网络连接问题**
   - 检查网络连接稳定性
   - 确认PopMart网站可访问
   - 考虑调整超时参数

4. **Cloudflare阻止**
   - 这是正常现象，程序会自动重试
   - 可以适当增加等待时间
   - 避免过于频繁的检查

### 调试模式

使用详细模式进行调试：
```bash
python monitor.py --verbose
```

这将显示每次检查的详细信息，帮助诊断问题。

## 📝 更新日志

### v2.0.0
- 🔄 重构为专注PopMart官网的监控器
- ❌ 移除AliExpress相关功能
- ✨ 简化命令行参数
- 📚 更新文档和配置

### v1.0.0
- ✨ 初始版本
- ✅ 支持多平台监控
- ✅ Discord通知功能
- ✅ 反检测机制

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## ⚠️ 免责声明

本工具仅供学习和个人使用。请遵守相关网站的服务条款和robots.txt规则。使用本工具产生的任何后果由用户自行承担。