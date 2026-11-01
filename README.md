# keynote-slides

一个 [Claude Code](https://claude.com/claude-code) skill：按作者自己的美术风格做学术报告 slides，交付可以继续手改的 Keynote 文件。

## 动机

把个人风格写成规则，容易得到千篇一律的结果：每场报告都长得像上一场。这个 skill 把规则分成三层，越往后越可以动：

| 层 | 含义 | 例子 |
|---|---|---|
| A 基因 | 风格本身，改了就不像作者了 | 颜色有含义，公式要能读，逐步揭示 |
| B 默认值 | 没有理由时照用，有理由就改 | 字号四档，Gill Sans，容器样式 |
| C 每场要变的 | 每场至少主动换一项，并说明换了什么 | 语义分配、封面、页面主导、节奏 |

旧 deck 提供的是词汇，不是模板。

规则提炼自作者的三份报告（共 158 页，实际讲过 71 页）。数字来自 `.key` 内部数据，画面判断来自缩略图。配色固定用紫禁城，色值是从截图目测估的。

## 当前状态

风格规则和工作流程已经定下来，但**从零生成 Keynote 文件的路线还没有跑通过**。在作者的机器上，Keynote 14.5 的 AppleScript 读不到文档，`export` 还让 Keynote 崩溃过一次；脚本字典里也没有 LaTeX 公式和构建动画。详见 [references/keynote-production.md](references/keynote-production.md)。

## 仓库结构

```
keynote-slides/
├── SKILL.md                        # 工作流程 + 三层规则 + 配色
├── references/
│   └── keynote-production.md       # 崩溃教训、脚本能力、待验证路线、读旧 deck
├── scripts/
│   └── iwa.py                      # 纯 Python 的 .iwa 读取器
└── README.md
```

## 安装

前提：已安装 [Claude Code](https://claude.com/claude-code)。

```bash
git clone https://github.com/jxzhang97/keynote-slides.git ~/Documents/AI/keynote-slides
```

```bash
ln -s ~/Documents/AI/keynote-slides ~/.claude/skills/keynote-slides
```

装好后**新开一个 Claude Code 会话**即生效。

## 使用

```
/keynote-slides 25 分钟的 anyon 超导报告，听众是凝聚态同行，素材在 notes/
```

或者直接说：“帮我做一份组会 slides，讲……”。

Claude 会先确认时长、听众和听众要记住的一句话，再交一份页面方案，你同意后才开始做。
