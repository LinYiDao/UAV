#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import  *
import windows
class widget_connect_pi():
    def __init__(self):
        self.initui()

    def initui(self):
        self.dialog = QDialog()
        self.dialog.setWindowTitle('IP+端口的输入')
        # dialog.setFixedSize(QSize(400, 200))
        self.namel1 = QLabel('&IP', self.dialog)
        self.nameEd1 = QLineEdit(self.dialog)
        self.nameEd1.setInputMask("000.000.000.000;_")  # 端口格式
        self.namel1.setBuddy(self.nameEd1)  # 设置快捷键

        self.namel2 = QLabel('&Port', self.dialog)
        self.nameEd2 = QLineEdit()
        pInt = QIntValidator(self.dialog)
        pInt.setRange(1, 9999)
        self.nameEd2.setValidator(pInt)
        self.namel2.setBuddy(self.nameEd2)  # 设置快捷键

        self.namel3 = QLabel('&Type', self.dialog)
        self.nameEd3 = QLineEdit()
        pInt = QIntValidator(self.dialog)
        pInt.setRange(1, 4)
        self.nameEd3.setValidator(pInt)
        self.namel3.setBuddy(self.nameEd3)  # 设置快捷键

        self.btnconnect = QPushButton('Connect')
        btnCancel = QPushButton('&Cancel')

        self.btnconnect.clicked.connect(lambda: windows.windows.thread1(windows.windows(),self.nameEd1.text(),int(self.nameEd2.text()),str(self.nameEd3.text())))
        self.btnconnect.clicked.connect(lambda: windows.windows.addmsg(windows.windows(),windows.jsonmake('CONN',self.nameEd3.text()).encode('utf-8'),str(self.nameEd3.text())))

        self.btnconnect.clicked.connect(self.dialog.close)


        # self.btnconnect.clicked.connect(lambda :windows.windows.test(windows.windows(),self.nameEd1.text(),int(self.nameEd2.text())))
        # self.btnconnect.clicked.connect(lambda:btnCancel.setEnabled(False))
        # 添加控件
        mainlayout = QGridLayout()
        mainlayout.addWidget(self.namel1, 0, 0)
        mainlayout.addWidget(self.nameEd1, 0, 1, 1, 2)
        mainlayout.addWidget(self.namel2, 1, 0)
        mainlayout.addWidget(self.nameEd2, 1, 1, 1, 2)
        mainlayout.addWidget(self.namel3, 2, 0)
        mainlayout.addWidget(self.nameEd3, 2, 1, 1, 2)
        mainlayout.addWidget(self.btnconnect, 3, 1)
        mainlayout.addWidget(btnCancel, 3, 2)
        self.dialog.setLayout(mainlayout)
