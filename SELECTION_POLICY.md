# Paper selection and verification policy

## Search window

默认优先当前年份向前五年。只有当近期论文依赖一个无法绕开的经典工作时，
才选择更早论文。

## Accepted-paper verification

“顶会论文”身份必须由至少一个权威来源确认：

- CVF Open Access proceedings；
- OpenReview venue decision；
- PMLR proceedings；
- NeurIPS proceedings；
- ACM/IEEE/Springer 官方 proceedings。

arXiv 页面、项目主页和 GitHub README 不能单独证明顶会录用身份。

## Repository verification

优先作者或实验室官方仓库。记录：

- repository URL；
- default branch；
- 精读时的 commit SHA；
- license；
- 最近一次提交时间；
- checkpoint/config 是否公开；
- 复现入口是否存在。

如果只有第三方复现，必须显式标注，不把它写成官方代码。

## Relevance rubric

每篇候选按 0–2 分评估：

| 维度 | 0 | 1 | 2 |
|---|---|---|---|
| 任务相关性 | 弱 | 邻近 | 直接 |
| 方法相关性 | 弱 | 可迁移 | 直接碰撞/核心依赖 |
| 代码可读性 | 无代码 | 部分 | 官方完整 |
| 证据质量 | 弱 | 一般 | 多数据/强基线/统计清楚 |
| 新颖性价值 | 低 | 启发 | 直接改变项目决策 |

优先选择总分至少 7/10 的论文。低于 7 分必须解释为何仍值得阅读。

## Deduplication

在选择前检查 `index/papers.csv`，按 DOI、arXiv ID、标准化标题和仓库 URL
去重。论文升级版和会议版可以再次阅读，但必须说明新增内容。

## Failure handling

如果当天无法获得全文或仓库：

1. 不伪造精读；
2. 记录失败原因；
3. 换选下一篇满足条件的论文；
4. 若所有候选均失败，提交一份“检索与阻塞记录”，但不能冒充论文精读。

