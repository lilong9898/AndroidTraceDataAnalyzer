# AndroidTraceDataAnalyzer
### 由来：
- 优化应用的启动速度，需要先找到瓶颈点
- 通过加入计时代码来检测，费时费力，而且无法复用到不同代码上
- 通过method trace来检测，无需改动代码
- Android IDE自带的TraceView或CPU Profiler可以分析trace log，但无法定制分析过程，大量非重点信息掩盖了重点信息
- 本工具通过python脚本分析trace log的原始数据，可以自定义分析过程，包括：
    - 只关注特定的线程
    - 只关注特定包名的方法
    - 将统计结果以XML方式输出，输出信息包括了调用链和每个方法的耗时
    - 更多分类，过滤和排序功能（全定制分析过程）
    
### 准备环境：
- 安装python3.5（项目按照python3.5规范编码)
- 下载该项目并安装各个依赖库: progressbar

### 准备输入文件：
- 准备好trace文件，名字应该是****.trace 

[生成trace文件的方法](https://developer.android.com/studio/profile/generate-trace-logs)
