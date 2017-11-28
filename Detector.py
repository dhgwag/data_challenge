#-*-coding:utf-8-*-
import time, datetime
import numpy as np
import matplotlib.pyplot as plt
import threading

from socket import *
from select import *
import sys, time 

# Global Data

#0. Total_Data
Total_Data = []

# 1. CAN Frame
Timestamp = []
ID = []
Sub_ID = []
DLC = []
Data = []

# 2. Sokcet Data
HOST = '127.0.0.1'
PORT = 56789
ADDR = (HOST, PORT)
c = None


#Socket
class Data_Reciver(threading.Thread):
	def interval_of_time(self, time1, time2):
		return float(Timestamp[time1]) * 100 * self.interval_scale - float(Timestamp[time2]) * 100 * self.interval_scale

	def print_percent(self):
		for num, count in enumerate(self.ID_Per_Sec):
			if count == 0 :
				continue
			else:
				#print "ID : {}, count : {}, Total_count : {}, Percent : {}".format(num, count, self.ID_Per_Secount, (float(count) / self.ID_Per_Secount) * 100)
				self.count_graph_x.append(num)
				self.count_graph_y.append(count)

	def Detect_Dos(self):
		for num, count in enumerate(self.ID_Per_Sec):
			if count == 0:
				continue
			else:
				if int((float(count) / self.ID_Per_Secount) * 100) > 30:
					return True
		return False
		
	def detector(self) :
		global c
		if(len(Data) > self.it) :
			if float(Timestamp[self.it])*100*self.interval_scale - float(Timestamp[0])*100*self.interval_scale - self.time_bef > 10000: #variance start
				average, variance_tmp = self.variance(self.tInterval, self.val_num)
				self.variance_graph[int(self.time_bef/10000)] = variance_tmp
				self.print_percent()

				c.send("Total_Count : {}\n".format(self.ID_Per_Secount))
				#c.send("Count x : {}, Count y : {}\n".format(self.count_graph_x, self.count_graph_y))
				c.send("variance_tmp : {}\n".format(variance_tmp))
				
				
				if(variance_tmp > 300 and self.attack_flag == False) :
					self.start_it = self.it
					self.end_it_buf = self.it
					self.end_it = self.it
					self.attack_flag = True
					self.attack_type = "Warning"
					self.Dos_count = 0
				elif(variance_tmp > 300 and self.attack_flag == True) :
					self.end_it = self.end_it_buf
					self.end_it_buf = self.it
					self.threshold = (self.threshold * self.threshold_count + variance_tmp)/(self.threshold_count + 1)
					self.threshold_count += 1
					self.Dos_count += self.Detect_Dos()
					
				elif(variance_tmp <= 300 and self.attack_flag == True) :
					start_id_dict = dict(zip((ID[:self.start_it]), (Timestamp[:self.start_it])))
					end_id_dict = dict(zip((ID[:self.end_it]), (Timestamp[:self.end_it])))

					try :
						st_t, ed_t = self.time_detection(average, self.start_it, self.end_it, start_id_dict, end_id_dict, self.threshold)
						self.attack_flag = False
						self.threshold = 0
						self.threshold_count = 0
						
						if int(float(ed_t) - float(st_t)) / 2 < self.Dos_count:
							self.attack_type = "DoS"
						else:
							self.attack_type = "Fuzzy"
						
						c.send("attack start : {}, attack end : {}, attack type : {}\n".format(st_t, ed_t, self.attack_type))
						print "attack start : {}, attack end : {}, attack type : {}".format(st_t, ed_t, self.attack_type)
					except Exception as e:
						print "Exception e : {}".format(e)

				self.tInterval = [0 for row in range(self.interval_scale)]
				self.ID_Per_Sec = [0 for row in range(0xFFFF)]
				self.count_graph_x, self.count_graph_y = [], []
				self.val_num, self.ID_Per_Secount = 0, 0
				self.time_bef += 10000

			if ID[self.it] in self.id_dic :
				if int(self.interval_of_time(self.it, 0) - self.id_dic[ID[self.it]]) < (self.interval_scale / 2) :
					self.tInterval[0] += 1
				else :
					self.tInterval[(int(self.interval_of_time(self.it, 0) - self.id_dic[ID[self.it]]) + (self.interval_scale/2)) % self.interval_scale] += 1
				self.val_num += 1
				self.id_dic[ID[self.it]] = self.interval_of_time(self.it, 0)
			else :
				self.id_dic[ID[self.it]] = self.interval_of_time(self.it, 0)
				self.time_bef = int(self.interval_of_time(self.it, 0))
			self.ID_Per_Sec[int(ID[self.it],16)] += 1
			self.ID_Per_Secount += 1
			self.it += 1

	def variance(self, tInterval, val_num):
		val_sum = 0.0
		for i in range(len(tInterval)) :
			val_sum += i * tInterval[i]
		average = float(val_sum/val_num)
		variance_sum = 0.0
		for i in range(len(tInterval)) :
			variance_sum += ((average - i) * (average - i)) * tInterval[i]
		return average, float(variance_sum / val_num)

	def time_detection(self, average, start_it, end_it, attack_start_time_id_dic, attack_end_time_id_dic, threshold) :
		it = start_it
		counter = 0
		while True :
			if ID[it] in attack_start_time_id_dic :
				if float(attack_start_time_id_dic[ID[it]])*100*self.interval_scale - float(Timestamp[it])*100*self.interval_scale < (self.interval_scale / 2) :
					variance_val = (average) * (average) 
				else :
					variance_val = (average - ((float(attack_start_time_id_dic[ID[it]])*100*self.interval_scale - float(Timestamp[it])*100*self.interval_scale+50)%100)) ** 2 
				
				if variance_val < threshold :
					counter += 1
				else :
					attack_start_time = Timestamp[it]
					counter = 0
			if counter >= 8 :
				break
			attack_start_time_id_dic[ID[it]] = Timestamp[it]
			it -= 1

		it = end_it
		counter = 0
		while True :
			if ID[it] in attack_end_time_id_dic :
				if float(Timestamp[it])*100*self.interval_scale - float(attack_end_time_id_dic[ID[it]])*100*self.interval_scale < (self.interval_scale / 2) :
					variance_val = (average) * (average) 
				else :
					variance_val = (average - ((float(attack_end_time_id_dic[ID[it]])*100*self.interval_scale - float(Timestamp[it])*100*self.interval_scale+50)%100)) ** 2 
				if variance_val < threshold :
					counter += 1
				else :
					attack_end_time = Timestamp[it]
					counter = 0
			if counter >= 8 :
				break
			attack_end_time_id_dic[ID[it]] = Timestamp[it]
			it += 1

		return attack_start_time, attack_end_time

	def recv_line(self):
		text = ""
		while True:
			data = self.clientSocket.recv(1)
			if data == "\n":
				break
			text += data
		return text

	def __init__(self, HOST, PORT):
		super(Data_Reciver, self).__init__()
		self.HOST = HOST
		self.PORT = PORT
		self.BUFSIZE = 100
		self.ADDR = (HOST,PORT)
		self.serverSocket = socket(AF_INET, SOCK_STREAM)
		self.serverSocket.bind(self.ADDR)
		self.serverSocket.listen(100)
		self.clientSocket, self.addr_info = self.serverSocket.accept()
		
		self.interval_scale = 100 #number of time inverval in 10ms
		self.time_range = 4000
		self.id_dic = {}
		
		self.tInterval = [0 for row in range(self.interval_scale)] #x축 time interval 10으로 나눈 나머지, y축 패킷 개수
		self.variance_graph = [0 for row in range(self.time_range)] #x축 시간, y축 분산
		self.count_graph_x = []
		self.count_graph_y = []
		self.ID_Per_Sec = [0 for row in range(0xFFFF)]
		self.ID_Per_Secount = 0
		self.val_num = 0
		self.time_bef = 0
		self.it = 0
		self.attack_flag = False
		self.start_it = 0
		self.end_it_buf = 0
		self.end_it = 0
		self.threshold = 0
		self.threshold_count = 0
		self.Dos_count = 0
		self.attack_type = ""

	def run(self):
		while True:
			buf = self.recv_line()
			Timestamp.append(buf.split('Timestamp: ')[1][:17])
			ID.append(buf.split('ID: ')[1][:4])
			Sub_ID.append(buf.split('ID: ')[1][8:11])
			DLC.append(buf.split('DLC: ')[1][:1])
			Data.append(buf.split('DLC: ')[1][5:].split(' '))
			Total_Data.append(buf)
			self.detector()
		
	def stop(self):
		self.clientSocket.close()
		self.serverSocket.close()

def Connect_GUI():
	global c
	c = socket(AF_INET, SOCK_STREAM)
	try:
		c.connect(ADDR)
		print "connect!"
		return 1
	except Exception as e:
		print('%s:%s' % ADDR)
	return 0
	
if __name__ == "__main__":

	Connect_GUI()
		
	Thread = []
	th = Data_Reciver("", 10000)
	th.daemon = True
	th.start()
	Thread.append(th)
	
	for i in range(0,len(Thread)):
		Thread[i].join()

