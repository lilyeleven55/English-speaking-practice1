# AI 英语口语陪练 | English Speaking Coach

> 场景式 AI 英语口语练习 Web 应用 —— 七牛云议题实战作品

---

## 🎬 Demo 视频

**[点击观看 Demo 视频](https://your-demo-video-link-here)** ← 请替换为 B 站 / 网盘链接

> ⚠️ 演示视频需包含完整旁白，覆盖所有核心功能模块。

---

## 项目简介

本项目是一个基于 **Python + Flask + 智谱 GLM API** 的英语口语陪练 Web 应用。用户可以在不同场景（餐厅点餐、日常问候）下与 AI 进行英文对话练习，AI 会：

- 根据场景给出自然的英文回应（基于智谱 GLM 大模型）
- 维持多轮对话上下文
- 根据场景目标推进对话
- 检测并提示语法/用词错误
- 在连续出错时给出鼓励性反馈
- 记录学习统计数据
- 支持语音输入和朗读

当前版本已接入**智谱 GLM 真实大模型 API**，提供智能对话体验。

---

## 功能特性

| 功能 | 说明 |
|------|------|
| 💬 聊天式界面 | AJAX 无刷新对话，流畅交互 |
| 🧠 多轮对话 | 基于会话历史的上下文理解 |
| 🍽️ 场景切换 | 餐厅点餐 / 日常问候，一键切换 |
| 🎯 场景目标 | 任务驱动的对话引导 |
| 📝 语法纠错 | 基于规则检测 15+ 种常见 ESL 错误 |
| 📊 学习统计 | 记录练习次数、正确率等数据 |
| 🎤 语音功能 | 语音输入（Web Speech API）+ 朗读（TTS） |
| 💪 鼓励机制 | 连续答错时自动给出鼓励提示 |
| 🤖 智谱 GLM | 真实大模型 API 接入 |

---

## 技术栈与依赖

| 类别 | 技术 |
|------|------|
| 后端 | Python 3.10+, Flask 3.x |
| 前端 | HTML5, CSS3, 原生 JavaScript |
| 大模型 | 智谱 GLM (glm-5.1) |
| 构建工具 | 无（零构建，直接运行） |

**第三方依赖（见 `requirements.txt`）：**

- `flask>=3.0.0` — Web 框架
- `python-dotenv>=1.0.0` — 环境变量管理

---

## 原创功能说明

以下为本人原创实现的核心逻辑（非第三方库提供）：

1. **`utils/scenarios.py`** — 场景数据结构、目标机制、开场白与回复模板库
2. **`utils/grammar_checker.py`** — ESL 常见错误模式库与纠错提示生成
3. **`utils/ai_responder.py`** — 场景感知回复引擎、连续错误鼓励机制、智谱 GLM API 集成
4. **`app.py`** — 会话管理、学习统计、数据库集成
5. **`static/app.js`** — 前端 AJAX 聊天交互、场景切换、语音功能
6. **`static/style.css`** — 聊天界面 UI 设计

---

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
```

### 6. 打开浏览器

访问 [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 项目结构

```
English-speaking-practice1/
├── app.py                  # Flask 主入口（含会话、统计、数据库）
├── requirements.txt        # Python 依赖
├── .env                    # 环境变量（API Key，不提交 Git）
├── .env.example            # 环境变量示例文件
├── .gitignore              # Git 忽略规则
├── README.md               # 项目文档
├── templates/
│   └── index.html          # 聊天页面模板
├── static/
│   ├── style.css           # 界面样式
│   └── app.js              # 前端交互逻辑（含语音功能）
└── utils/
    ├── scenarios.py        # 场景定义与目标机制
    ├── grammar_checker.py  # 语法纠错引擎
    └── ai_responder.py     # AI 回复引擎（智谱 GLM 集成）
```

---

## 接入智谱 GLM API 说明

本项目已原生集成智谱 GLM API，无需额外安装 SDK。

### 配置步骤

1. 访问 [智谱 AI 开放平台](https://bigmodel.cn) 注册账号
2. 在控制台创建 API Key
3. 将 API Key 填入 `.env` 文件的 `ZHIPU_API_KEY`
4. 启动应用即可使用真实大模型

### 回退机制

如果未配置 `ZHIPU_API_KEY` 或 API 调用失败，系统会自动回退到模板模式，确保应用始终可用。

---

## 使用示例

1. 打开页面，默认进入「餐厅点餐」场景
2. 输入 `Hi, I want a coffee` → AI 会自然回应并询问更多信息
3. 输入 `I are want a hamburger` → AI 会回应并提示语法错误 `I are` → `I am`
4. 连续输入 2 句有语法错误的句子 → 触发鼓励提示
5. 点击「日常问候」切换场景，开始新的对话练习
6. 点击麦克风按钮使用语音输入，点击喇叭按钮朗读 AI 回复

---

## 开发者

- GitHub: [lilyeleven55](https://github.com/lilyeleven55)
- 议题：AI 英语口语陪练

---

## License

MIT
