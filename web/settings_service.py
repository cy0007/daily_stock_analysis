# -*- coding: utf-8 -*-
"""
===================================
Web 设置服务层 - 设置业务逻辑
===================================

职责：
1. 获取和保存各类配置
2. 敏感值掩码处理
3. 配置验证
4. 测试邮件发送
"""

from __future__ import annotations

import re
import logging
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)


class SettingsService:
    """
    设置业务服务
    
    封装设置相关的业务逻辑
    """
    
    _instance: Optional['SettingsService'] = None
    
    @classmethod
    def get_instance(cls) -> 'SettingsService':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_all_settings(self) -> Dict[str, Any]:
        """
        获取所有设置（用于页面渲染）
        
        Returns:
            包含所有配置的字典，敏感值已掩码
        """
        from src.config_store import get_config_store
        from src.config import get_config
        
        store = get_config_store()
        config = get_config()
        
        # 从数据库获取配置
        db_configs = store.get_all()
        
        # 构建设置字典
        settings = {
            # API Keys
            'gemini_api_key': self._get_masked_value(db_configs, 'gemini_api_key', config.gemini_api_key),
            'gemini_api_key_raw': db_configs.get('gemini_api_key') or config.gemini_api_key or '',
            'gemini_model': db_configs.get('gemini_model') or config.gemini_model,
            'gemini_model_fallback': db_configs.get('gemini_model_fallback') or config.gemini_model_fallback,
            'tushare_token': self._get_masked_value(db_configs, 'tushare_token', config.tushare_token),
            'tushare_token_raw': db_configs.get('tushare_token') or config.tushare_token or '',
            'tavily_api_keys': self._get_masked_value(db_configs, 'tavily_api_keys', ','.join(config.tavily_api_keys)),
            'tavily_api_keys_raw': db_configs.get('tavily_api_keys') or ','.join(config.tavily_api_keys),
            'serpapi_keys': self._get_masked_value(db_configs, 'serpapi_keys', ','.join(config.serpapi_keys)),
            'serpapi_keys_raw': db_configs.get('serpapi_keys') or ','.join(config.serpapi_keys),
            'openai_api_key': self._get_masked_value(db_configs, 'openai_api_key', config.openai_api_key),
            'openai_api_key_raw': db_configs.get('openai_api_key') or config.openai_api_key or '',
            'openai_base_url': db_configs.get('openai_base_url') or config.openai_base_url or '',
            'openai_model': db_configs.get('openai_model') or config.openai_model,
            
            # DeepSeek
            'deepseek_api_key': self._get_masked_value(db_configs, 'deepseek_api_key', None),
            'deepseek_api_key_raw': db_configs.get('deepseek_api_key') or '',
            
            # 智谱 AI
            'zhipu_api_key': self._get_masked_value(db_configs, 'zhipu_api_key', None),
            'zhipu_api_key_raw': db_configs.get('zhipu_api_key') or '',
            
            # 自选股
            'stock_list': db_configs.get('stock_list') or ','.join(config.stock_list),
            
            # 邮件配置
            'email_sender': db_configs.get('email_sender') or config.email_sender or '',
            'email_password': self._get_masked_value(db_configs, 'email_password', config.email_password),
            'email_password_raw': db_configs.get('email_password') or config.email_password or '',
            'email_receivers': db_configs.get('email_receivers') or ','.join(config.email_receivers),
            
            # 定时任务
            'schedule_enabled': self._parse_bool(db_configs.get('schedule_enabled'), config.schedule_enabled),
            'schedule_time': db_configs.get('schedule_time') or config.schedule_time,
            'market_review_enabled': self._parse_bool(db_configs.get('market_review_enabled'), config.market_review_enabled),
        }
        
        # 计算下次执行时间
        settings['next_run_time'] = self._get_next_run_time(
            settings['schedule_enabled'],
            settings['schedule_time']
        )
        
        return settings
    
    def _get_masked_value(self, db_configs: Dict, key: str, fallback: Optional[str]) -> str:
        """获取掩码后的值"""
        value = db_configs.get(key) or fallback or ''
        return self.mask_sensitive_value(value)
    
    def _parse_bool(self, value: Optional[str], default: bool) -> bool:
        """解析布尔值"""
        if value is None:
            return default
        return value.lower() == 'true'
    
    def _get_next_run_time(self, enabled: bool, schedule_time: str) -> str:
        """计算下次执行时间"""
        if not enabled:
            return '定时任务未启用'
        
        from datetime import datetime, timedelta
        
        times = [t.strip() for t in schedule_time.split(',') if t.strip()]
        if not times:
            return '未设置执行时间'
        
        now = datetime.now()
        next_times = []
        
        for t in times:
            try:
                hour, minute = map(int, t.split(':'))
                run_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if run_time <= now:
                    run_time += timedelta(days=1)
                next_times.append(run_time)
            except ValueError:
                continue
        
        if not next_times:
            return '时间格式错误'
        
        next_run = min(next_times)
        return next_run.strftime('%Y-%m-%d %H:%M')
    
    def save_api_keys(self, keys: Dict[str, str]) -> Tuple[bool, str]:
        """
        保存 API Keys
        
        Args:
            keys: API Keys 字典
            
        Returns:
            (是否成功, 消息)
        """
        from src.config_store import get_config_store
        
        store = get_config_store()
        
        try:
            # 保存各个 API Key
            key_mappings = {
                'gemini_api_key': 'api_keys',
                'tushare_token': 'api_keys',
                'tavily_api_keys': 'api_keys',
                'serpapi_keys': 'api_keys',
                'openai_api_key': 'api_keys',
                'openai_base_url': 'api_keys',
                'openai_model': 'api_keys',
                'gemini_model': 'api_keys',
                'gemini_model_fallback': 'api_keys',
                'deepseek_api_key': 'api_keys',
                'zhipu_api_key': 'api_keys',
            }
            
            for key, category in key_mappings.items():
                if key in keys:
                    value = keys[key].strip() if keys[key] else ''
                    store.set(key, value, category)
            
            # 刷新配置
            from src.config import get_config
            get_config().reload()
            
            logger.info("API Keys 配置已保存")
            return True, "API Keys 配置已保存"
            
        except Exception as e:
            logger.error(f"保存 API Keys 失败: {e}")
            return False, f"保存失败: {str(e)}"
    
    def save_stock_list(self, stocks: str) -> Tuple[bool, str]:
        """
        保存自选股列表
        
        同时更新数据库和 .env 文件（保持向后兼容）
        
        Args:
            stocks: 股票代码字符串
            
        Returns:
            (是否成功, 消息)
        """
        from src.config_store import get_config_store
        
        # 验证并规范化股票代码
        codes = [c.strip() for c in stocks.replace('\n', ',').split(',') if c.strip()]
        
        # 验证格式
        invalid_codes = []
        valid_codes = []
        for code in codes:
            if self.validate_stock_code(code):
                valid_codes.append(code)
            else:
                invalid_codes.append(code)
        
        if invalid_codes:
            return False, f"无效的股票代码: {', '.join(invalid_codes)}"
        
        normalized = ','.join(valid_codes)
        
        try:
            # 保存到数据库
            store = get_config_store()
            store.set('stock_list', normalized, 'stocks')
            
            # 同时更新 .env 文件
            self._update_env_stock_list(normalized)
            
            # 刷新配置
            from src.config import get_config
            get_config().reload()
            
            logger.info(f"自选股列表已保存: {len(valid_codes)} 只股票")
            return True, f"已保存 {len(valid_codes)} 只股票"
            
        except Exception as e:
            logger.error(f"保存自选股列表失败: {e}")
            return False, f"保存失败: {str(e)}"
    
    def _update_env_stock_list(self, stock_list: str) -> None:
        """更新 .env 文件中的 STOCK_LIST"""
        env_path = Path(__file__).parent.parent / '.env'
        
        if not env_path.exists():
            return
        
        try:
            content = env_path.read_text(encoding='utf-8')
            
            # 替换 STOCK_LIST 行
            pattern = r'^(\s*STOCK_LIST\s*=\s*).*$'
            replacement = f'STOCK_LIST={stock_list}'
            
            new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
            
            if count == 0:
                # 如果没有找到，添加到文件末尾
                if not new_content.endswith('\n'):
                    new_content += '\n'
                new_content += f'STOCK_LIST={stock_list}\n'
            
            env_path.write_text(new_content, encoding='utf-8')
            
        except Exception as e:
            logger.warning(f"更新 .env 文件失败: {e}")
    
    def save_email_config(self, config: Dict[str, str]) -> Tuple[bool, str]:
        """
        保存邮件配置
        
        Args:
            config: 邮件配置字典
            
        Returns:
            (是否成功, 消息)
        """
        from src.config_store import get_config_store
        
        store = get_config_store()
        
        try:
            store.set('email_sender', config.get('email_sender', '').strip(), 'email')
            store.set('email_password', config.get('email_password', '').strip(), 'email')
            store.set('email_receivers', config.get('email_receivers', '').strip(), 'email')
            
            # 刷新配置
            from src.config import get_config
            get_config().reload()
            
            logger.info("邮件配置已保存")
            return True, "邮件配置已保存"
            
        except Exception as e:
            logger.error(f"保存邮件配置失败: {e}")
            return False, f"保存失败: {str(e)}"
    
    def save_schedule_config(self, config: Dict[str, str]) -> Tuple[bool, str]:
        """
        保存定时任务配置
        
        Args:
            config: 定时任务配置字典
            
        Returns:
            (是否成功, 消息)
        """
        from src.config_store import get_config_store
        
        store = get_config_store()
        
        try:
            # 验证时间格式
            schedule_time = config.get('schedule_time', '').strip()
            if schedule_time:
                times = [t.strip() for t in schedule_time.split(',')]
                for t in times:
                    if not re.match(r'^\d{1,2}:\d{2}$', t):
                        return False, f"时间格式错误: {t}，请使用 HH:MM 格式"
            
            store.set('schedule_enabled', config.get('schedule_enabled', 'false'), 'schedule')
            store.set('schedule_time', schedule_time, 'schedule')
            store.set('market_review_enabled', config.get('market_review_enabled', 'true'), 'schedule')
            
            # 刷新配置
            from src.config import get_config
            get_config().reload()
            
            logger.info("定时任务配置已保存")
            return True, "定时任务配置已保存"
            
        except Exception as e:
            logger.error(f"保存定时任务配置失败: {e}")
            return False, f"保存失败: {str(e)}"
    
    def test_email_send(self) -> Tuple[bool, str]:
        """
        测试邮件发送
        
        Returns:
            (是否成功, 消息)
        """
        from src.config import get_config
        
        config = get_config()
        
        if not config.email_sender or not config.email_password:
            return False, "请先配置发件人邮箱和密码"
        
        try:
            from src.notification import Notifier
            
            notifier = Notifier(config)
            
            # 发送测试邮件
            test_content = """
# 📧 测试邮件

这是一封来自 **A股自选股智能分析系统** 的测试邮件。

如果您收到此邮件，说明邮件配置正确！

---
*此邮件由系统自动发送*
"""
            
            success = notifier._send_email("测试邮件 - A股分析系统", test_content)
            
            if success:
                return True, "测试邮件发送成功，请检查收件箱"
            else:
                return False, "邮件发送失败，请检查配置"
                
        except Exception as e:
            logger.error(f"测试邮件发送失败: {e}")
            return False, f"发送失败: {str(e)}"
    
    @staticmethod
    def mask_sensitive_value(value: Optional[str]) -> str:
        """
        掩码敏感值
        
        规则：长度 > 4 时，保留前 2 个字符和后 4 个字符，中间用 **** 替代
        
        Args:
            value: 原始值
            
        Returns:
            掩码后的值
        """
        if not value:
            return ''
        
        if len(value) <= 4:
            return '*' * len(value)
        
        return value[:2] + '****' + value[-4:]
    
    @staticmethod
    def validate_stock_code(code: str) -> bool:
        """
        验证股票代码格式
        
        支持：
        - A股：6位数字
        - 港股：hk + 5位数字
        - 美股：1-5个大写字母
        - 指数：6位数字
        
        Args:
            code: 股票代码
            
        Returns:
            是否有效
        """
        code = code.strip().lower()
        
        # A股/指数：6位数字
        if re.match(r'^\d{6}$', code):
            return True
        
        # 港股：hk + 5位数字
        if re.match(r'^hk\d{5}$', code):
            return True
        
        # 美股：1-5个字母
        if re.match(r'^[a-zA-Z]{1,5}$', code):
            return True
        
        return False


# 便捷函数
def get_settings_service() -> SettingsService:
    """获取设置服务实例"""
    return SettingsService.get_instance()
