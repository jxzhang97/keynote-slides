# Keynote 制作说明

这份文件记录已知事实和待验证的路线。标了“未验证”的内容都没有跑过，不要当成结论告诉用户。跑通或跑不通之后，把结果写回这里。

## 先保护用户开着的文档

2026-10-31 在 Keynote 14.5 上用 `osascript` 驱动时：

- `documents`、`windows` 报 -1728 或 -1708，读不到任何文档。
- `open` 能打开文件。
- 随后的 `export` 报 -609，Keynote 因未捕获异常崩溃。当时用户开着别的文档。
- 崩溃后 Keynote 自动重开，恢复了所有窗口，包括我打开的临时副本。

原因未查明，重启 Keynote 后也没有复测。所以：

1. 先用 `pgrep -x Keynote` 看它是否在运行。这个命令不发 Apple 事件。
2. 如果在运行，先请用户保存并关闭重要文档。用户同意之前不要发 AppleScript 或 JXA 事件。
3. 只在新文件或副本上试，不要动用户的原文件。打开过临时副本要告诉用户，崩溃恢复可能把它带回窗口列表。

## 脚本字典能做什么

以下来自 `/Applications/Keynote.app/Contents/Resources/Keynote.sdef`（14.5）。这里只读过字典，没有实际运行。

| 需求 | 字典里有没有 |
|---|---|
| 新建页，加文本框、形状、图片、线、表格 | 有：`make`，以及 `slide`、`text item`、`shape`、`image`、`line`、`table` |
| 跳过某页 | 有：`skipped` |
| 演讲者备注 | 有：`presenter notes` |
| 转场 | 有：`transition properties` |
| 导出 | 有：`export`，但这条命令上次让 Keynote 崩溃 |
| LaTeX 公式 | 没有 |
| 逐步出现的构建动画 | 没有 |

公式和动画正好是用户风格的核心，而脚本做不了，所以它们要走界面操作，或者留给用户手工补。

## 建议路线（未验证）

1. **先跑探针。** 第一次使用时，用户同意后，在新文档上只做三页：一页文本框和形状，一页用 Insert → Equation 插入的 LaTeX 公式，一页一个 Appear 动画。跑通哪条路线就用哪条，并把结果写回这里。
2. **骨架用脚本。** 字典访问正常时，用 AppleScript 或 JXA 建页、放文字、形状和图片。
3. **公式和动画用界面操作。** 通过 computer use 在 Keynote 里插入公式、添加 Appear 动画。公式多的报告这一步会很慢，要提前告诉用户。
4. **脚本仍然失败时**，有两个退路：
   - 全程用 computer use 操作 Keynote。
   - 用 python-pptx 生成 `.pptx`（本机没装，需要先装到临时目录），再用 Keynote 打开并保存为 `.key`。这样得到的公式不是 Keynote 的 LaTeX 公式，动画也要另外处理。

不管走哪条路线，都要在交付时列出没有做完的部分。

## 读旧 deck

只读内容时直接解包，不需要打开 Keynote。`.key` 是 zip：

| 路径 | 内容 |
|---|---|
| `preview.jpg` | 第一页预览 |
| `Data/st-*.jpg` | 每页 356×200 的缩略图，细节不够判断字号和对齐 |
| `Data/` 其余文件 | 图片和公式。Keynote 的公式存成 PDF |
| `Index/*.iwa` | 页面结构、文字、样式、动画 |

大 deck 全部解压可能写满磁盘，只解需要的部分：

```bash
unzip -q deck.key 'Index/*' 'Data/st-*' preview.jpg -d out
```

`scripts/iwa.py` 是不依赖第三方库的 `.iwa` 读取器。直接运行时列出对象类型和数量：

```bash
python3 -I scripts/iwa.py out
```

要读具体内容时，从脚本里调用 `load(root)` 得到 `{id: (type, payload, refs)}`，再用 `pb()` 和 `sub()` 解 protobuf。

下面的字段是解三份 deck 时观察到的，不是官方格式：

| type | 含义 | 字段 |
|---|---|---|
| 2 | Show | f3 指向页面树，f3.2 是按顺序的节点引用，f4 是画布大小 |
| 4 | SlideNode | f2 指向 Slide，f4 是跳过标记（从内容推断），f16 是缩略图 id |
| 5 | Slide | |
| 8 | Build | 动画 |
| 15 | Transition | 转场 |
| 2001 | 文本存储 | f3 文字，f5 段落样式表，f8 字符样式表 |
| 2011 | 带文字的形状 | f1→f1 是几何信息，其中 f1 位置、f2 大小 |
| 2021 | 字符样式 | |
| 2022 | 段落样式 | f1：1 名称、3 父样式；f11：1 粗体、2 斜体、3 字号、5 字体、7 颜色 |
| 2025 | 形状样式 | 路径 1,11 下：1 填充、2 描边、3 不透明度、4 阴影 |
| 3005 | 图片 | |

颜色的 f3、f4、f5 是 r、g、b 浮点数，f6 是 alpha。
