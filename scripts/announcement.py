# announcement.py 或者你原来的文件
import json
import requests
from typing import Dict, Any

from .config import ANNOUNCEMENT_URL

def get_announcement() -> Dict[str, Any]:
    """
    从 GitHub 获取公告，返回统一格式的字典。
    成功时：{"success": True, "data": {公告字典}}
    失败时：{"success": False, "error": "错误提示"}
    """
    try:
        response = requests.get(ANNOUNCEMENT_URL, timeout=10)
        response.raise_for_status()          # 4xx/5xx 会抛异常
        data = response.json()               # 自动解析 JSON → dict

        # 顺手做个简单校验，防止你哪天不小心把文件写坏了
        if not isinstance(data, dict):
            raise ValueError("公告文件不是有效的 JSON 对象")

        return {"success": True, "data": data}

    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"网络错误，无法获取公告，官方网站：tkf.pyden.dev"}
    except (json.JSONDecodeError, ValueError) as e:
        return {"success": False, "error": f"公告错误{e}"}
    except Exception as e:  # 兜底，永远不会崩溃
        return {"success": False, "error": f"未知错误: {e}"}