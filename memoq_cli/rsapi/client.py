# -*- coding: utf-8 -*-
"""
memoQ CLI - RSAPI Client Base Class
"""

import time
import functools
import requests
import urllib3
from typing import Optional, Dict, Any, Callable, TypeVar

from ..config import get_config
from ..utils import get_logger
from ..exceptions import (
    RSAPIError,
    AuthenticationError,
    TaskTimeoutError,
    TaskFailedError,
)

# Disable SSL warnings when verify_ssl is False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

T = TypeVar("T")


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
) -> Callable:
    """
    Retry decorator with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise

            raise last_exception

        return wrapper
    return decorator


class RSAPIClient:
    """
    memoQ RSAPI (REST API) 客户端基类
    
    支持的 API 端点示例:
        - https://memoq.example.com:28081/memoqserverhttpapi/v1/auth/login
        - https://memoq.example.com:28081/memoqserverhttpapi/v1/tms
        - https://memoq.example.com:28081/memoqserverhttpapi/v1/tbs
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_path: Optional[str] = None,
        api_key: Optional[str] = None,
        verify_ssl: bool = False
    ):
        """
        初始化 RSAPI 客户端
        
        Args:
            host: 服务器主机地址 (如 https://memoq.example.com)
            port: RSAPI 端口 (如 28081)
            api_path: API 路径 (如 memoqserverhttpapi/v1)
            api_key: API Key
            verify_ssl: 是否验证 SSL 证书
        """
        self.config = get_config()
        self.logger = get_logger("rsapi")
        
        # 优先使用传入参数，否则使用配置
        self._host = host or self.config.server_host
        self._port = port or self.config.rsapi_port
        self._api_path = api_path or self.config.rsapi_path
        self._api_key = api_key or self.config.api_key
        self._username = self.config.username
        self._password = self.config.password
        self.verify_ssl = verify_ssl
        
        # 创建会话
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # 访问令牌
        self._access_token: Optional[str] = None
    
    @property
    def base_url(self) -> str:
        """
        获取 API 基础 URL
        
        Returns:
            完整的基础 URL，如:
            https://memoq.example.com:28081/memoqserverhttpapi/v1
        """
        host = self._host.rstrip("/")
        path = self._api_path.strip("/")
        return f"{host}:{self._port}/{path}"
    
    def _get_url(self, endpoint: str) -> str:
        """
        构建完整 URL
        
        Args:
            endpoint: API 端点 (如 "auth/login", "tms", "tms/{guid}")
        
        Returns:
            完整 URL
        """
        endpoint = endpoint.lstrip("/")
        return f"{self.base_url}/{endpoint}"
    
    def authenticate(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> str:
        """
        使用用户名密码获取访问令牌 (MemoQServerUser LoginMode 0)

        Returns:
            访问令牌

        Raises:
            requests.HTTPError: 认证失败
        """
        url = self._get_url("auth/login")

        self.logger.debug(f"认证请求: {url}")

        payload = {
            "username": username if username is not None else self._username,
            "password": password if password is not None else self._password,
            "LoginMode": 0,
        }

        response = self.session.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        self._access_token = data.get("AccessToken")

        if not self._access_token:
            raise ValueError("认证响应中未包含 AccessToken")

        # memoQ RSAPI 使用 MQS-API 认证头
        self.session.headers["Authorization"] = f"MQS-API {self._access_token}"

        self.logger.info("RSAPI 认证成功")
        return self._access_token

    def authenticate_with_password(self, username: str, password: str) -> str:
        """Authenticate with explicit username/password credentials."""
        return self.authenticate(username=username, password=password)
    
    def ensure_authenticated(self):
        """确保已认证，如未认证则自动认证"""
        if not self._access_token:
            self.authenticate()
    
    def get(
        self, 
        endpoint: str, 
        params: Optional[Dict] = None,
        **kwargs
    ) -> Any:
        """
        GET 请求
        
        Args:
            endpoint: API 端点
            params: 查询参数
            **kwargs: 其他 requests 参数
        
        Returns:
            JSON 响应数据
        """
        self.ensure_authenticated()
        
        url = self._get_url(endpoint)
        self.logger.debug(f"GET {url}")
        
        response = self.session.get(url, params=params, **kwargs)
        response.raise_for_status()
        
        # 检查响应是否为 JSON
        if response.headers.get("Content-Type", "").startswith("application/json"):
            return response.json()
        return response.text
    
    def post(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        **kwargs
    ) -> Any:
        """
        POST 请求

        Args:
            endpoint: API 端点
            data: 表单数据
            json_data: JSON 数据
            params: 查询参数
            **kwargs: 其他 requests 参数

        Returns:
            JSON 响应数据
        """
        self.ensure_authenticated()

        url = self._get_url(endpoint)
        self.logger.debug(f"POST {url}")

        if json_data is not None:
            response = self.session.post(url, json=json_data, params=params, **kwargs)
        else:
            response = self.session.post(url, data=data, params=params, **kwargs)

        response.raise_for_status()

        # 204 No Content or empty body
        if response.status_code == 204 or not response.content:
            return None

        if response.headers.get("Content-Type", "").startswith("application/json"):
            return response.json()
        return response.text

    def put(
        self, 
        endpoint: str, 
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        **kwargs
    ) -> Any:
        """
        PUT 请求
        
        Args:
            endpoint: API 端点
            data: 表单数据
            json_data: JSON 数据
            **kwargs: 其他 requests 参数
        
        Returns:
            JSON 响应数据
        """
        self.ensure_authenticated()
        
        url = self._get_url(endpoint)
        self.logger.debug(f"PUT {url}")
        
        if json_data is not None:
            response = self.session.put(url, json=json_data, **kwargs)
        else:
            response = self.session.put(url, data=data, **kwargs)
        
        response.raise_for_status()
        
        if response.headers.get("Content-Type", "").startswith("application/json"):
            return response.json()
        return response.text
    
    def delete(self, endpoint: str, **kwargs) -> bool:
        """
        DELETE 请求
        
        Args:
            endpoint: API 端点
            **kwargs: 其他 requests 参数
        
        Returns:
            True 如果成功
        """
        self.ensure_authenticated()
        
        url = self._get_url(endpoint)
        self.logger.debug(f"DELETE {url}")
        
        response = self.session.delete(url, **kwargs)
        response.raise_for_status()
        
        return True
    
    def upload_file(
        self,
        endpoint: str,
        file_path: str,
        file_field: str = "file",
        additional_data: Optional[Dict] = None
    ) -> Any:
        """
        上传文件
        
        Args:
            endpoint: API 端点
            file_path: 文件路径
            file_field: 文件字段名
            additional_data: 附加表单数据
        
        Returns:
            JSON 响应数据
        """
        self.ensure_authenticated()
        
        url = self._get_url(endpoint)
        self.logger.debug(f"UPLOAD {url}")
        
        with open(file_path, "rb") as f:
            files = {file_field: f}
            
            # 临时移除 Content-Type 让 requests 自动设置 multipart
            headers = dict(self.session.headers)
            headers.pop("Content-Type", None)
            
            response = self.session.post(
                url, 
                files=files, 
                data=additional_data,
                headers=headers
            )
        
        response.raise_for_status()
        
        if response.headers.get("Content-Type", "").startswith("application/json"):
            return response.json()
        return response.text
    
    def download_file(
        self,
        url: str,
        output_path: str,
        chunk_size: int = 8192
    ) -> str:
        """
        下载文件
        
        Args:
            url: 文件 URL (完整 URL 或相对端点)
            output_path: 输出文件路径
            chunk_size: 下载块大小
        
        Returns:
            输出文件路径
        """
        self.ensure_authenticated()
        
        # 如果不是完整 URL，则构建
        if not url.startswith("http"):
            url = self._get_url(url)
        
        self.logger.debug(f"DOWNLOAD {url}")
        
        response = self.session.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        
        return output_path
    
    def close(self):
        """Close the session"""
        self.session.close()

    def wait_for_task(
        self,
        task_id: str,
        timeout: int = 300,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Wait for an async task to complete.

        Args:
            task_id: Task ID to wait for
            timeout: Maximum wait time in seconds (default 5 minutes)
            poll_interval: Seconds between status checks

        Returns:
            Task result when completed

        Raises:
            TaskTimeoutError: If task doesn't complete within timeout
            TaskFailedError: If task fails
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.get(f"tasks/{task_id}")
            status = result.get("Status", "")

            if status == "Completed":
                self.logger.debug(f"Task {task_id} completed")
                return result
            elif status == "Failed":
                error_msg = result.get("ErrorMessage", "Unknown error")
                raise TaskFailedError(task_id, error_msg)

            time.sleep(poll_interval)

        raise TaskTimeoutError(task_id, timeout)

    def download_to_file(
        self,
        url: str,
        output_path: str,
        chunk_size: int = 8192
    ) -> str:
        """
        Download content from URL to a file.

        Args:
            url: Full URL or relative endpoint
            output_path: Path to save the file
            chunk_size: Download chunk size in bytes

        Returns:
            Path to the downloaded file
        """
        self.ensure_authenticated()

        # Build full URL if relative
        if not url.startswith("http"):
            url = self._get_url(url)

        self.logger.debug(f"Downloading: {url}")

        response = self.session.get(url, stream=True)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)

        return output_path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
