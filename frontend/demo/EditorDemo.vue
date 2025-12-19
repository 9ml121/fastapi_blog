<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed, watch } from 'vue'
import { useSelection } from '../composables/useSelection'
import { useMarkdown } from '../composables/useMarkdown'
import { useHistory } from '../composables/useHistory'
import { getNodeAndOffset, getTextContent } from '../utils/selection'
import type { InlineFormatType, ParagraphFormatType, BlockInsertType } from '../composables/editor.types'

// ==============状态管理===============
const editorRef = ref<HTMLDivElement | null>(null)

const editorState = reactive({
  content: '', // 保存的是编辑器 innerHtml
  isDirty: false,
})

// 用于展示的选中状态（包含 hasSelection）
const selectionState = reactive({
  start: 0,
  end: 0,
  selectedText: '',
  isEmpty: true,
  hasSelection: false,
})

// 操作日志
interface Log {
  time: string
  type: 'info' | 'success' | 'warning'
  message: string
}

const logs = ref<Log[]>([])

const selectionAPI = useSelection(editorRef)
const markdownAPI = useMarkdown(selectionAPI)
const historyAPI = useHistory()

// ==============生命周期=====================

onMounted(() => {
  if (editorRef.value) {
    // 初始化 content 状态，以便调试工具显示
    editorState.content = getTextContent(editorRef.value)
    updateSelectionState()
    addLog('编辑器初始化完成', 'success')
    addLog('提示：选中文本查看实时状态变化', 'info')
  }
})

onUnmounted(() => {
  if (selectionAPI) {
    addLog('编辑器已卸载', 'warning')
  }
})

// ===============工具函数====================

function addLog(message: string, type: Log['type'] = 'info') {
  const now = new Date()
  logs.value.unshift({
    time: now.toLocaleTimeString(),
    type,
    message,
  })
  // 限制日志数量
  if (logs.value.length > 50) {
    logs.value.pop()
  }
}

function clearLogs() {
  logs.value = []
  addLog('日志已清空', 'info')
}

function updateSelectionState() {
  if (!selectionAPI) return

  const info = selectionAPI.getSelectionInfo()
  selectionState.start = info.start
  selectionState.end = info.end
  selectionState.selectedText = info.selectedText
  selectionState.isEmpty = info.isEmpty
  selectionState.hasSelection = !info.isEmpty
}

function resetEditor() {
  if (editorRef.value) {
    // ✅ 保留空行结构，避免完全清空导致DOM操作失败
    editorRef.value.innerHTML = '<div><br></div>'
    editorState.content = '\n'
    updateSelectionState()
    addLog('编辑器内容已清空', 'info')
  }
}

// ==================事件处理===================
function handleSelectionChange() {
  updateSelectionState()
  if (selectionState.hasSelection) {
    addLog(
      `选中文本: "${selectionState.selectedText}" (${selectionState.start}-${selectionState.end})`,
      'info',
    )
  }
}

function onInput() {
  if (editorRef.value) {
    editorState.content = getTextContent(editorRef.value)
  }
}


// =================调试工具和监听===================
const debugState = reactive({
  // checkNodeAndOffset 测试参数
  targetOffset: 0,
  checkResult: '',
  // setCursor 测试参数
  cursorPos: 0,
  // selectRange 测试参数
  rangeStart: selectionState.start,
  rangeEnd: selectionState.end,
  // wrapSelection 测试参数
  wrapBefore: '**',
  wrapAfter: '**',
  // replaceRange 测试参数
  replaceStart: selectionState.start,
  replaceEnd: selectionState.end,
  replaceText: '#',
  // insertText 测试参数
  insertContent: '@',
  // getCurrentLine 测试参数
  lineStart: selectionState.start,
  lineEnd: selectionState.end,
  lineText: '',
  // applyInlineFormat 测试参数
  inlineFormat: 'bold' as InlineFormatType,
  // applyParagraphFormat 测试参数
  paragraphFormat: 'heading1' as ParagraphFormatType,
  // insertBlock 测试参数
  blockInsertType: 'divider' as BlockInsertType,
})
// Keep debugState ranges in sync with editor selection
watch(
  () => [selectionState.start, selectionState.end] as [number, number],
  ([newStart, newEnd]) => {
    debugState.targetOffset = newStart
    debugState.cursorPos = newStart
    debugState.rangeStart = newStart
    debugState.replaceStart = newStart
    debugState.rangeEnd = newEnd
    debugState.replaceEnd = newEnd
  },
)

