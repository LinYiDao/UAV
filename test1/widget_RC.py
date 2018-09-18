#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import windows

class widget_RC():
    def __init__(self):
        self.initui()

    def initui(self):
        self.dialog=QDialog()
        self.dialog.setFixedSize(QSize(400, 200))
        self.dialog.setWindowTitle('遥控器模式')
        # 初始化按钮
        self.btnup=QPushButton('↑')
        self.btnup.setFixedSize(QSize(60, 40))
        self.btnup.setEnabled(False)
        self.btndown = QPushButton('↓')
        self.btndown.setFixedSize(QSize(60, 40))
        self. btndown.setEnabled(False)
        self.btnleft = QPushButton('←')
        self.btnleft.setFixedSize(QSize(60, 40))
        self.btnleft.setEnabled(False)
        self.btnright = QPushButton('→')
        self. btnright.setFixedSize(QSize(60, 40))
        self. btnright.setEnabled(False)
        self. btntakeoff = QPushButton('Take-OFF')
        self. btntakeoff.setFixedSize(QSize(100, 50))
        self.btnland = QPushButton('LAND')
        self. btnland.setEnabled(True)
        self. btnland.setFixedSize(QSize(100, 50))
        #复选框
        self.checkbox1 = QCheckBox('1')
        self.checkbox2 = QCheckBox('2')
        self.checkbox3 = QCheckBox('3')
        self.checkbox4 = QCheckBox('4')

        #复选框的信号槽 ,准备把复选框的信号写入到btn的信号槽中
        # self.checkbox1.clicked.connect(self.test)
        #添加信号1,起飞后解锁所有按钮并且封印自己
        self.btntakeoff.clicked.connect(lambda :self.btnland.setEnabled(True))
        self.btntakeoff.clicked.connect(lambda: self.btnup.setEnabled(True))
        self.btntakeoff.clicked.connect(lambda: self.btndown.setEnabled(True))
        self.btntakeoff.clicked.connect(lambda: self.btnleft.setEnabled(True))
        self.btntakeoff.clicked.connect(lambda: self.btnright.setEnabled(True))
        self.btntakeoff.clicked.connect(lambda: self.btntakeoff.setEnabled(False))
        #每个按钮的通信信号
        # 协议传输 一定要encode，变成字节
        # self.btntakeoff.clicked.connect(lambda: windows.windows.addmsg(windows.windows(),windows.jsonmake('RC','0','1').encode('utf-8')))
        # self.btnland.clicked.connect(lambda: windows.windows.addmsg(windows.windows(),windows.jsonmake('RC','0','2').encode('utf-8')))
        # self.btnup.clicked.connect(lambda: windows.windows.addmsg(windows.windows(),windows.jsonmake('RC','0','3').encode('utf-8')))
        # self.btndown.clicked.connect(lambda: windows.windows.addmsg(windows.windows(),windows.jsonmake('RC','0','4').encode('utf-8')))
        # self.btnleft.clicked.connect(lambda: windows.windows.addmsg(windows.windows(),windows.jsonmake('RC','0','5').encode('utf-8')))
        # self.btnright.clicked.connect(lambda: windows.windows.addmsg(windows.windows(),windows.jsonmake('RC','0','6').encode('utf-8')))

        self.btntakeoff.clicked.connect(lambda: self.RCsend('1'))
        self.btnland.clicked.connect(lambda: self.RCsend('2'))
        self.btnup.clicked.connect(lambda: self.RCsend('3'))
        self.btndown.clicked.connect(lambda: self.RCsend('4'))
        self.btnleft.clicked.connect(lambda: self.RCsend('5'))
        self.btnright.clicked.connect(lambda: self.RCsend('6'))

        #添加控件
        mainlayout=QGridLayout()
        mainlayout.addWidget(self.checkbox1, 0, 0)
        mainlayout.addWidget(self.checkbox2, 1, 0)
        mainlayout.addWidget(self.checkbox3, 2, 0)
        mainlayout.addWidget(self.checkbox4, 3, 0)

        mainlayout.addWidget(self.btntakeoff, 0, 1)
        mainlayout.addWidget(self.btnland, 2, 1)
        mainlayout.addWidget(self.btnup, 0, 3)
        mainlayout.addWidget(self.btndown, 2, 3)
        mainlayout.addWidget(self.btnleft, 1, 2)
        mainlayout.addWidget(self.btnright, 1, 4)
        self.dialog.setLayout(mainlayout)

    def test(self):
        if(self.checkbox1.isChecked()):
            print('okok')

    def RCsend(self,cmd):
        if(self.checkbox1.isChecked()):
            windows.windows.addmsg(windows.windows(), windows.jsonmake('RC', self.checkbox1.text(), cmd).encode('utf-8'),self.checkbox1.text())
        if (self.checkbox2.isChecked()):
            windows.windows.addmsg(windows.windows(), windows.jsonmake('RC', self.checkbox2.text(), cmd).encode('utf-8'), self.checkbox2.text())
        if (self.checkbox3.isChecked()):
            windows.windows.addmsg(windows.windows(), windows.jsonmake('RC', self.checkbox3.text(), cmd).encode('utf-8'), self.checkbox3.text())
        if (self.checkbox4.isChecked()):
            windows.windows.addmsg(windows.windows(), windows.jsonmake('RC', self.checkbox4.text(), cmd).encode('utf-8'), self.checkbox4.text())