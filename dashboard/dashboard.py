from dotenv import load_dotenv
import mysql.connector
import time
import random
import os
import requests

load_dotenv("")

print("Welcome to trafficsharperX fill out details:")
time.sleep(5)

name = input("Enter your name: ")
email = input("Enter your email: ")

thresold = int(input("Enter your threshould: "))
l_buf = int(input("Enter lower buffer: "))
h_buf = int(input("Enter higher buffer: "))



print("Now we need the technical info for finding best server and make best security group:")
time.sleep(5)

work_load = input("Enter you server used for (webapp/api_backend/ml_trainning/ai_trainng/): ")

print("now we need hardware details:")

print("the os be ubuntu by default")
time.sleep(5)

cpu = (input("Provide the range of cpus you want [(2-4)/(4-6)/(6-8)]: "))
ram = (input("Provide the range of amount of ram you want [(4-8)/(8-12)/(12-16)/(16-24)]: "))
storage = int(input("Enter the amount of storage you want: "))
network = input("Enter you network priority [low/med/high]: ")

print("now we want the networking details:")

public = input("DO you want server to have public access(yes/no): ")
inbound = []
outbound = []
while True:

    ports = (input("Enter the inbound ports you want to open (if done than write done): "))

    if ports == "done":
        break

    inbound.append(int(ports))

while True:

    ports = (input("Enter the outbound ports you want to open (if done than write done)/(if all write all): "))

    if ports == "done":
        break

    if ports == "all":

        outbound.append("all")
        break

    outbound.append(int(ports))

print("we want some additional info")
time.sleep(5)

scale_mode = input("Enter the aggressiveness of scaling (conservative/balanced/aggressive): ")
cooldown = int(input("Enter the cooldown period on seconds: "))

id = random.randint(0,10000)
print(f"your id is {id} remember this")

print(name,thresold,l_buf,h_buf,work_load,cpu,ram,storage,network,scale_mode,cooldown)

for i in range(len(inbound)):
    print(inbound[i])
for i in range(len(outbound)):
    print(outbound[i])

print("Need some extra tools mention/ If no than put NO:")
time.sleep(5)

tools = []

while True:

    tool = (input("Enter the tool name: "))

    if tool == "NO":

        break

    tools.append(tool)

payload = {
    "workload": work_load,
    "cpu": cpu,
    "ram": ram,
    "storage": storage,
    "network": network,
    "inbound": list(inbound),
    "outbound": list(outbound),
    "tools": list(tools)
}
# url = ""
# response = requests.post(url,json=payload)

# con = mysql.connector.connect(
#     host=os.getenv("DB_HOST"),
#     user=os.getenv("DB_USER"),
#     password = os.getenv("PASSWORD"),
#     database = os.getenv("DATABASE")
# )
#
# cursor = con.cursor()
#
# values = (int(id),name,int(thresold),int(l_buf),int(h_buf),email)
# query = "insert into client_info(clinet_id,client_name,thresold,l_buff,h_buff,email) values(%s,%s,%s,%s,%s,%s)"
#
# cursor.execute(query,values)
# con.commit()