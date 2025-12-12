---
epoch: 1765243714030
modelKey: "gemini-2.5-flash|google"
topic: "Obsidian Mermaid 图预览"


tags:
  - copilot-conversation
---

**user**: obsidian 有没有mermaid图预览的插件？
[Context: Notes: 2-设计文档/登录功能概设.md]
[Timestamp: 2025/12/09 09:28:34]

**ai**: 
<errorChunk>Model request failed: Error creating model: google/gemini-2.5-flash|openrouterai - API key is not provided for the model: google/gemini-2.5-flash|openrouterai.</errorChunk>
[Timestamp: 2025/12/09 09:28:34]

**user**: obsidian 有没有mermaid图预览的插件？

[Context: Notes: 2-设计文档/登录功能概设.md]
[Timestamp: 2025/12/09 09:30:56]

**ai**: 根据您提供的上下文，[[登录功能概设]] 这篇笔记中包含了 Mermaid 图，但它并没有提及关于 Obsidian Mermaid 图预览插件的信息。

关于 Obsidian 是否有 Mermaid 图预览插件，Obsidian 本身就内置了对 Mermaid 图的支持，您无需安装额外的插件。在编辑模式下，您可以直接编写 Mermaid 语法，然后在预览模式下（或者使用分屏预览）就能看到渲染后的图表。

例如，在您的笔记中输入以下内容：

```mermaid
graph TD
    A[开始] --> B{决策}
    B -->|是| C[操作1]
    B -->|否| D[操作2]
    C --> E[结束]
    D --> E
```

切换到预览模式后，Obsidian 会自动将其渲染成流程图。
[Timestamp: 2025/12/09 09:30:58]