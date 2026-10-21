# apple-design-skill 采集实现核查

实际核查版本：dickwu/apple-design-skill，提交 `914b6a377c22755597e4405e54911b996de822d7`。

实际阅读：README.md、AGENTS.md、references/hig-lookup.md 的目录及表格、scripts/pull-hig.mjs 全部 786 行。没有逐篇读完生成的 123 篇 HIG。

## 实际流程

1. 六个固定 HIG 栏目作为入口：getting-started、foundations、patterns、components、inputs、technologies。
2. listedPages 从 topicSections.identifiers 经 references 找到 slug；crawlSection 再展开一层 collectionGroup，而非无限递归所有链接。
3. 直接获取 Apple 页面渲染 JSON：`https://developer.apple.com/tutorials/data/design/human-interface-guidelines/<slug>.json`。Node 18+，无额外依赖；正文页默认 6 并发。
4. 读取 supported-platforms，仅保留涉及 iOS/iPadOS/macOS 的范围；另按作者维护的 OMITTED_PAGES 排除 Apple 专属硬件/服务，并输出排除原因。
5. 自行将 JSON 转成每页 Markdown。普通图片、视频以及特定平台章节被丢弃，平台标题会改写；表格合并单元格会重复原始文字，勾叉图保留符号。它并非逐字节或视觉完整的网页镜像。
6. 生成本地页间链接，并映射 Apple 与 GitHub 的标题锚点。不存在或被筛掉的锚点降级到页面，不伪造有效章节链接。
7. 自动生成 hig-lookup.md：按栏目分组，记录标题、文件、官方摘要、Apple 更新时间；作者手写 Liquid Glass 指南由 CURATED_FILES 单独保护。
8. 默认清理不再发现的生成页。识别特定生成头部，保护手写文件；删除超过 max(3, floor(旧文件数*10%)) 时拒绝，除非 --force-prune。拒绝清理不等于整个更新事务回滚。

## 缓存与验证边界

传 --cache 时，fetchPageJson 能读到本地 JSON 就直接返回，不访问远端，也没有 ETag/Last-Modified 新鲜度核验。默认不传 cache 才直接刷新网络。没有请求超时、重试、持久队列或断点恢复实现。

维护检查依赖语法检查、重复运行后 git 差异、doc:// 残留检索和技能发现。未见专门转换器测试套件。重复运行不变主要证明同一输入和同日输出的确定性，不证明官网未变化；生成索引还包含运行日期。

## 对 SwiftUI 项目的采用

采用：官方结构化正文为依据、逐页 Markdown、自动主题索引、来源及排除记录、作者资料分离和生成文件保护。

不照搬：HIG 的单层 slug/两层目录、跨平台作者排除表、删除其他平台原文的策略、无远端核验的缓存。SwiftUI 需要完整多级路径、具体重载标识、声明、版本与语言变体元数据；当前全量任务采用 SwiftUI 引用图闭包并明确范围。

最关键的交付区别：原项目已有可直接阅读的生成正文；仅提供来源 URL 或采集脚本不能等价替代这一部分。本项目的正文快照、检索目录和真实覆盖报告应一起可取得，同时不把下载状态标为已读或已编译。
