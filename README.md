# swiftui-macos-skill

开发预览版：面向 macOS 原生 SwiftUI 的实现、排错、审查与版本核验技能。Skill 名称为 `swiftui-macos`。不是 SwiftUI 全量离线文档库。

## 安装

将本仓库克隆至工程的技能目录，例如在工程根目录执行：

```bash
git clone https://github.com/Pixvild/swiftui-macos-skill.git --branch codex/swiftui-macos-skill .agents/skills/swiftui-macos
```

也可克隆至 `~/.agents/skills/swiftui-macos` 跨项目使用。已存在同名目录时先比较内容，不覆盖；不将技能加入 Xcode 资源 target。不要把本仓库 AGENTS.md 覆盖到应用工程根目录。实际发现和触发仍需在使用者的 Codex 环境确认。

首次使用可发送：

```text
请使用 swiftui-macos 检查当前 macOS 工程。本次不修改应用代码。
读取实际工程配置、技能覆盖报告和相关官方资料；
区分官方事实、作者建议和待验证内容，不预设大纲必须采用 Inspector。
报告真实 Xcode、SDK、部署目标和未执行的检查。
```

## 资料结构

- [技能入口](SKILL.md)：工程检查、查证、实现与验证流程。
- [主题索引](references/swiftui-lookup.md)：六篇作者编写的中文指南及 20 条种子来源。
- [覆盖边界](references/coverage.md)：已发现、已获取、已阅读和已编译分别统计。
- [同步说明](references/sync-workflow.md)：在线刷新、离线重建和有界导航发现。
- [验证记录](reports/verification.md)：实际命令、结果和剩余缺口。

`apple-design` 负责 HIG 与设计评审；本技能负责工程、API 与验证。外部技能缺失时不自动安装，不把 iOS 规则直接套到 macOS。

## 工具

需要 Python 3.9+，只用标准库。在仓库根目录运行：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_skill.py
python3 scripts/probe_environment.py
python3 scripts/discover_docs.py --limit 10
python3 scripts/sync_docs.py --id SW03 --id SW04 --id SW05 --id SW07 --id SW17
python3 scripts/search_catalog.py Window
python3 scripts/search_catalog.py --catalog references/local/discovery/catalog.json --platform macOS
```

网络采集只在显式运行命令时发生。在线同步优先获取 DocC JSON，失败后尝试 Markdown；缓存通过条件请求重新核验。离线模式不联网，也不证明远端新鲜度。发现只沿 SwiftUI topicSections 导航，逐页保存队列，可恢复、重试失败项；外框架只登记。`--limit` 限制本轮处理页面数，不代表全量覆盖。

原始响应和转换正文留在 `.cache/` 与 `references/local/`，已从 Git 排除。本仓库仅维护技能、作者指南、来源和验证摘要。下载不代表已读，转换成功不代表全文或视觉保真，也不代表示例已编译。

## 已验证与待办

本轮 55 项自动化测试通过，5 个种子页面在线同步成功；导航实际处理 10 页，发现 264 条目，254 待处理。详细时间与摘要见 reports/。仍需完善 DocC 变体支持、验证更多真实结构、在 macOS/Xcode 构建并验证交互。尚未进行系统性的有/无技能代理 A/B 评测；不发布正式 Release。

## 全量采集与完成后合并

`collect-full.yml` 在开发分支更新采集代码时启动。采集从 SwiftUI 根页遍历内部 DocC 文档引用闭包，跨框架另行登记；并发限速，保存队列与原始 JSON。恢复时从原始响应重建遗漏队列，隔离损坏 HTTP 缓存。

```bash
python3 scripts/collect_docs.py --retry-failed
python3 scripts/export_collection.py --require-complete
python3 scripts/search_catalog.py --catalog references/local/full/export/catalog.json --platform macOS
```

逐页正文、原始数据和自动索引保存在工作流的 `swiftui-official-complete-*` 采集存档。存档默认保留 90 天；它不是永久镜像。下载后解压至 `references/local/full`，阅读 `export/lookup.md`，按需打开 `export/official/*.md`。完成后生成的 `references/full-coverage.md` 会给出真实计数和下载入口，`references/full-catalog.json` 与 `references/full-sources.json` 保存完整检索清单。

只有队列及失败均为零、原始引用图闭包与文件散列通过核对、生成结果提交后在 Python 3.9/3.13 上通过远端测试，流程才会将 PR #1 标为可合并并按用户授权合并。任何采集或验证失败都会阻止合并，不把未链接页面、语言变体解释、媒体核对或 macOS 编译算作完成。

[参考仓库采集核查](docs/collection-reference-review.md) 记录了实际阅读的源码、采用的做法与没有照搬的边界。
