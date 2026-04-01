"""
Slang Manager
Handles persistent storage of custom abbreviations and slang mappings
"""
import json
from pathlib import Path
from core.config import BASE_DIR

SLANG_FILE = BASE_DIR / "data" / "custom_abbreviations.json"

class SlangManager:
    """
    Manage custom abbreviation mappings
    """
    
    def __init__(self):
        """Initialize slang manager"""
        self.slang_file = SLANG_FILE
        self._ensure_file_exists()
        self.mappings = self.load_mappings()
    
    def _ensure_file_exists(self):
        """Create empty json file if it doesn't exist"""
        if not self.slang_file.parent.exists():
            self.slang_file.parent.mkdir(parents=True)
        
        if not self.slang_file.exists():
            with open(self.slang_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def load_mappings(self) -> dict:
        """Load mappings from disk"""
        try:
            with open(self.slang_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def save_mapping(self, short: str, full: str):
        """Save a new mapping"""
        self.mappings[short.lower()] = full
        with open(self.slang_file, 'w', encoding='utf-8') as f:
            json.dump(self.mappings, f, ensure_ascii=False, indent=2)
    
    def get_formatted_slang(self) -> str:
        """Returns slang as a formatted string for LLM prompts"""
        if not self.mappings:
            return "Không có từ viết tắt tùy chỉnh."
        
        lines = [f"- {short}: {full}" for short, full in self.mappings.items()]
        return "\n".join(lines)
