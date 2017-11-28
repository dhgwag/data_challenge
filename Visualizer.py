# -*- coding: utf8 -*-

from PyQt4 import QtGui
from PyQt4 import QtCore
import numpy as np
import matplotlib
matplotlib.use("Qt4Agg")
from matplotlib.figure import Figure
from matplotlib.animation import TimedAnimation
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import threading
from socket import *
from select import *
import sys, time


def setCustomSize(x, width, height):
	sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
	sizePolicy.setHorizontalStretch(0)
	sizePolicy.setVerticalStretch(0)
	sizePolicy.setHeightForWidth(x.sizePolicy().hasHeightForWidth())
	x.setSizePolicy(sizePolicy)
	x.setMinimumSize(QtCore.QSize(width, height))
	x.setMaximumSize(QtCore.QSize(width, height))

''''''

class CustomMainWindow(QtGui.QMainWindow):

	def __init__(self):
		super(CustomMainWindow, self).__init__()

		# Define the geometry of the main window
		self.setGeometry(300, 300, 1500, 400)
		self.setWindowTitle("IDS")

		# Create FRAME_A
		self.FRAME_A = QtGui.QFrame(self)
		self.FRAME_A.setStyleSheet("QWidget { background-color: %s }" % QtGui.QColor(210,210,235,255).name())
		self.LAYOUT_A = QtGui.QGridLayout()
		self.FRAME_A.setLayout(self.LAYOUT_A)
		self.setCentralWidget(self.FRAME_A)

		# Place the zoom button
		# self.zoomBtn = QtGui.QPushButton(text = 'zoom')
		# setCustomSize(self.zoomBtn, 50, 50)
		# self.zoomBtn.clicked.connect(self.zoomBtnAction)
		# self.LAYOUT_A.addWidget(self.zoomBtn, *(0,0))

		# Place the matplotlib figure
		self.TotalCountFig = TotalCountFigCanvas()
		self.VarianceFig = VarianceFigCanvas()
		self.LogView = LogTableWidgetView()
		
		setCustomSize(self.TotalCountFig, 550, 400)
		setCustomSize(self.VarianceFig, 550, 400)
		setCustomSize(self.LogView, 350, 400)
		
		self.LAYOUT_A.addWidget(self.TotalCountFig, *(0,1))
		self.LAYOUT_A.addWidget(self.VarianceFig, *(0,2))
		self.LAYOUT_A.addWidget(self.LogView, *(0,3))

		callback_list = [self.TotaladdData_callbackFunc, self.VarianceaddData_callbackFunc, self.AddLogView]

		# Add the callbackfunc to ..
		myDataLoop = threading.Thread(name = 'DataLoop', target = dataSendLoop, args = (callback_list,))
		myDataLoop.daemon = True
		myDataLoop.start()
		self.show()

	def TotaladdData_callbackFunc(self, value):
		# print("Add data: " + str(value))
		self.TotalCountFig.addData(value)

	def VarianceaddData_callbackFunc(self, value):
		# print("Add data: " + str(value))
		self.VarianceFig.addData(value)

	def AddLogView(self, value):
		self.LogView.setTableWidgetData(value)
''' End Class '''


class LogTableWidgetView(QtGui.QTableWidget):
	def __init__(self):
		super(LogTableWidgetView, self).__init__()
		self.resize(230, 290)
		self.setRowCount(1)
		self.setColumnCount(3)
		self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
		column_headers = ['attack type', 'start time', 'end time']
		self.setHorizontalHeaderLabels(column_headers)

	def setTableWidgetData(self, attack_result):
		column_idx_lookup = {'attack type': 0, 'attack start': 1, 'attack end': 2}
		for k, v in attack_result.items():
			# k - key, v - value
			row = self.rowCount()-1
			col = column_idx_lookup[k]
			item = QtGui.QTableWidgetItem(v)
			item.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
			self.setItem(row, col, item)
		self.setRowCount(self.rowCount()+1)
		self.resizeColumnsToContents()
		self.resizeRowsToContents()


class TotalCountFigCanvas(FigureCanvas, TimedAnimation):

	def __init__(self):

		self.addedData = []
		print(matplotlib.__version__)

		# The data
		self.xlim = 300
		self.n = np.linspace(0, self.xlim-1, self.xlim)
		self.y = (self.n * 0.0) + 0

		# The window
		self.fig = Figure(figsize=(5,5), dpi=100)
		self.ax1 = self.fig.add_subplot(111)


		# self.ax1 settings
		self.ax1.set_xlabel('time')
		self.ax1.set_ylabel('Total Count')
		self.line1 = Line2D([], [], color='blue')
		self.line1_tail = Line2D([], [], color='red', linewidth=2)
		self.line1_head = Line2D([], [], color='red', marker='o', markeredgecolor='r')
		self.ax1.add_line(self.line1)
		self.ax1.add_line(self.line1_tail)
		self.ax1.add_line(self.line1_head)
		self.ax1.set_xlim(0, self.xlim - 1)
		self.ax1.set_ylim(0, 5000)


		FigureCanvas.__init__(self, self.fig)
		TimedAnimation.__init__(self, self.fig, interval = 50, blit = True)

	def new_frame_seq(self):
		return iter(range(self.n.size))

	def _init_draw(self):
		lines = [self.line1, self.line1_tail, self.line1_head]
		for l in lines:
			l.set_data([], [])

	def addData(self, value):
		self.addedData.append(value)

	def _step(self, *args):
		# Extends the _step() method for the TimedAnimation class.
		try:
			TimedAnimation._step(self, *args)
		except Exception as e:
			self.abc += 1
			print(str(self.abc))
			TimedAnimation._stop(self)
			pass

	def _draw_frame(self, framedata):
		margin = 2
		while(len(self.addedData) > 0):
			self.y = np.roll(self.y, -1)
			self.y[-1] = self.addedData[0]
			del(self.addedData[0])


		self.line1.set_data(self.n[ 0 : self.n.size - margin ], self.y[ 0 : self.n.size - margin ])
		self.line1_tail.set_data(np.append(self.n[-10:-1 - margin], self.n[-1 - margin]), np.append(self.y[-10:-1 - margin], self.y[-1 - margin]))
		self.line1_head.set_data(self.n[-1 - margin], self.y[-1 - margin])
		self._drawn_artists = [self.line1, self.line1_tail, self.line1_head]


