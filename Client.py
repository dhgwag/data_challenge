# -*- coding: utf-8 -*-
from socket import *
from select import *
import sys
import time

with open("CAN_Dataset.txt", "r") as f:
    can_data = f.readlines()

HOST = '127.0.0.1'
PORT = 10000
ADDR = (HOST, PORT)
clientSocket = socket(AF_INET, SOCK_STREAM) 

try:
    clientSocket.connect(ADDR) 
    print "connect!"
except Exception as e:
	print('%s:%s' % ADDR)
	sys.exit()

start_time = time.time()
for i in can_data:
	timestamp = i.split('Timestamp: ')[1][:17]
	timestamp = float(timestamp) - 1479109284.0,

	# time wait
	# while(1):
	# 	runtime = time.time() - start_time
	# 	# print runtime, timestamp[0]
	# 	if runtime > timestamp[0]:
	# 		break

	# send data
	clientSocket.send(i)
	print i,

clientSocket.close()