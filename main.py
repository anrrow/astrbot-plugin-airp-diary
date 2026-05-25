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
                            persona = persona_mgr.get_persona(persona_id)
                            if persona:
                                name = (
                                    getattr(persona, "persona_id", None)
                                    or persona_id
                                )
                                prompt = getattr(persona, "system_prompt", "") or ""
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
                persona = persona_mgr.get_default_persona_v3(umo=umo)
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

    def _get_memory(self, character_name: str) -> CharacterMemory:
        """根据角色名获取该角色独立的 memory 实例"""
        # 防止文件系统不喜欢的字符出现在路径
        safe_name = re.sub(r'[\\/:*?"<>|]', "_", character_name).strip() or "default"
        return CharacterMemory(safe_name, base_dir="data/airp_diary")

    async def _get_weather(self) -> str:
        """获取今天的天气"""
        try:
            if self.config.get("use_weather_api", False):
                city = self.config.get("default_city", "东京")
                api = get_weather_api()
                weather = await api.get_weather(city)
                if weather:
                    return weather
        except Exception as e:
            logger.warning(f"[airp_diary] 获取天气失败: {e}")
        return WeatherAPI._default_weather()

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

            system_prompt = load_prompt("system")
            diary_context_prompt = load_prompt("diary_context")
            if use_offline:
                try:
                    diary_template = load_prompt("diary_offline")
                except FileNotFoundError:
                    diary_template = system_prompt
            else:
                diary_template = system_prompt

            weather = await self._get_weather()
            character_info = self._build_character_info(name, profile)

            context_prompt = diary_context_prompt.format(
                mood=state.get("mood", "平静"),
                energy=state.get("energy", 75),
                last_place=state.get("last_place", "家"),
                recent_event=state.get("recent_event", "无"),
                unfinished_thought=state.get("unfinished_thought", ""),
                system_prompt=diary_template,
            )

            full_prompt = (
                f"{character_info}\n\n"
                f"{context_prompt}\n\n"
                f"今天的日期是：{today_cn()}\n"
                f"今天的天气：{weather}\n\n"
                f"{self._get_mode_hint()}\n\n"
                f"请以上述角色的视角和说话习惯，"
                f"严格按照[日记]格式，生成 ta 今天的日记。"
                f"内容必须贴合角色设定，禁止脱离人设。"
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
            voice_prompt = load_prompt("voice")
            character_info = self._build_character_info(name, profile)

            last_diary = memory.load_diary()
            diary_context = (
                f"\n最近的日记片段：\n{last_diary}" if last_diary else ""
            )

            full_prompt = (
                f"{character_info}\n\n"
                f"当前状态：{state.get('mood', '平静')}，能量值{state.get('energy', 75)}/100\n"
                f"{diary_context}\n\n"
                f"{voice_prompt}\n\n"
                f"{self._get_mode_hint()}\n\n"
                f"请以上述角色的视角、语气、习惯，生成 ta 此刻的心声。"
                f"内容必须贴合角色设定。"
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
            footprint_prompt = load_prompt("footprint")
            character_info = self._build_character_info(name, profile)

            full_prompt = (
                f"{character_info}\n\n"
                f"最近常去的地点：{state.get('favorite_places', '家、咖啡馆')}\n"
                f"{footprint_prompt}\n\n"
                f"请以上述角色的视角，生成 ta 最近的足迹。"
                f"内容必须贴合角色设定。"
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
                history_prompt = load_prompt("history")
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
            lines = ["🔍 AIRP 日记插件 - 当前会话人格诊断", ""]
            lines.append(f"会话标识 (umo): {umo}")
            lines.append("")

            # 1. 看会话管理器
            conv_mgr = getattr(self.context, "conversation_manager", None)
            lines.append(f"conversation_manager 可用: {conv_mgr is not None}")

            cid = None
            conv = None
            if conv_mgr:
                try:
                    cid = await conv_mgr.get_curr_conversation_id(umo)
                    lines.append(f"当前会话ID (cid): {cid}")
                except Exception as e:
                    lines.append(f"获取 cid 失败: {e}")

                if cid:
                    try:
                        conv = await conv_mgr.get_conversation(umo, cid)
                        lines.append(f"会话对象: {conv is not None}")
                        if conv:
                            pid = getattr(conv, "persona_id", None)
                            lines.append(f"会话绑定的 persona_id: {pid!r}")
                    except Exception as e:
                        lines.append(f"获取会话对象失败: {e}")

            lines.append("")

            # 2. 调用真正的 _resolve_persona
            name, profile = await self._resolve_persona(event)
            lines.append(f"插件最终解析到的角色名: {name!r}")
            lines.append(f"人格 prompt 长度: {len(profile)} 字符")
            lines.append("")
            lines.append("人格 prompt 前 300 字符预览：")
            lines.append("-" * 30)
            if profile:
                lines.append(profile[:300])
                if len(profile) > 300:
                    lines.append("...(已截断)")
            else:
                lines.append("⚠️ 空！插件没读到任何人格内容！")
            lines.append("-" * 30)

            yield event.plain_result("\n".join(lines))

        except Exception as e:
            logger.error(f"[airp_diary] 调试失败: {e}", exc_info=True)
            yield event.plain_result(f"❌ 调试失败：{e}")