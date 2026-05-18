from tkinter import *
import oracledb

con = oracledb.connect(
    user="system",
    password="LF8",
    dsn="localhost:1251/XEPDB1"
)

cur = con.cursor()
cur.execute("Select * FROM dual")

for row in cur:
    print(row)
cur.close()
con.close()

# can i update this for fucks sake
if __name__ == "__main__":

    root_window = Tk()
    root_window.mainloop()