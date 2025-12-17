import mysql.connector
import time
import random

print("Welcome to trafficsharperX fill ouut details:")
time.sleep(5)

name = input("Enter your name: ")
thresold = int(input("Enter your threshould: "))
l_buf = int(input("Enter lower buffer: "))
h_buf = int(input("Enter higher buffer: "))

id = random.randint(0,10000)
print(f"your id is {id} remember this")

con = mysql.connector.connect(
    host="",
    user="",
    password = "",
    database = ""
)

cursor = con.cursor()

values = (name,int(id),int(thresold),int(l_buf),int(h_buf))
query = "insert into client_info(name,id,thresold,l_buff,h_buff) values(%s,%s,%s,%s,%s)"

cursor.execute(query,values)
con.commit()