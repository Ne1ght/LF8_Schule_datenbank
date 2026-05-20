import oracledb

con = oracledb.connect(
    user="system",
    password="LF8",
    dsn="localhost:1251/XEPDB1"
)

cur = con.cursor()
