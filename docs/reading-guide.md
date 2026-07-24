# 阅读与维护说明

[返回首页](../README.md) · [全部精读](../index/papers.md) ·
[选文规则](../SELECTION_POLICY.md)

## 一篇笔记怎样读

所有精读使用同一条连续路线：

1. **看原图**：先建立方法的空间结构和信息流；
2. **读原式**：逐符号理解论文真正定义了什么；
3. **看结果**：判断数字是否支持作者主张；
4. **对源码**：核对公式在固定 commit 中怎样实现；
5. **记结论**：留下贡献、证据边界和开放问题。

首页只提供一个“开始今天的精读”主入口。历史论文分别进入
[全部精读](../index/papers.md)和[主题路线](../index/topics.md)。

## 图表规则

- 第 1 部分至少保留一张真正决定理解的原文方法图，第 3 部分至少保留一张
  支撑主张的原文结果表；
- 只截取必要图表，不保存或重新发布整篇 PDF；
- 图片存放在 `assets/notes/<note-key>/`，不能依赖会失效的外链热链；
- 每张图都写明原文 Figure/Table 编号、PDF 页码、官方原文链接与权利归属；
- 每张图后第一个非空内容必须是其“原图出处”块，关键图表不放进折叠区；
- 图片必须有可读的替代文本，并在提交前按 GitHub 页面宽度人工检查；
- 原图只用于必要的学术评论与讲解，版权归原作者及其他权利人。

如果某篇论文的许可或图像复用条件不清晰，优先制作自己的解释图并链接原图，
不要把整页论文或大量图表复制进仓库。

## 公式规则

GitHub 官方文档说明，Markdown 数学公式由 Web 界面的 JavaScript MathJax
组件呈现。GitHub 原生移动 App 不保证执行同一套网页组件；实际设备上可能把
`math` fence 或 inline TeX 当成普通代码。为保证浏览器、GitHub iPad/iPhone
App、深色模式和读屏场景得到同一内容，精读正文不依赖 live MathJax。

[GitHub 官方数学表达式说明](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions)

本仓库采用三层交付：

1. **公式 PNG**：正文直接显示，不透明白底、近黑文字、固定 2048 px 宽；
2. **纯文字读法**：图片失败或使用读屏时仍能理解公式语义；
3. **TeX 源**：放在该笔记 `formulas/source.tex`，供复制和逐项核对。

正文结构固定为：

````text
**原文公式：** 论文 Eq. (7)，PDF p. 4。

![公式图：Eq. 7，类别状态递推更新](../../assets/notes/<note-key>/formulas/eq-07-class-update.png)

> **公式来源：** 作者、编号、PDF 页、官方 PDF、按原符号重排说明、
> [可复制 TeX](../../assets/notes/<note-key>/formulas/source.tex)。

**纯文字读法：** 下一类别状态 = 当前状态与历史状态融合后归一化。
````

维护时必须遵守：

- `notes/` 和 `templates/` 中不使用 inline dollar math、fenced `math`、
  TeX 括号分隔符或双 dollar block；
- 简单行内符号写成普通 code span，例如 `M_t`、`delta`、`p + f`；
- 每张公式图使用准确、非 LaTeX 堆砌的中文 alt text；
- 公式图后的第一个非空内容必须是连续的“公式来源”引用块；
- PNG 必须是 2048 px 宽、192–1536 px 高、不透明白底；长公式主动换行，
  不能靠缩小字体塞进一行；
- 原文公式标明 Eq. 编号、PDF 页码和源码映射；
- 原文没有编号时明确标“原文未编号公式”并给 PDF 页码，不自行补编号；
- 论文自定义宏先展开，再进入独立 TeX 源；
- 笔记自己的推导或量级估算明确标成“[判断] 非原文公式”；
- 如果论文没有不可替代的关键公式，明确说明，不为满足模板而编造；
- 关键原式保持在正文可见区域，不放进 `<details>`；
- 公式 PNG、TeX 命名块和正文引用必须一一对应，不能留下孤儿资产；
- 类比之后必须回到正式符号、论文定义和证据边界。

发布前运行：

```bash
python scripts/render_formula_assets.py --check
python scripts/rebuild_index.py
python scripts/rebuild_index.py --check
python scripts/lint_markdown_math.py
python -m unittest discover -s tests -v
```

分支推送后，公开页面 smoke test 还会在 iPad 尺寸下检查：公式图全部加载、
页面不存在 `math-renderer`、图片具备至少 2× 像素密度、正文没有横向溢出。

## 证据边界

- **[论文]**：论文、补充材料或权威 proceedings 可以直接支持；
- **[源码]**：固定 commit 的官方代码可以直接支持；
- **[判断]**：基于前两类证据的解释、批评或推断；
- **[未核验]**：尚未运行、复现或向作者确认。

“源码已读”不等于“结果已复现”，“时间更稳定”也不自动等于“预测更正确”。
