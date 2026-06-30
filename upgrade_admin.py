import sqlite3
conn = sqlite3.connect('C:/Users/13425/Desktop/software/backend-java/data/repair_java.db')
cursor = conn.cursor()
cursor.execute('UPDATE users SET role=? WHERE id=1', ('admin',))
conn.commit()
print('User upgraded to admin')
conn.close()