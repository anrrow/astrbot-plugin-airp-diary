# 更新日志

## v2.1.0 (2026-05-25)

### ✨ 突破性改进：与AstrBot人格系统深度集成

**主要变化：插件不再独立管理人格，而是自动从AstrBot读取**

#### 🎯 新架构优势

- ✅ **无重复配置** - 一套人格配置服务所有功能
- ✅ **自动同步** - 修改AstrBot人格即时生效
- ✅ **高度集成** - 与AstrBot生态完美协作
- ✅ **配置极简** - 插件配置从必填2项减至0项

#### 📝 API 变化

**被移除：**
- 配置项 `character_profile` 不再支持
- 插件不再管理独立的人格系统

**新增：**
- 自动从 `bot.personality` 读取人格
- 自动从 `bot.character` 读取人格（兼容多个AstrBot版本）
- 自动降级到 `bot.character_name` 属性

#### 📦 版本迁移指南

**v2.0 → v2.1 迁移步骤：**

1. 移除插件配置中的 `character_profile`
2. 确保在AstrBot配置中有人格定义
3. 重启AstrBot

详见 [INTEGRATION.md](INTEGRATION.md)

---

## v2.0.0 (2026-05-25)

### ✨ 完整功能实现版本

**实现了所有9大高级改进：**

1. ✅ Prompt模块化管理 - 独立.txt文件，易于维护
2. ✅ 状态上下文缓存 - 记录角色状态，增加连续感
3. ✅ 日记历史存档 - 自动保存，支持查看历史
4. ✅ 严格格式校验 - 自动修复，零翻车率
5. ✅ 天气自动读取 - 支持3大API
6. ✅ 随机小动作库 - 降低AI味
7. ✅ Markdown + HTML双渲染 - 兼容性强
8. ✅ 心声与日记互动 - 形成对话关系
9. ✅ 足迹地图逻辑增强 - 更生动的记录

#### 🎯 核心特性

- **prompt_loader.py** - 模块化加载系统
- **memory.py** - 完整的内存和历史管理
- **validator.py** - 格式校验和小动作库
- **weather.py** - 天气API集成
- **render.py** - 渲染格式转换

#### 📊 指令集

| 指令 | 功能 |
|------|------|
| 查看日记 | 生成今天日记（融入状态、天气、小动作） |
| 查看心声 | 读取最近日记，生成更连贯的心声 |
| 查看足迹 | 生成地点+情绪+细节 |
| 查看昨天日记 | 从本地历史读取或生成 |
| 查看上周日记 | 自动计算日期 |
| 翻日记 | 浏览最近5篇日记列表 |

#### 📁 项目结构

```
airp_diary/
├── plugin.py              # 主插件类
├── prompt_loader.py       # Prompt加载系统
├── memory.py              # 内存和历史
├── validator.py           # 格式校验+小动作
├── weather.py             # 天气API
├── render.py              # 渲染转换
├── prompts/               # Prompt模板目录
│   ├── system.txt
│   ├── diary_context.txt
│   ├── voice.txt
│   ├── footprint.txt
│   └── history.txt
└── styles.css
```

#### 🔧 配置示例

```json
{
  "airp-diary": {
    "character_name": "小月",
    "character_profile": "详细的角色设定...",
    "default_city": "东京",
    "enable_state_cache": true,
    "enable_diary_history": true,
    "enable_action_injection": true,
    "render_mode": "html",
    "use_weather_api": false
  }
}
```

---

## v1.0.0 (2024-03-15)

### 初版发布

- ✨ 基础日记功能
- 💭 心声生成
- 🚶 足迹记录
- 🎨 HTML文本格式支持

---

## 版本对比

| 特性 | v1.0 | v2.0 | v2.1 |
|------|------|------|------|
| 日记生成 | ✓ | ✓ | ✓ |
| 心声生成 | ✓ | ✓ | ✓ |
| 足迹记录 | ✓ | ✓ | ✓ |
| 状态缓存 | ✗ | ✓ | ✓ |
| 日记历史 | ✗ | ✓ | ✓ |
| 格式校验 | ✗ | ✓ | ✓ |
| 天气API | ✗ | ✓ | ✓ |
| 小动作 | ✗ | ✓ | ✓ |
| 双渲染模式 | ✗ | ✓ | ✓ |
| Prompt模块化 | ✗ | ✓ | ✓ |
| AstrBot人格集成 | ✗ | ✗ | ✓ |
| 配置必填项 | 2项 | 2项 | 0项 |

---

## 未来规划

### 可能的下一步改进

- [ ] WebUI仪表板 - 查看角色信息和日记统计
- [ ] 数据库支持 - 处理大量日记
- [ ] 多语言支持 - 支持不同语言
- [ ] 云备份 - 自动备份日记
- [ ] 图片支持 - 在日记中添加配图
- [ ] 语音合成 - 朗读日记
- [ ] 高级分析 - 性格变化趋势分析

---

## 获取帮助

- 📖 [README](README.md) - 项目文档
- 📚 [使用指南](GUIDE.md) - 详细教程
- 🔗 [集成说明](INTEGRATION.md) - AstrBot集成
- 🐛 [Issue](https://github.com/anrrow/astrbot-plugin-airp-diary/issues) - 报告问题
