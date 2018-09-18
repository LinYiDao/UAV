#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject, pyqtSignal,pyqtSlot
import json

class connectObject(QObject):
    sigMapMsg = pyqtSignal(str)
    sigEleMsg = pyqtSignal(str)

    def __init__(self,parent = None):
        super().__init__(parent)

    def sendMap(self,msg):
        #jsonmsg = json.dumps(msg)
        self.sigMapMsg.emit(msg)
      #  print("esss")
