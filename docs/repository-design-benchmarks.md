# 高 Star 论文仓库设计对照

[返回首页](../README.md) · [全部论文](../index/papers.md) ·
[主题路线](../index/topics.md)

查询日期：**2026-07-24**。Star 数来自 GitHub 仓库页面/API，只表示社区关注度，
会随时间变化；它不是内容质量或学术可靠性的证明。

## 对照结果

| 仓库 | 查询时 Star | 最值得借鉴的结构 | 本仓库如何采用 |
|---|---:|---|---|
| [papers-we-love/papers-we-love](https://github.com/papers-we-love/papers-we-love) | 108,076 | 首页先说明用途与版权边界，再把大量内容分到主题目录 | 首页保留用途、证据和公开边界；详细内容进入 `notes/` 与 `index/` |
| [labmlai/annotated_deep_learning_paper_implementations](https://github.com/labmlai/annotated_deep_learning_paper_implementations) | 67,213 | 解释与实现并列；按技术主题直达关键模块 | 每篇固定链接论文概念与源码 symbol/commit，并提供主题入口 |
| [floodsung/Deep-Learning-Papers-Reading-Roadmap](https://github.com/floodsung/Deep-Learning-Papers-Reading-Roadmap) | 39,549 | 不只列论文，还明确“由浅入深、由通用到具体”的阅读顺序 | 增加分层阅读入口和完整感知分类路线 |
| [mli/paper-reading](https://github.com/mli/paper-reading) | 33,597 | 首页最先展示已完成内容；日期、标题、简述和状态在一个表里 | 首页自动展示今日与最近精读，完整清单另放人类可读索引 |
| [terryum/awesome-deep-learning-papers](https://github.com/terryum/awesome-deep-learning-papers) | 26,167 | 用主题和简短价值说明降低选择成本 | 每篇索引同时显示主题、证据状态与一句话结论 |
| [dair-ai/AI-Papers-of-the-Week](https://github.com/dair-ai/AI-Papers-of-the-Week) | 12,670 | 当前年份优先，旧内容按年份归档，首页不承担所有细节 | `notes/YYYY/` 按年归档，首页只显示今日和最近条目 |
| [dair-ai/ML-Papers-Explained](https://github.com/dair-ai/ML-Papers-Explained) | 8,580 | 技术分类清楚，读者可以按问题而非日期进入 | 增加主题路线和自动标签索引 |
| [arXivTimes/arXivTimes](https://github.com/arXivTimes/arXivTimes) | 3,900 | 一句话总结优先，统一模板区分概要、新颖性、方法、结果和评论 | 单篇笔记先给完整摘要译文与术语解释，再用一句话导读展开证据与判断 |
| [LMD0311/Awesome-World-Model](https://github.com/LMD0311/Awesome-World-Model) | 2,165 | 年份、venue、Paper/Code/Project 链接紧邻展示 | 索引同时给出录用状态、官方论文、代码和固定 SHA |
| [Thinklab-SJTU/Awesome-LLM4AD](https://github.com/Thinklab-SJTU/Awesome-LLM4AD) | 1,878 | 领域 taxonomy、目录和数据/资源入口适合自动驾驶读者 | 将大模型作为感知交叉轴，并保留完整的传统感知主分类 |
| [Vincentqyw/cv-arxiv-daily](https://github.com/Vincentqyw/cv-arxiv-daily) | 1,488 | 配置作为单一分类来源，由脚本生成 README/JSON/网页 | CSV 作为唯一真源；脚本生成首页与索引并提供 `--check` |
| [patrick-llgc/Learning-Deep-Learning](https://github.com/patrick-llgc/Learning-Deep-Learning) | 1,269 | 月度记录、专题综述与单篇 `tl;dr / key ideas / details` 并存 | 保留时间与主题双入口，但限制首页只显示最近条目 |

## 最终采用的设计原则

1. **首页回答三个问题**：今天读什么、先看哪一段、全部内容在哪里。
2. **完成内容优先**：最新笔记放在方法说明和贡献指南之前。
3. **时间与主题双入口**：既可按日期追踪习惯，也可按研究问题系统学习。
4. **渐进披露**：摘要完整译文和术语解释先出现，3 分钟结论随后可见，源码
   审计和证据账本放在深读层。
5. **论文与代码相邻**：每个关键判断都能回到 proceedings 或固定 commit。
6. **机器索引只有一个真源**：`index/papers.csv` 驱动首页和 Markdown 索引。
7. **自动化必须可校验**：生成脚本支持 `--check`，防止新增笔记后首页过期。
8. **公开性优先**：一般文献缺口可以公开，未投稿贡献的完整配方不进入日志。

## 明确没有照搬的做法

- 不在 README 中持续堆叠数百篇论文，避免首页越来越难打开；
- 不用 Star 图标代替证据质量评分；
- 不依赖外部网站才能看到笔记正文；
- 不用大图、封面或动态播放量占据首屏；
- 不把“收录”写成“深度阅读”，也不把“有代码链接”写成“已经复现”。
