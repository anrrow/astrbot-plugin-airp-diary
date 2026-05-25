"""
与 ThinkingMaster 思维链插件的适配层
处理在线 / 线下模式的自动切换和 prompt 注入

通过 AstrBot 的 context.get_all_stars() API 查找已加载的 ThinkingMaster 插件实例。
即使 ThinkingMaster 未安装，所有方法也会安全降级返回默认值，不会抛错。
"""

from typing import Optional


class ThinkingMasterAdapter:
    """与 ThinkingMaster 插件的适配器"""

    def __init__(self, context):
        """
        初始化适配器

        Args:
            context: AstrBot 的 Context 实例
        """
        self.context = context
        self.thinking_master = None
        self._detect_thinking_master()

    def _detect_thinking_master(self):
        """检测 ThinkingMaster 插件是否已加载"""
        try:
            if hasattr(self.context, "get_all_stars"):
                stars = self.context.get_all_stars() or []
                for star_meta in stars:
                    name = (getattr(star_meta, "name", "") or "").lower()
                    if "thinking_master" in name or "thinkingmaster" in name:
                        inst = (
                            getattr(star_meta, "star_cls_inst", None)
                            or getattr(star_meta, "instance", None)
                            or star_meta
                        )
                        self.thinking_master = inst
                        return

            for attr in ("stars", "plugins"):
                stars = getattr(self.context, attr, None)
                if not stars:
                    continue
                for star in stars:
                    cls_name = star.__class__.__name__.lower()
                    if "thinkingmaster" in cls_name or "thinking_master" in cls_name:
                        self.thinking_master = star
                        return
        except Exception as e:
            print(f"[airp_diary] 检测 ThinkingMaster 失败: {e}")

    def is_enabled(self) -> bool:
        """检查 ThinkingMaster 是否存在且可用"""
        return self.thinking_master is not None

    def get_current_mode(self) -> str:
        """获取当前模式：online 或 offline"""
        if not self.is_enabled():
            return "online"
        try:
            return getattr(self.thinking_master, "current_mode", "online")
        except Exception:
            return "online"

    def should_use_novel_format(self) -> bool:
        """offline 模式时使用小说体"""
        return self.get_current_mode() == "offline"

    def get_mode_prompt_suffix(self) -> str:
        """根据当前模式返回 prompt 后缀"""
        if self.should_use_novel_format():
            return (
                "【当前为线下模式】请以小说体、叙述风格生成日记。"
                "用（）包裹动作、环境描写，用*斜体*表示角色内心活动。"
            )
        return "【当前为线上模式】保持标准的日记格式，直接描述当天的经历和感受。"


_adapter_instance: Optional[ThinkingMasterAdapter] = None


def init_adapter(context) -> ThinkingMasterAdapter:
    """初始化全局适配器"""
    global _adapter_instance
    _adapter_instance = ThinkingMasterAdapter(context)
    return _adapter_instance


def get_adapter() -> Optional[ThinkingMasterAdapter]:
    """获取全局适配器实例"""
    return _adapter_instance
