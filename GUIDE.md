# AIRP Diary Plugin v2.0 使用指南

这是一份详细的使用指南，帮助你充分利用插件的所有功能。

## 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [高级用法](#高级用法)
4. [故障排查](#故障排查)

---

## 快速开始

### 最小化配置

**插件会自动从AstrBot的人格系统读取角色信息，无需在插件中重复配置！**

只需确保AstrBot中配置了人格：

```json
{
  "personality": {
    "name": "你的角色名字",
    "profile": "角色介绍"
  }
}
```

然后安装插件，重启AstrBot即可。在机器人处输入：

```
查看日记
查看心声
查看足迹
```

### 推荐配置

如果想自定义插件功能，可以配置：

```json
{
  "airp-diary": {
    "default_city": "东京",
    "enable_state_cache": true,
    "enable_diary_history": true,
    "enable_action_injection": true,
    "render_mode": "html"
  }
}
```

---

## 核心概念

### 1. 角色设定（Character Profile）

这是最重要的配置项。设定越详细，生成的内容越准确。

**包括以下内容：**

```
【基本信息】
- 名字、年龄
- 职业、身份
- 常驻地点

【个性特征】
- 性格（内向/外向）
- 优点和缺点
- 说话习惯（常用的词汇或短语）
- 肢体习惯（小动作）

【背景故事】
- 出身背景
- 重要经历
- 与他人的关系

【当前状态】
- 最近的心情
- 最近发生的事
- 当前的困扰或期待

【偏好与厌恶】
- 喜欢的事物/人
- 讨厌的事物/人
- 兴趣爱好
```

**示例：**

```
小月，24岁，从小镇来到东京独自工作的女孩。

性格：温和但有点倔强，容易自卑，但在熟人面前会开玩笑。常说"算了"、"无所谓"这样的话。有点自嘲。

背景：来自一个小镇，家里不是特别富裕。上大学时来到东京，毕业后留在了这里。一个人租房住。

偏好：喜欢看书（特别是推理小说）、喝咖啡、一个人发呆。喜欢雨天。

厌恶：被催促、加班、虚伪的人、被指责。

当前状态：最近工作有点烦躁，考虑要不要换个工作。但舍不得现在的咖啡馆和朋友。
```

### 2. 状态缓存（State Cache）

插件会自动记录角色的当前状态：

```json
{
  "mood": "烦躁",           // 当前情绪
  "energy": 52,             // 能量值（0-100）
  "last_place": "便利店",   // 最近去过的地点
  "recent_event": "电车晚点", // 最近发生的事
  "unfinished_thought": "昨天的事还在想" // 未说完的话
}
```

生成日记时，这些状态会自动融入prompt，让日记看起来更连贯。

**自动更新时机：**
- 每次生成日记后，自动更新日期
- 手动调用更新（见高级用法）

### 3. 日记历史（Diary History）

每篇日记自动保存到本地：

```
data/
  小月/
    diaries/
      2026-05-25.json  <- 今天
      2026-05-24.json  <- 昨天
      2026-05-23.json
```

可以通过以下指令查看历史：

- `查看昨天日记` - 查看昨天保存的日记（如果有）
- `查看上周日记` - 查看一周前的日记
- `翻日记` - 查看最近5篇日记的列表

### 4. 小动作注入（Action Injection）

插件会在日记中随机注入小动作，大幅降低AI味。

**可用的小动作：**

```python
"揉了揉眼睛",
"把纸杯压扁",
"盯着窗外看了一会",
"鞋跟敲了两下地板",
"叹了口气",
"伸了个懒腰",
...（共15种）
```

**示例：**

```
原文：<p>今天又睡到中午。</p>

注入后：<p>揉了揉眼睛，今天又睡到中午。</p>
```

### 5. 渲染模式（Render Mode）

支持两种输出格式：

**HTML 模式（默认）：**
- 支持完整的 `<span class="">` 标签
- 视觉效果最好
- 建议用于网页显示

**Markdown 模式：**
- 使用标准Markdown语法
- 兼容性最强
- 建议用于纯文本平台

---

## 高级用法

### 手动管理角色状态

```python
from airp_diary.memory import CharacterMemory

# 创建内存管理器
memory = CharacterMemory("小月")

# 加载当前状态
state = memory.load_state()
print(state)
# 输出:
# {
#   "mood": "平静",
#   "energy": 75,
#   "last_place": "家",
#   "recent_event": "无",
#   "unfinished_thought": ""
# }

# 更新状态
memory.update_state(
    mood="开心",
    energy=85,
    last_place="咖啡馆",
    recent_event="和朋友约好了"
)

# 保存状态
memory.save_state(state)
```

### 查询和管理日记

```python
from airp_diary.memory import CharacterMemory

memory = CharacterMemory("小月")

# 加载今天的日记
diary = memory.load_diary()  # 默认加载今天
print(diary)

# 加载特定日期的日记
diary = memory.load_diary("2026-05-24")

# 加载几天前的日记
yesterday_diary = memory.get_recent_diary(days_ago=1)
last_week_diary = memory.get_recent_diary(days_ago=7)

# 列出最近的日记（按日期降序）
diaries = memory.list_diaries(limit=10)
for d in diaries:
    print(f"{d['date']}: {d['content'][:50]}...")
```

### 自定义小动作

编辑 `airp_diary/validator.py` 中的 `DIARY_ACTIONS` 列表：

```python
DIARY_ACTIONS = [
    "揉了揉眼睛",
    "转了转笔",
    "你的自定义小动作",
    ...
]
```

### 修改Prompt模板

所有prompt都保存在 `airp_diary/prompts/` 目录下。

**修改日记风格 - 编辑 `system.txt`：**

```txt
你是AIRP角色扮演日记系统。
...
【内容风格要求】
- 加入更多碎碎念
- 使用方言口语
- 更加感伤
...
```

**修改心声风格 - 编辑 `voice.txt`：**

```txt
...
【内容要求】
- 更直率
- 更多吐槽
...
```

修改后重启插件即可生效。

### 支持多个角色

只需在配置中修改 `character_name`，插件会自动为每个角色创建独立的数据目录。

```json
{
  "airp-diary": {
    "character_name": "小月"  // 修改这里
  }
}
```

数据会自动保存在：

```
data/小月/     <- 角色A的数据
data/小安/     <- 角色B的数据（如果切换了）
```

### 启用天气API

#### OpenWeather（推荐，免费）

1. 访问 https://openweathermap.org/api
2. 注册账号，获取API密钥（免费层：5天天气预报）
3. 配置：

```json
{
  "airp-diary": {
    "use_weather_api": true,
    "weather_provider": "openweather",
    "weather_api_key": "sk-xxxxxxxxxxxxxx"
  }
}
```

#### 和风天气（中国用户推荐）

1. 访问 https://www.qweather.com/
2. 注册账号，获取API密钥
3. 配置：

```json
{
  "airp-diary": {
    "use_weather_api": true,
    "weather_provider": "heweather",
    "weather_api_key": "xxxxxxxxxxxxxx"
  }
}
```

---

## 故障排查

### 日记生成失败

**症状：** 插件回复错误信息

**检查清单：**

1. 检查LLM是否可用（试试其他指令）
2. 检查角色设定是否过长或有特殊字符
3. 查看AstrBot日志输出

```bash
# 查看完整日志
tail -f astrbot.log | grep airp
```

### 日期、天气显示错误

**症状：** 日期是错的，或天气一直是默认值

**检查清单：**

1. 系统时区是否正确：

```bash
timedatectl
```

2. 如果启用了天气API，检查：
   - API密钥是否正确
   - 网络连接是否正常
   - API配额是否用完

### 日记始终是AI味

**症状：** 日记看起来不像这个角色说的话

**改进方案：**

1. **增强角色设定** - 添加更多细节和说话风格
2. **启用小动作** - 让 `enable_action_injection: true`
3. **调整Prompt** - 编辑 `prompts/system.txt`
4. **更新状态** - 定期更新角色的mood和energy

### 找不到历史日记

**症状：** `查看昨天日记` 提示没有保存的日记

**原因：**

- 日记还没生成过（生成过日记才会保存）
- `enable_diary_history` 被设置为 false

**解决方案：**

1. 确保 `enable_diary_history: true`
2. 先生成一篇日记（`查看日记`）
3. 然后再查看历史

### 状态没有更新

**症状：** `state.json` 中的mood总是"平静"

**原因：**

- `enable_state_cache` 被设置为 false
- 还没有生成过日记（生成日记时会更新状态）

**解决方案：**

1. 确保 `enable_state_cache: true`
2. 生成日记会自动更新日期等信息
3. 其他状态需要手动更新（见高级用法）

---

## 常见用法模式

### 模式1：每日日记记录

```
每天：查看日记 -> 自动保存到历史 -> 状态更新
定期：翻日记 -> 查看最近的日记列表
```

### 模式2：角色成长记录

```
初期：设定基础角色
中期：定期更新状态（mood, energy等）
后期：查看翻日记，回顾角色的成长
```

### 模式3：故事创作辅助

```
主线：用日记推进故事
支线：用心声展现内心独白
细节：用足迹补充世界观
```

---

## 技术细节

### 文件结构

```
data/角色名/
  state.json              # 当前状态
  diaries/
    2026-05-25.json      # 日期.json
    2026-05-24.json
  archives/               # 状态备份
    state_20260525_120000.json
```

### JSON格式

**state.json：**

```json
{
  "mood": "平静",
  "energy": 75,
  "last_place": "家",
  "recent_event": "无",
  "unfinished_thought": ""
}
```

**diaries/2026-05-25.json：**

```json
{
  "date": "2026-05-25",
  "content": "[日记]\n日期：2026年05月25日 星期日\n...",
  "saved_at": "2026-05-25T12:34:56.789012"
}
```

---

## 最佳实践

1. **详细的角色设定** = 更好的日记质量
2. **定期更新状态** = 更连贯的故事
3. **观看日记列表** = 确保逻辑一致性
4. **自定义Prompt** = 独特的风格
5. **备份重要日记** = 防止数据丢失

---

## 获取帮助

- 📖 完整文档：[README.md](README.md)
- 🐛 报告问题：[GitHub Issues](https://github.com/anrrow2002-ctrl/astrbot-plugin-airp-diary/issues)
- 💬 讨论交流：[GitHub Discussions](https://github.com/anrrow2002-ctrl/astrbot-plugin-airp-diary/discussions)

---

**祝你创作愉快！** ✨
