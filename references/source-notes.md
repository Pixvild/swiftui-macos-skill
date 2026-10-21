# 官方来源卡片

这些是作者编写的简短观察，不是 Apple 全文转换稿。除 SW01 外，本轮通过官方页面的搜索索引取得相关片段；未逐页对照完整正文、图片或代码工程。日期为 2026-10-21 的阅读日期，不是 Apple 的更新日期。

## SW01 · SwiftUI framework
官方来源：<https://developer.apple.com/documentation/swiftui>
阅读层级：entry_only。相关章节：未取得可用正文。
入口；当前网页只返回 JavaScript 提示，不能当作全文已读。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW02 · Navigation
官方来源：<https://developer.apple.com/documentation/swiftui/navigation>
阅读层级：official_search_index_excerpt。相关章节：Presenting views in columns。
两栏或三栏导航具有前列选择影响后列内容的语义。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW03 · inspectorColumnWidth(min:ideal:max:)
官方来源：<https://developer.apple.com/documentation/swiftui/view/inspectorcolumnwidth(min:ideal:max:)>
阅读层级：official_search_index_excerpt。相关章节：Parameters / Discussion。
检查器宽度偏好、应用位置与平台差异需一起考虑。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW04 · Window
官方来源：<https://developer.apple.com/documentation/swiftui/window>
阅读层级：official_search_index_excerpt。相关章节：Overview / Dismiss a window programmatically。
唯一窗口与窗口组的角色及关闭行为不同。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW05 · WindowGroup.init(_:id:for:content:)
官方来源：<https://developer.apple.com/documentation/swiftui/windowgroup/init(_:id:for:content:)-3hbmw>
阅读层级：official_search_index_excerpt。相关章节：Declaration / Parameters / Discussion。
该重载按数据类型与值呈现窗口，并有明确泛型约束。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW06 · Settings.init(content:)
官方来源：<https://developer.apple.com/documentation/swiftui/settings/init(content:)>
阅读层级：official_search_index_excerpt。相关章节：Discussion。
提供查看和修改应用设置的场景内容。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW07 · Managing model data in your app
官方来源：<https://developer.apple.com/documentation/swiftui/managing-model-data-in-your-app>
阅读层级：official_search_index_excerpt。相关章节：Overview / Note / Make model data observable / Create the source of truth。
官方 Note 将 SwiftUI 的 Observation 支持起点列为 macOS 14；不要推广成所有相关成员的版本。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW08 · Model data
官方来源：<https://developer.apple.com/documentation/swiftui/model-data>
阅读层级：official_search_index_excerpt。相关章节：Overview / Topics。
区分本地状态、共享绑定和可观察模型的数据连接职责。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW09 · FocusState
官方来源：<https://developer.apple.com/documentation/swiftui/focusstate>
阅读层级：official_search_index_excerpt。相关章节：Overview / Avoid ambiguous focus bindings。
焦点状态绑定需避免多个控件复用同一匹配值的歧义。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW10 · FocusedValue
官方来源：<https://developer.apple.com/documentation/swiftui/focusedvalue>
阅读层级：official_search_index_excerpt。相关章节：Overview。
从当前焦点视图或其祖先观察上下文值。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW11 · Building and customizing the menu bar with SwiftUI
官方来源：<https://developer.apple.com/documentation/swiftui/building-and-customizing-the-menu-bar-with-swiftui>
阅读层级：official_search_index_excerpt。相关章节：Update menus and menu items dynamically。
菜单可依赖当前场景与焦点上下文；示例中的新宏仍需版本核验。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW12 · DocumentGroup
官方来源：<https://developer.apple.com/documentation/swiftui/documentgroup>
阅读层级：official_search_index_excerpt。相关章节：Topics / Creating a document group。
集合页包含不同文档初始化器；本轮检索显示部分 Beta 和弃用标记，必须逐个核对。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW13 · DocumentGroup.init(newDocument:editor:)
官方来源：<https://developer.apple.com/documentation/swiftui/documentgroup/init(newdocument:editor:)>
阅读层级：official_search_index_excerpt。相关章节：Declaration / Discussion。
具体页讨论文件文档编辑；与集合页的弃用标记呈现存在差异，不能仅凭索引定案。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW14 · Building a document-based app with SwiftUI
官方来源：<https://developer.apple.com/documentation/swiftui/building-a-document-based-app-with-swiftui>
阅读层级：official_search_index_excerpt。相关章节：Overview / Configure the sample code project。
Writing App 是研究文档创建、修改和阅读的官方样本，而非产品架构定案。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW15 · TextEditor.init(text:)
官方来源：<https://developer.apple.com/documentation/swiftui/texteditor/init(text:)>
阅读层级：official_search_index_excerpt。相关章节：Declaration / Discussion。
这个 String 绑定初始化器提供纯文本编辑；其限制不能代表所有新重载。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW16 · Building rich SwiftUI text experiences
官方来源：<https://developer.apple.com/documentation/swiftui/building-rich-swiftui-text-experiences>
阅读层级：official_search_index_excerpt。相关章节：Overview。
官方提供基于 attributed strings 的富文本样例，需另查实际版本和 SDK。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW17 · NSViewRepresentable
官方来源：<https://developer.apple.com/documentation/swiftui/nsviewrepresentable>
阅读层级：official_search_index_excerpt。相关章节：Overview / Warning / Topics。
将 AppKit 视图放入 SwiftUI，包含创建、更新、清理与布局控制边界。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW18 · NSHostingView
官方来源：<https://developer.apple.com/documentation/swiftui/nshostingview>
阅读层级：official_search_index_excerpt。相关章节：Overview。
把 SwiftUI 视图层级嵌入 AppKit，桥接方向与 NSViewRepresentable 相反。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW19 · NSViewRepresentable.makeCoordinator()
官方来源：<https://developer.apple.com/documentation/swiftui/nsviewrepresentable/makecoordinator()>
阅读层级：official_search_index_excerpt。相关章节：Discussion。
需要协调原生回调与 SwiftUI 状态时可提供 Coordinator。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。

## SW20 · focusedSceneValue(_:_:)
官方来源：<https://developer.apple.com/documentation/swiftui/view/focusedscenevalue(_:_:)>
阅读层级：official_search_index_excerpt。相关章节：Discussion。
场景范围发布的上下文与局部焦点范围不同。
边界：全文未下载；完整可用性、弃用版本和 SDK 编译尚未核验。
