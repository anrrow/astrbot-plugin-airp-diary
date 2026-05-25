# AstrBot AIRP Diary Plugin

> AIRP角色日记系统 - 为你的角色记录每一个碎碎念，让AI生成更「活」的日记

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)

## 🎯 核心特性

这是一个为 [AstrBot](https://github.com/astrbot/astrbot) 设计的高级角色日记插件。

**✨ 最重要的改进：直接集成AstrBot的人格系统！**
- 插件会自动读取你在AstrBot中配置的人格信息
- 无需重复配置，开箱即用
- 日记内容完全基于AstrBot的人格设定生成

### 📋 新版本改进亮点

#### 🔗 与AstrBot人格系统深度集成
- 自动从AstrBot读取角色名和人格设定
- 无需在插件中重复配置人格
- 日记、心声、足迹都基于统一的人格

#### ✨ 状态上下文缓存
- 记录角色的**情绪、能量值、最近地点、最近事件**等状态
- 生成日记时自动融入这些上下文
- 让日记产生**连续感和一致性**

```json
{
  "mood": "烦躁",
  "energy": 52,
  "last_place": "便利店",
  "recent_event": "电车晚点",
  "unfinished_thought": "昨天那件事还是有点在意"
}
```

#### 🛡️ 严格格式校验与自动修复
- LLM生成的日记自动验证格式
- 自动修复缺失的日期、天气、内容标签
- **零概率翻车**，输出总是符合规范

#### 🌤️ 天气自动获取
- 支持 **OpenWeather**、**和风天气**、**彩云天气** 三大API
- 日记中的天气自动对接真实天气数据
- 用户会觉得"哇，它真知道今天下雨"

#### 📚 日记历史存档
- 自动保存每天的日记到本地
- 支持查看**昨天、上周、上个月**的日记
- 新指令 `翻日记` 查看最近的日记列表

```
data/
  角色名称/
    diaries/
      2026-05-25.json
      2026-05-24.json
    state.json  # 角色状态
```

#### 🔗 心声与日记互动
- 心声生成时自动读取最近的日记
- 日记说"不想说"，心声会说"其实是想说的，只是..."
- 形成**对话关系**，更加真实

#### 🎬 随机小动作库
- 日记中自动注入小动作：揉眼睛、叹气、转笔等
- **大幅降低AI味**
- 可配置概率和自定义动作

```python
"揉了揉眼睛"
"盯着窗外看了一会"
"叹了口气"
"搓了搓手"
```

#### 🎨 Markdown + HTML双渲染
- 默认输出HTML格式（支持完整的<span class>）
- 可切换到Markdown（兼容性强）
- 自动转换：`~~删除线~~`、`==高亮==` 等

#### 📦 Prompt模块化管理
```
prompts/
  system.txt        # 日记系统提示
  diary_context.txt # 上下文融合提示
  voice.txt         # 心声生成提示
  footprint.txt     # 足迹生成提示
  history.txt       # 历史日记提示
```

修改prompt只需编辑对应的.txt文件，无需改代码。

---

## 📖 功能清单

| 指令 | 功能 | 新增特性 |
|------|------|---------|
| `查看日记` | 生成今天日记 | ✅ 状态缓存、天气API、格式校验、小动作 |
| `查看心声` | 生成内心独白 | ✅ 日记上下文、情绪同步 |
| `查看足迹` | 生成最近地点 | ✅ 地点+情绪+细节 |
| `查看昨天日记` | 查看过去日记 | ✅ 从历史存档读取 |
| `查看上周日记` | 查看一周前日记 | ✅ 自动计算日期 |
| `翻日记` | 浏览日记列表 | ✨ 新指令 |

---

## 🎨 支持的文本格式

在日记中可以使用以下HTML标签：

```html
<!-- 删除线 -->
<span class="strikethrough">我改主意了</span>

<!-- 高亮 -->
<span class="highlight">重要的事</span>

<!-- 下划线 -->
<span class="underline">重点</span>

<!-- 强调 -->
<span class="emphasis">非常重要</span>

<!-- 手写体 -->
<span class="handwritten">签名</span>

<!-- 涂黑（隐私） -->
<span class="censored">隐私信息</span>

<!-- 混乱体 -->
<span class="messy">乱糟糟的想法</span>
```

或者使用Markdown格式：

```markdown
~~删除线~~
==高亮==
__下划线__
**强调**
```

---

## 💾 日记格式

```
[日记]
日期：2026年05月25日 星期日
天气：☀️ 晴朗 / 22℃
内容：
<p>今天又睡到中午，罪恶感来了，但我选择<span class="strikethrough">反思</span>躺着。</p>
<p>买了新的<span class="highlight">花</span>，在窗边晒太阳。</p>
<p>下午有点<span class="emphasis">烦躁</span>，原因不详。喝了咖啡后好多了。</p>
```

---

## 🚀 安装与配置

### 1️⃣ 克隆仓库

```bash
cd /path/to/AstrBot/plugins
git clone https://github.com/anrrow2002-ctrl/astrbot-plugin-airp-diary.git
cd astrbot-plugin-airp-diary
```

### 2️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 3️⃣ 配置（可选）

**✨ 重要：插件会自动从AstrBot的人格系统读取角色名和人格设定，无需额外配置！**

如果你想覆盖AstrBot的人格设定，或者自定义其他功能，可以在AstrBot配置中添加：

```json
{
  "airp-diary": {
    "character_name": "",
    "comment": "留空则使用AstrBot人格系统中的角色名",
    
    "default_city": "东京",
    "render_mode": "html",
    "enable_state_cache": true,
    "enable_diary_history": true,
    "enable_action_injection": true,
    "use_weather_api": false
  }
}
```

### 4️⃣ （可选）配置天气API

如果要启用真实天气，需要配置API密钥：

#### OpenWeather（推荐）

1. 申请API密钥：https://openweathermap.org/api
2. 在配置中添加：

```json
{
  "airp-diary": {
    "use_weather_api": true,
    "weather_provider": "openweather",
    "weather_api_key": "你的API密钥"
  }
}
```

#### 和风天气（HeyWeather）

1. 申请API密钥：https://www.qweather.com/
2. 在配置中添加：

```json
{
  "airp-diary": {
    "use_weather_api": true,
    "weather_provider": "heweather",
    "weather_api_key": "你的API密钥"
  }
}
```

### 5️⃣ 重启AstrBot

```bash
# AstrBot会自动加载插件
```

---

## ⚙️ 完整配置说明

| 配置项 | 类型 | 必需 | 默认值 | 说明 |
|-------|------|------|--------|------|
| `character_name` | string | ❌ | - | 角色名称（留空使用AstrBot人格系统） |
| `default_city` | string | ❌ | 东京 | 常驻城市（用于天气） |
| `render_mode` | string | ❌ | html | 渲染模式（html/markdown） |
| `enable_state_cache` | boolean | ❌ | true | 启用状态缓存 |
| `enable_diary_history` | boolean | ❌ | true | 启用日记历史 |
| `enable_action_injection` | boolean | ❌ | true | 启用小动作注入 |
| `use_weather_api` | boolean | ❌ | false | 启用天气API |
| `weather_provider` | string | ❌ | openweather | 天气源（openweather/heweather/caiyun） |
| `weather_api_key` | string | ❌ | null | 天气API密钥 |
| `mood_types` | array | ❌ | [...] | 可用情绪类型 |

---

## 📁 项目结构

```
astrbot-plugin-airp-diary/
├── README.md                    # 项目说明
├── manifest.yaml                # 插件元数据
├── config.schema.json           # 配置schema
├── requirements.txt             # Python依赖
├── .gitignore                  # Git忽略规则
│
├── airp_diary/
│   ├── __init__.py             # 包初始化
│   ├── plugin.py               # 📌 插件主类（指令处理）
│   ├── prompt_loader.py        # 📌 Prompt加载系统
│   ├── memory.py               # 📌 内存和历史管理
│   ├── formatter.py            # 日期格式化
│   ├── validator.py            # 📌 日记格式校验和小动作
│   ├── weather.py              # 📌 天气API集成
│   ├── render.py               # 📌 渲染格式转换
│   ├── prompts.py              # 向后兼容层
│   ├── styles.css              # HTML样式表
│   │
│   └── prompts/                # 📌 Prompt模板（新）
│       ├── system.txt
│       ├── diary_context.txt
│       ├── voice.txt
│       ├── footprint.txt
│       └── history.txt
│
└── data/                        # 📌 数据目录（自动生成）
    └── 角色名称/
        ├── state.json          # 当前状态
        └── diaries/            # 日记历史
            └── 2026-05-25.json
```

---

## 🔧 高级用法

### 手动更新角色状态

```python
from airp_diary.memory import CharacterMemory

memory = CharacterMemory("小月")

# 加载当前状态
state = memory.load_state()

# 修改状态
state.update({
    "mood": "开心",
    "energy": 85,
    "last_place": "咖啡馆",
    "recent_event": "和朋友约好了",
})

# 保存状态
memory.save_state(state)
```

### 修改Prompt

编辑 `airp_diary/prompts/` 目录中的对应文件即可。例如，要改日记的风格，编辑 `system.txt`：

```txt
你是AIRP角色扮演日记系统。

当用户输入"查看日记"时，你必须严格使用以下格式回复：

[日记]
日期：YYYY年MM月DD日 星期X
...
```

修改后重启插件即可生效。

### 自定义小动作

编辑 `validator.py` 中的 `DIARY_ACTIONS` 列表：

```python
DIARY_ACTIONS = [
    "揉了揉眼睛",
    "盯着窗外看了一会",
    "你的自定义动作",
    ...
]
```

### 使用Markdown渲染

配置中设置：

```json
{
  "airp-diary": {
    "render_mode": "markdown"
  }
}
```

---

## 📊 工作流程

```
用户输入（查看日记）
    ↓
加载角色状态 (mood, energy, last_place...)
    ↓
加载Prompt模板
    ↓
融合上下文 (状态 + 天气 + 最近日记)
    ↓
调用LLM生成内容
    ↓
格式校验 & 自动修复
    ↓
注入随机小动作
    ↓
保存到历史存档
    ↓
转换渲染格式
    ↓
回复用户
```

---

## 🎓 最佳实践

### 如何写好角色设定

```
年龄、身份：24岁，公司员工
性格特点：温和、有点内向、容易自卑
背景故事：从小镇来到东京，一个人生活
说话习惯：常说"算了"、"无所谓"，有点自嘲
喜欢的事：看书、喝咖啡、一个人发呆
讨厌的事：被催促、加班、虚伪的人
当前处境：最近有点疲惫，在考虑要不要辞职
```

### 如何维护日记的连贯性

1. 定期查看 `state.json` 了解角色最近的状态
2. 在关键事件发生后，手动更新状态
3. 定期查看 `翻日记` 确保故事逻辑连贯

### 提升日记质量的技巧

1. **详细的角色设定** - 越详细的设定，越容易生成贴切的日记
2. **定期更新状态** - 让状态随着故事发展而变化
3. **关注prompt模板** - 如果不满意输出，先调整prompt再调整配置

---

## 🐛 常见问题

**Q: 为什么日记还是有点AI味？**

A: 
1. 检查 `character_profile` 是否足够详细
2. 启用 `enable_action_injection` 以注入小动作
3. 调整 `prompts/system.txt` 中的风格描述
4. 定期更新 `state.json` 中的状态

**Q: 日期、天气显示错误？**

A:
1. 检查服务器时区设置（`timedatectl`)
2. 确保系统时间正确
3. 如果使用天气API，检查API密钥是否有效

