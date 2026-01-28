# -*- coding: utf-8 -*-
"""
===================================
Web 设置页面处理器
===================================

职责：
1. 处理设置页面的 HTTP 请求
2. 渲染设置页面
3. 处理配置保存请求
"""

from __future__ import annotations

import json
import logging
from http import HTTPStatus
from typing import Dict, Any
from urllib.parse import parse_qs

from web.handlers import Response, HtmlResponse, JsonResponse
from web.settings_service import get_settings_service

logger = logging.getLogger(__name__)


class SettingsHandler:
    """设置页面处理器"""
    
    def __init__(self):
        self.service = get_settings_service()
    
    def handle_settings_page(self, query: Dict[str, list] = None) -> Response:
        """
        GET /settings - 渲染设置页面
        """
        from web.templates import render_settings_page
        
        settings = self.service.get_all_settings()
        
        # 检查是否有消息参数
        message = None
        message_type = 'success'
        if query:
            msg_list = query.get('msg', [])
            if msg_list:
                message = msg_list[0]
            type_list = query.get('type', [])
            if type_list:
                message_type = type_list[0]
        
        body = render_settings_page(settings, message, message_type)
        return HtmlResponse(body)
    
    def handle_save_api_keys(self, form_data: Dict[str, list]) -> Response:
        """
        POST /settings/api-keys - 保存 API Keys
        """
        keys = {
            'gemini_api_key': self._get_form_value(form_data, 'gemini_api_key'),
            'gemini_model': self._get_form_value(form_data, 'gemini_model'),
            'gemini_model_fallback': self._get_form_value(form_data, 'gemini_model_fallback'),
            'tushare_token': self._get_form_value(form_data, 'tushare_token'),
            'tavily_api_keys': self._get_form_value(form_data, 'tavily_api_keys'),
            'serpapi_keys': self._get_form_value(form_data, 'serpapi_keys'),
            'openai_api_key': self._get_form_value(form_data, 'openai_api_key'),
            'openai_base_url': self._get_form_value(form_data, 'openai_base_url'),
            'openai_model': self._get_form_value(form_data, 'openai_model'),
            'deepseek_api_key': self._get_form_value(form_data, 'deepseek_api_key'),
            'zhipu_api_key': self._get_form_value(form_data, 'zhipu_api_key'),
        }
        
        success, message = self.service.save_api_keys(keys)
        
        return self._redirect_with_message('/settings', message, 'success' if success else 'error')
    
    def handle_save_stocks(self, form_data: Dict[str, list]) -> Response:
        """
        POST /settings/stocks - 保存自选股
        """
        stocks = self._get_form_value(form_data, 'stock_list')
        
        success, message = self.service.save_stock_list(stocks)
        
        return self._redirect_with_message('/settings', message, 'success' if success else 'error')
    
    def handle_save_email(self, form_data: Dict[str, list]) -> Response:
        """
        POST /settings/email - 保存邮件配置
        """
        config = {
            'email_sender': self._get_form_value(form_data, 'email_sender'),
            'email_password': self._get_form_value(form_data, 'email_password'),
            'email_receivers': self._get_form_value(form_data, 'email_receivers'),
        }
        
        success, message = self.service.save_email_config(config)
        
        return self._redirect_with_message('/settings', message, 'success' if success else 'error')
    
    def handle_save_schedule(self, form_data: Dict[str, list]) -> Response:
        """
        POST /settings/schedule - 保存定时任务配置
        """
        config = {
            'schedule_enabled': 'true' if self._get_form_value(form_data, 'schedule_enabled') else 'false',
            'schedule_time': self._get_form_value(form_data, 'schedule_time'),
            'market_review_enabled': 'true' if self._get_form_value(form_data, 'market_review_enabled') else 'false',
        }
        
        success, message = self.service.save_schedule_config(config)
        
        return self._redirect_with_message('/settings', message, 'success' if success else 'error')
    
    def handle_test_email(self, form_data: Dict[str, list]) -> Response:
        """
        POST /settings/test-email - 测试邮件发送
        """
        success, message = self.service.test_email_send()
        
        return JsonResponse({
            'success': success,
            'message': message
        })
    
    def _get_form_value(self, form_data: Dict[str, list], key: str, default: str = '') -> str:
        """从表单数据获取值"""
        values = form_data.get(key, [])
        return values[0] if values else default
    
    def _redirect_with_message(self, path: str, message: str, msg_type: str = 'success') -> Response:
        """重定向并带上消息参数"""
        from urllib.parse import quote
        
        redirect_url = f"{path}?msg={quote(message)}&type={msg_type}"
        
        # 返回 HTML 重定向
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0;url={redirect_url}">
</head>
<body>
    <p>正在跳转...</p>
    <script>window.location.href = "{redirect_url}";</script>
</body>
</html>'''
        
        return HtmlResponse(html.encode('utf-8'))


# 单例实例
_settings_handler: SettingsHandler | None = None


def get_settings_handler() -> SettingsHandler:
    """获取设置处理器实例"""
    global _settings_handler
    if _settings_handler is None:
        _settings_handler = SettingsHandler()
    return _settings_handler
