#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import windows
class widget_guided():
    def __init__(self):
        self.initui()

    def initui(self):
        self.dialog = QDialog()
        self.dialog.setWindowTitle('guided模式')
        self.namel1 = QLabel('北', self.dialog)
        self.nameEd1 = QLineEdit()
        pInt = QIntValidator(self.dialog)
        pInt.setRange(1, 20)
        self.nameEd1.setValidator(pInt)
        # self.namel2.setBuddy(self.nameEd2)  # 设置快捷键
        #
        self.namel2 = QLabel('东', self.dialog)
        self.nameEd2 = QLineEdit()
        pInt = QIntValidator(self.dialog)
        pInt.setRange(1, 20)
        self.nameEd2.setValidator(pInt)
        # self.namel2.setBuddy(self.nameEd2)  # 设置快捷键
        #
        #复选框
        self.checkbox1 = QCheckBox('1')
        self.checkbox2 = QCheckBox('2')
        self.checkbox3 = QCheckBox('3')
        self.checkbox4 = QCheckBox('4')

        self.btnconnect = QPushButton('fly')
        self.btnconnect.clicked.connect(lambda:self.RCsend(self.nameEd1.text(),self.nameEd2.text()))

        # 添加控件
        mainlayout = QGridLayout()
        mainlayout.addWidget(self.checkbox1, 0, 0)
        mainlayout.addWidget(self.checkbox2, 0, 1)
        mainlayout.addWidget(self.checkbox3, 2, 0)
        mainlayout.addWidget(self.checkbox4, 2, 1)
        mainlayout.addWidget(self.namel1, 0, 2)
        mainlayout.addWidget(self.nameEd1, 0, 3)
        mainlayout.addWidget(self.namel2, 1, 2)
        mainlayout.addWidget(self.nameEd2, 1, 3)
        mainlayout.addWidget(self.btnconnect, 2, 3)
        self.dialog.setLayout(mainlayout)

    def RCsend(self,north,east):
        if(self.checkbox1.isChecked()):
            windows.windows.addmsg(windows.windows(), windows.jsonmake('GU', self.checkbox1.text(), content=[north,east]).encode('utf-8'),self.checkbox1.text())
        if (self.checkbox2.isChecked()):
            windows.windows.addmsg(windows.windows(), windows.jsonmake('GU', self.checkbox2.text(), content=[north,east]).encode('utf-8'), self.checkbox2.text())
        if (self.checkbox3.isChecked()):
            windows.windows.addmsg(windows.windows(), windows.jsonmake('GU', self.checkbox3.text(), content=[north,east]).encode('utf-8'), self.checkbox3.text())
        if (self.checkbox4.isChecked()):
            windows.windows.addmsg(windows.windows(), windows.jsonmake('GU', self.checkbox4.text(), content=[north,east]).encode('utf-8'), self.checkbox4.text())