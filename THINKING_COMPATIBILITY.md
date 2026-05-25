# AIRP Diary 与 ThinkingMaster 思维链插件兼容性说明

## 📋 概述

AIRP Diary v2.1+ 已针对 ThinkingMaster 思维链插件进行深度优化，两个插件可以完美协作，无冲突。

---

## ✅ 冲突分析与解决方案

### 问题1：Prompt注入冲突

**症状**：两个插件都修改system_prompt

**解决方案**：
- AIRP Diary 构建自己的prompt，不直接修改system_prompt
- ThinkingMaster 在外层注入CoT指令和原生屏蔽
- 两个的作用域不冲突（AIRP是内容prompt，ThinkingMaster是方法论prompt）

### 问题2：响应处理冲突

**症状**：ThinkingMaster提取<thinking>标签，可能破坏日记格式

**解决方案**：
- AIRP Diary生成的日记格式为：`[日记]\n日期：...\n天气：...\n内容：...`
- 即使有thinking标签，也会被提取出来，不影响日记的结构完整性
- 日记的核心内容（日期、天气、内容）在thinking标签之外，不会被破坏

### 问题3：模式感知冲突

**症状**：用户切换线下模式，日记格式没有改变

**解决方案**：✨ **已实现**
- AIRP Diary 现在会检测 ThinkingMaster 的当前模式
- 如果是 `offline` 模式，自动使用小说体prompt
- 如果是 `online` 模式，使用标准格式prompt
- 模式检测在初始化和每次请求时都会进行

---

## 🔄 工作流程

### 1. 用户输入"查看日记"

```
用户：查看日记
  ↓
AIRP Diary.diary()
  ↓
检测ThinkingMaster状态
  ├─ 是否存在？
  ├─ 当前模式是什么？(online/offline)
  └─ 选择对应prompt
  ↓
构建prompt
  ├─ 标准系统提示
  ├─ 模式相关提示（来自thinking_adapter）
  └─ 角色信息、天气、日期等
  ↓
调用 bot.llm.ask(prompt)
  ↓
LLM响应，可能包含：
  <thinking>...推理过程...</thinking>
  [日记]
  日期：...
  ...
  ↓
ThinkingMaster 拦截响应
  ├─ 提取<thinking>部分
  ├─ 从回复中移除thinking标签
  └─ 保留[日记]内容
  ↓
AIRP Diary 继续处理
  ├─ 格式校验
  ├─ 小动作注入
  ├─ 渲染转换
  └─ 保存历史
  ↓
用户：[日记]\n日期：...\n...
```

### 2. 模式切换流程

```
用户：线下模式
  ↓
ThinkingMaster.cmd_offline()
  ├─ 设置 current_mode = "offline"
  └─ 保存到文件
  ↓
用户：查看日记
  ↓
AIRP Diary.diary()
  ├─ 检测：thinking_adapter.should_use_novel_format()
  ├─ 结果：True（offline模式）
  ├─ 加载 diary_offline.txt（小说体prompt）
  └─ 模式提示：【当前为线下模式】...
  ↓
LLM 生成小说体日记
  ├─ 自称"我"
  ├─ （）包裹环境描写
  ├─ *斜体*表示内心活动
  └─ 仍保留[日记]格式
  ↓
用户看到：小说体风格的日记
```

---

## 🔧 技术实现

### ThinkingMaster 检测

```python
# 在 thinking_adapter.py 中
class ThinkingMasterAdapter:
    def _detect_thinking_master(self):
        """自动检测ThinkingMaster插件"""
        # 尝试多种方式获取
        # 1. bot.get_star_instance()
        # 2. bot.stars 列表
        # 3. 类名匹配
    
    def is_enabled(self) -> bool:
        """检查插件是否存在且启用"""
    
    def get_current_mode(self) -> str:
        """获取当前模式(online/offline)"""
    
    def should_use_novel_format(self) -> bool:
        """是否应该使用小说体格式"""
```

### 动态Prompt选择

```python
# 在 plugin.py 的 diary() 方法中
if use_offline_mode:
    diary_template = load_prompt("diary_offline")  # 小说体
else:
    diary_template = load_prompt("system")          # 标准
```

### Prompt内容

| 模式 | Prompt | 特点 |
|------|--------|------|
| online | `diary_context.txt` | 标准格式 + 上下文融合 |
| offline | `diary_offline.txt` | 小说体 + 环境细节 + 内心活动 |

---

## 📝 小说体格式示例

当启用线下模式时，日记会是这样：

```
[日记]
日期：2026年05月25日 星期日
天气：☀️ 晴朗 / 22℃
内容：

（午后的阳光透过窗户洒进来，有点晃眼。我从床上坐起来，揉了揉眼睛。）

又睡到中午了。*该反省一下，但其实不想改。*（赤脚踩在地板上，冷意从脚心窜上来。）

（走出门，便利店的冰柜又坏了。）店员说这花很适合窗边的光，我就买下来了。*奇怪的是，拿着这束花时，心情就莫名地好了一点。*
```

---

## ⚙️ 配置说明

无需额外配置！AIRP Diary 会自动检测和适配 ThinkingMaster。

如果想禁用自动检测，可以在config中添加：

```json
{
  "airp-diary": {
    "thinking_master_aware": false  // 禁用ThinkingMaster感知（可选）
  }
}
```

---

## 🐛 已知限制和注意事项

### 1. 顺序依赖

ThinkingMaster 必须在 AIRP Diary 之前加载（或无关），因为：
- AIRP Diary 在初始化时检测 ThinkingMaster
- 如果 ThinkingMaster 还未加载，检测可能失败

**解决方案**：两个插件都支持动态检测，即使顺序不对也能工作，只是可能需要重启后才能同步。

### 2. Thinking标签位置

如果LLM在日记**中间**插入thinking标签：

```
[日记]
日期：...
<thinking>思考过程</thinking>
天气：...
内容：...
```

ThinkingMaster 会提取thinking，结果变为：

```
[日记]
日期：...
天气：...
内容：...
```

**处理**：AIRP Diary 的 `DiaryValidator` 会自动修复格式，确保完整性。

### 3. 模式切换延迟

从 online 切换到 offline，下一次查看日记时才会生效。

**解决方案**：这是正常的，因为检测是动态的（每次请求时检测一次）。

---

## 🧪 测试检查清单

使用前，请检查以下几点：

- [ ] ThinkingMaster 插件已正确安装
- [ ] AIRP Diary 插件已更新到 v2.1+
- [ ] 两个插件都在plugins目录中
- [ ] AstrBot 能正常加载两个插件（查看日志无报错）

**测试步骤**：

1. 启动AstrBot
2. 查看日记（应该正常工作）
3. 输入"线下模式"
4. 再次查看日记（应该显示小说体格式）
5. 输入"线上模式"
6. 再次查看日记（应该恢复标准格式）

---

## 📚 相关文档

- [README.md](README.md) - 项目文档
- [GUIDE.md](GUIDE.md) - 使用指南
- [INTEGRATION.md](INTEGRATION.md) - AstrBot集成说明
- [thinking_adapter.py](airp_diary/thinking_adapter.py) - 适配器源码

---

## 🤝 问题反馈

如果遇到冲突或问题，请检查：

1. 日志是否有报错信息
2. 两个插件的版本是否兼容
3. 是否按顺序加载
4. AstrBot 是否正确初始化了两个插件

**报告Issue时请提供**：
- AstrBot版本
- AIRP Diary 版本
- ThinkingMaster 版本
- 具体错误日志
- 复现步骤

---

**两个插件已完美适配，享受更智慧的日记系统！** ✨
