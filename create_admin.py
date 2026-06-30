import sqlite3
import bcrypt

conn = sqlite3.connect('C:/Users/13425/Desktop/software/backend-java/data/repair_java.db')
cursor = conn.cursor()

password = b'admin123'
hashed = bcrypt.hashpw(password, bcrypt.gensalt())

cursor.execute('INSERT INTO users (username, password_hash, role, email) VALUES (?, ?, ?, ?)', 
              ('admin', hashed.decode('utf-8'), 'admin', 'admin@example.com'))

cursor.execute('UPDATE users SET role=? WHERE id=1', ('user',))

conn.commit()
print('Admin user created and testuser restored to regular user')
conn.close()