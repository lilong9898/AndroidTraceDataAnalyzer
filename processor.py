#! /usr/bin/python3.5
# coding=utf-8

# 必须输入一个参数，即原始trace文件的路径
import subprocess
from subprocess import *
import sys
import re
import os
import progressbar
from progressbar import *
import shutil
from xml.dom.minidom import Document
from Stack import *
from MethodExecution import *
from ProcessLineResult import *
import webbrowser

# 工程中的html css js文件的路径
HTML_ABS_PATH = os.path.realpath(
    os.path.abspath(os.path.dirname(sys.argv[0])) + os.path.sep + "XMLDisplay.html");
CSS_ABS_PATH = os.path.realpath(
    os.path.abspath(os.path.dirname(sys.argv[0])) + os.path.sep + "XMLDisplay.css");
JS_ABS_PATH = os.path.realpath(
    os.path.abspath(os.path.dirname(sys.argv[0])) + os.path.sep + "XMLDisplay.js");

# XML node 属性名字：方法名
XML_NODE_ATTR_METHOD_SIGNATURE = "method"

# XML node 属性名字：此次执行总时间（微秒，包括内部调用的其它方法）
XML_NODE_ATTR_METHOD_TIME = "time"

# XML node 属性名字：此次执行的耗时，在所有方法中排第几
XML_NODE_ATTR_METHOD_TIME_PRIORITY = "priority"

# XML node 属性名字：所有子方法的执行总时间（微秒，因为只统计掌阅包名的方法，所以一个方法的总时间是大于其所有子方法的总时间的）
XML_NODE_ATTR_CHILD_METHOD_TIME = "time_children"

# XML node 属性名字：深度
XML_NODE_ATTR_DEPTH = "depth"

# XML node 属性名字：当前方法时间占总时间的百分比
XML_NODE_ATTR_PERCENTAGE = "time_percentage"

# 只标注前多少名的priority
LEAST_PRIORITY_CONCERNED = 20;

# 进程号-进程名的列表
threadMap = {};

# 方法进入/退出信息被放进这个stack里进行配对
stack = Stack()

# 用来存放所有方法开始执行时的MethodExecution的容器，为了排序
methodEnters = []

# 解析trace文件完毕后，调用信息会输出到xml里
doc = Document()
# 给这个xml设置一个根节点，只为了补齐逻辑，不代表任何函数调用
# XML 根节点名字
XML_ROOT_NODE_NAME = "root"
rootNode = doc.createElement(XML_ROOT_NODE_NAME)
rootNode.setAttribute(XML_NODE_ATTR_DEPTH, "0")
doc.appendChild(rootNode)

# android framework中的包名, 这些包名需要被过滤掉
AndroidFrameworkPackageNames = ["android\.", "java\."];


def getAndroidFrameworkPackageNamesRE():
    strAndroidFrameworkPackageNamesRE = "("
    for i in range(0, len(AndroidFrameworkPackageNames)):
        if i == 0:
            strAndroidFrameworkPackageNamesRE = strAndroidFrameworkPackageNamesRE + \
                                                AndroidFrameworkPackageNames[i]
        else:
            strAndroidFrameworkPackageNamesRE = strAndroidFrameworkPackageNamesRE + "|" + \
                                                AndroidFrameworkPackageNames[i]
    return strAndroidFrameworkPackageNamesRE + ")";


# 用于正则表达式的android framework包名
AndroidFrameworkRE = getAndroidFrameworkPackageNamesRE()


