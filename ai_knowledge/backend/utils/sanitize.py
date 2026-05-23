"""HTML 清洗工具 - 防止 XSS 攻击"""
import bleach

# 允许的 HTML 标签（仅保留安全、基本的排版标签）
ALLOWED_TAGS = [
    "p", "br", "b", "i", "u", "em", "strong",
    "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "blockquote", "pre", "code",
    "img",
]

# 允许的属性
ALLOWED_ATTRIBUTES = {
    "img": ["src", "alt", "title", "width", "height"],
}

# 允许的协议（仅安全的图片源）
ALLOWED_PROTOCOLS = ["http", "https"]


def sanitize_html(html_content: str) -> str:
    """清洗 HTML 内容，移除危险标签和属性"""
    if not html_content:
        return ""
    return bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )