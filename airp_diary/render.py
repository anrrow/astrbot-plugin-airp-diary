"""
渲染模式管理 - 支持HTML和Markdown两种输出格式
"""

from enum import Enum
from typing import Optional
import re


class RenderMode(Enum):
    """渲染模式"""

    HTML = "html"
    MARKDOWN = "markdown"


class RenderConverter:
    """渲染格式转换器"""

    # HTML到Markdown的映射
    SPAN_STYLE_MAP = {
        "strikethrough": "~~",
        "highlight": "==",
        "underline": "__",
        "emphasis": "**",
        "handwritten": "*",
        "messy": "*",
        "censored": "█",
    }

    @staticmethod
    def html_to_markdown(html_text: str) -> str:
        """
        将HTML格式转换为Markdown
        
        Args:
            html_text: HTML格式的文本
            
        Returns:
            str: Markdown格式的文本
        """
        result = html_text

        # 替换<span>标签
        for style, markdown_marker in RenderConverter.SPAN_STYLE_MAP.items():
            pattern = rf'<span class="{style}">(.*?)</span>'

            if style == "strikethrough":
                replacement = rf"\1 (划掉)"
            elif style == "highlight":
                replacement = rf"「\1」"
            elif style == "underline":
                replacement = rf"__\1__"
            elif style == "emphasis":
                replacement = rf"**\1**"
            elif style == "handwritten":
                replacement = rf"*\1*"
            elif style == "messy":
                replacement = rf"~\1~"
            elif style == "censored":
                # 用█替换敏感内容
                def censor(match):
                    text = match.group(1)
                    return "█" * len(text)
                result = re.sub(pattern, censor, result)
                continue
            else:
                replacement = rf"\1"

            result = re.sub(pattern, replacement, result)

        # 替换<p>标签
        result = re.sub(r"<p>(.*?)</p>", r"\1", result, flags=re.DOTALL)

        # 段落之间加空行
        result = re.sub(r"\n(?!\n)", "\n\n", result)

        return result.strip()

    @staticmethod
    def markdown_to_html(markdown_text: str) -> str:
        """
        将Markdown格式转换为HTML
        
        Args:
            markdown_text: Markdown格式的文本
            
        Returns:
            str: HTML格式的文本
        """
        result = markdown_text

        # ~~删除线~~ -> <span class="strikethrough">删除线</span>
        result = re.sub(
            r"~~(.*?)~~",
            r'<span class="strikethrough">\1</span>',
            result,
        )

        # ==高亮== -> <span class="highlight">高亮</span>
        result = re.sub(
            r"==(.*?)==",
            r'<span class="highlight">\1</span>',
            result,
        )

        # __下划线__ -> <span class="underline">下划线</span>
        result = re.sub(
            r"__(.*?)__",
            r'<span class="underline">\1</span>',
            result,
        )

        # **强调** -> <span class="emphasis">强调</span>
        result = re.sub(
            r"\*\*(.*?)\*\*",
            r'<span class="emphasis">\1</span>',
            result,
        )

        # 段落处理 - 空行分隔的文本包装成<p>
        paragraphs = re.split(r"\n\n+", result)
        result = "\n".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())

        return result

    @staticmethod
    def convert(text: str, from_mode: RenderMode, to_mode: RenderMode) -> str:
        """
        在两种渲染模式之间转换
        
        Args:
            text: 源文本
            from_mode: 源格式
            to_mode: 目标格式
            
        Returns:
            str: 转换后的文本
        """
        if from_mode == to_mode:
            return text

        if from_mode == RenderMode.HTML and to_mode == RenderMode.MARKDOWN:
            return RenderConverter.html_to_markdown(text)
        elif from_mode == RenderMode.MARKDOWN and to_mode == RenderMode.HTML:
            return RenderConverter.markdown_to_html(text)
        else:
            return text


class RenderSelector:
    """渲染模式选择器"""

    def __init__(self, mode: str = "html"):
        """
        初始化渲染模式
        
        Args:
            mode: 渲染模式（html/markdown）
        """
        try:
            self.mode = RenderMode(mode.lower())
        except ValueError:
            self.mode = RenderMode.HTML

    def convert(self, text: str, from_mode: RenderMode = RenderMode.HTML) -> str:
        """
        根据当前模式转换文本
        
        Args:
            text: 源文本（假设为HTML格式）
            from_mode: 源格式（默认HTML）
            
        Returns:
            str: 转换后的文本
        """
        return RenderConverter.convert(text, from_mode, self.mode)

    def is_markdown(self) -> bool:
        """检查是否为Markdown模式"""
        return self.mode == RenderMode.MARKDOWN

    def is_html(self) -> bool:
        """检查是否为HTML模式"""
        return self.mode == RenderMode.HTML