# 解析trace文件
# 最终输出xml html css js这四个文件到trace同级目录下，然后用浏览器打开html作为最终显示的结果
def processTrace(strTraceFilePath):

    strTraceFileAbsPath = os.path.abspath(strTraceFilePath)

    # 输入的trace文件的目录
    strTraceFileDirPath = os.path.split(strTraceFileAbsPath)[0]

    # 输入的trace文件的名字(不含.trace后缀)
    strTraceFileName = os.path.splitext(os.path.split(strTraceFileAbsPath)[1])[0];

    # 输出的过滤后的方法执行信息的文本文件路径
    strMethodExecutionInfoOutputAbsPath = os.path.join(strTraceFileDirPath,
                                                       strTraceFileName + ".txt")

    # 输出的xml文件的路径
    strXMLOutputAbsPath = os.path.join(strTraceFileDirPath, strTraceFileName + ".xml")

    # 输出的html/css/js文件的路径
    strHTMLOutputAbsPath = os.path.join(strTraceFileDirPath, strTraceFileName + ".html")
    strCSSOutputAbsPath = os.path.join(strTraceFileDirPath, strTraceFileName + ".css")
    strJSOutputAbsPath = os.path.join(strTraceFileDirPath, strTraceFileName + ".js")

    # 删除之前的所有输出文件
    if os.path.exists(strMethodExecutionInfoOutputAbsPath):
        os.remove(strMethodExecutionInfoOutputAbsPath)
    if os.path.exists(strXMLOutputAbsPath):
        os.remove(strXMLOutputAbsPath)
    if os.path.exists(strHTMLOutputAbsPath):
        os.remove(strHTMLOutputAbsPath)
    if os.path.exists(strCSSOutputAbsPath):
        os.remove(strCSSOutputAbsPath)
    if os.path.exists(strJSOutputAbsPath):
        os.remove(strJSOutputAbsPath)

    widgets = [Timer()]

    bar = progressbar.ProgressBar(widgets=widgets);

    commandDmTraceDump = ["dmtracedump", "-o", strTraceFileAbsPath]
    pOpenInstance = subprocess.Popen(commandDmTraceDump, stdout=PIPE, bufsize=1)

    order = 0;
    # 运行总时间，微秒
    totalTimeMicroSec = 0;
    print("Working...")
    for line in bar(iter(pOpenInstance.stdout.readline, b'')):
        line = line.decode().strip()
        line = re.sub(r"\s+", " ", line)
        processLineResult = processLine(order, line)
        if processLineResult and "stopMethodTracing" in processLineResult.strLine:
            # 向xml的rootNode设置stopMethodTracing时的elapsedTime(微秒)，这也就是所trace的整个过程的耗时
            rootNode.setAttribute(XML_NODE_ATTR_METHOD_TIME, processLineResult.strElapsedMicroSec)
            totalTimeMicroSec = int(processLineResult.strElapsedMicroSec)
        order = order + 1
    pOpenInstance.stdout.close()

    # 文件读取和逐行的处理完成，进行整体处理

    # (1)针对方法的耗时，进行排序并选取前几个标注为特殊颜色
    # 同时针对方法的耗时，计算占总时间的百分比，并标注在xml中
    methodEntersSorted = sorted(methodEnters,
                                key=lambda methodExecution: methodExecution.executionTimeMicroSec,
                                reverse=True)

    priority = 0;
    for methodExecutionEnter in methodEntersSorted:
        nodeForMethodExecutionEnter = \
        doc.getElementsByTagName("_tmp_" + str(methodExecutionEnter.order))[0]
        nodeForMethodExecutionEnter.setAttribute(XML_NODE_ATTR_METHOD_TIME,
                                                 str(methodExecutionEnter.executionTimeMicroSec))
        if priority <= LEAST_PRIORITY_CONCERNED and int(
                nodeForMethodExecutionEnter.getAttribute(XML_NODE_ATTR_DEPTH)) < 3:
            nodeForMethodExecutionEnter.setAttribute(XML_NODE_ATTR_METHOD_TIME_PRIORITY,
                                                     str(priority))
            priority = priority + 1
        nodeForMethodExecutionEnter.setAttribute(XML_NODE_ATTR_PERCENTAGE, str(
            round(100.0 * methodExecutionEnter.executionTimeMicroSec / totalTimeMicroSec)) + "%")
        nodeForMethodExecutionEnter.tagName = "_" + str(methodExecutionEnter.executionTimeMicroSec)

    # (2)处理stack中剩余项的信息，剩余项是有ENTER无EXIT的方法执行，正常情况下总数应该<=1个
    # 对于stack中剩余项，应该将其对应的xml node的time标记为unknown
    if stack.size() > 0:
        for methodExecution in stack.getItems():
            stillInStackNode = doc.getElementsByTagName("_tmp_" + str(methodExecution.order))[0]
            stillInStackNode.tagName = "unknown"
            stillInStackNode.setAttribute(XML_NODE_ATTR_METHOD_TIME, "unknown")

    # (3) xml内容写入磁盘
    with open(strXMLOutputAbsPath, 'w') as f:
        # 　写入xml内容
        strXML = doc.toprettyxml(indent='\t', encoding='utf-8').decode()
        # 用浏览器打开xml的时候需注掉下面两行
        # strXML = re.sub(r"&lt;", "<", strXML)
        # strXML = re.sub(r"&gt;", ">", strXML)
        f.write(strXML)

    # (4) 其它辅助文件写入磁盘
    # 直接复制即可
    shutil.copy(HTML_ABS_PATH, strHTMLOutputAbsPath)
    shutil.copy(CSS_ABS_PATH, strCSSOutputAbsPath)
    shutil.copy(JS_ABS_PATH, strJSOutputAbsPath)

    # 然后改掉html里引用的css，js和xml的名字，改掉actualTime
    with open(strHTMLOutputAbsPath, "r") as htmlFile:
        htmlContent = htmlFile.read()
        htmlContent = htmlContent.replace("XMLDisplay", strTraceFileName)
        htmlContent = htmlContent.replace("example_dmtrace", strTraceFileName)
    with open(strHTMLOutputAbsPath, "w") as htmlFile:
        htmlFile.write(htmlContent)

    # 读取xml内容到字符串
    with open(strXMLOutputAbsPath, "r") as xmlFile:
        xmlContent = xmlFile.read()

    # 替换掉js里的getXMLString方法的返回值
    with open(strJSOutputAbsPath, "r") as jsFile:
        jsContent = jsFile.read()
        jsContent = jsContent.replace("XML_STR_PLACE_HOLDER",
                                      xmlContent.replace("\"", "\\\"").replace("\n", "\"+\n\""))
    with open(strJSOutputAbsPath, "w") as jsFile:
        jsFile.write(jsContent)

    print("-------------Done, current stack size is {0}--------------".format(str(stack.size())))
    stack.print()

    # 用浏览器打开html
    webbrowser.open("file:///" + strHTMLOutputAbsPath)
    pass;


