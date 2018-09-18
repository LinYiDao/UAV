#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from PyQt5.QtCore import *
import PyQt5.QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebChannel import *
import socket
import time
import threading
import queue
import json
from connectObject import*

from PyQt5.QtWebEngineWidgets import QWebEngineView

import widget_connect_pi
import widget_RC
import widget_guided
################################################
#   定义一下json协议的传输规则
# { Header:CONN(连接树莓派)、
#   Type: 哪个飞机。}{'cmd':0 (默认为无)
#                         }
#
#
# { Header:RC(模拟遥控器)、
#   Type: 哪个飞机。}
#
# { 'cmd': 1(takeoff) 、
#          2(land) 、
#          3、4、5 、6(上、下、左、右) 、
#    'content':''
# }
#
#  {Header:GU、type:哪个飞机}
#  { ‘cmd’:'','content':['bei','dong']
# }
#
#
#################################################



#定义全局的协议. ---conn协议
# json_conn=json.dumps([{'Header':'conn','type':'0'},{}])
#RC模式下的协议控制
# json_rc_0=json.dumps([{'Header':'RC','type':'0'},{'cmd':'0'}])
# json_rc_1=json.dumps([{'Header':'RC','type':'0'},{'cmd':'1'}])
# json_rc_2=json.dumps([{'Header':'RC','type':'0'},{'cmd':'2'}])
# json_rc_3=json.dumps([{'Header':'RC','type':'0'},{'cmd':'3'}])
# json_rc_4=json.dumps([{'Header':'RC','type':'0'},{'cmd':'4'}])
# json_rc_5=json.dumps([{'Header':'RC','type':'0'},{'cmd':'5'}])

#定义 host 和 cilent 、 host 是无人机  cilent是地面站.
host=''
host_port=''
cilent='223.3.103.170'
cilent_port=8888

#全局的消息队列。
send_queue=queue.Queue()
send_queue2=queue.Queue()
send_queue3=queue.Queue()
send_queue4=queue.Queue()

#通过udp接收到的消息。
recv_queue = queue.Queue()
recv_queue2 = queue.Queue()
recv_queue3 = queue.Queue()
recv_queue4 = queue.Queue()

#发送位置信息队列
map_queue = queue.Queue()


def jsonmake(header,type,cmd='0',content='0'):
    return json.dumps([{'Header':header,'type':type},{'cmd':cmd,'content':content}])
def mapJson(lng,lat):
    return json.dumps({'lon':lng,'lat':lat})


#设置共享数据类型
class MyObject(PyQt5.QtCore.QObject):
    def __init__(self):
        pass
    def readval(self):
        pass
    def setval(self):
        pass
    ppval=PyQt5.QtCore.pyqtProperty(list, readval, setval)

