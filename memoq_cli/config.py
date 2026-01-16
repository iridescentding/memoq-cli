# -*- coding: utf-8 -*-
"""
memoQ CLI - 配置管理
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

# 默认配置文件搜索路径
CONFIG_SEARCH_PATHS = [
    Path.cwd() / "config.json",
    Path.home() / ".memoq" / "config.json",
    Path.home() / ".config" / "memoq" / "config.json",
]

# 全局配置实例
_config_instance: Optional["Config"] = None


class Config:
    """配置管理类"""
    
    def __init__(self, config_path: Optional[str] = None):
        self._config: Dict[str, Any] = {}
        self._config_path: Optional[Path] = None
        
        if config_path:
            self.load(config_path)
        else:
            self._auto_load()
    
    def _auto_load(self):
        """自动搜索并加载配置文件"""
        for path in CONFIG_SEARCH_PATHS:
            if path.exists():
                self.load(str(path))
                return
        
        # 如果没找到配置文件，使用默认值
        self._config = self._get_defaults()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "server": {
                "host": "https://localhost",
                "wsapi_port": 8080,
                "rsapi_base": "memoqserverhttpapi/v1"
            },
            "auth": {
                "api_key": "",
                "username": "",
                "password": ""
            },
            "export": {
                "default_path": "./exports",
                "xliff_version": "1.2"
            },
            "import": {
                "default_path": "./imports",
                "filter_system_files": True
            },
            "logging": {
                "level": "INFO",
                "log_file": ""
            }
        }
    
    def load(self, config_path: str):
        """加载配置文件"""
        path = Path(config_path)
        
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            self._config = json.load(f)
        
        self._config_path = path
    
    def save(self, config_path: Optional[str] = None):
        """保存配置文件"""
        path = Path(config_path) if config_path else self._config_path
        
        if not path:
            path = CONFIG_SEARCH_PATHS[0]
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=4, ensure_ascii=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._config.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值 (支持点号分隔的路径)"""
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split(".")
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    # ==================== 便捷属性 ====================
    
    @property
    def server_host(self) -> str:
        return self.get("server.host", "https://localhost")
    
    @property
    def wsapi_port(self) -> int:
        return self.get("server.wsapi_port", 8080)
    
    @property
    def rsapi_base(self) -> str:
        return self.get("server.rsapi_base", "memoqserverhttpapi/v1")
    
    @property
    def api_key(self) -> str:
        return self.get("auth.api_key", "")
    
    @property
    def username(self) -> str:
        return self.get("auth.username", "")
    
    @property
    def password(self) -> str:
        return self.get("auth.password", "")
    
    @property
    def export_path(self) -> str:
        return self.get("export.default_path", "./exports")
    
    @property
    def import_path(self) -> str:
        return self.get("import.default_path", "./imports")
    
    @property
    def log_level(self) -> str:
        return self.get("logging.level", "INFO")
    
    @property
    def log_file(self) -> str:
        return self.get("logging.log_file", "")

    @property
    def rsapi_port(self) -> int:
        return self.get("server.rsapi_port", 443)

    @property
    def rsapi_path(self) -> str:
        return self.get("server.rsapi_path", self.rsapi_base)

    @property
    def wsapi_base_url(self) -> str:
        """Get full WSAPI base URL"""
        host = self.server_host.rstrip("/")
        return f"{host}:{self.wsapi_port}/memoqservices"

    @property
    def rsapi_base_url(self) -> str:
        """Get full RSAPI base URL"""
        host = self.server_host.rstrip("/")
        path = self.rsapi_path.strip("/")
        return f"{host}:{self.rsapi_port}/{path}"


def get_config(config_path: Optional[str] = None) -> Config:
    """Get global config instance"""
    global _config_instance

    if _config_instance is None or config_path:
        _config_instance = Config(config_path)

    return _config_instance


def reset_config() -> None:
    """Reset global config instance"""
    global _config_instance
    _config_instance = None
