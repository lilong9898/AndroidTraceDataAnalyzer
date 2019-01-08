#! /usr/bin/python3.5
# coding=utf-8

# 必须输入一个参数，即原始trace文件的路径
import subprocess
from subprocess import Popen, PIPE, STDOUT
import sys
import re
import MethodExecution
import os
from Stack import *
from MethodExecution import *
from xml.dom.minidom import Document

# 进程号-进程名的列表
threadMap = {};

# 方法进入/退出信息被放进这个stack里进行配对
stack = Stack()

# 解析trace文件完毕后，调用信息会输出到xml里
doc = Document()

# 输出的xml文件的路径
XML_OUTPUT_ABS_PATH = os.path.realpath(os.path.abspath(os.path.dirname(sys.argv[0])) + os.path.sep + "output.xml");

# 解析trace文件
def processTrace(strTraceFileAbsPath):
    commandDmTraceDump = ["dmtracedump", "-o", strTraceFileAbsPath]
    pOpenInstance = subprocess.Popen(commandDmTraceDump, stdout=PIPE, bufsize=1)
    order = 0;
    for line in iter(pOpenInstance.stdout.readline, b''):
        line = line.decode().strip()
        line = re.sub(r" \.+", " ", line)
        line = re.sub(r"\s+", " ", line)
        processLine(order, line)
        print(str(order) + ", " + line)
        order = order + 1
    pOpenInstance.stdout.close()
    print(str(stack.size()))
    with open(XML_OUTPUT_ABS_PATH, 'w') as f:
        f.write(doc.toprettyxml(indent='\t', encoding='utf-8').decode())
    pass;


# 处理dmtracedump得到的trace文本文件中的一行
def processLine(order, strLine):
    # 如果该行是线程号-线程名的对应，则存入表中
    isThreadMap = re.match(r"^[0-9]+ ([a-zA-Z0-9-_:/.]+[ :-_])*[a-zA-Z0-9-_:/.]+$", strLine)
    splitResult = strLine.split(" ", 1)
    if isThreadMap:
        threadNumber = splitResult[0]
        threadName = splitResult[1]
        threadMap[threadNumber] = threadName
    # 如果该行是方法进入/退出的信息
    isMethodExecution = re.match(r"^[0-9]+ (ent|xit).*$", strLine)
    if isMethodExecution:
        splitResult = strLine.split(" ", 5)
        strMethodThreadNumber = splitResult[0]
        strExecutionBoundaryAction = MethodExecution.ENTER
        if splitResult[1] == "ent":
            strExecutionBoundaryAction = MethodExecution.ENTER
        elif splitResult[1] == "xit":
            strExecutionBoundaryAction = MethodExecution.EXIT
        strElapsedTimeMicroSec = splitResult[2]
        strMethodSignature = splitResult[3] + " " + splitResult[4]
        strMethodClass = splitResult[5]
        # 根据解析出的信息创建MethodExecution对象
        methodExecution = MethodExecution(order, threadMap[strMethodThreadNumber],
                                          strMethodSignature, strMethodClass,
                                          strExecutionBoundaryAction, strElapsedTimeMicroSec)
        # 只考虑主线程的方法
        if methodExecution.strMethodThreadName != "main":
            return

        # 栈是空的，直接入栈，并写入xml
        if stack.is_empty():
            # if methodExecution.methodBoundaryAction == MethodExecution.ENTER:
            stack.push(methodExecution)
            node = doc.createElement(str(methodExecution.order))
            # 这时xml也是空的，加入首个node
            doc.appendChild(node)
        # 栈非空，取出最上面的元素，跟目前这个进行配对检测
        else:
            methodExecutionInStack = stack.peek()
            isMatch = matchMethodExecution(methodExecutionInStack, methodExecution)
            # 如果能配对，则互相登记对方的order
            # 然后出栈
            if isMatch:
                methodExecutionInStack.counterPartOrder = methodExecution.order
                methodExecution.counterPartOrder = methodExecutionInStack.order
                stack.pop()
            # 如果无法配对，则入栈，并写入xml
            else:
                # 写入xml
                node = doc.createElement(str(methodExecution.order))
                # stack中上一个methodExecution所对应的xml node一定是当前这个要插入的xml node的parent
                # 找出并作为parent node加入当前的node
                lastNodeInStack = stack.peek()
                parentNode = doc.getElementsByTagName(str(lastNodeInStack.order))[0]
                parentNode.appendChild(node)
                # 入栈
                stack.push(methodExecution)
pass;

# 检测两个MethodExecution是否信息一样，但是动作相反（一个是进入，一个是退出）
def matchMethodExecution(methodExecution1:MethodExecution, methodExecution2:MethodExecution):
    return methodExecution1.strMethodThreadName == methodExecution2.strMethodThreadName and methodExecution1.strMethodClass == methodExecution2.strMethodClass and methodExecution1.strMethodSignature == methodExecution2.strMethodSignature and methodExecution1.methodBoundaryAction != methodExecution2.methodBoundaryAction


# if len(sys.argv) == 2:
# processTrace(sys.argv[1]);
processTrace("/home/lilong/bin/dmtrace.trace")