const contentChars = computed(() => {
  const content = editorState.content || ''
  return content.split('').map((char, index) => ({
    index,
    char: char === '\n' ? '↵' : char,
  }))
})

// =================调试工具方法===================

function handleCheckNodeAndOffset() {
  if (!editorRef.value) return
  const result = getNodeAndOffset(debugState.targetOffset, editorRef.value)
  if (result) {
    debugState.checkResult = `
      nodeName: ${result.node.nodeName}，
      nodeText: ${result.node.textContent}，
      nodeOffset: ${result.offset}，
      `
    addLog(
      `检查 Offset ${debugState.targetOffset} -> NodeText: ${result.node.textContent}, DOM Offset: ${result.offset}`,
      'info',
    )
  } else {
    debugState.checkResult = '未找到对应的 DOM 节点'
    addLog(`检查 Offset ${debugState.targetOffset} -> 未找到`, 'warning')
  }
}

function handleSetCursor() {
  if (!selectionAPI) return
  selectionAPI.setCursor(debugState.cursorPos)
  updateSelectionState()
  addLog(`执行 setCursor(${debugState.cursorPos})`, 'success')
}

function handleSelectRange() {
  if (!selectionAPI) return
  selectionAPI.selectRange(debugState.rangeStart, debugState.rangeEnd)
  updateSelectionState()
  addLog(`执行 selectRange(${debugState.rangeStart}, ${debugState.rangeEnd})`, 'success')
}

function handleWrap() {
  if (!selectionAPI) return
  selectionAPI.wrapSelection(debugState.wrapBefore, debugState.wrapAfter)
  updateSelectionState()
  addLog(`执行 wrapSelection("${debugState.wrapBefore}", "${debugState.wrapAfter}")`, 'success')
}

function handleReplaceRange() {
  if (!selectionAPI) return

  // 💡 如果用户没有手动设置，使用当前选区
  const selection = selectionAPI.getSelectionInfo()
  const start = debugState.replaceStart || selection.start
  const end = debugState.replaceEnd || selection.end

  selectionAPI.replaceRange(start, end, debugState.replaceText, {
    moveCursorToEnd: true,
  })

  updateSelectionState()
  addLog(
    `执行 replaceRange(${debugState.replaceStart},${debugState.replaceEnd},"${debugState.replaceText}")`,
    'success',
  )
}

function handleInsertText() {
  selectionAPI.insertText(debugState.insertContent)
  updateSelectionState()
  addLog(`执行 insertText("${debugState.insertContent}")`, 'success')
}

function handleGetCurrentLine() {
  const { lineStart, lineEnd, lineText } = selectionAPI.getCurrentLineInfo()
  debugState.lineStart = lineStart
  debugState.lineEnd = lineEnd
  debugState.lineText = lineText
  addLog(`执行 getCurrentLine() -> "${lineText}"(${lineStart}-${lineEnd})`, 'info')
}

function handleApplyInlineFormat() {
  if (!selectionAPI) return
  markdownAPI.toggleInlineFormat(debugState.inlineFormat)
  updateSelectionState()
  addLog(`执行 toggleInlineFormat("${debugState.inlineFormat}")`, 'success')
}

function handleApplyParagraphFormat() {
  if (!selectionAPI) return
  markdownAPI.toggleParagraphFormat(debugState.paragraphFormat)
  updateSelectionState()
  addLog(`执行 toggleParagraphFormat("${debugState.paragraphFormat}")`, 'success')
}

