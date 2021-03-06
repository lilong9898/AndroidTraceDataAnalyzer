#! /usr/bin/python3.5
# coding=utf-8

class Stack(object):
    # 初始化栈为空列表
    def __init__(self):
        self.items = []

    # 判断栈是否为空，返回布尔值
    def is_empty(self):
        return self.items == []

    # 返回栈顶元素
    def peek(self):
        return self.items[len(self.items) - 1]

    # 返回栈的大小
    def size(self):
        return len(self.items)

    # 把新的元素堆进栈里面（程序员喜欢把这个过程叫做压栈，入栈，进栈……）
    def push(self, item):
        self.items.append(item)

    # 把栈顶元素丢出去（程序员喜欢把这个过程叫做出栈……）
    def pop(self):
        return self.items.pop()

    # 返回栈中元素
    def getItems(self):
        return self.items

    # 打印栈中元素
    def print(self):
        for item in self.items:
            item.print()

    # 打印栈的大小
    def printSize(self):
        print(str(self.size()))