class VarianceFigCanvas(FigureCanvas, TimedAnimation):

	def __init__(self):

		self.addedData = []
		print(matplotlib.__version__)

		# The data
		self.xlim = 300
		self.n = np.linspace(0, self.xlim-1, self.xlim)
		self.y = (self.n * 0.0) + 0

		# The window
		self.fig = Figure(figsize=(5,5), dpi=100)
		self.ax1 = self.fig.add_subplot(111)


		# self.ax1 settings
		self.ax1.set_xlabel('time')
		self.ax1.set_ylabel('Variance')
		self.line1 = Line2D([], [], color='blue')
		self.line1_tail = Line2D([], [], color='red', linewidth=2)
		self.line1_head = Line2D([], [], color='red', marker='o', markeredgecolor='r')
		self.ax1.add_line(self.line1)
		self.ax1.add_line(self.line1_tail)
		self.ax1.add_line(self.line1_head)
		self.ax1.set_xlim(0, self.xlim - 1)
		self.ax1.set_ylim(0, 1000)


		FigureCanvas.__init__(self, self.fig)
		TimedAnimation.__init__(self, self.fig, interval = 50, blit = True)

	def new_frame_seq(self):
		return iter(range(self.n.size))

	def _init_draw(self):
		lines = [self.line1, self.line1_tail, self.line1_head]
		for l in lines:
			l.set_data([], [])

	def addData(self, value):
		self.addedData.append(value)

	def _step(self, *args):
		# Extends the _step() method for the TimedAnimation class.
		try:
			TimedAnimation._step(self, *args)
		except Exception as e:
			self.abc += 1
			print(str(self.abc))
			TimedAnimation._stop(self)
			pass

	def _draw_frame(self, framedata):
		margin = 2
		while(len(self.addedData) > 0):
			self.y = np.roll(self.y, -1)
			self.y[-1] = self.addedData[0]
			del(self.addedData[0])


		self.line1.set_data(self.n[ 0 : self.n.size - margin ], self.y[ 0 : self.n.size - margin ])
		self.line1_tail.set_data(np.append(self.n[-10:-1 - margin], self.n[-1 - margin]), np.append(self.y[-10:-1 - margin], self.y[-1 - margin]))
		self.line1_head.set_data(self.n[-1 - margin], self.y[-1 - margin])
		self._drawn_artists = [self.line1, self.line1_tail, self.line1_head]



''' End Class '''


# You need to setup a signal slot mechanism, to
# send data to your GUI in a thread-safe way.
# Believe me, if you don't do this right, things
# go very very wrong..
class Communicate(QtCore.QObject):
	data_signal = QtCore.pyqtSignal(float)

class Communicate_dict(QtCore.QObject):
	data_signal = QtCore.pyqtSignal(dict)
	
''' End Class '''


def recvline(s):
	 data = ''
	 while not data.endswith('\n'):
		tmp = s.recv(1)
		if not tmp : break
		data += tmp
	 return data

def dataSendLoop(callback_list):

	TotalCountSrc = Communicate()
	TotalCountSrc.data_signal.connect(callback_list[0])

	VarianceSrc = Communicate()
	VarianceSrc.data_signal.connect(callback_list[1])

	LogViewSrc = Communicate_dict()
	LogViewSrc.data_signal.connect(callback_list[2])	

	# 호스트, 포트와 버퍼 사이즈를 지정
	HOST = ''
	PORT = 56789
	BUFSIZE = 1024
	ADDR = (HOST, PORT)

	# socket 서버 생성
	serverSocket = socket(AF_INET, SOCK_STREAM)
	serverSocket.bind(ADDR)
	serverSocket.listen(10)
	conn, addr = serverSocket.accept()
	print 'Connected by', addr
	while 1:
		recvData = recvline(conn)
		if 'Total_Count : ' in recvData:
			Total_Count = int(recvData.split('Total_Count : ')[1])	
			TotalCountSrc.data_signal.emit(Total_Count) # <- Here you emit a signal!
		elif "variance_tmp : " in recvData:
			variance_tmp = int(float(recvData.split('variance_tmp : ')[1][:-1]))
			VarianceSrc.data_signal.emit(variance_tmp) # <- Here you emit a signal!
		else:
			print recvData
			attack_result = recvData.split(', ')
			attack_start = "%.6f" % (float(attack_result[0].split('attack start : ')[1]))
			attack_end = "%.6f" % (float(attack_result[1].split('attack end : ')[1]))
			attack_type = attack_result[2].split('attack type : ')[1][:-1]
			attack_result = {"attack start" : attack_start, "attack end" : attack_end, "attack type" : attack_type}
			LogViewSrc.data_signal.emit(attack_result) # <- Here you emit a signal!

	conn.close()

if __name__== '__main__':

	app = QtGui.QApplication(sys.argv)
	QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Plastique'))
	myGUI = CustomMainWindow()


	sys.exit(app.exec_())

''''''