function handleInsertBlock() {
  if (!selectionAPI) return
  markdownAPI.insertBlock(debugState.blockInsertType)
  updateSelectionState()
  addLog(`执行 insertBlock("${debugState.blockInsertType}")`, 'success')
}
</script>

<template>
  <div class="page-container">
    <div class="content-wrapper">
      <!-- 标题 -->
      <div class="header-section">
        <h1>useSelection Demo</h1>
        <p>实时查看 useSelection 的工作效果</p>
      </div>

      <!-- 主内容区域 -->
      <div class="main-grid">
        <!-- 左侧：编辑器 -->
        <div class="column">
          <!-- 编辑器容器 -->
          <div class="card">
            <h2 class="card-title">编辑器</h2>
            <div
              ref="editorRef"
              contenteditable="true"
              class="editor-input"
              @mouseup="handleSelectionChange"
              @keyup="handleSelectionChange"
              @input="onInput"
            >
              <div># 一级标题</div>
              <div><br /></div>
              <div>这是一个 **粗体** 和 *斜体* 的示例。</div>
              <div>- 列表项 1</div>
              <div>- 列表项 2</div>
            </div>
          </div>
        </div>

        <!-- 右侧：状态显示 -->
        <div class="column">
          <!-- 调试工具 -->
          <div class="card">
            <h2 class="card-title">调试工具 (Debug Tools)</h2>

            <!-- 坐标可视化 -->
            <div class="debug-section">
              <div class="info-label">Content Coordinates:</div>
              <div class="char-grid">
                <div
                  v-for="item in contentChars"
                  :key="item.index"
                  :class="[
                    'char-item',
                    {
                      active: item.index >= selectionState.start && item.index < selectionState.end,
                      cursor: item.index === selectionState.end,
                    },
                  ]"
                >
                  <span class="char-val">{{ item.char }}</span>
                  <span class="char-idx">{{ item.index }}</span>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="debug-section">
              <div class="button-group">
                <button @click="resetEditor" class="btn btn-green btn-sm">清空编辑区</button>
                <button @click="clearLogs" class="btn btn-red btn-sm">清空日志</button>
                <button @click="handleGetCurrentLine" class="btn btn-gray btn-sm">
                  getCurrentLine
                </button>
              </div>
            </div>

            <!-- 动态 API 测试 -->
            <div class="debug-section">
              <div class="info-label">Dynamic API Tests:</div>

              <!-- getNodeAndOffset 测试-->
              <div class="input-group">
                <label for="offset">请输入查找的绝对字符索引：</label>
                <input
                  id="offset"
                  type="number"
                  v-model.number="debugState.targetOffset"
                  class="debug-input"
                />
                <button @click="handleCheckNodeAndOffset" class="btn btn-gray btn-sm">
                  GetNodeAndOffset
                </button>
              </div>
              <div class="debug-result" v-if="debugState.checkResult">
                【Current NodeAndOffset】{{ debugState.checkResult }}
              </div>

              <!-- setCursor -->
              <div class="input-group">
                <label for="pos">请输入设置的光标位置：</label>
                <input
                  id="pos"
                  type="number"
                  v-model.number="debugState.cursorPos"
                  class="debug-input"
                  placeholder="Pos"
                />
                <button @click="handleSetCursor" class="btn btn-blue btn-sm">Set Cursor</button>
              </div>

              <!-- selectRange -->
              <div class="input-group">
                <input
                  type="number"
                  v-model.number="debugState.rangeStart"
                  class="debug-input"
                  placeholder="Start"
                />
                <input
                  type="number"
                  v-model.number="debugState.rangeEnd"
                  class="debug-input"
                  placeholder="End"
                />
                <button @click="handleSelectRange" class="btn btn-green btn-sm">
                  Select Range
                </button>
              </div>

              <!-- wrapSelection -->
              <div class="input-group">
                <input
                  type="text"
                  v-model="debugState.wrapBefore"
                  class="debug-input"
                  placeholder="Before"
                />
                <input
                  type="text"
                  v-model="debugState.wrapAfter"
                  class="debug-input"
                  placeholder="After"
                />
                <button
                  @click="handleWrap"
                  class="btn btn-purple btn-sm"
                  :disabled="!selectionState.hasSelection"
                >
                  Wrap
                </button>
              </div>

              <!-- replaceRange 测试 -->
              <div class="input-group">
                <input
                  type="number"
                  v-model="debugState.replaceStart"
                  class="debug-input"
                  placeholder="Start"
                />
                <input
                  type="number"
                  v-model="debugState.replaceEnd"
                  class="debug-input"
                  placeholder="End"
                />
                <input
                  type="text"
                  v-model="debugState.replaceText"
                  class="debug-input"
                  placeholder="Content"
                />
                <button @click="handleReplaceRange" class="btn btn-orange btn-sm">Replace</button>
              </div>

              <!-- insertText 测试 -->
              <div class="input-group">
                <input
                  type="text"
                  v-model="debugState.insertContent"
                  class="debug-input"
                  placeholder="Text to insert"
                />
                <button @click="handleInsertText" class="btn btn-indigo btn-sm">Insert Text</button>
              </div>

              <!-- applyInlineFormat 测试 -->
              <div class="input-group">
                <select v-model="debugState.inlineFormat" class="debug-input">
                  <option disabled value="" selected>请选择内联格式</option>

                  <option value="bold">Bold (**)</option>
                  <option value="italic">Italic (*)</option>
                  <option value="code">Code (`)</option>
                  <option value="highlight">Highlight (==)</option>
                  <option value="link">Link ([]())</option>
                </select>
                <button @click="handleApplyInlineFormat" class="btn btn-purple btn-sm">
                  Apply Inline Format
                </button>
              </div>

              <!-- new: applyParagraphFormat 测试 -->
              <div class="input-group">
                <select v-model="debugState.paragraphFormat" class="debug-input">
                  <option disabled value="" selected>请选择段落格式</option>

                  <option value="heading1">Heading 1 (#)</option>
                  <option value="heading2">Heading 2 (##)</option>
                  <option value="heading3">Heading 3 (###)</option>
                  <option value="quote">Quote (>)</option>
                </select>
                <button @click="handleApplyParagraphFormat" class="btn btn-green btn-sm">
                  Apply Paragraph Format
                </button>
              </div>

              <!-- new: insertBlock 测试 -->
              <div class="input-group">
                <select v-model="debugState.blockInsertType" class="debug-input">
                  <option disabled value="" selected>请选择块类型</option>
                  <option value="divider">Divider (---)</option>
                  <option value="codeBlock">Code Block (```)</option>
                  <option value="image">Image (![]( ))</option>
                  <option value="table">Table (| | |)</option>
                  <option value="video">Video (&lt;video&gt;)</option>
                  <option value="embedLink">Embed Link ([]())</option>
                </select>
                <button @click="handleInsertBlock" class="btn btn-orange btn-sm">
                  Insert Block
                </button>
              </div>
            </div>
          </div>

          <!-- 操作日志 -->
          <div class="card">
            <h2 class="card-title">操作日志</h2>
            <div class="log-container">
              <div v-for="(log, index) in logs" :key="index" :class="['log-item', log.type]">
                <div class="log-header">
                  <span class="log-time">{{ log.time }}</span>
                  <span :class="['log-type', log.type]">{{ log.type }}</span>
                </div>
                <div class="log-message">{{ log.message }}</div>
              </div>
              <div v-if="logs.length === 0" class="log-empty">暂无日志</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ============================================================================
   布局容器
   ============================================================================ */
