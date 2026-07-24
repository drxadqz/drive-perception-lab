# YYYY-MM-DD — Paper title

> [!TIP]
> **先读结论：** 用一句话说明论文做了什么、最强证据是什么、最大边界是什么。

`Venue YYYY` · `Accepted / Preprint` ·
`论文已读 / 源码已读 / 已运行或未运行`

[▶ 从第一张图开始](#1-看图论文到底做了什么) ·
[返回首页](../../README.md) · [全部精读](../../index/papers.md) ·
[官方论文](https://example.org/paper.pdf) ·
[官方代码 @ 固定 SHA](https://github.com/example/repo/tree/FULL_SHA)

**学习顺序：**
[1 看原图](#1-看图论文到底做了什么) →
[2 读原式](#2-读公式核心机制怎样表达) →
[3 看结果](#3-看结果证据是否支持主张) →
[4 对源码](#4-对源码公式如何落地) →
[5 记结论](#5-记结论贡献边界与开放问题)

证据标签：**[论文]** 作者材料直接支持；**[源码]** 固定 commit 直接支持；
**[判断]** 本笔记分析；**[未核验]** 尚未独立运行或确认。

## 1. 看图：论文到底做了什么

![能够独立说明图片内容的替代文本](../../assets/notes/NOTE_KEY/fig-method.png)

> **原图出处：** Author et al., Venue YYYY, Figure X, PDF p. Y。
> [官方 PDF](https://example.org/paper.pdf)。仅作学术讲解所需的局部摘录，
> 原图版权归原作者及其他权利人。

### 这张图按什么顺序看

1. 先看输入、坐标系或状态；
2. 再看论文真正新增的模块；
3. 最后看输出、训练目标或状态写回。

**看完应能复述：** 用一句话把信息流讲清楚。

**这张图没有证明：** 写清方法图不能替代哪些实验事实。

## 2. 读公式：核心机制怎样表达

### 原文公式 1：公式名称

**原文公式：** 论文 Eq. (X)，PDF p. Y。

<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="../../assets/notes/NOTE_KEY/formulas/eq-x-short-name-dark.png"><img src="../../assets/notes/NOTE_KEY/formulas/eq-x-short-name-light.png" alt="公式：论文 Eq. X，用自然语言说明这条公式做什么" width="480" height="84"></picture></p>

> **公式来源：** Author et al., Venue YYYY, Eq. (X)，PDF p. Y；
> 本图按原符号重排。[官方 PDF](https://example.org/paper.pdf) ·
> [可复制 TeX](../../assets/notes/NOTE_KEY/formulas/source.tex)。

**符号说明**

- *x*：标量；
- *M*<sub>*t*</sub>：时刻 *t* 的记忆状态；
- *ψ*：论文定义的映射。

**纯文字读法：** 用普通文本完整朗读公式，确保图片加载失败时仍能理解。

**玩具例子：** 用一个明确标为“教学示例、不是论文实验”的小数字走一遍。

**专业解释：** 说明这条式子定义的运算、假设和信息流。

**回到上面的图：** 指出对应箭头或模块。

**落到源码：** [文件 / symbol @ 固定 SHA](https://github.com/example/repo/blob/FULL_SHA/path#L1-L20)

**公式省略了什么：** 写出实现中的 shape、mask、坐标、状态或数值细节。

> 如果论文没有不可替代的公式，删除上面的占位式并明确写：
> **原文无必要公式：** 这篇论文的核心贡献由算法流程或系统设计表达，
> 本笔记不为满足模板而编造公式。
>
> 如果关键原式没有编号，写成：
> **原文未编号公式：** 论文 PDF p. Y。不要为了通过检查伪造 Eq. 编号。
>
> “原文公式 / 原文未编号公式”与“原文无必要公式”只能选择一种模式。
>
> 块级公式由同一 TeX 命名块生成内容紧裁、像素尺寸一致的 2× light/dark
> PNG pair，并用单行 `<p><picture>…</picture></p>` 按自然尺寸居中；
> `<img>` 的 `width` / `height` 写显示尺寸，不把短公式铺满正文。普通行内数学
> 使用 Unicode、Markdown 斜体/粗斜体和 `<sub>` / `<sup>`；反引号只保留给
> `real_source_symbol` 这类真实源码标识。正文不使用 live MathJax。复杂源码
> 等价式或本笔记推导也使用公式图，但必须分别标成
> **[源码] 非论文原式** 或 **[判断] 非论文原式**。

## 3. 看结果：证据是否支持主张

![能够独立说明表格内容的替代文本](../../assets/notes/NOTE_KEY/table-main.png)

> **原图出处：** Author et al., Venue YYYY, Table X, PDF p. Y。
> [官方 PDF](https://example.org/paper.pdf)。仅作学术讲解所需的局部摘录，
> 原图版权归原作者及其他权利人。

### 三个必须看的对照

1. **最强 baseline：**
2. **关键消融：**
3. **效率、稳健性或泛化：**

### 证据支持

- **[论文]**

### 证据没有支持

- **[判断]**
- **[未核验]**

## 4. 对源码：公式如何落地

```text
input
→ encoder
→ state read
→ key module
→ state write
→ prediction
```

### 1. 状态读取：`symbol`

- **论文对应：**
- **源码行为：**
- **需要留意：**
- [打开固定 SHA 源码](https://github.com/example/repo/blob/FULL_SHA/path#L1-L20)

### 2. 核心计算：`symbol`

- **论文对应：**
- **源码行为：**
- **需要留意：**
- [打开固定 SHA 源码](https://github.com/example/repo/blob/FULL_SHA/path#L1-L20)

### 3. 状态写回或输出：`symbol`

- **论文对应：**
- **源码行为：**
- **需要留意：**
- [打开固定 SHA 源码](https://github.com/example/repo/blob/FULL_SHA/path#L1-L20)

<details>
<summary><strong>展开完整源码审计、环境和复现风险</strong></summary>

- 状态张量与辅助状态：
- in-place 更新：
- 训练与测试差异：
- 环境与依赖：
- checkpoint / config：
- 最短复现命令：

</details>

## 5. 记结论：贡献、边界与开放问题

### 学完必须记住的三点

1. **[论文] 方法核心：**
2. **[论文/源码] 最强证据：**
3. **[判断] 最大缺口：**

### 仍未解决的问题

- **已观察事实：**
- **为什么仍是问题：**
- **能区分解释的最小测试：**
- **相邻工作：**

<details>
<summary><strong>身份、许可与证据账本</strong></summary>

- Venue 与权威录用来源：
- Paper / supplement：
- 官方仓库与固定 commit：
- License：
- Checkpoint：
- 已读源码：
- 尚未运行或核验：

</details>

> [!NOTE]
> 发布前必须运行索引、公式资产和公开页面检查；逐张核对图号、页码、出处、
> 替代文本、PNG/TeX 一致性及 iPad 竖屏/横屏清晰度；原文公式与本笔记推导
> 不得混写，正文必须保持零 live MathJax。
