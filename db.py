import oracledb

connection_info = (
    "system",
    "LF8",
    "localhost:1251/XEPDB1"
)

con = oracledb.connect(
    user="system",
    password="LF8",
    dsn="localhost:1251/XEPDB1"
)

cur = con.cursor()