.page-container {
  /* 最小高度占满整个视口 */
  min-height: 100vh;

  /* 浅灰色背景 - Tailwind gray-50 */
  background-color: #f9fafb;

  /* 四周内边距 32px */
  padding: 32px;
}

.content-wrapper {
  /* 最大宽度 1280px - 防止在超大屏幕上内容过于分散 */
  max-width: 1280px;

  /* 水平居中：上下边距0，左右边距自动计算 */
  margin: 0 auto;
}

/* ============================================================================
   标题区域
   ============================================================================ */
.header-section {
  /* 标题区域底部留白 24px */
  margin-bottom: 24px;
}

.header-section h1 {
  /* 大标题字体大小 30px */
  font-size: 30px;

  /* 粗体 */
  font-weight: bold;

  /* 深灰色文字 - Tailwind gray-900 */
  color: #111827;
}

.header-section p {
  /* 副标题顶部留白 8px */
  margin-top: 8px;

  /* 中灰色文字 - Tailwind gray-500 */
  color: #6b7280;
}

/* ============================================================================
   网格布局 - 响应式两列，高度自动对齐
   ============================================================================ */
.main-grid {
  /* 使用 CSS Grid 布局 */
  display: grid;

  /* 默认单列布局（移动端） */
  grid-template-columns: 1fr;

  /* 列之间间距 24px */
  gap: 24px;

  /* 关键：从顶部对齐，让两列独立增长（不强制相同高度） */
  align-items: start;
}

