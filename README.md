# AI 英语口语陪练 | English Speaking Coach

> 场景式 AI 英语口语练习 Web 应用 —— 七牛云议题实战作品

***

## 🎬 Demo 视频

**[点击观看 Demo 视频](https://b23.tv/g9TRNnN)** ←  B 站链接

***

## 项目简介

本项目是一个基于 **Python + Flask + 智谱 GLM API** 的英语口语陪练 Web 应用。用户可以在不同场景下与 AI 进行英文对话练习，AI 会：

- 根据场景给出自然的英文回应（基于智谱 GLM 大模型）
- 维持多轮对话上下文
- 检测并提示语法/用词错误
- 在连续出错时给出鼓励性反馈
- 记录学习统计数据
- 支持语音输入和朗读
- 管理生词本
- 记录连续打卡
- 提供日历查看功能（支持翻页）
- 支持 PK 对战
- 提供待办清单功能

当前版本已接入**智谱 GLM 真实大模型 API**，提供智能对话体验。

***

## 功能特性

| 功能         | 说明                            |
| ---------- | ----------------------------- |
| 💬 聊天式界面   | AJAX 无刷新对话，流畅交互               |
| 🧠 多轮对话    | 基于会话历史的上下文理解                  |
| 🍽️ 6种预设场景 | 餐厅点餐、机场出行、日常购物、职场面试、校园选课、短途问路 |
| ✨ 自定义场景    | 用户可创建自己的练习场景                  |
| 🎯 场景目标    | 任务驱动的对话引导                     |
| 📝 语法纠错    | 基于规则检测常见 ESL 错误               |
| 📊 学习统计    | 记录练习次数、正确率等数据                 |
| 🔥 连续打卡    | 记录学习连续天数                      |
| 📅 学习日历    | 可翻页查看历史学习记录                   |
| 🎤 语音功能    | 语音输入（Web Speech API）+ 朗读（TTS） |
| 💪 鼓励机制    | 连续答错时自动给出鼓励提示                 |
| 📖 生词本     | 添加、编辑、删除、搜索、导出生词              |
| 🏆 勋章系统    | 完成目标获得勋章                      |
| 🎮 PK 对战   | 与朋友一起练习英语                     |
| 📝 待办清单    | 管理学习任务                        |
| 🤖 智谱 GLM  | 真实大模型 API 接入                  |

***

## 技术栈与依赖

| 类别   | 技术                         |
| ---- | -------------------------- |
| 后端   | Python 3.10+, Flask 3.x    |
| 前端   | HTML5, CSS3, 原生 JavaScript |
| 大模型  | 智谱 GLM (glm-5.1)           |
| 数据库  | SQLite                     |
| 构建工具 | 无（零构建，直接运行）                |

**第三方依赖（见** **`requirements.txt`）：**

- `flask>=3.0.0` — Web 框架
- `python-dotenv>=1.0.0` — 环境变量管理

***

## 原创功能说明

以下为本人原创实现的核心逻辑（非第三方库提供）：

1. **`utils/scenarios.py`** — 场景数据结构、目标机制、开场白与回复模板库
2. **`utils/grammar_checker.py`** — ESL 常见错误模式库与纠错提示生成
3. **`utils/ai_responder.py`** — 场景感知回复引擎、连续错误鼓励机制、智谱 GLM API 集成
4. **`app.py`** — 会话管理、学习统计、数据库集成、词汇本 API
5. **`static/app.js`** — 前端 AJAX 聊天交互、场景切换、语音功能、侧边栏、日历、PK 系统、待办清单
6. **`static/style.css`** — 完整的界面 UI 设计，包含侧边栏、主内容区、右侧面板
7. **`utils/word_list.py`** — 单词列表与拼写检查功能

***

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/lilyeleven55/English-speaking-practice1.git
cd English-speaking-practice1
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置智谱 API Key

复制 `.env.example` 为 `.env`（如已创建则直接编辑）：

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Windows CMD
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

编辑 `.env` 文件，填入你的智谱 API Key：

```
ZHIPU_API_KEY=your-api-key-here
```

> 💡 获取 API Key：访问 [智谱 AI 开放平台](https://bigmodel.cn) 注册并创建 API Key

### 5. 启动应用

```bash
python app.py

# 或者使用生产模式启动
python run_server.py
```

### 6. 打开浏览器

访问 <http://127.0.0.1:5000>

***

## 项目结构

```
English-speaking-practice1/
├── app.py                          # Flask 主入口（含会话、统计、数据库、词汇 API）
├── run_server.py                   # 生产模式启动脚本
├── requirements.txt                # Python 依赖
├── .env                            # 环境变量（API Key，不提交 Git）
├── .env.example                    # 环境变量示例文件
├── .gitignore                      # Git 忽略规则
├── README.md                       # 项目文档
├── LICENSE                         # MIT 许可证
├── start.bat                       # Windows 快速启动脚本
├── templates/
│   └── index.html                  # 聊天页面模板
├── static/
│   ├── style.css                   # 完整的界面样式
│   └── app.js                      # 前端交互逻辑（含语音、侧边栏、日历、PK、待办等）
├── utils/
│   ├── __init__.py
│   ├── scenarios.py                # 场景定义与目标机制（6个预设场景）
│   ├── grammar_checker.py          # 语法纠错引擎
│   ├── ai_responder.py             # AI 回复引擎（智谱 GLM 集成）
│   └── word_list.py                # 单词列表与拼写检查
├── tests/
│   ├── test_spelling.py            # 拼写检查单元测试
│   └── test_vocabulary.py          # 词汇本 API 测试
└── practice.db                     # SQLite 数据库（运行时自动创建）
```

***

## 预设场景列表

| 场景   | 图标  | 说明              |
| ---- | --- | --------------- |
| 餐厅点餐 | 🍽️ | 练习在餐厅点餐和饮品      |
| 机场出行 | ✈️  | 练习机场对话：值机、行李、问路 |
| 日常购物 | 🛍️ | 练习购物对话：问价、尺码、砍价 |
| 职场面试 | 💼  | 练习英语面试对话        |
| 校园选课 | 📚  | 练习课程注册和学术咨询     |
| 短途问路 | 🗺️ | 练习用英语问路和指路      |

***

## API 接口说明

### 场景相关

- `GET /api/scenarios` - 获取所有场景列表

### 对话相关

- `POST /api/chat` - 发送聊天消息并获取回复
- `POST /api/reset` - 重置当前会话

### 统计相关

- `GET /api/stats` - 获取学习统计数据

### 词汇本相关

- `GET /api/vocabulary` - 获取词汇列表（支持搜索）
- `POST /api/vocabulary` - 添加新词汇
- `PUT /api/vocabulary/<id>` - 编辑词汇
- `DELETE /api/vocabulary/<id>` - 删除词汇
- `GET /api/vocabulary/export?format=csv|txt` - 导出词汇

***

## 接入智谱 GLM API 说明

本项目已原生集成智谱 GLM API，无需额外安装 SDK。

### 配置步骤

1. 访问 [智谱 AI 开放平台](https://bigmodel.cn) 注册账号
2. 在控制台创建 API Key
3. 将 API Key 填入 `.env` 文件的 `ZHIPU_API_KEY`
4. 启动应用即可使用真实大模型

### 回退机制

如果未配置 `ZHIPU_API_KEY` 或 API 调用失败，系统会自动回退到模板模式，确保应用始终可用。

***

## 使用示例

1. 打开页面，默认进入「餐厅点餐」场景
2. 输入 `Hi, I'd like to order a coffee` → AI 会自然回应并询问更多信息
3. 输入 `I are want a hamburger` → AI 会回应并提示语法错误 `I are` → `I am`
4. 连续输入 2 句有语法错误的句子 → 触发鼓励提示
5. 点击其他场景按钮切换场景，开始新的对话练习
6. 点击「自定义场景」创建自己的练习场景
7. 点击麦克风按钮使用语音输入，点击喇叭按钮朗读 AI 回复
8. 在侧边栏查看学习日历、添加生词、记录待办事项
9. 与朋友一起使用 PK 对战功能练习

***

## 运行测试

本项目包含单元测试，可运行以下命令：

```bash
# 运行拼写检查测试
python tests/test_spelling.py

# 运行词汇本 API 测试
python tests/test_vocabulary.py
```

***

## 开发者

- GitHub: [lilyeleven55](https://github.com/lilyeleven55)
- 议题：AI 英语口语陪练

***

## License

MIT