**Q: 如何禁用某些功能？**

A:
- 禁用小动作：设置 `enable_action_injection: false`
- 禁用历史存档：设置 `enable_diary_history: false`
- 禁用状态缓存：设置 `enable_state_cache: false`

**Q: 如何重置角色状态？**

A:
删除 `data/角色名称/state.json` 文件，重启插件会自动重建默认状态。

**Q: 支持多个角色吗？**

A:
支持！每个角色会自动在 `data/` 目录下创建独立的文件夹。只需在配置中修改 `character_name` 即可切换角色。

---

## 📝 更新日志

### v2.1.0 (2026-05-25)

- 🔗 **突破性改进**：与AstrBot人格系统深度集成
- ✨ 自动从AstrBot读取角色名和人格设定
- 📦 无需重复配置，开箱即用
- 🎯 插件配置从必填2项减至0项
- 📄 完整的集成说明文档

### v2.0.0 (2026-05-25)

- ✨ 状态上下文缓存系统
- 🛡️ 严格格式校验与自动修复
- 🌤️ 天气API集成（OpenWeather/和风天气）
- 📚 日记历史存档与查询
- 🔗 心声与日记互动联动
- 🎬 随机小动作库
- 🎨 Markdown + HTML双渲染
- 📦 Prompt模块化管理
- 🎯 完整的内存和配置系统

### v1.0.0 (2024-03-15)

- ✨ 初版发布
- 📝 支持查看日记
- 💭 支持查看心声
- 🚶 支持查看足迹

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 提交前请确保：

1. 代码符合PEP8规范
2. 新功能有相应的Prompt模板
3. 修改了说明文档
4. 测试通过

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

感谢 [AstrBot](https://github.com/astrbot/astrbot) 提供的开放平台！

---

## 📧 联系方式

- GitHub: [@anrrow2002-ctrl](https://github.com/anrrow2002-ctrl)
- Issues: [提交问题](https://github.com/anrrow2002-ctrl/astrbot-plugin-airp-diary/issues)

---

**让每个碎碎念都活起来。** ✨
