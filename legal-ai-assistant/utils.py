# utils.py - 保留的工具函数（向后兼容）

from document_processor import process_uploaded_files
from database import get_db_connection, get_user_id

__all__ = ['process_uploaded_files', 'get_db_connection', 'get_user_id']