"""
AstrBot AIRP Diary Plugin - 主入口文件

AIRP角色日记系统：支持查看日记、查看心声、查看足迹、翻日记、历史日记。
自动跟随当前会话使用的 AstrBot 人格，每个人格独立存档。
"""

import re
from datetime import datetime, timedelta

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig, logger

from .airp_diary.memory import CharacterMemory
from .airp_diary.formatter import today_cn
from .airp_diary.validator import DiaryValidator, inject_action
from .airp_diary.weather import init_weather_api, get_weather_api, WeatherAPI
from .airp_diary.render import RenderSelector, RenderMode
from .airp_diary.prompt_loader import load_prompt

try:
    from .airp_diary.thinking_adapter import init_adapter
    THINKING_MASTER_AVAILABLE = True
except ImportError:
    THINKING_MASTER_AVAILABLE = False


@register(
    "airp_diary",
    "anrrow2002-ctrl",
    "AIRP角色日记系统 - 自动跟随当前会话人格，支持多角色独立存档",
    "2.2.0",
    "https://github.com/anrrow/astrbot-plugin-airp-diary",
)
class AirpDiary(Star):
    """AIRP 角色日记插件"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

        # 渲染模式
        render_mode = self.config.get("render_mode", "html")
        self.renderer = RenderSelector(render_mode)

        # 天气 API
        if self.config.get("use_weather_api", False) and self.config.get(
            "weather_api_key"
        ):
            init_weather_api(
                self.config.get("weather_provider", "openweather"),
                self.config.get("weather_api_key"),
            )

        # ThinkingMaster 适配器（可选）
        self.thinking_adapter = None
        if THINKING_MASTER_AVAILABLE:
            try:
                self.thinking_adapter = init_adapter(context)
            except Exception as e:
                logger.warning(f"[airp_diary] ThinkingMaster 适配器初始化失败: {e}")

        logger.info("[airp_diary] 插件已加载，将自动跟随当前会话人格")

    # ---------- 核心：从当前会话动态获取人格 ----------

    async def _resolve_persona(self, event: AstrMessageEvent):
        """
        获取当前会话正在使用的人格信息

        Returns:
            (name: str, profile: str) 元组
            name: 人格名（用于存档目录）
            profile: 人格完整 system_prompt（传给 LLM）
        """
        umo = event.unified_msg_origin

        # 优先级 1：从当前会话 conversation 拿到 persona_id
        try:
            conv_mgr = getattr(self.context, "conversation_manager", None)
            persona_mgr = getattr(self.context, "persona_manager", None)

            if conv_mgr and persona_mgr:
                cid = await conv_mgr.get_curr_conversation_id(umo)
                if cid:
                    conv = await conv_mgr.get_conversation(umo, cid)
                    persona_id = getattr(conv, "persona_id", None) if conv else None

                    if persona_id:
                        try:
                            persona = await persona_mgr.get_persona(persona_id)
                            if persona:
                                name = (
                                    getattr(persona, "persona_id", None)
                                    or persona_id
                                )
                                prompt = (
                                    getattr(persona, "system_prompt", None)
                                    or getattr(persona, "prompt", None)
                                    or ""
                                )
                                return str(name), str(prompt)
                        except Exception as e:
                            logger.debug(
                                f"[airp_diary] 读取 persona {persona_id} 失败: {e}"
                            )
        except Exception as e:
            logger.debug(f"[airp_diary] 从会话读取人格失败: {e}")

        # 优先级 2：默认人格 (v3 兼容格式)
        try:
            persona_mgr = getattr(self.context, "persona_manager", None)
            if persona_mgr and hasattr(persona_mgr, "get_default_persona_v3"):
                persona = await persona_mgr.get_default_persona_v3(umo=umo)
                if persona and isinstance(persona, dict):
                    name = persona.get("name") or "未命名角色"
                    prompt = persona.get("prompt", "") or ""
                    return str(name), str(prompt)
        except Exception as e:
            logger.debug(f"[airp_diary] 读取默认人格失败: {e}")

        # 优先级 3：插件配置里手动指定的角色名（兜底）
        configured = (self.config.get("character_name") or "").strip()
        if configured:
            return configured, ""

        return "未命名角色", ""

    async def _get_conversation_history(
        self, event: AstrMessageEvent, max_messages: int = 30
    ) -> str:
        """
        获取当前会话最近的对话历史

        Args:
            event: 消息事件
            max_messages: 最多取多少条历史消息

        Returns:
            格式化后的对话历史字符串，用于注入 prompt
        """
        umo = event.unified_msg_origin
        try:
            conv_mgr = getattr(self.context, "conversation_manager", None)
            if not conv_mgr:
                return ""

            cid = await conv_mgr.get_curr_conversation_id(umo)
            if not cid:
                return ""

            conv = await conv_mgr.get_conversation(umo, cid)
            if not conv:
                return ""

            # 兜底多个字段名 (不同 astrbot 版本字段名可能不同)
            raw_history = (
                getattr(conv, "history", None)
                or getattr(conv, "messages", None)
                or getattr(conv, "chat_history", None)
                or ""
            )

            # history 可能是 JSON 字符串，也可能是 list
            history_list = None
            if isinstance(raw_history, str):
                if not raw_history.strip():
                    return ""
                try:
                    import json
                    history_list = json.loads(raw_history)
                except Exception:
                    return raw_history[-3000:]  # 解析失败就当文本截断返回
            elif isinstance(raw_history, list):
                history_list = raw_history

            if not history_list:
                return ""

            # 取最近 max_messages 条
            recent = history_list[-max_messages:]
            lines = []
            for msg in recent:
                if not isinstance(msg, dict):
                    continue
                role = msg.get("role", "?")
                content = msg.get("content", "")

                # 多模态消息（list of parts）
                if isinstance(content, list):
                    parts = []
                    for c in content:
                        if isinstance(c, dict):
                            t = c.get("text") or c.get("content")
                            if t:
                                parts.append(str(t))
                        elif isinstance(c, str):
                            parts.append(c)
                    content = " ".join(parts)

                content = str(content).strip()
                if not content:
                    continue

                # 截断过长的单条消息
                if len(content) > 400:
                    content = content[:400] + "..."

                role_name = {
                    "user": "用户",
                    "assistant": "角色",
                    "system": "[系统]",
                }.get(role, role)

                lines.append(f"{role_name}: {content}")

            return "\n".join(lines)

        except Exception as e:
            logger.warning(f"[airp_diary] 读取对话历史失败: {e}")
            return ""

    def _get_memory(self, character_name: str) -> CharacterMemory:
        """根据角色名获取该角色独立的 memory 实例"""
        # 防止文件系统不喜欢的字符出现在路径
        safe_name = re.sub(r'[\\/:*?"<>|]', "_", character_name).strip() or "default"
        return CharacterMemory(safe_name, base_dir="data/airp_diary")

    async def _get_weather(self) -> str:
        """
        获取今天的天气

        Returns:
            - 启用了真实天气 API：返回真实天气字符串
            - 未启用 API：返回空字符串，让 LLM 在生成日记时根据角色处境自己虚构
        """
        try:
            if self.config.get("use_weather_api", False):
                city = self.config.get("default_city", "东京")
                api = get_weather_api()
                weather = await api.get_weather(city)
                if weather:
                    return weather
        except Exception as e:
            logger.warning(f"[airp_diary] 获取天气失败，改由LLM自行虚构: {e}")
        return ""

    async def _call_llm(self, prompt: str, event: AstrMessageEvent) -> str:
        """调用 LLM 生成内容"""
        provider = self.context.get_using_provider(
            umo=event.unified_msg_origin
        )
        if not provider:
            raise RuntimeError("未配置任何可用的 LLM 提供商，请到 AstrBot 配置中添加。")

        resp = await provider.text_chat(
            prompt=prompt,
            contexts=[],
            system_prompt="",
        )
        return resp.completion_text

    def _get_mode_hint(self) -> str:
        """获取 ThinkingMaster 模式提示"""
        if self.thinking_adapter and self.thinking_adapter.is_enabled():
            return self.thinking_adapter.get_mode_prompt_suffix()
        return ""

    def _get_prompt(self, name: str) -> str:
        """
        获取 prompt：优先使用用户在 WebUI 配置里自定义的，留空则回退到插件内置 .txt 文件

        Args:
            name: prompt 名称（system / diary_context / voice / footprint / history / diary_offline）

        Returns:
            prompt 内容字符串
        """
        config_key = f"prompt_{name}"
        custom = (self.config.get(config_key) or "").strip()
        if custom:
            logger.debug(f"[airp_diary] 使用用户自定义的 {name} prompt")
            return custom
        return load_prompt(name)

    def _build_character_info(self, name: str, profile: str) -> str:
        """拼接角色信息块"""
        if profile.strip():
            return f"【角色名】{name}\n【角色设定】\n{profile}"
        return f"【角色名】{name}\n（未在 AstrBot 中配置详细人格 prompt）"

    # ---------- 指令 ----------

    @filter.command("查看日记")
    async def diary(self, event: AstrMessageEvent):
        """生成今天的日记（按当前会话人格）"""
        try:
            name, profile = await self._resolve_persona(event)
            memory = self._get_memory(name)
            state = memory.load_state()

            # ThinkingMaster 模式判断
            use_offline = False
            if self.thinking_adapter and self.thinking_adapter.is_enabled():
                use_offline = self.thinking_adapter.should_use_novel_format()

            system_prompt = self._get_prompt("system")
            diary_context_prompt = self._get_prompt("diary_context")
            if use_offline:
                try:
                    diary_template = self._get_prompt("diary_offline")
                except FileNotFoundError:
                    diary_template = system_prompt
            else:
                diary_template = system_prompt

            weather = await self._get_weather()
            character_info = self._build_character_info(name, profile)
            chat_history = await self._get_conversation_history(event, max_messages=30)

            context_prompt = diary_context_prompt.format(
                mood=state.get("mood", "平静"),
                energy=state.get("energy", 75),
                last_place=state.get("last_place", "家"),
                recent_event=state.get("recent_event", "无"),
                unfinished_thought=state.get("unfinished_thought", ""),
                system_prompt=diary_template,
            )

            if weather:
                weather_line = f"今天的天气：{weather}"
            else:
                weather_line = (
                    "今天的天气：（请根据角色当前所在地点、季节、心情，"
                    "在日记里合理虚构一个天气，格式 emoji + 天气描述 + 温度）"
                )

            history_block = ""
            if chat_history:
                history_block = (
                    f"\n\n【最近的对话记录（这是今天/最近真实发生的事，日记必须围绕这些内容展开）】\n"
                    f"{chat_history}\n"
                    f"【对话记录结束】\n"
                )

            full_prompt = (
                f"{character_info}\n"
                f"{history_block}\n"
                f"{context_prompt}\n\n"
                f"今天的日期是：{today_cn()}\n"
                f"{weather_line}\n\n"
                f"{self._get_mode_hint()}\n\n"
                f"请以上述角色的视角和说话习惯，"
                f"严格按照[日记]格式，生成 ta 今天的日记。"
                f"内容必须贴合角色设定且必须围绕上面【最近的对话记录】里实际发生的事来写——"
                f"是谁说了什么、做了什么、感受到了什么。不要凭空虚构对话里没发生的事。"
                f"如果没有对话记录，再按角色当前状态合理生成日常内容。"
            )

            result = await self._call_llm(full_prompt, event)
            _, result = DiaryValidator.validate(result)

            if self.config.get("enable_action_injection", True):
                result = inject_action(result)

            if self.config.get("enable_diary_history", True):
                memory.save_diary(result)

            memory.update_state(last_diary_date=today_cn())
            result = self.renderer.convert(result, RenderMode.HTML)

            yield event.plain_result(result)

        except Exception as e:
            logger.error(f"[airp_diary] 日记生成失败: {e}", exc_info=True)
            yield event.plain_result(f"❌ 日记生成失败：{e}")

    @filter.command("查看心声")
    async def inner_voice(self, event: AstrMessageEvent):
        """生成角色当下的心声"""
        try:
            name, profile = await self._resolve_persona(event)
            memory = self._get_memory(name)
            state = memory.load_state()
            voice_prompt = self._get_prompt("voice")
            character_info = self._build_character_info(name, profile)
            chat_history = await self._get_conversation_history(event, max_messages=20)

            last_diary = memory.load_diary()
            diary_context = (
                f"\n最近的日记片段：\n{last_diary}" if last_diary else ""
            )

            history_block = ""
            if chat_history:
                history_block = (
                    f"\n【最近的对话记录（这是 ta 实际经历的事）】\n"
                    f"{chat_history}\n"
                    f"【对话记录结束】\n"
                )

            full_prompt = (
                f"{character_info}\n"
                f"{history_block}\n"
                f"当前状态：{state.get('mood', '平静')}，能量值{state.get('energy', 75)}/100\n"
                f"{diary_context}\n\n"
                f"{voice_prompt}\n\n"
                f"{self._get_mode_hint()}\n\n"
                f"请以上述角色的视角、语气、习惯，生成 ta 此刻的内心独白。"
                f"独白必须围绕上面对话记录里实际发生的事——是 ta 没说出口的话、藏在心里的想法、"
                f"对刚才那段对话的真实感受。不要脱离对话内容空谈。"
            )

            result = await self._call_llm(full_prompt, event)
            result = self.renderer.convert(result, RenderMode.HTML)

            yield event.plain_result(result)

        except Exception as e:
            logger.error(f"[airp_diary] 心声生成失败: {e}", exc_info=True)
            yield event.plain_result(f"❌ 心声生成失败：{e}")

    @filter.command("查看足迹")
    async def footprint(self, event: AstrMessageEvent):
        """生成角色最近的足迹"""
        try:
            name, profile = await self._resolve_persona(event)
            memory = self._get_memory(name)
            state = memory.load_state()
            footprint_prompt = self._get_prompt("footprint")
            character_info = self._build_character_info(name, profile)
            chat_history = await self._get_conversation_history(event, max_messages=20)

            history_block = ""
            if chat_history:
                history_block = (
                    f"\n【最近的对话记录（从中提炼 ta 可能去过的地方）】\n"
                    f"{chat_history}\n"
                    f"【对话记录结束】\n"
                )

            full_prompt = (
                f"{character_info}\n"
                f"{history_block}\n"
                f"最近常去的地点：{state.get('favorite_places', '家、咖啡馆')}\n"
                f"{footprint_prompt}\n\n"
                f"请以上述角色的视角，生成 ta 最近的足迹。"
                f"如果对话记录里提到了具体地点或事件，请优先把这些地点写进去；"
                f"其余地点用角色生活范围内合理的场所补充。"
            )

            result = await self._call_llm(full_prompt, event)
            result = self.renderer.convert(result, RenderMode.HTML)

            yield event.plain_result(result)

        except Exception as e:
            logger.error(f"[airp_diary] 足迹生成失败: {e}", exc_info=True)
            yield event.plain_result(f"❌ 足迹生成失败：{e}")

    @filter.command("翻日记")
    async def flip_diary(self, event: AstrMessageEvent):
        """列出当前角色近期的日记"""
        try:
            name, _ = await self._resolve_persona(event)
            memory = self._get_memory(name)

            diaries = memory.list_diaries(limit=5)
            if not diaries:
                yield event.plain_result(f"【{name}】还没有保存的日记呢。")
                return

            message = f"📖 【{name}】最近的日记：\n\n"
            for i, d in enumerate(diaries, 1):
                date = d.get("date", "未知日期")
                content = (d.get("content", "") or "")[:100]
                content = (
                    content.replace("\n", "")
                    .replace("<p>", "")
                    .replace("</p>", "")
                )
                message += f"{i}. {date}\n   {content}...\n\n"

            yield event.plain_result(message)

        except Exception as e:
            logger.error(f"[airp_diary] 翻日记失败: {e}", exc_info=True)
            yield event.plain_result(f"❌ 翻日记失败：{e}")

    @filter.regex(r"查看(\d+天前|昨天|前天|上周|上个月)日记")
    async def history_diary(self, event: AstrMessageEvent):
        """查看历史日记（昨天/前天/上周/N天前/上个月）"""
        try:
            name, profile = await self._resolve_persona(event)
            memory = self._get_memory(name)

            msg = event.message_str

            timeframe_map = {
                "昨天": (1, "昨天"),
                "前天": (2, "前天"),
                "上周": (7, "上周"),
                "上个月": (30, "上个月"),
            }

            days_ago = 1
            date_desc = "昨天"
            matched = False

            for key, (days, desc) in timeframe_map.items():
                if key in msg:
                    days_ago = days
                    date_desc = desc
                    matched = True
                    break

            if not matched:
                m = re.search(r"(\d+)天前", msg)
                if m:
                    days_ago = int(m.group(1))
                    date_desc = f"{days_ago}天前"

            diary = memory.get_recent_diary(days_ago)
            if diary:
                result = diary
            else:
                target_date = (
                    datetime.now() - timedelta(days=days_ago)
                ).strftime("%Y-%m-%d")
                history_prompt = self._get_prompt("history")
                character_info = self._build_character_info(name, profile)

                full_prompt = (
                    f"{character_info}\n\n"
                    f"{history_prompt.format(date_desc=date_desc)}\n\n"
                    f"请以上述角色视角，生成 ta 在{date_desc}的日记。"
                )

                result = await self._call_llm(full_prompt, event)
                _, result = DiaryValidator.validate(result)

                if self.config.get("enable_diary_history", True):
                    memory.save_diary(result, target_date)

            result = self.renderer.convert(result, RenderMode.HTML)
            yield event.plain_result(result)

        except Exception as e:
            logger.error(f"[airp_diary] 历史日记失败: {e}", exc_info=True)
            yield event.plain_result(f"❌ 历史日记生成失败：{e}")

    async def terminate(self):
        """插件卸载时调用"""
        logger.info("[airp_diary] 插件已卸载")

    @filter.command("airp调试")
    async def debug_persona(self, event: AstrMessageEvent):
        """调试：查看当前会话插件读到了什么人格信息"""
        try:
            umo = event.unified_msg_origin
            lines = ["🔍 AIRP 日记插件 - 深度诊断", ""]
            lines.append(f"会话标识: {umo}")
            lines.append("")

            conv_mgr = getattr(self.context, "conversation_manager", None)
            persona_mgr = getattr(self.context, "persona_manager", None)

            lines.append(f"conversation_manager: {conv_mgr is not None}")
            lines.append(f"persona_manager: {persona_mgr is not None}")

            persona_id = None
            if conv_mgr:
                try:
                    cid = await conv_mgr.get_curr_conversation_id(umo)
                    if cid:
                        conv = await conv_mgr.get_conversation(umo, cid)
                        if conv:
                            persona_id = getattr(conv, "persona_id", None)
                            lines.append(f"会话绑定 persona_id: {persona_id!r}")
                except Exception as e:
                    lines.append(f"读取会话失败: {e}")

            lines.append("")
            lines.append("=" * 30)
            lines.append("【persona 对象深度探测】")
            lines.append("=" * 30)

            if persona_mgr and persona_id:
                # 尝试 get_persona
                try:
                    persona = await persona_mgr.get_persona(persona_id)
                    lines.append(f"get_persona({persona_id!r}) 返回: {persona is not None}")
                    if persona is not None:
                        lines.append(f"对象类型: {type(persona).__name__}")
                        lines.append("")
                        lines.append("所有可见属性:")
                        for attr in dir(persona):
                            if attr.startswith("_"):
                                continue
                            try:
                                val = getattr(persona, attr)
                                if callable(val):
                                    continue
                                val_str = repr(val)
                                if len(val_str) > 200:
                                    val_str = val_str[:200] + "..."
                                lines.append(f"  • {attr} = {val_str}")
                            except Exception as e:
                                lines.append(f"  • {attr} = <读取失败: {e}>")
                except Exception as e:
                    lines.append(f"get_persona 抛异常: {type(e).__name__}: {e}")

                # 尝试 get_all_personas
                lines.append("")
                lines.append("=" * 30)
                lines.append("【所有人格列表】")
                try:
                    all_personas = await persona_mgr.get_all_personas()
                    lines.append(f"共 {len(all_personas)} 个人格")
                    for p in all_personas[:5]:
                        pid = getattr(p, "persona_id", "?")
                        sp = (
                            getattr(p, "system_prompt", None)
                            or getattr(p, "prompt", None)
                            or ""
                        )
                        lines.append(f"  - {pid!r} (prompt 长度: {len(sp)})")
                except Exception as e:
                    lines.append(f"get_all_personas 失败: {e}")

                # 尝试 v3 兼容方法
                lines.append("")
                lines.append("=" * 30)
                lines.append("【default_persona_v3】")
                try:
                    pv3 = await persona_mgr.get_default_persona_v3(umo=umo)
                    lines.append(f"返回: {pv3!r}"[:500])
                except Exception as e:
                    lines.append(f"失败: {e}")

            yield event.plain_result("\n".join(lines))

        except Exception as e:
            logger.error(f"[airp_diary] 调试失败: {e}", exc_info=True)
            yield event.plain_result(f"❌ 调试失败：{e}")

    @filter.command("airp历史调试")
    async def debug_history(self, event: AstrMessageEvent):
        """调试：查看插件能不能读到对话历史"""
        try:
            lines = ["🔍 对话历史读取诊断", ""]

            umo = event.unified_msg_origin
            conv_mgr = getattr(self.context, "conversation_manager", None)
            if not conv_mgr:
                yield event.plain_result("❌ 没有 conversation_manager")
                return

            cid = await conv_mgr.get_curr_conversation_id(umo)
            lines.append(f"会话ID: {cid}")
            if not cid:
                yield event.plain_result("\n".join(lines))
                return

            conv = await conv_mgr.get_conversation(umo, cid)
            lines.append(f"会话对象: {conv is not None}")
            if not conv:
                yield event.plain_result("\n".join(lines))
                return

            # 探测可能的字段
            for field in ("history", "messages", "chat_history"):
                val = getattr(conv, field, None)
                if val is None:
                    lines.append(f"  • {field}: 不存在")
                    continue
                t = type(val).__name__
                if isinstance(val, (list, str)):
                    lines.append(f"  • {field}: {t}, 长度={len(val)}")
                else:
                    lines.append(f"  • {field}: {t}")

            # 实际调用 _get_conversation_history
            lines.append("")
            lines.append("=" * 30)
            lines.append("【插件实际读到的历史（前500字符）】")
            history = await self._get_conversation_history(event, max_messages=10)
            if history:
                lines.append(history[:500])
            else:
                lines.append("⚠️ 空")

            yield event.plain_result("\n".join(lines))

        except Exception as e:
            logger.error(f"[airp_diary] 历史调试失败: {e}", exc_info=True)
            yield event.plain_result(f"❌ 历史调试失败：{e}")