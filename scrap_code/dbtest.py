import MySQLdb

host_var="localhost"
user_var="root"
passwd_var="sniper67"
db_var="warcraft"

def load_db():
    return MySQLdb.connect(host=host_var,
                           user=user_var,
                           passwd=passwd_var,
                           db=db_var)

db = load_db()
cur = db.cursor()
cur.execute("SELECT * FROM currentfaction")
data = cur.fetchall()

print data
