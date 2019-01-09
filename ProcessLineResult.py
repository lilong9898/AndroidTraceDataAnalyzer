#! /usr/bin/python3.5
# coding=utf-8


# processor.py中的processLine方法，执行完一次后，需要返回的信息
class ProcessLineResult:

    def __init__(self, order, strLine, strElapsedTimeMicroSec):
       self.order = order
       self.strLine = strLine
       self.strElapsedMicroSec = strElapsedTimeMicroSec
