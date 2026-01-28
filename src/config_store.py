# -*- coding: utf-8 -*-
"""
===================================
A股自选股智能分析系统 - 配置存储服务
===================================

职责：
1. 配置的持久化读写（SQLite 数据库）
2. 敏感字段加密/解密
3. 批量配置操作
"""

import os
import base64
import hashlib
import logging
from typing import Optional, Dict, List
from datetime import datetime

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class ConfigStore:
    """
    配置存储服务
    
    负责配置的持久化读写，包含加密/解密逻辑。
    """
    
    # 敏感字段列表（需要加密）
    SENSITIVE_KEYS = {
        'gemini_api_key',
        'tushare_token',
        'tavily_api_keys',
        'serpapi_keys',
        'bocha_api_keys',
        'email_password',
        'openai_api_key',
        'deepseek_api_key',
        'zhipu_api_key',
        'telegram_bot_token',
        'discord_bot_token',
        'feishu_app_secret',
        'dingtalk_app_secret',
    }
    
    _instance: Optional['ConfigStore'] = None
    _fernet: Optional[Fernet] = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化配置存储服务
        
        Args:
            db_path: 数据库路径（用于生成加密密钥）
        """
        if self._initialized:
            return
        
        self._db_path = db_path or os.getenv('DATABASE_PATH', './data/stock_analysis.db')
        self._init_encryption()
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'ConfigStore':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（用于测试）"""
        cls._instance = None
        cls._fernet = None
    
    def _init_encryption(self) -> None:
        """初始化加密器"""
        try:
            key = self._get_encryption_key()
            self._fernet = Fernet(key)
            logger.debug("加密器初始化成功")
        except Exception as e:
            logger.warning(f"加密器初始化失败，将使用明文存储: {e}")
            self._fernet = None
    
    def _get_encryption_key(self) -> bytes:
        """
        生成加密密钥
        
        基于数据库路径生成固定密钥，确保重启后可解密
        """
        salt = self._db_path.encode()
        key = hashlib.pbkdf2_hmac('sha256', b'stock-analysis-secret', salt, 100000)
        return base64.urlsafe_b64encode(key)
    
    def _encrypt(self, value: str) -> str:
        """加密敏感值"""
        if not value or not self._fernet:
            return value
        try:
            encrypted = self._fernet.encrypt(value.encode())
            return encrypted.decode()
        except Exception as e:
            logger.warning(f"加密失败: {e}")
            return value
    
    def _decrypt(self, value: str) -> str:
        """解密敏感值"""
        if not value or not self._fernet:
            return value
        try:
            decrypted = self._fernet.decrypt(value.encode())
            return decrypted.decode()
        except InvalidToken:
            logger.warning("解密失败：密钥不匹配或数据损坏")
            return ""
        except Exception as e:
            logger.warning(f"解密失败: {e}")
            return value
    
    def _get_session(self):
        """获取数据库 Session"""
        from src.storage import DatabaseManager
        return DatabaseManager.get_instance().get_session()
    
    def get(self, key: str) -> Optional[str]:
        """
        获取单个配置值
        
        Args:
            key: 配置键
            
        Returns:
            配置值，不存在返回 None
        """
        from src.storage import SystemSetting
        from sqlalchemy import select
        
        try:
            with self._get_session() as session:
                result = session.execute(
                    select(SystemSetting).where(SystemSetting.key == key)
                ).scalar_one_or_none()
                
                if result is None:
                    return None
                
                value = result.value
                if result.is_encrypted and value:
                    value = self._decrypt(value)
                
                return value
        except Exception as e:
            logger.error(f"获取配置 {key} 失败: {e}")
            return None
    
    def get_all(self, category: Optional[str] = None) -> Dict[str, str]:
        """
        获取所有配置
        
        Args:
            category: 可选，按分类过滤
            
        Returns:
            配置字典 {key: value}
        """
        from src.storage import SystemSetting
        from sqlalchemy import select
        
        try:
            with self._get_session() as session:
                query = select(SystemSetting)
                if category:
                    query = query.where(SystemSetting.category == category)
                
                results = session.execute(query).scalars().all()
                
                configs = {}
                for setting in results:
                    value = setting.value
                    if setting.is_encrypted and value:
                        value = self._decrypt(value)
                    configs[setting.key] = value
                
                return configs
        except Exception as e:
            logger.error(f"获取所有配置失败: {e}")
            return {}
    
    def set(self, key: str, value: Optional[str], category: str = 'general', description: str = '') -> bool:
        """
        设置单个配置
        
        Args:
            key: 配置键
            value: 配置值（None 或空字符串将删除配置）
            category: 分类
            description: 描述
            
        Returns:
            是否成功
        """
        from src.storage import SystemSetting
        from sqlalchemy import select
        
        # 空值删除配置
        if value is None or value == '':
            return self.delete(key)
        
        try:
            is_sensitive = key in self.SENSITIVE_KEYS
            stored_value = self._encrypt(value) if is_sensitive else value
            
            with self._get_session() as session:
                existing = session.execute(
                    select(SystemSetting).where(SystemSetting.key == key)
                ).scalar_one_or_none()
                
                if existing:
                    existing.value = stored_value
                    existing.is_encrypted = 1 if is_sensitive else 0
                    existing.category = category
                    existing.description = description
                    existing.updated_at = datetime.now()
                else:
                    setting = SystemSetting(
                        key=key,
                        value=stored_value,
                        is_encrypted=1 if is_sensitive else 0,
                        category=category,
                        description=description,
                    )
                    session.add(setting)
                
                session.commit()
                logger.debug(f"配置 {key} 已保存")
                return True
                
        except Exception as e:
            logger.error(f"保存配置 {key} 失败: {e}")
            return False
    
    def set_batch(self, configs: Dict[str, str], category: str = 'general') -> bool:
        """
        批量设置配置
        
        Args:
            configs: 配置字典 {key: value}
            category: 分类
            
        Returns:
            是否全部成功
        """
        success = True
        for key, value in configs.items():
            if not self.set(key, value, category):
                success = False
        return success
    
    def delete(self, key: str) -> bool:
        """
        删除配置
        
        Args:
            key: 配置键
            
        Returns:
            是否成功
        """
        from src.storage import SystemSetting
        from sqlalchemy import select
        
        try:
            with self._get_session() as session:
                existing = session.execute(
                    select(SystemSetting).where(SystemSetting.key == key)
                ).scalar_one_or_none()
                
                if existing:
                    session.delete(existing)
                    session.commit()
                    logger.debug(f"配置 {key} 已删除")
                
                return True
                
        except Exception as e:
            logger.error(f"删除配置 {key} 失败: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查配置是否存在"""
        return self.get(key) is not None


# 便捷函数
def get_config_store() -> ConfigStore:
    """获取配置存储服务实例"""
    return ConfigStore.get_instance()
