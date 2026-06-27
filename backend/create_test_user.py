import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_db, init_db
from models.user import User
from services.auth_service import get_password_hash

def create_test_user():
    init_db()
    db = next(get_db())
    
    test_user = db.query(User).filter(User.username == "user").first()
    if test_user:
        print("测试用户已存在")
        return
    
    hashed_password = get_password_hash("user123")
    new_user = User(
        username="user",
        password_hash=hashed_password,
        email="user@example.com",
        role="user"
    )
    db.add(new_user)
    db.commit()
    print("测试用户创建成功: user/user123")

if __name__ == "__main__":
    create_test_user()
