# Keynote 制作说明

这份文件记录已知事实和跑通的路线。标了“未验证”的内容都没有跑过，不要当成结论告诉用户。跑通或跑不通之后，把结果写回这里。

## 先保护用户开着的文档

2026-10-31 在 Keynote 14.5 上用 `osascript` 驱动时：

- `documents`、`windows` 报 -1728 或 -1708，读不到任何文档。
- `open` 能打开文件。
- 随后的 `export` 报 -609，Keynote 因未捕获异常崩溃。当时用户开着别的文档。
- 崩溃后 Keynote 自动重开，恢复了所有窗口，包括我打开的临时副本。

原因未查明。2026-11-01 重启 Keynote 后复测，读文档、`save`、`export` 都正常，多次导出也没有崩溃。当时开着的都是这次做的 deck 或副本，用户其他文档开着时是否复现仍不知道。所以：

1. 先用 `pgrep -x Keynote` 看它是否在运行。这个命令不发 Apple 事件。
2. 如果在运行，先请用户保存并关闭重要文档。用户同意之前不要发 AppleScript 或 JXA 事件。
3. 只在新文件或副本上试，不要动用户的原文件。打开过临时副本要告诉用户，崩溃恢复可能把它带回窗口列表。
4. 只按名字关闭自己打开的文档，不用 `close every document`。关闭前先确认 `modified` 是 false。

## 脚本字典能做什么

以下来自 `/Applications/Keynote.app/Contents/Resources/Keynote.sdef`（14.5）。读文档、`save` 和 `export` 实际跑过，其余只读过字典。

| 需求 | 字典里有没有 |
|---|---|
| 新建页，加文本框、形状、图片、线、表格 | 有：`make`，以及 `slide`、`text item`、`shape`、`image`、`line`、`table` |
| 跳过某页 | 有：`skipped` |
| 演讲者备注 | 有：`presenter notes` |
| 转场 | 有：`transition properties` |
| 导出 | 有：`export`。加 `{all stages:true}` 能按动画阶段逐页导出 |
| 形状填充色 | 没有 |
| LaTeX 公式 | 没有 |
| 逐步出现的构建动画 | 没有 |

脚本设不了填充色，也做不了公式和动画，所以骨架和动画走 `.pptx` 导入，公式走界面操作。

## 跑通的路线

2026-11-01 在 Keynote 14.5 上跑通，做出了两版 15 页的 deck。

1. **生成 `.pptx`。** 用 python-pptx，本机没装时先装到临时目录。按 pt 写 1920×1080 的画布。形状、字体、透明度、渐变、自由路径和 Appear 动画导入后都保留。
2. **后台导入。** `open -g -a Keynote deck.pptx`，文档名是 `deck`。
3. **保存和检查。** 用 `save document "deck" in POSIX file "…"` 存成 `.key`。再用 `export … as PDF` 看版面，用 `{all stages:true}` 检查动画：导出页数应该等于页数加动画步数。
4. **最后插公式。** 公式放在占位文本框里，用 Insert → Equation（`alt+cmd+e`）替换占位文字，这样公式跟着动画走。

公式这一步的操作：

- **选中占位文字。** 文本框在组里时要连续双击进入编辑。后台用 `cmd+up` 再 `shift+cmd+down` 选中，前台用 `cmd+a`。
- **窗口在当前桌面时。** 菜单、输入和 Insert 按钮都能在后台完成，不用接管屏幕。
- **用户在全屏应用里时。** Keynote 窗口不在当前桌面，也移不过来，菜单是灰的，`alt+cmd+e` 也没有反应，只能接管屏幕。先说明要做哪一步，因为用户可能没看到授权弹窗。
- **接管屏幕期间。** 其他应用可能抢到前台，这次是 ChatGPT 和 Universal Control，输入会中断。把 Keynote 拉回前台，全选对话框里的内容后重新输入。其他应用会被临时隐藏，结束后要告诉用户。

导入时遇到的坑：

- **单对象的组。** 只含一个对象的组导入后丢失了。单个对象直接放在页面上，动画也直接指向它。
- **字体名。** `STIXGeneral` 读不到，文字退回 Helvetica，Keynote 提示缺字体。正文数学符号用 `Times New Roman`。
- **文档名。** `.pptx` 打开后的文档名是 `deck`，这次打开两份旧 deck 的副本时也没有 `.key` 后缀。操作前先用 `get name of every document` 确认。

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
