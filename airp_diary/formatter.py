"""
格式化工具 - 处理日期、时间等通用格式化
"""

from datetime import datetime

WEEKDAY_MAP = {
    0: "星期一",
    1: "星期二",
    2: "星期三",
    3: "星期四",
    4: "星期五",
    5: "星期六",
    6: "星期日",
}


def today_cn() -> str:
    """
    获取当前日期的中文格式
    
    Returns:
        str: 格式为 "YYYY年MM月DD日 星期X" 的日期字符串
    """
    now = datetime.now()
    return (
        f"{now.year}年"
        f"{now.month:02d}月"
        f"{now.day:02d}日 "
        f"{WEEKDAY_MAP[now.weekday()]}"
    )


def format_date(dt: datetime) -> str:
    """
    格式化任意日期为中文格式
    
    Args:
        dt: datetime 对象
        
    Returns:
        str: 格式为 "YYYY年MM月DD日 星期X" 的日期字符串
    """
    return (
        f"{dt.year}年"
        f"{dt.month:02d}月"
        f"{dt.day:02d}日 "
        f"{WEEKDAY_MAP[dt.weekday()]}"
    )


def wrap_span(text: str, cls: str) -> str:
    """
    将文本包装在 span class 中
    
    Args:
        text: 要包装的文本
        cls: CSS class 名称
        
    Returns:
        str: HTML 格式的包装文本
    """
    return f'<span class="{cls}">{text}</span>'


def wrap_paragraph(text: str) -> str:
    """
    将文本包装在段落标签中
    
    Args:
        text: 要包装的文本
        
    Returns:
        str: HTML 格式的段落文本
    """
    return f"<p>{text}</p>"
