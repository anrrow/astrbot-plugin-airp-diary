# AstrBot 人格系统集成说明

## ✨ 重要变化（v2.1+）

从v2.1版本开始，**AIRP Diary插件不再独立管理角色人格**。相反，它会**自动从AstrBot的人格系统读取**你已经配置的人格信息。

### 这意味着什么？

**之前（v1.0-v2.0）：**
```json
{
  "airp-diary": {
    "character_name": "小月",
    "character_profile": "详细的人格设定..."  // ← 重复配置
  }
}
```

**现在（v2.1+）：**
```json
{
  "airp-diary": {
    // 无需配置！插件自动从AstrBot读取
  }
}
```

---

## 🚀 快速开始

### 步骤1：在AstrBot中配置人格

确保你在AstrBot的配置中定义了人格：

```json
{
  "personality": {
    "name": "小月",
    "profile": "性格温和但有点倔强的女孩...",
    "background": "24岁，来自小镇..."
  }
}
```

或者（取决于你的AstrBot版本）：

```json
{
  "character": {
    "name": "小月",
    "description": "详细的人格设定..."
  }
}
```

### 步骤2：安装AIRP Diary插件

```bash
cd /path/to/AstrBot/plugins
git clone https://github.com/anrrow2002-ctrl/astrbot-plugin-airp-diary.git
```

### 步骤3：重启AstrBot

插件会自动读取你的人格配置，无需额外配置！

---

## 📋 工作原理

插件会按以下优先级读取人格信息：

```
1. 尝试从 bot.personality 读取
   ├─ personality.name 或 personality.character_name
   └─ personality.profile / description / background

2. 尝试从 bot.character 读取
   ├─ character.name 或 character.character_name
   └─ character.profile / description

3. 尝试从 bot.character_name 直接读取

4. 使用插件配置中的 character_name（如果有）

5. 默认值："未命名角色"
```

---

## 🎯 配置选项

现在插件的配置非常简洁：

```json
{
  "airp-diary": {
    "character_name": "",                    // 可选：覆盖AstrBot的角色名
    "default_city": "东京",                 // 可选：用于天气API
    "render_mode": "html",                  // html或markdown
    "enable_state_cache": true,             // 启用状态缓存
    "enable_diary_history": true,           // 启用日记历史
    "enable_action_injection": true,        // 启用小动作
    "use_weather_api": false,               // 启用天气API
    "weather_provider": "openweather",      // 天气源
    "weather_api_key": null                 // 天气API密钥
  }
}
```

---

## ❓ 常见问题

### Q: 我之前的character_profile配置呢？

A: v2.1+版本不再支持在插件中配置character_profile。应该在AstrBot的人格系统中配置。

**如何迁移：**

1. 找到你在 `config.example.json` 中的 character_profile
2. 将内容移到AstrBot的personality配置中
3. 删除插件配置中的character_profile

### Q: 可以覆盖AstrBot的人格吗？

A: 可以！设置 `character_name` 字段来覆盖AstrBot的角色名：

```json
{
  "airp-diary": {
    "character_name": "我的自定义名字"  // 这会覆盖AstrBot的角色名
  }
}
```

但是**人格描述**仍然会从AstrBot读取，除非你修改AstrBot的配置。

### Q: 如果AstrBot没有配置人格怎么办？

A: 插件会使用默认值"未命名角色"，一切正常工作，只是缺少个性化的人格描述。

### Q: 如何知道插件是否成功读取了人格？

A: 生成日记时，如果日记的内容与你的AstrBot人格设定相符，说明集成成功！

也可以查看日记中的"内容"部分，是否反映了你定义的人格特征。

---

## 🔍 排查问题

### 日记不符合人格？

1. 确认你的人格描述足够详细
2. 查看AstrBot是否正确加载了人格配置
3. 检查插件是否成功读取了人格（查看log）

### 提示"未命名角色"？

这表示插件没有从AstrBot读取到人格。检查：

1. AstrBot是否配置了人格系统
2. 人格字段的名称是否为：personality / character / character_name
3. AstrBot是否正确初始化了人格

---

## 📝 从其他AI机器人迁移

如果你从其他AI机器人框架迁移到AstrBot，你需要：

1. 在AstrBot中重新配置人格（按照AstrBot的格式）
2. 安装AIRP Diary插件
3. 插件会自动使用新的人格配置

**无需在插件中重复配置人格！**

---

## 🔗 相关链接

- [AstrBot 官方文档](https://github.com/astrbot/astrbot)
- [AIRP Diary 项目](https://github.com/anrrow2002-ctrl/astrbot-plugin-airp-diary)
- [使用指南](GUIDE.md)
- [README](README.md)

---

**让你的角色用一套配置就能活起来！** ✨
