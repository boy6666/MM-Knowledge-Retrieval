"""
统一响应格式工具
所有接口返回统一结构：{code, message, data}
"""


def success(data=None, message: str = "操作成功"):
    return {
        "code": 200,
        "message": message,
        "data": data,
    }


def fail(message: str = "操作失败", code: int = 400, data=None):
    return {
        "code": code,
        "message": message,
        "data": data,
    }


def paginated(items, total: int, page: int = 1, page_size: int = 10):
    return success({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


class BizException(Exception):
    """业务异常，可被统一异常处理捕获"""
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(message)