class windows(PyQt5.QtWidgets.QWidget):


    view: QWebEngineView
    sigSendMapMsg = pyqtSignal(str)

    def __init__(self):
        super(windows, self).__init__()
        self. initUI()


    def initUI(self):
        mainlayout = PyQt5.QtWidgets.QHBoxLayout()  # 主页面
        # 这个是四台无人机状态的控件

        self.textedit1 = PyQt5.QtWidgets.QListWidget()
        self.textedit5 = PyQt5.QtWidgets.QListWidget()
        self.view = QWebEngineView()
        self.textedit2 = PyQt5.QtWidgets.QListWidget()
        self.textedit3 = PyQt5.QtWidgets.QListWidget()
        self.textedit4 = PyQt5.QtWidgets.QListWidget()
        self.textedit1.setMaximumSize(PyQt5.QtCore.QSize(200, 150))
        self.textedit2.setMaximumSize(PyQt5.QtCore.QSize(200, 150))
        self.textedit3.setMaximumSize(PyQt5.QtCore.QSize(200, 150))
        self.textedit4.setMaximumSize(PyQt5.QtCore.QSize(200, 150))
        glayout = PyQt5.QtWidgets.QGridLayout()  # pix的布局
        glayout.addWidget(self.textedit1, 0, 0)
        glayout.addWidget(self.textedit2, 0, 1)
        glayout.addWidget(self.textedit3, 1, 0)
        glayout.addWidget(self.textedit4, 1, 1)
        pixwidget = PyQt5.QtWidgets.QWidget()  # 左边的
        pixwidget.setFixedSize(PyQt5.QtCore.QSize(400, 300))
        pixwidget.setLayout(glayout)  # 这个是四台无人机状态的控件
        # 这个是连接按钮和指令台的控件。
        btn = PyQt5.QtWidgets.QPushButton('连接无人机')
        self.textedit5.setFixedSize(PyQt5.QtCore.QSize(250, 150))
        btn.setFixedSize(PyQt5.QtCore.QSize(100, 100))  # 改变按钮的大小
        hlayout = PyQt5.QtWidgets.QHBoxLayout()
        hlayout.addWidget(btn)
        hlayout.addWidget(self.textedit5)
        connectwidget = PyQt5.QtWidgets.QWidget()
        connectwidget.setFixedSize(PyQt5.QtCore.QSize(400, 150))
        connectwidget.setLayout(hlayout)  # 这个是连接按钮和指令台的控件。
        # 三个模式的控件
        modewidget = PyQt5.QtWidgets.QWidget()
        self.modebtn1 = PyQt5.QtWidgets.QPushButton('导航模式')
        self.modebtn2 = PyQt5.QtWidgets.QPushButton('RC模式')
        self.modebtn3 = PyQt5.QtWidgets.QPushButton('--模式')
        modelayout = PyQt5.QtWidgets.QHBoxLayout()
        self.modebtn1.setFixedSize(PyQt5.QtCore.QSize(100, 100))
        self.modebtn2.setFixedSize(PyQt5.QtCore.QSize(100, 100))
        self.modebtn3.setFixedSize(PyQt5.QtCore.QSize(100, 100))
        #刚开始是不可以活动的
        self.modebtn1.setEnabled(False)
        self.modebtn2.setEnabled(False)
        self.modebtn3.setEnabled(False)
        modelayout.addWidget(self.modebtn1)
        modelayout.addWidget(self.modebtn2)
        modelayout.addWidget(self.modebtn3)
        modewidget.setFixedSize(PyQt5.QtCore.QSize(400, 100))
        modewidget.setLayout(modelayout)  # 三个模式的控件
        #mode2的点击弹出
        self.modebtn2.clicked.connect(self.RC)
        self.modebtn1.clicked.connect(self.guided)
        #连接无人机的点击弹出。
        btn.clicked.connect(self.connectshow)
        # btn.clicked.connect(self.modebtn2.setEnabled(True))
        # 这是左侧三个东西的控件
        leftwidget = PyQt5.QtWidgets.QWidget()
        leftlayout = PyQt5.QtWidgets.QVBoxLayout()

        leftlayout.addWidget(pixwidget)
        leftlayout.addWidget(connectwidget)
        leftlayout.addWidget(modewidget)
        leftwidget.setLayout(leftlayout)
        # 右边的地图的控件
        #   rightwidget=QWidget()# 右边的地图的控件
        map = PyQt5.QtWidgets.QWidget()
        #创建一个侨界对象
        map.setFixedSize(PyQt5.QtCore.QSize(600, 550))
        ll=PyQt5.QtWidgets.QVBoxLayout()
        map.setLayout(ll)
        self.channel = QWebChannel()
        url = r'F://test1/index.html'
        self.view.load(PyQt5.QtCore.QUrl(url))
        ll.addWidget(self.view)
        self.obj = connectObject()
        self.channel.registerObject("bridge",self.obj)
        self.view.page().setWebChannel(self.channel)
