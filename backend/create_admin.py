import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_db, init_db
from models.user import User
from services.auth_service import get_password_hash

def create_admin():
    init_db()
    db = next(get_db())
    
    admin_user = db.query(User).filter(User.username == "admin").first()
    if admin_user:
        print("管理员用户已存在")
        return
    
    hashed_password = get_password_hash("admin123")
    new_admin = User(
        username="admin",
        password_hash=hashed_password,
        email="admin@example.com",
        role="admin"
    )
    db.add(new_admin)
    db.commit()
    print("管理员用户创建成功: admin/admin123")

if __name__ == "__main__":
    create_admin()
