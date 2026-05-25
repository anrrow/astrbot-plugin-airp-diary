"""
日记格式校验和自动修复 - 确保日记输出格式正确
"""

import re
from typing import Tuple


class DiaryValidator:
    """日记格式校验器"""

    DIARY_START = "[日记]"
    CONTENT_MARKER = "内容："

    @staticmethod
    def validate(text: str) -> Tuple[bool, str]:
        """
        校验日记格式，如果不完整则自动修复
        
        Args:
            text: 日记文本
            
        Returns:
            tuple: (是否修复了, 修复后的文本)
        """
        original = text
        fixed = False

        # 检查是否以[日记]开头
        if not text.strip().startswith(DiaryValidator.DIARY_START):
            text = DiaryValidator.DIARY_START + "\n" + text
            fixed = True

        # 检查是否包含日期行
        if not re.search(r"日期：\d{4}年\d{2}月\d{2}日", text):
            text = DiaryValidator._inject_date(text)
            fixed = True

        # 检查是否包含天气行
        if not re.search(r"天气：", text):
            text = DiaryValidator._inject_weather(text)
            fixed = True

        # 检查是否包含内容标记
        if DiaryValidator.CONTENT_MARKER not in text:
            text = text.rstrip() + f"\n{DiaryValidator.CONTENT_MARKER}\n"
            fixed = True

        # 不再强制要求 <p> 标签，新版 system.txt 输出纯文本

        return fixed, text

    @staticmethod
    def _inject_date(text: str) -> str:
        """注入日期行"""
        from .formatter import today_cn

        date_line = f"日期：{today_cn()}"

        # 在[日记]之后插入
        if "[日记]" in text:
            text = text.replace("[日记]", f"[日记]\n{date_line}", 1)
        else:
            text = f"[日记]\n{date_line}\n" + text

        return text

    @staticmethod
    def _inject_weather(text: str) -> str:
        """注入天气行（默认值）"""
        weather_line = "天气：🌤️ 普通 / 20℃"

        # 在日期之后插入
        date_match = re.search(r"日期：.*\n", text)
        if date_match:
            text = text[:date_match.end()] + weather_line + "\n" + text[date_match.end():]
        else:
            text = text.rstrip() + f"\n{weather_line}\n"

        return text

    @staticmethod
    def _inject_paragraph(text: str) -> str:
        """注入段落（如果没有的话）"""
        if "内容：" in text:
            # 在内容：之后添加默认段落
            text = re.sub(
                r"(内容：)\n*",
                r"\1\n<p>……今天有点乱。</p>\n",
                text,
            )
        else:
            text = text.rstrip() + "\n内容：\n<p>……今天有点乱。</p>\n"

        return text

    @staticmethod
    def _fix_paragraphs(text: str) -> str:
        """修复未闭合的<p>标签"""
        # 查找所有<p>标签
        p_open = text.count("<p>")
        p_close = text.count("</p>")

        # 如果开标签多于闭标签，补充闭标签
        if p_open > p_close:
            missing = p_open - p_close
            for _ in range(missing):
                text += "</p>"

        # 如果闭标签多于开标签（这种情况少见，但也修复）
        elif p_close > p_open:
            missing = p_close - p_open
            for _ in range(missing):
                text = "<p>" + text

        return text

    @staticmethod
    def is_valid(text: str) -> bool:
        """
        检查日记是否有效（不修复）
        
        Args:
            text: 日记文本
            
        Returns:
            bool: 是否有效
        """
        checks = [
            text.strip().startswith("[日记]"),
            re.search(r"日期：\d{4}年\d{2}月\d{2}日", text) is not None,
            "天气：" in text,
            "内容：" in text,
            re.search(r"<p>.*?</p>", text, re.DOTALL) is not None,
        ]

        return all(checks)


# 小动作库 - 增加日记的人味
DIARY_ACTIONS = [
    "揉了揉眼睛",
    "把纸杯压扁",
    "盯着窗外看了一会",
    "鞋跟敲了两下地板",
    "叹了口气",
    "伸了个懒腰",
    "托着下巴想了想",
    "转了转笔",
    "抖了抖腿",
    "摸了摸脸",
    "指尖敲了敲桌子",
    "看了一眼手机又放下",
    "吹了吹发丝",
    "搓了搓手",
    "闭眼深呼吸",
]


def inject_action(text: str, probability: float = 0.3) -> str:
    """
    随机在日记中注入小动作（增加人味）
    
    Args:
        text: 日记文本
        probability: 注入概率（0-1）
        
    Returns:
        str: 注入后的文本
    """
    import random

    if random.random() > probability:
        return text

    action = random.choice(DIARY_ACTIONS)

    # 在"内容："标记后的第一段开头插入
    match = re.search(r"内容：\s*\n+", text)
    if match:
        insert_pos = match.end()
        text = text[:insert_pos] + action + "，" + text[insert_pos:]
    else:
        # 兜底：在文本最末尾追加
        text = text.rstrip() + "\n" + action + "。"

    return text