/* 大屏幕（1024px 以上）：切换为两列布局 */
@media (min-width: 1024px) {
  .main-grid {
    /* 两列等宽布局 */
    grid-template-columns: 1fr 1fr;
  }
}

/* 列容器 - 内部元素垂直排列 */
.column {
  /* 使用 Flexbox 布局 */
  display: flex;

  /* 子元素垂直排列 */
  flex-direction: column;

  /* 子元素之间间距 16px */
  gap: 16px;
}

/* ============================================================================
   卡片样式 - 通用卡片容器
   ============================================================================ */
.card {
  /* 白色背景 */
  background-color: white;

  /* 1px 灰色边框 - Tailwind gray-300 */
  border: 1px solid #d1d5db;

  /* 圆角 8px */
  border-radius: 8px;

  /* 内边距 16px */
  padding: 16px;

  /* 轻微阴影 - 提升视觉层次 */
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.card-title {
  /* 卡片标题底部留白 12px */
  margin-bottom: 12px;

  /* 字体大小 18px */
  font-size: 18px;

  /* 半粗体 */
  font-weight: 600;

  /* 深灰色 - Tailwind gray-700 */
  color: #374151;
}

/* ============================================================================
   编辑器输入框 - contenteditable 元素样式
   ============================================================================ */
.editor-input {
  /* 最小高度 100px - 保证足够的编辑空间 */
  min-height: 100px;

  /* 内边距 12px */
  padding: 12px;

  /* 边框 1px 浅灰色 - Tailwind gray-200 */
  border: 1px solid #e5e7eb;

  /* 圆角 4px */
  border-radius: 4px;

  /* 白色背景 */
  background-color: white;

  /* 移除浏览器默认的聚焦轮廓 */
  outline: none;
}

/* 编辑器聚焦状态 */
.editor-input:focus {
  /* 蓝色边框 - Tailwind blue-500 */
  border-color: #3b82f6;

  /* 蓝色发光效果 - 模拟 Tailwind 的 ring */
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* ============================================================================
   按钮样式 - 修饰符模式实现按钮组件
   ============================================================================ */
.button-group {
  /* 使用 CSS flex 布局 */
  display: flex;

  /* 按钮太多时会自动换行 */
  flex-wrap: wrap;

  /* 按钮之间间距 8px */
  gap: 8px;

  /* 靠左排列，避免空隙 */
  justify-content: flex-start;

  /* 垂直居中对齐 */
  align-items: center;
}

/* 按钮基础样式 - 所有按钮的通用样式 */
.btn {
  /* 内边距：上下 8px，左右 16px */
  padding: 8px 16px;

  /* 移除浏览器默认边框 */
  border: none;

  /* 圆角 4px */
  border-radius: 4px;

  /* 白色文字 */
  color: white;

  /* 半粗体 */
  font-weight: 500;

  /* 鼠标指针变为手型 */
  cursor: pointer;

  /* 背景色过渡动画 - 200ms */
  transition: background-color 0.2s;
}

/* 按钮禁用状态 */
.btn:disabled {
  background-color: #d1d5db;
  /* 灰色背景 */
  color: #6b7280;
  /* 灰色文字 */
  cursor: not-allowed;
  /* 鼠标指针变为禁止符号 */
  opacity: 1;
  /* 保持不透明 */
}

/* 按钮颜色变体 - 使用修饰符模式实现不同颜色 */

/* 蓝色按钮 */
.btn-blue {
  background-color: #3b82f6;
  /* Tailwind blue-500 */
}

.btn-blue:hover:not(:disabled) {
  background-color: #2563eb;
  /* Tailwind blue-600 - 悬停时变深 */
}

/* 绿色按钮 */
.btn-green {
  background-color: #10b981;
  /* Tailwind green-500 */
}

.btn-green:hover:not(:disabled) {
  background-color: #059669;
  /* Tailwind green-600 */
}

/* 紫色按钮 */
.btn-purple {
  background-color: #8b5cf6;
  /* Tailwind purple-500 */
}

.btn-purple:hover:not(:disabled) {
  background-color: #7c3aed;
  /* Tailwind purple-600 */
}

/* 靛蓝色按钮 */
.btn-indigo {
  background-color: #6366f1;
  /* Tailwind indigo-500 */
}

.btn-indigo:hover:not(:disabled) {
  background-color: #4f46e5;
  /* Tailwind indigo-600 */
}

/* 橙色按钮 */
.btn-orange {
  background-color: #f97316;
  /* Tailwind orange-500 */
}

.btn-orange:hover:not(:disabled) {
  background-color: #ea580c;
  /* Tailwind orange-600 */
}

/* 灰色按钮 */
.btn-gray {
  background-color: #6b7280;
  /* Tailwind gray-500 */
}

.btn-gray:hover:not(:disabled) {
  background-color: #4b5563;
  /* Tailwind gray-600 */
}

.btn-red {
  background-color: #ef4444; /* Tailwind red-500 */
}
.btn-red:hover:not(:disabled) {
  background-color: #dc2626; /* Tailwind red-600 */
}
/* ============================================================================
   状态显示区域 - SelectionInfo 实时状态
   ============================================================================ */
.info-list {
  /* Flexbox 垂直布局 */
  display: flex;
  flex-direction: column;

  /* 行之间间距 8px */
  gap: 8px;

  /* 等宽字体 - 适合显示代码和数据 */
  font-family: monospace;

  /* 字体大小 14px */
  font-size: 14px;
}

.info-row {
  /* Flexbox 水平布局 */
  display: flex;

  /* 两端对齐：标签在左，值在右 */
  justify-content: space-between;
}

.info-label {
  /* 中灰色标签 - Tailwind gray-500 */
  color: #6b7280;
}

.info-value {
  /* 粗体值 */
  font-weight: bold;

  /* 默认蓝色 - Tailwind blue-600 */
  color: #3b82f6;
}

/* 激活状态（如 hasSelection: true） */
.info-value.active {
  /* 绿色 - 表示"是"或"已激活" */
  color: #10b981;
  /* Tailwind green-500 */
}

/* 未激活状态（如 isEmpty: true） */
.info-value.inactive {
  /* 浅灰色 - 表示"否"或"未激活" */
  color: #9ca3af;
  /* Tailwind gray-400 */
}

/* selectedText 显示区域 */
.selected-text-area {
  /* 顶部留白 12px */
  margin-top: 12px;

  /* 顶部内边距 12px */
  padding-top: 12px;

  /* 顶部分隔线 */
  border-top: 1px solid #e5e7eb;
}

.selected-text {
  /* 最大高度 80px - 超出显示滚动条 */
  max-height: 80px;

  /* 垂直滚动 */
  overflow-y: auto;

  /* 内边距 8px */
  padding: 8px;

  /* 浅灰色背景 - Tailwind gray-100 */
  background-color: #f3f4f6;

  /* 圆角 4px */
  border-radius: 4px;

  /* 深灰色文字 - Tailwind gray-800 */
  color: #1f2937;
}

/* 空文本状态 */
.selected-text.empty {
  /* 浅灰色 - 表示占位符 */
  color: #9ca3af;
}

/* 有文本状态 */
.selected-text.has-text {
  /* 加粗 - 突出显示选中的文本 */
  font-weight: 600;
}

/* ============================================================================
   日志区域 - 操作日志显示
   ============================================================================ */
.log-container {
  /* 最大高度 300px - 超出显示滚动条 */
  max-height: 300px;

  /* 垂直滚动 */
  overflow-y: auto;

  /* Flexbox 垂直布局 */
  display: flex;
  flex-direction: column;

  /* 日志项之间间距 4px */
  gap: 4px;

  /* 等宽字体 */
  font-family: monospace;

  /* 小字体 12px */
  font-size: 12px;
}

.log-item {
  /* 内边距 8px */
  padding: 8px;

  /* 浅灰色背景 */
  background-color: #f9fafb;

  /* 圆角 4px */
  border-radius: 4px;

  /* 左侧彩色边框（颜色由修饰符决定） */
  border-left: 4px solid;
}

/* 日志类型：info（蓝色） */
.log-item.info {
  border-left-color: #3b82f6;
}

/* 日志类型：success（绿色） */
.log-item.success {
  border-left-color: #10b981;
}

/* 日志类型：warning（橙色） */
.log-item.warning {
  border-left-color: #f97316;
}

/* 日志头部（时间 + 类型） */
.log-header {
  /* Flexbox 水平布局 */
  display: flex;

  /* 两端对齐 */
  justify-content: space-between;

  /* 顶部对齐 */
  align-items: flex-start;
}

.log-time {
  /* 灰色时间戳 */
  color: #6b7280;
}

.log-type {
  /* 更小的字体 11px */
  font-size: 11px;
}

/* 日志类型颜色 */
.log-type.info {
  color: #3b82f6;
}

.log-type.success {
  color: #10b981;
}

.log-type.warning {
  color: #f97316;
}

/* 日志消息内容 */
.log-message {
  /* 顶部留白 4px */
  margin-top: 4px;

  /* 深灰色文字 */
  color: #1f2937;
}

/* 无日志占位符 */
.log-empty {
  /* 上下内边距 32px */
  padding: 32px 0;

  /* 文字居中 */
  text-align: center;

  /* 浅灰色 */
  color: #9ca3af;
}

/* ============================================================================
   调试工具样式
   ============================================================================ */
.debug-section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #e5e7eb;
}

.debug-section:last-child {
  border-bottom: none;
  padding-bottom: 0;
  margin-bottom: 0;
}

.char-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  margin-top: 8px;
  font-family: monospace;
}

.char-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: #f3f4f6;
  border-radius: 2px;
  padding: 2px;
  min-width: 20px;
}

.char-item.active {
  background-color: #bfdbfe;
  /* blue-200 */
}

.char-item.cursor {
  border: 1px solid #3b82f6;
}

.char-val {
  font-size: 14px;
  color: #1f2937;
}

.char-idx {
  font-size: 10px;
  color: #9ca3af;
}

.input-group {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.debug-input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
}

.debug-result {
  margin-top: 8px;
  font-size: 12px;
  color: #059669;
  font-family: monospace;
}
</style>
