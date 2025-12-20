from dotenv import load_dotenv
import mysql.connector
import time
import random
import os

load_dotenv("")

print("Welcome to trafficsharperX fill ouut details:")
time.sleep(5)

name = input("Enter your name: ")
thresold = int(input("Enter your threshould: "))
l_buf = int(input("Enter lower buffer: "))
h_buf = int(input("Enter higher buffer: "))
email = input("Enter your email: ")

id = random.randint(0,10000)
print(f"your id is {id} remember this")

con = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password = os.getenv("PASSWORD"),
    database = os.getenv("DATABASE")
)

cursor = con.cursor()

values = (int(id),name,int(thresold),int(l_buf),int(h_buf),email)
query = "insert into client_info(clinet_id,client_name,thresold,l_buff,h_buff,email) values(%s,%s,%s,%s,%s,%s)"

cursor.execute(query,values)
con.commit()