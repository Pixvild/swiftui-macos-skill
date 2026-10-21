# 开发预览验证记录

本轮使用 Linux / Python 3.12。原包的 1.0.0 不作为正式版本；本报告只覆盖实际执行的检查。

## 结果

- `python3 -m unittest discover -s tests -v`：55 项通过，退出码 0。日志见 test-results.txt。
- `python3 scripts/validate_skill.py`：检查文件、元数据、索引和本地链接。实际输出见 package-validation.txt。
- `python3 scripts/discover_docs.py --limit 2`，随后 `--limit 8`：10 页成功，0 失败，264 条目被发现，254 待处理，均退出 0。统计见 discovery-online.json。
- `python3 scripts/sync_docs.py --id SW03 --id SW05 --id SW04 --id SW07 --id SW17 --timeout 10 --retries 0`：5 页成功，均为 DocC JSON 转换。原始状态、散列与警告摘要见 live-sync-summary.json。
- 修改后的同步逻辑以 `--mode offline` 对同样 5 个真实缓存复测，5 页成功，退出码 0；不更新远端核验时间，不冒充再次在线获取。
- 对 5 个真实缓存逐项比较结构化声明和平台元数据，保留一致；生成正文包含所有提取声明。见 real-payload-check.json。这不是全文保真验证。
- 目录检索 CLI 对种子与发现摘要实际运行；结果是候选资料，不能保证具体部署版本可用。

新增回归测试先实际失败，再修复通过，覆盖：发现失败退出码、JSON 优先、来源 ID 改绑、写元数据失败时保留旧快照、异常文档标识、坏结构继续处理、macOS 不可用标记、重试发现数量去重及目录检索。旧日志不再作为本轮验收依据。

## 技能行为检查

独立代理实际使用技能回答“部署 macOS 13、全部迁移 @Observable、固定用 Inspector”场景：拒绝无依据确认兼容，指出 Observation 的版本限制，并把 Inspector 的具体重载可用性列为待查；未假称编译或读取未打开的 Apple 原文。该结果只是一个定性检查，没有执行有/无技能的系统 A/B 基准。

独立代码审查发现的来源身份、成组快照写入、文档标识、平台标记、重试统计和坏结构问题，已补充能复现问题的回归测试并修正。

## 未验证及限制

未运行 macOS/Xcode 构建、输入法、焦点、撤销、多窗口、无障碍交互。未全量获取 SwiftUI，未逐页核对全文、图片或语言变体；实际页面仍报告 variants/variantOverrides 及保真度警告。下载不登记为已读，样例不登记为已编译。

CI 配置验证 Python 3.9/3.13，但本轮本机只运行 Python 3.12；远端 Actions 是否运行通过必须另查，不能用本地结果代替。仓库只有开发预览代码、作者指南、来源与元数据摘要，不上传 Apple 正文缓存。

## 全量流程扩展验证

已按参考仓库补充逐页正文导出及自动索引，并加入完整引用图采集、限速并发、原始快照恢复和 HTTP 缓存隔离。独立审查后增加原始引用图闭包检查，防止仅清空队列就误判完成。新增内容在 Linux/Python 3.12 上实际运行，当前 55 项测试通过，工作流 YAML 和 shell 语法通过。

新增工作流将在真实采集完成、原始散列和闭包核对成功、生成提交通过远端 Python 3.9/3.13 验证后才合并。此处只记录流程已经实现，不能提前将正在进行的全量采集或其未来 CI 结果记为成功。最终采集数量以工作流生成的 reports/full-coverage.json 为准。
