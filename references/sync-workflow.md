# 本地资料同步

## 依赖与默认行为

Python 3.9 或更新版本，仅标准库。Skill 的文字工作流程不依赖 Python；只有辅助脚本需要它。没有 Python 时仍可正常读取指南和在线查证，不自动安装运行时。

下面命令在解压后的 `swiftui-macos` 目录运行。安装到技能目录后，也可用其完整路径运行脚本。

```bash
python3 scripts/sync_docs.py --help
python3 scripts/sync_docs.py --id SW04 --id SW07
python3 scripts/sync_docs.py --id SW04 --id SW07 --mode offline
```

最后一条命令要求已经有缓存，没有缓存会失败，不会偷偷联网。省略 --id 将处理清单的全部 20 项；这只是“清单全部”，不是“SwiftUI 全部”。

## 输出与新鲜度

`references/local/<URL散列>/<快照代次>/content.md` 保存局部转换快照；同目录 metadata.json 保存来源、声明和平台字段、警告、内容散列及时间。

`.cache/docs/` 保存原始响应和验证信息。`references/local/sync-state.json` 与 sync-report.md 记录每条来源结果，失败返回非零退出码。不会改写作者来源登记，也不会删除旧快照。

在线模式始终向服务端请求；已有 ETag 或 Last-Modified 时发送条件请求。304 代表已重新验证已有内容，不代表重新阅读全文。`--force` 不发送这些验证头，重新请求内容。离线模式只使用散列校验后的缓存，不更新远端核验时间。

网络更新失败时保留之前的内容，但明确标记 failed 和 stale_snapshot_retained。不得继续把这份旧内容说成刚刚同步成功。

## 明确的限制

优先尝试 DocC 渲染 JSON，再尝试官方文档 URL 后加 `.md`；Markdown 回退不提供结构化版本保证。本轮已成功获取代表性 DocC JSON，但这些候选路径仍非保证稳定的 API。工具不会寻找第三方镜像，不会跨到其他域名，不会绕过 401/403。

JSON 转换器保留常见标题、正文、代码、声明、参数、返回、警告、主题链接和元数据；复杂变体、未知节点及表格细节需要查看原始 JSON 和官网。图片/视频只保留引用，未验证视觉内容。

不应把此工具作为不加审阅的大规模镜像发布工具。更新采用串行低频请求、有界重试、8 MiB 单响应上限，并遵守来源站点的访问限制。

## 新增来源

确认官方页面真实存在，再加入 sources.json。ID 必须唯一，URL 必须是 SwiftUI 官方文档路径，不使用标题作为唯一标识。不同重载保留各自 URL 和后缀。

运行 `python3 scripts/validate_skill.py`。扩充索引和指南时同时更新 coverage.md；不要自动把下载状态改成阅读状态。新增 API 不自动继承旧 API 的可用版本。

## 有界导航发现

运行 `python3 scripts/discover_docs.py --limit 10`，从 SwiftUI 根页的 topicSections 递归发现，按规范 URL 去重并保留重载。每页后持久化队列；重复运行继续，失败项用 `--retry-failed` 重试；有失败记录时退出码为 1，避免自动化误报成功；`--mode offline` 仅使用缓存。默认输出位于 references/local/discovery，不随技能分发。

输出 discovery.json（队列与状态）、catalog.json（含声明和平台）、sources.json（可交给 sync_docs.py 的清单）和 coverage.json。用 `sync_docs.py --manifest <sources.json路径>` 获取发现页的 Markdown 快照。

macos_status 的 listed 表示该页列有 macOS（不保证当前工程兼容），unavailable 表示该页明确标记 macOS 不可用，not_listed 表示平台列表不列 macOS，unknown 表示平台元数据缺失；不得因此删除概念文章。外框架只登记，不自动抓取。仅遍历 topicSections，不等同整个框架符号或语言变体全集。分开统计已发现、已获取、失败和待处理；自动工具不登记已读或已编译。

## 检索

`python3 scripts/search_catalog.py Window` 检索种子目录。通过 `--catalog references/local/discovery/catalog.json --platform macOS` 检索发现目录。按关键词匹配记录（包括声明），保留不同 URL 的重载；平台未知条目保留，失败页排除。输出是候选资料，不能据此保证部署兼容。

## 完整引用图采集

`python3 scripts/collect_docs.py --retry-failed` 沿根页 DocC references 遍历 SwiftUI 内部链接，而非只展开主题导航。限速并发，保存可恢复状态、原始 JSON 和转换快照；不跨框架采集。只接受可验证的文档身份；恢复时重建遗漏的链接队列并重新获取损坏的快照。

`python3 scripts/export_collection.py --require-complete` 从原始响应重新核对散列和引用图闭包，再生成可读正文、机器目录和主题路由表。队列被截断不能据此通过完成检查。未知渲染结构和语言变体保持警告，原始数据始终保留。

自动流程见 `.github/workflows/collect-full.yml`：成功时保留完整采集存档、发布完整索引与覆盖报告；对生成提交执行 Python 3.9/3.13 远端测试后才可合并已授权的 PR #1。失败不合并。工作流缓存与存档均有保留期限，不能冒充永久离线资料库。
