#! /usr/bin/python3.5
# coding=utf-8

# 某个方法的一次调用
class MethodExecution:

    # 该方法开始执行
    ENTER = "ENTER";
    # 该方法执行完毕
    EXIT = "EXIT";
    # 未定的序号
    ORDER_UNKNOWN = -1

    def __init__(self, order, strMethodThreadName, strMethodSignature, strMethodClass, methodBoundaryAction, strElapsedTimeMicroSec):

        # 序号，自增
        self.order = order;

        # 与之匹配的另一个事件（如果这个是ENTER，则匹配的是EXIT，如果这个是EXIT，则匹配的是ENTER）的序号
        self.counterPartOrder = self.ORDER_UNKNOWN;

        # 方法所在的线程名
        self.strMethodThreadName = strMethodThreadName

        # 方法签名
        self.strMethodSignature = strMethodSignature

        # 方法所在的类名
        self.strMethodClass = strMethodClass

        # 方法此时处于开始执行还是执行完毕的时候
        self.methodBoundaryAction = methodBoundaryAction

        # 此时相对startMethodTracing开始时过去的时间（微秒）
        self.elapsedTimeMicroSec = int(strElapsedTimeMicroSec)

        # 此次方法执行所用的总时间（包括其内部调用的其它方法的耗时）（微秒）
        self.executionTimeMicroSec = 0
        pass

    pass