#
        # 主页面的修改
        mainlayout.addWidget(leftwidget)  # 左上的部件。
        mainlayout.addWidget(map)  # 左上的部件。
        self.setLayout(mainlayout)
        self.setGeometry(400, 200, 1000, 550)

        self.sigSendMapMsg.connect(self.obj.sendMap)

    def setable(self,num):
        if(num == 1):
            self.modebtn1.setEnabled(True)
        if (num == 2):
            self.modebtn1.setEnabled(True)
        if (num == 3):
            self.modebtn1.setEnabled(True)

    # 界面 ---连接无人机按钮的连接到地方’，弹出IP连接的地址
    def connectshow(self):
        widget_con = widget_connect_pi.widget_connect_pi()
        #连接了无人机才能起飞
        widget_con.btnconnect.clicked.connect(lambda :self.modebtn2.setEnabled(True))
        #根据是第几个无人机，选择开哪个线程。
        widget_con.btnconnect.clicked.connect(lambda :self.thread2(widget_con.nameEd3.text()))
        widget_con.dialog.exec_()

    #界面 ---mode RC 的界面
    def RC(self):
        widget_rc = widget_RC.widget_RC()
        #
        widget_rc.btntakeoff.clicked.connect(lambda :self.modebtn1.setEnabled(True))
        widget_rc.dialog.exec_()
    #界面 导航模式的界面
    def guided(self):
        widget_guid=widget_guided.widget_guided()
        widget_guid.dialog.exec_()
    #利用线程防止阻塞:连接树莓派
    def thread1(self , addr ,port,type):
        t = threading.Thread(target=self.connectpi, args=(addr,port,type))
        t.start()

    #利用线程 根据是第几个飞机，来选择监听哪个线程
    def thread2(self , type):
        t = threading.Thread(target=self.monitorPC,args=type)
        t.start()

    def test(self,a=0,b=0):
        print('class hhhh',a,b)

    #利用线程防止阻塞：udp监听本机端口
    # 现在是手动开四个线程，怎么才能自动？ 要思考
    def workthread(self):
        t1 = threading.Thread(target=self.handlemsg)
        t1.start()

    #往不同的消息队列中添加消息。
    def addmsg(self,msg,type):
        print(msg)
        if(type=='1'):
            print('queue 1 put a msg')
            send_queue.put(msg)
        if(type=='2'):
            print('queue 2 put a msg')
            send_queue2.put(msg)
        if(type=='3'):
            print('queue 3 put a msg')
            send_queue3.put(msg)
        if(type=='4'):
            print('queue 4 put a msg')
            send_queue4.put(msg)

    #分析接收队列中的消息的内容。
    #这里还需要进行异常处理。
    #连接到树莓派的函数.并且保持通信
    def connectpi(self,addr,port,type):
        socket_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # tcp连接、用于发送消息。
        # 建立连接:
        print((addr,port))
        socket_send.connect((addr,port))
        if(type=='1'):
            while True:
                if (send_queue.qsize() != 0):
                    print('send queue 1 pre to send msg')
                    socket_send.send(send_queue.get())
                time.sleep(0.5)
        if(type=='2'):
            while True:
                if (send_queue2.qsize() != 0):
                    print('send queue 2 pre to send msg')
                    socket_send.send(send_queue2.get())
                time.sleep(0.5)
        if(type=='3'):
            while True:
                if (send_queue3.qsize() != 0):
                    print('send queue 3 pre to send msg')
                    socket_send.send(send_queue3.get())
                time.sleep(0.5)
        if(type=='4'):
            while True:
                if (send_queue4.qsize() != 0):
                    print('send queue 4 pre to send msg')
                    socket_send.send(send_queue4.get())
                time.sleep(0.5)


     #监听本机的函数。
    def monitorPC(self,type):
        print('the port monitor '+type+'has already monited')
        socket_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # udp 连接、接受返回的各种消息。
        # 绑定端口: 根据是第几台无人机自动的绑定无人机
        port=cilent_port+int(type)
        socket_recv.bind((cilent, port))
        l=0
        while True:
            # 接收数据:
            l=l+1
            print('this is '+str(l)+' time')
            data, addr = socket_recv.recvfrom(1024)
            print('Received from %s:%s.' % addr)
            #接收队列中收到的是传来的消息。
            msg=json.loads(data.decode('utf-8'))
            if(msg[0]['type']=='1'):
                print('recv_queue1 has get a msg', msg)
                recv_queue.put(msg)
                print(recv_queue.qsize())
                print(recv_queue)
            # if(recv_queue.qsize()==1):
            #     print('already 1')
            if (msg[0]['type'] == '2'):
                print('recv_queue 2 has get a msg',msg)
                recv_queue2.put(msg)
            if (msg[0]['type'] == '3'):
                print('recv_queue 3 has get a msg',msg)
                recv_queue3.put(msg)
            if (msg[0]['type'] == '4'):
                print('recv_queue 4 has get a msg',msg)
                recv_queue4.put(msg)
            time.sleep(0.5)


    #处理收到的消息的函数
    def handlemsg(self):
        while True:

            if(recv_queue.qsize()!=0):
                msg = recv_queue.get()
                print(msg)
                #都未对经纬度进行处理。
                if (msg[0]['Header'] == 'RE' and msg[0]['type']=='1'):
                    self.textedit1.clear()
                    self.textedit1.addItem('version:'+msg[1]['version'])
                    self.textedit1.addItem('battery:' + str(msg[1]['battery']))
                    self.textedit1.addItem('mode:' + str(msg[1]['mode']))
                    self.textedit1.addItem('status:' + msg[1]['status'])
                    self.textedit1.addItem('lat:' + str(msg[1]['lat']))
                    self.textedit1.addItem('lon:' + str(msg[1]['lon']))
                    mapMsg = mapJson(msg[1]['lon'],msg[1]['lat'])
                    self.sigSendMapMsg.emit(mapMsg)
                # 对多个无人机的消息处理 还没进行 。
                if(msg[0]['Header'] == 'CMD'):
                    self.textedit5.addItem(msg[0]['type']+':'+msg[1]['msg'])
                    #每次都是到最底下。
                    self.textedit5.setCurrentRow(self.textedit5.count()-1)

            if (recv_queue2.qsize() != 0):
                msg = recv_queue2.get()
                print(msg)
                # 都未对经纬度进行处理。
                if (msg[0]['Header'] == 'RE' and msg[0]['type'] == '2'):
                    self.textedit2.clear()
                    self.textedit2.addItem('version:' + msg[1]['version'])
                    self.textedit2.addItem('battery:' + str(msg[1]['battery']))
                    self.textedit2.addItem('mode:' + str(msg[1]['mode']))
                    self.textedit2.addItem('status:' + msg[1]['status'])
                    self.textedit2.addItem('lat:' + str(msg[1]['lat']))
                    self.textedit2.addItem('lon:' + str(msg[1]['lon']))
                    mapMsg = mapJson(msg[1]['lon'],msg[1]['lat'])
                    self.sigSendMapMsg.emit(mapMsg)
                # 对多个无人机的消息处理 还没进行 。
                if (msg[0]['Header'] == 'CMD'):
                    self.textedit5.addItem(msg[0]['type'] + ':' + msg[1]['msg'])
                    # 每次都是到最底下。
                    self.textedit5.setCurrentRow(self.textedit5.count() - 1)
            if (recv_queue3.qsize() != 0):
                msg = recv_queue3.get()
                #print(msg)
                # 都未对经纬度进行处理。
                if (msg[0]['Header'] == 'RE' and msg[0]['type'] == '3'):
                    self.textedit3.clear()
                    self.textedit3.addItem('version:' + msg[1]['version'])
                    self.textedit3.addItem('battery:' + str(msg[1]['battery']))
                    self.textedit3.addItem('mode:' + str(msg[1]['mode']))
                    self.textedit3.addItem('status:' + msg[1]['status'])
                    self.textedit3.addItem('lat:' + str(msg[1]['lat']))
                    self.textedit3.addItem('lon:' + str(msg[1]['lon']))
                    mapMsg = mapJson(msg[1]['lon'],msg[1]['lat'])
                    self.sigSendMapMsg.emit(mapMsg)
                # 对多个无人机的消息处理 还没进行 。
                if (msg[0]['Header'] == 'CMD'):
                    self.textedit5.addItem(msg[0]['type'] + ':' + msg[1]['msg'])
                    # 每次都是到最底下。
                    self.textedit5.setCurrentRow(self.textedit5.count() - 1)
            if (recv_queue4.qsize() != 0):
                msg = recv_queue4.get()
                print(msg)
                # 都未对经纬度进行处理。
                if (msg[0]['Header'] == 'RE' and msg[0]['type'] == '4'):
                    self.textedit4.clear()
                    self.textedit4.addItem('version:' + msg[1]['version'])
                    self.textedit4.addItem('battery:' + str(msg[1]['battery']))
                    self.textedit4.addItem('mode:' + str(msg[1]['mode']))
                    self.textedit4.addItem('status:' + msg[1]['status'])
                    self.textedit4.addItem('lat:' + str(msg[1]['lat']))
                    self.textedit4.addItem('lon:' + str(msg[1]['lon']))
                    mapMsg = mapJson(msg[1]['lon'],msg[1]['lat'])
                    self.sigSendMapMsg.emit(mapMsg)
                # 对多个无人机的消息处理 还没进行 。
                if (msg[0]['Header'] == 'CMD'):
                    self.textedit5.addItem(msg[0]['type'] + ':' + msg[1]['msg'])
                    # 每次都是到最底下。
                    self.textedit5.setCurrentRow(self.textedit5.count() - 1)

            time.sleep(0.5)


if __name__=='__main__':
    app=PyQt5.QtWidgets.QApplication(sys.argv)
    icon=windows()
    icon.show()
    #开启工作线程
    icon.workthread()
    sys.exit(app.exec_())
