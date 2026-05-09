# input_validator.py - 输入验证模块

import re
from typing import Optional, Tuple

def validate_user_input(user_input: str) -> Tuple[bool, str, str]:
    """
    验证用户输入的安全性
    
    Args:
        user_input: 用户输入的文本
        
    Returns:
        (is_valid, cleaned_input, error_message)
    """
    if not user_input or not user_input.strip():
        return False, "", "输入不能为空"
    
    cleaned_input = user_input.strip()
    
    # 检查输入长度
    if len(cleaned_input) > 2000:
        return False, "", "输入过长，请限制在2000字符以内"
    
    # 检查是否包含潜在危险字符（防止注入攻击）
    dangerous_patterns = [
        r"['\";`]",           # SQL注入相关字符
        r"(SELECT|INSERT|DELETE|UPDATE|DROP|UNION|EXEC)\s",  # SQL关键字
        r"<script[^>]*>.*?</script>",  # XSS脚本
        r"<[^>]+>",          # HTML标签
        r"(javascript:|vbscript:|data:)",  # 脚本协议
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, cleaned_input, re.IGNORECASE):
            return False, "", "输入包含不安全的内容，请重新输入"
    
    # 检查是否包含过多的特殊字符
    special_chars = re.findall(r'[^\w\s\u4e00-\u9fff。，！？、；：]', cleaned_input)
    if len(special_chars) > len(cleaned_input) * 0.3:
        return False, "", "输入包含过多特殊字符，请重新输入"
    
    return True, cleaned_input, ""

def sanitize_input(user_input: str) -> str:
    """
    清理用户输入，移除潜在危险内容
    
    Args:
        user_input: 用户输入的文本
        
    Returns:
        清理后的文本
    """
    if not user_input:
        return ""
    
    # 移除HTML标签
    cleaned = re.sub(r"<[^>]+>", "", user_input)
    
    # 移除脚本协议
    cleaned = re.sub(r"(javascript:|vbscript:|data:)", "", cleaned, flags=re.IGNORECASE)
    
    # 转义特殊字符
    cleaned = cleaned.replace("'", "''").replace('"', '\\"')
    
    return cleaned.strip()

def validate_file_name(file_name: str) -> Tuple[bool, str]:
    """
    验证文件名的安全性
    
    Args:
        file_name: 文件名
        
    Returns:
        (is_valid, error_message)
    """
    if not file_name or not file_name.strip():
        return False, "文件名不能为空"
    
    # 检查是否包含路径遍历字符
    if any(char in file_name for char in ['/', '\\', '..']):
        return False, "文件名不能包含路径分隔符"
    
    # 检查是否包含特殊字符
    if re.search(r'[<>:"|?*]', file_name):
        return False, "文件名包含非法字符"
    
    # 检查文件扩展名
    valid_extensions = ['pdf', 'docx', 'txt']
    if '.' in file_name:
        ext = file_name.split('.')[-1].lower()
        if ext not in valid_extensions:
            return False, f"不支持的文件类型，请上传 {', '.join(valid_extensions)} 文件"
    
    return True, ""

def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """
    验证API Key的格式
    
    Args:
        api_key: API密钥
        
    Returns:
        (is_valid, error_message)
    """
    if not api_key or not api_key.strip():
        return False, "API Key不能为空"
    
    # 检查长度
    if len(api_key.strip()) < 10:
        return False, "API Key格式不正确"
    
    return True, ""