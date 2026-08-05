# 高 Star 论文仓库设计对照

[返回首页](../README.md) · [全部论文](../index/papers.md) ·
[主题路线](../index/topics.md)

查询日期：**2026-08-05**。Star 数来自 GitHub 仓库页面/API，只表示社区关注度，
会随时间变化；它不是内容质量或学术可靠性的证明。

## 对照结果

| 仓库 | 查询时 Star | 最值得借鉴的结构 | 本仓库如何采用 |
|---|---:|---|---|
| [papers-we-love/papers-we-love](https://github.com/papers-we-love/papers-we-love) | 108,476 | 首页先说明用途与版权边界，再把大量内容分到主题目录 | 首页保留短价值主张；详细证据进入 `notes/`、`taste/` 与 `index/` |
| [labmlai/annotated_deep_learning_paper_implementations](https://github.com/labmlai/annotated_deep_learning_paper_implementations) | 67,270 | 解释与实现并列；按技术主题直达关键模块 | 每张设计卡把机制、接口、固定源码和失败边界放在同一页面 |
| [floodsung/Deep-Learning-Papers-Reading-Roadmap](https://github.com/floodsung/Deep-Learning-Papers-Reading-Roadmap) | 39,552 | 不只列论文，还明确由浅入深的阅读顺序 | 保留 13 类系统路线，并新增“瓶颈 → 接口 → 证据 → 反证”的设计卡路线 |
| [mli/paper-reading](https://github.com/mli/paper-reading) | 33,654 | 首屏优先展示已完成内容，日期和主题都能定位 | 首页首屏直接给今日精读与今日 Taste，不先讲维护细节 |
| [dair-ai/AI-Papers-of-the-Week](https://github.com/dair-ai/AI-Papers-of-the-Week) | 12,708 | 当前内容优先，旧内容按年份归档 | `notes/YYYY/` 与 `taste/YYYY/` 双归档，首页只保留最新入口 |
| [dair-ai/ML-Papers-Explained](https://github.com/dair-ai/ML-Papers-Explained) | 8,579 | 技术分类清楚，读者可以按问题而非日期进入 | 论文用主方向和交叉标签；设计卡用机制家族和迁移目标 |
| [OpenDriveLab/End-to-end-Autonomous-Driving](https://github.com/OpenDriveLab/End-to-end-Autonomous-Driving) | 3,664 | 论文集合旁边保留 roadmap、挑战、benchmark、教程与未来趋势 | 用 13 类路线保持全域视角，但只把有感知贡献的工作计入核心覆盖 |
| [Thinklab-SJTU/Awesome-LLM4AD](https://github.com/Thinklab-SJTU/Awesome-LLM4AD) | 1,882 | 领域 taxonomy 和资源入口贴合自动驾驶读者 | 大模型保留为交叉轴，不挤掉检测、深度、雷达、定位和协同感知 |
| [Vincentqyw/cv-arxiv-daily](https://github.com/Vincentqyw/cv-arxiv-daily) | 1,490 | 配置作为单一真源，由脚本生成读者页面 | `papers.csv` 与 `taste.csv` 分别驱动两类索引并由 CI 检查陈旧页面 |
| [worldbench/awesome-vla-for-ad](https://github.com/worldbench/awesome-vla-for-ad) | 456 | 新内容快速聚合，细分 VLA / 世界模型交叉方向 | 作为候选发现源，不让热点轴替代传统感知覆盖与正式录用核验 |
| [PeterJaq/Awesome-Autonomous-Driving](https://github.com/PeterJaq/Awesome-Autonomous-Driving) | 355 | 从传感器、标定、感知到预测和部署的工程 taxonomy 较宽 | 用于检查漏搜方向；最终精读仍回到原论文、补充材料和官方仓库 |

## 最终采用的设计原则

1. **首页回答四个问题**：今天精读什么、今天学哪个设计、从哪里开始、如何继续浏览。
2. **完成内容优先**：最新笔记放在方法说明和贡献指南之前。
3. **时间与主题双入口**：既可按日期追踪习惯，也可按研究问题系统学习。
4. **渐进披露**：先公开“为什么今天值得读”与摘要完整译文，30 分钟层读机制
   与结果，研究层再进入源码、复现账本和相邻工作核查。
5. **论文与代码相邻**：每个关键判断都能回到 proceedings 或固定 commit。
6. **每类资产只有一个机器真源**：`papers.csv` 驱动精读，`taste.csv` 驱动设计卡；二者不混成一个含义含糊的大表。
7. **自动化必须可校验**：生成脚本支持 `--check`，防止新增笔记后首页过期。
8. **公开性优先**：一般文献缺口可以公开，未投稿贡献的完整配方不进入日志。
9. **形成可分享的最小单元**：一张 Taste 卡只讲一个设计，标题、原理图、适用场景和最大边界在移动端连续可见。
10. **给社区一个安全入口**：公开 Issue 可以推荐已发表论文与模块，但明确禁止披露未投稿想法和私有结果。
11. **新近性优先但不短视**：最近 24 个月与当前/前两个会议年份先进入候选池；
    对仍定义今天研究问题的经典工作保留可解释的例外。
12. **团队是脉络，不是捷径**：跟踪 MIT 等顶尖学术与工业团队的连续工作，
    但 affiliation、Star、引用和帖子热度都不能替代受控证据。
13. **研究空白必须可审计**：先检索机制词、问题词和同义词，读最接近工作，
    只允许输出带日期与范围的覆盖判断。
14. **先补上下文再讲模块**：借鉴解析型站点的叙事，把具体问题、任务定义和
    前置论文路线放到第一张方法图之前，但所有事实仍回到官方材料。
15. **先给实验地图再给超参数**：Section 3 先汇总数据集、实验分组、
    train/val/test 路线、指标问题、最强证据与边界，再进入逐项配置。

## 解析型网站的可读性对照

- [Distill](https://distill.pub/about/)主张机器学习研究解释应当清晰、动态、
  适合 Web；本仓库采用它“先建立可操作直觉，再回到形式化定义”的顺序，但
  GitHub/iPad/iPhone 交付仍使用静态图、纵向正文和可审计来源。
- [labml annotated implementations](https://github.com/labmlai/annotated_deep_learning_paper_implementations)
  把论文解释与真实实现放在一起；本仓库对应为每个机制紧邻固定 SHA 源码、
  梯度路径、配置差异和未运行声明。
- [Papers with Code](https://cs.paperswithcode.com/about)把论文、代码、数据集、
  方法和评测表连接起来；本仓库进一步要求 Section 3 明说每个数据集承担哪组
  实验、指标回答什么问题，而不是只挂入口。

这些网站与解析帖子是结构参考和发现入口，不是事实裁判。录用身份、方法定义、
数字、数据划分和源码行为仍由官方 proceedings、原论文/补充材料、benchmark
与固定 commit 支撑。

## 阅读方法对照

S. Keshav 的 [How to Read a Paper](https://www.mit.edu/~fadel/courses/MAS.S66/papers/howtoread.pdf)
提出三遍阅读：第一遍判断类别、上下文、正确性、贡献与清晰度；第二遍重点核对
图表、结果与证据；第三遍通过“虚拟复现”挑战假设、寻找失败条件和遗漏引用。
它与本仓库的新三层入口一一对应：5 分钟先判断为什么值得读，30 分钟理解图、
公式和证据，研究级再对固定源码与相邻工作。Keshav 对文献检索还建议从近期高
引用论文的共同引文、作者主页和顶会 proceedings 扩展，这里进一步加上三路
检索式、最接近工作四轴比较和受限结论措辞。

## 这轮据此完成的改动

- 首页新增 5 分钟、30 分钟和研究级三种读法，不删减深度内容；
- 选文队列明确优先最近 24 个月和当前/前两个会议年份的正式顶会论文；
- 评分加入影响/社区信号和作者/团队研究脉络，但明确它们不能替代证据；
- 新笔记公开同轮候选对照，让读者知道为什么今天是这篇；
- 新笔记在首图前建立问题背景、任务定义和至少两篇官方前置论文路线；
- Section 3 先给数据集与实验设计总览，再展开配置、流程和结果；
- 开放问题新增相邻工作核查状态，未审计旧问题不再被误读成新颖性声明；
- 校验器从 2026-08-06 起阻止缺选择理由、缺三路检索、最接近工作无官方链接、
  检索受阻或把有限检索写成“学界无人做过”的笔记合并。

## 明确没有照搬的做法

- 不在 README 中持续堆叠数百篇论文，避免首页越来越难打开；
- 不用 Star 图标代替证据质量评分；
- 不依赖外部网站才能看到笔记正文；
- 不用大图、封面或动态播放量占据首屏；
- 不把“收录”写成“深度阅读”，也不把“有代码链接”写成“已经复现”。