# 处理dmtracedump得到的trace文本文件中的一行
def processLine(order, strLine):
    # 如果该行是线程号-线程名的对应，则存入表中
    isThreadMap = re.match(
        r"^[0-9]+ ([a-zA-Z0-9-_:/.\u4e00-\u9fa5]+[ :-_])*[a-zA-Z0-9-_:/.\u4e00-\u9fa5]+$", strLine)
    splitResult = strLine.split(" ", 1)
    if isThreadMap:
        threadNumber = splitResult[0]
        threadName = splitResult[1]
        threadMap[threadNumber] = threadName

    # 如果该行是方法进入/退出的信息
    isMethodExecution = re.match(r"^[0-9]+ (ent|xit).*$", strLine)
    if isMethodExecution:
        strLine = strLine.replace("-", " ")
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

        methodExecution = None
        try:
            # 创建methodExecution，因为有时候dmtrace.trace中的线程表不全，所以这里try catch一下，让找不到线程名的methodExecution被忽略掉
            methodExecution = MethodExecution(order, threadMap[strMethodThreadNumber],
                                              strMethodSignature, strMethodClass,
                                              strExecutionBoundaryAction, strElapsedTimeMicroSec)
        except BaseException:
            return ProcessLineResult(order, strLine, strElapsedTimeMicroSec)

        # 按照多个条件进行过滤
        if shouldBeFiltered(methodExecution):
            return ProcessLineResult(order, strLine, strElapsedTimeMicroSec)

        # 栈是空的，直接入栈，并写入xml
        if stack.is_empty():
            # if methodExecution.methodBoundaryAction == MethodExecution.ENTER:
            stack.push(methodExecution)
            node = doc.createElement("_tmp_" + str(methodExecution.order))
            node.setAttribute(XML_NODE_ATTR_METHOD_SIGNATURE,
                              re.sub(r"^\.+", "", methodExecution.strMethodSignature))
            node.setAttribute(XML_NODE_ATTR_DEPTH, "1")
            # 这时xml也是空的，加入首个node
            rootNode.appendChild(node)
        # 栈非空，取出最上面的元素，跟目前这个进行配对检测
        else:
            methodExecutionInStack = stack.peek()
            isMatch = matchMethodExecution(methodExecutionInStack, methodExecution)
            # 如果能配对，则互相登记对方的order，给即将出栈的MethodExecution登记总耗时（包括其内部调用的其它方法耗时在内）
            # 然后出栈
            if isMatch:
                methodExecutionInStack.counterPartOrder = methodExecution.order
                methodExecution.counterPartOrder = methodExecutionInStack.order
                methodExecutionInStack.executionTimeMicroSec = methodExecution.elapsedTimeMicroSec - methodExecutionInStack.elapsedTimeMicroSec
                # 即将出栈的MethodExecution是方法执行开始时的信息，现在已经执行完了，给他设置上总耗时
                nodeForMethodExecutionInStack = \
                doc.getElementsByTagName("_tmp_" + str(methodExecution.counterPartOrder))[0]
                methodEnters.append(methodExecutionInStack)

                # 计算其上级node中所包含的所有方法的总时间
                if nodeForMethodExecutionInStack.parentNode:
                    if nodeForMethodExecutionInStack.parentNode.getAttribute(
                            XML_NODE_ATTR_CHILD_METHOD_TIME):
                        parentNodeChildMethodTime = int(
                            nodeForMethodExecutionInStack.parentNode.getAttribute(
                                XML_NODE_ATTR_CHILD_METHOD_TIME))
                    else:
                        parentNodeChildMethodTime = 0
                    parentNodeChildMethodTime = parentNodeChildMethodTime + methodExecutionInStack.executionTimeMicroSec
                    nodeForMethodExecutionInStack.parentNode.setAttribute(
                        XML_NODE_ATTR_CHILD_METHOD_TIME, str(parentNodeChildMethodTime))

                stack.pop()
            # 如果无法配对，则入栈，并写入xml
            else:
                # 写入xml
                node = doc.createElement("_tmp_" + str(methodExecution.order))
                # stack中上一个methodExecution所对应的xml node一定是当前这个要插入的xml node的parent
                # 找出并作为parent node加入当前的node
                lastNodeInStack = stack.peek()
                parentNode = doc.getElementsByTagName("_tmp_" + str(lastNodeInStack.order))[0]
                parentNodeDepth = parentNode.getAttribute(XML_NODE_ATTR_DEPTH)
                nodeDepth = int(parentNodeDepth) + 1
                node.setAttribute(XML_NODE_ATTR_DEPTH, str(nodeDepth))
                parentNode.appendChild(node)
                node.setAttribute(XML_NODE_ATTR_METHOD_SIGNATURE,
                                  re.sub(r"^\.+", "", methodExecution.strMethodSignature))
                # 入栈
                stack.push(methodExecution)
        return ProcessLineResult(order, strLine, strElapsedTimeMicroSec)


