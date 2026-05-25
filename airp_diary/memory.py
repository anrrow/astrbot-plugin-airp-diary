"""
角色状态内存系统 - 保存和加载角色状态、日记历史等
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

DEFAULT_STATE = {
    "mood": "平静",
    "energy": 75,
    "last_place": "家",
    "recent_event": "无",
    "unfinished_thought": "",
}


class CharacterMemory:
    """角色状态内存管理器"""

    def __init__(self, character_name: str, base_dir: str = "data"):
        """
        初始化角色内存
        
        Args:
            character_name: 角色名称
            base_dir: 数据保存目录（默认data/）
        """
        self.character_name = character_name
        self.base_dir = Path(base_dir)
        self.char_dir = self.base_dir / character_name
        self.state_file = self.char_dir / "state.json"
        self.diary_dir = self.char_dir / "diaries"

        # 创建目录
        self.char_dir.mkdir(parents=True, exist_ok=True)
        self.diary_dir.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> Dict[str, Any]:
        """
        加载角色当前状态
        
        Returns:
            dict: 角色状态，包括情绪、能量、最近地点等
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        return DEFAULT_STATE.copy()

    def save_state(self, state: Dict[str, Any]):
        """
        保存角色状态
        
        Args:
            state: 要保存的状态字典
        """
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def update_state(self, **kwargs):
        """
        更新角色状态（部分更新）
        
        Args:
            **kwargs: 要更新的字段和值
        """
        state = self.load_state()
        state.update(kwargs)
        self.save_state(state)

    def save_diary(self, content: str, date: Optional[str] = None) -> str:
        """
        保存日记
        
        Args:
            content: 日记内容
            date: 日期（格式：YYYY-MM-DD，默认今天）
            
        Returns:
            str: 保存的日记文件路径
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        diary_data = {
            "date": date,
            "content": content,
            "saved_at": datetime.now().isoformat(),
        }

        diary_file = self.diary_dir / f"{date}.json"

        with open(diary_file, "w", encoding="utf-8") as f:
            json.dump(diary_data, f, ensure_ascii=False, indent=2)

        return str(diary_file)

    def load_diary(self, date: Optional[str] = None) -> Optional[str]:
        """
        加载日记
        
        Args:
            date: 日期（格式：YYYY-MM-DD，默认今天）
            
        Returns:
            str: 日记内容，不存在返回None
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        diary_file = self.diary_dir / f"{date}.json"

        if diary_file.exists():
            try:
                with open(diary_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("content")
            except (json.JSONDecodeError, IOError):
                pass

        return None

    def get_recent_diary(self, days_ago: int = 1) -> Optional[str]:
        """
        获取过去N天的日记
        
        Args:
            days_ago: 几天前（1=昨天，7=上周）
            
        Returns:
            str: 日记内容
        """
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        return self.load_diary(date)

    def list_diaries(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        列出最近的日记
        
        Args:
            limit: 返回的最大数量
            
        Returns:
            list: 日记列表，按日期降序排列
        """
        diaries = []

        if not self.diary_dir.exists():
            return diaries

        for diary_file in sorted(self.diary_dir.glob("*.json"), reverse=True)[:limit]:
            try:
                with open(diary_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    diaries.append({
                        "date": data.get("date"),
                        "content": data.get("content"),
                    })
            except (json.JSONDecodeError, IOError):
                continue

        return diaries

    def archive_state(self):
        """
        存档当前状态（用于后续恢复）
        """
        archive_dir = self.char_dir / "archives"
        archive_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_file = archive_dir / f"state_{timestamp}.json"

        state = self.load_state()

        with open(archive_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
