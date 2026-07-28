# 高 Star 论文仓库设计对照

[返回首页](../README.md) · [全部论文](../index/papers.md) ·
[主题路线](../index/topics.md)

查询日期：**2026-07-29**。Star 数来自 GitHub 仓库页面/API，只表示社区关注度，
会随时间变化；它不是内容质量或学术可靠性的证明。

## 对照结果

| 仓库 | 查询时 Star | 最值得借鉴的结构 | 本仓库如何采用 |
|---|---:|---|---|
| [papers-we-love/papers-we-love](https://github.com/papers-we-love/papers-we-love) | 108,196 | 首页先说明用途与版权边界，再把大量内容分到主题目录 | 首页保留短价值主张；详细证据进入 `notes/`、`taste/` 与 `index/` |
| [labmlai/annotated_deep_learning_paper_implementations](https://github.com/labmlai/annotated_deep_learning_paper_implementations) | 67,233 | 解释与实现并列；按技术主题直达关键模块 | 每张设计卡把机制、接口、固定源码和失败边界放在同一页面 |
| [floodsung/Deep-Learning-Papers-Reading-Roadmap](https://github.com/floodsung/Deep-Learning-Papers-Reading-Roadmap) | 39,552 | 不只列论文，还明确由浅入深的阅读顺序 | 保留 13 类系统路线，并新增“瓶颈 → 接口 → 证据 → 反证”的设计卡路线 |
| [mli/paper-reading](https://github.com/mli/paper-reading) | 33,628 | 首屏优先展示已完成内容，日期和主题都能定位 | 首页首屏直接给今日精读与今日 Taste，不先讲维护细节 |
| [dair-ai/AI-Papers-of-the-Week](https://github.com/dair-ai/AI-Papers-of-the-Week) | 12,682 | 当前内容优先，旧内容按年份归档 | `notes/YYYY/` 与 `taste/YYYY/` 双归档，首页只保留最新入口 |
| [dair-ai/ML-Papers-Explained](https://github.com/dair-ai/ML-Papers-Explained) | 8,579 | 技术分类清楚，读者可以按问题而非日期进入 | 论文用主方向和交叉标签；设计卡用机制家族和迁移目标 |
| [Thinklab-SJTU/Awesome-LLM4AD](https://github.com/Thinklab-SJTU/Awesome-LLM4AD) | 1,877 | 领域 taxonomy 和资源入口贴合自动驾驶读者 | 大模型保留为交叉轴，不挤掉检测、深度、雷达、定位和协同感知 |
| [Vincentqyw/cv-arxiv-daily](https://github.com/Vincentqyw/cv-arxiv-daily) | 1,489 | 配置作为单一真源，由脚本生成读者页面 | `papers.csv` 与 `taste.csv` 分别驱动两类索引并由 CI 检查陈旧页面 |

## 最终采用的设计原则

1. **首页回答四个问题**：今天精读什么、今天学哪个设计、从哪里开始、如何继续浏览。
2. **完成内容优先**：最新笔记放在方法说明和贡献指南之前。
3. **时间与主题双入口**：既可按日期追踪习惯，也可按研究问题系统学习。
4. **渐进披露**：摘要完整译文和术语解释先出现，3 分钟结论随后可见，源码
   审计和证据账本放在深读层。
5. **论文与代码相邻**：每个关键判断都能回到 proceedings 或固定 commit。
6. **每类资产只有一个机器真源**：`papers.csv` 驱动精读，`taste.csv` 驱动设计卡；二者不混成一个含义含糊的大表。
7. **自动化必须可校验**：生成脚本支持 `--check`，防止新增笔记后首页过期。
8. **公开性优先**：一般文献缺口可以公开，未投稿贡献的完整配方不进入日志。
9. **形成可分享的最小单元**：一张 Taste 卡只讲一个设计，标题、原理图、适用场景和最大边界在移动端连续可见。
10. **给社区一个安全入口**：公开 Issue 可以推荐已发表论文与模块，但明确禁止披露未投稿想法和私有结果。

## 这轮据此完成的改动

- 把首页首屏从长篇格式说明压缩为“今日精读 + 今日算法 Taste”双入口；
- 新增 `taste/` 年份归档、`index/taste.csv` 机器索引和可复制模板；
- 为首张设计卡加入原论文原理图、整体架构图、固定源码、受控消融、适用与不适用场景；
- 让生成脚本和测试阻止重复日期、缺图、图源不邻接、缺固定 SHA 与陈旧首页；
- 增加公开内容推荐入口，并继续把选文质量、证据边界和移动端阅读放在 Star 数之前。

## 明确没有照搬的做法

- 不在 README 中持续堆叠数百篇论文，避免首页越来越难打开；
- 不用 Star 图标代替证据质量评分；
- 不依赖外部网站才能看到笔记正文；
- 不用大图、封面或动态播放量占据首屏；
- 不把“收录”写成“深度阅读”，也不把“有代码链接”写成“已经复现”。
