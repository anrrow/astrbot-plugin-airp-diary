"""
Prompt 加载系统 - 支持模块化 prompt 管理
"""

import os
from pathlib import Path
from typing import Optional, Dict

PROMPT_DIR = Path(__file__).parent / "prompts"


class PromptLoader:
    """Prompt模板加载器"""

    _cache: Dict[str, str] = {}

    @classmethod
    def load(cls, name: str) -> str:
        """
        加载prompt模板
        
        Args:
            name: prompt名称（不需要.txt扩展名）
            
        Returns:
            str: 模板内容
            
        Raises:
            FileNotFoundError: 模板不存在
        """
        if name in cls._cache:
            return cls._cache[name]

        prompt_file = PROMPT_DIR / f"{name}.txt"

        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt template not found: {name}")

        with open(prompt_file, "r", encoding="utf-8") as f:
            content = f.read()

        cls._cache[name] = content
        return content

    @classmethod
    def clear_cache(cls):
        """清除缓存"""
        cls._cache.clear()


# 便捷函数
def load_prompt(name: str) -> str:
    """快速加载prompt"""
    return PromptLoader.load(name)
