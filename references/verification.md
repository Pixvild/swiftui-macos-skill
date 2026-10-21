# 环境与实现验证

性质：作者工作流程。不要把下面列出的检查写成已经完成。

## 环境基线

从实际工程读取 workspace/project、scheme、target、各配置部署目标、Swift 语言模式、SDK 和并发设置。保留设置来自哪个文件或哪次命令输出。不要把操作系统版本当部署目标，也不要从单个 debug target 推广到整个项目。

可先在技能目录运行：

```bash
python3 scripts/probe_environment.py
```

这个工具只读取宿主和工具链信息，不改设置，不解析 target，不运行构建。非 macOS 上即使存在 Swift 编译器，也不能据此验证 SwiftUI/AppKit。

## 构建前

确认实际的 workspace/project 和 scheme 后再选择 xcodebuild 参数，不编造名称。先检查项目既有测试命令、签名与依赖规则。列举或读取工程设置可能涉及依赖解析；遵守用户网络许可，不添加自动升级或包更新参数。

示意命令如下，尖括号项必须替换为实际发现的值，不能原样执行：

```text
xcodebuild -list -json -project <实际工程.xcodeproj>
xcodebuild -showBuildSettings -project <实际工程.xcodeproj> -scheme <实际scheme>
xcodebuild -project <实际工程.xcodeproj> -scheme <实际scheme> -configuration Debug -destination 'platform=macOS' build
```

使用 workspace 的工程对应改用 -workspace。不要为了通过构建擅自关签名、提高部署目标、禁用并发检查或移除测试。执行完整回归范围；未执行项写明原因。

## API 证据记录

每个关键 API 记录：规范 URL、完整重载、平台和版本、Beta/弃用、泛型与 actor 约束、核验日期和证据来源。SDK 的声明与网站有差异时保存两边证据，不混成一个“最新版”。宏能展开、类型能编译与功能可在目标系统运行是不同检查。

## 运行矩阵

基础：启动、窗口缩放、关闭和重开、全屏、设置、多窗口。

编辑：中文输入、选区、撤销重做、复制粘贴、大纲跳转、焦点恢复、快捷键作用对象。

数据：新建、打开、保存、另存、恢复、权限错误、外部修改、重复打开。

可达性：键盘遍历、VoiceOver、对比和减少动态效果；截图不能代替真实交互验证。

## 必需的结果字段

记录“做了什么、在哪个环境、执行命令、退出码、观察结果、日志位置、哪些没做”。日志可能包含本地路径或配置；分享前检查隐私，不收集密钥和账户信息。

写 `未运行：当前不是 macOS/Xcode 环境`，而不是 `已通过静态检查，因此编译应该通过`。计划的测试不算已执行测试。