# 检测两个MethodExecution是否信息一样，但是动作相反（一个是进入，一个是退出）
def matchMethodExecution(methodExecution1: MethodExecution, methodExecution2: MethodExecution):
    return methodExecution1.strMethodThreadName == methodExecution2.strMethodThreadName and methodExecution1.strMethodClass == methodExecution2.strMethodClass and methodExecution1.strMethodSignature == methodExecution2.strMethodSignature and methodExecution1.methodBoundaryAction != methodExecution2.methodBoundaryAction


# 检测某条方法执行信息是否要被过滤掉（按线程/方法包名等过滤）
def shouldBeFiltered(methodExecution: MethodExecution):
    shouldBeFiltered = False
    # 非主线程的过滤掉
    if methodExecution.strMethodThreadName != "main":
        shouldBeFiltered = True
    # framework中的类的包名过滤掉
    elif re.match(r".*" + AndroidFrameworkRE + ".*", methodExecution.strMethodSignature):
        shouldBeFiltered = True
    return shouldBeFiltered


# 入口
# 无参数，用示例的example_dmtrace.txt
if len(sys.argv) == 1:
    print("WARNING : NO ARGUMENTS, EXAMPLE DMTRACE WILL BE USED")
    processTrace(os.path.realpath(
        os.path.abspath(os.path.dirname(sys.argv[0])) + os.path.sep + "example_dmtrace.trace"))
    exit(0)
# 输入一个参数，即trace文件的绝对路径
elif len(sys.argv) == 2:
    processTrace(sys.argv[1]);
    exit(0)
# 输入两个参数，即time.txt和trace文件的绝对路径
elif len(sys.argv) == 3:
    processTrace(sys.argv[1], sys.argv[2])
    exit(0)
# 参数太多，错误
else:
    print("ERROR : TOO MANY ARGUMENTS, SHOULD HAVE 0, 1 OR 2 ARGUMENTS")
    exit(1)
