/**
 * 编辑器核心类型定义文件（重构版）
 *
 * 设计原则：
 * 1. 职责分离 - 不同的状态有不同的生命周期和用途
 * 2. 数据完整性 - 必要的元数据都要有定义
 * 3. 类型安全 - 用 TypeScript 的高级特性防止错误
 * 4. 扩展性 - 支持插件、权限、国际化等
 */

// ============================================================================
// 第一层：纯内容状态（必须持久化）
// ============================================================================

/**
 * EditorContent: 编辑器的核心内容
 *
 * 这层数据：
 * - 必须保存到数据库
 * - 用户最关心的数据
 * - 其他所有状态都围绕这个展开
 */
export interface EditorContent {
  title: string // 文章标题
  content: string // 文章正文内容（Markdown 格式）
}

// ============================================================================
// 第二层：操作历史（用于撤销重做，可选持久化）
// ============================================================================

/**
 * EditAction: 单个原子编辑操作（底层）
 *
 * 用途：记录编辑的最小单位，底层不可再分
 * 这些 Action 可能组合成一个 Transaction（用户可见的一个操作）
 *
 * 示例：
 * - 用户输入"hello" → 可能产生 5 个连续的 insert action（但合并成 1 个 transaction）
 * - 用户替换文本 → delete action + insert action（合并成 1 个 transaction）
 */
export interface EditAction {
  // 操作类型
  type: 'insert' | 'delete' | 'format' | 'replace'

  // 操作详情
  content?: string // 插入/删除/替换的内容
  start?: number // 操作的起始位置
  end?: number // 操作的结束位置

  // 撤销所需：记录操作前的内容
  previousContent?: string

  // 时间戳（用于自动合并判断）
  timestamp: number
}

/**
 * EditTransaction: 编辑事务（业界标准做法）
 *
 * 用途：
 * - 将多个相关的 EditAction 组合成一个逻辑操作
 * - 用户看到的"一次撤销/重做"对应一个 Transaction
 * - 支持自动合并（如连续输入、连续删除）
 *
 * 设计原理（参考 VS Code、ProseMirror、Google Docs）：
 * 1. 底层有原子的 EditAction（insert、delete 等）
 * 2. 但用户体验的是 EditTransaction 粒度的操作
 * 3. 例如：连续输入"hello"产生 5 个 insert action，但作为 1 个 transaction
 *
 * 示例：
 * ```
 * 用户操作：连续输入"hello"
 * ↓
 * 产生的 actions：[insert('h'), insert('e'), insert('l'), insert('l'), insert('o')]
 * ↓
 * 组合成 1 个 transaction（时间窗口内的相同类型操作自动合并）
 * ↓
 * 用户撤销 1 次 Ctrl+Z → 整个 "hello" 都被删除
 * ```
 */
export interface EditTransaction {
  // 事务的唯一标识
  id: string

  // 可读的描述（用于 UI 展示、调试）
  label: string // 如 "输入文本"、"删除文本"、"替换文本"、"应用格式" 等

  // 组成这个事务的所有原子操作
  // actions: EditAction[]
  content: string  // todo 先实现简单快照版本，后面升级到增量版本

  // 事务发生的时间（取第一个 action 的时间）
  timestamp: number
}

/**
 * EditorHistory: 编辑历史管理（改进版本）
 *
 * 用途：
 * - 管理撤销/重做栈
 * - 基于 Transaction 粒度而不是单个 Action
 *
 * 示例：
 * ```
 * transactions = [
 *   { id: '1', label: '输入"hello"', actions: [...], timestamp: 1000 },
 *   { id: '2', label: '删除文本', actions: [...], timestamp: 2000 },
 *   { id: '3', label: '应用加粗', actions: [...], timestamp: 3000 }
 * ]
 * currentIndex = 1  // 表示处于 transaction[1] 之后
 * ```
 *
 * 撤销/重做：
 * - currentIndex = -1 表示未进行任何操作（初始状态）
 * - currentIndex = 0 表示处于 transaction[0] 之后
 * - 当执行新操作时，删除 currentIndex 之后的所有 transactions（这样重做历史就清空了）
 */
export interface EditorHistory {
  // 所有已提交的事务列表（按时间顺序）
  // 这是历史记录，不会被撤销操作修改
  transactions: EditTransaction[]

  // 当前在历史中的位置
  // currentIndex = -1 表示未进行任何操作（初始状态）
  // currentIndex = 0 表示处于 transactions[0] 之后
  // currentIndex = n 表示处于 transactions[n] 之后
  //
  // 示例：
  // transactions.length = 5, currentIndex = 2
  // 表示已经执行了 transactions[0]、transactions[1]、transactions[2]
  // 可以重做 transactions[3]、transactions[4]
  currentIndex: number
}

// ============================================================================
// 第三层：实时 UI 状态（不持久化，频繁变化）
// ============================================================================

/**
 * SelectionInfo: 用户的文本选中信息
 *
 * 设计原则：只存储原始数据（start/end），其他都通过计算得出
 */
export interface SelectionInfo {
  start: number // 选中的开始位置（字符索引，从 0 开始）
  end: number // 选中的结束位置

  // 选中的文字（可以从 content[start:end] 得出，但为了方便存储）
  selectedText: string

  // 状态属性（通过计算得出：start === end）
  isEmpty: boolean
}

/**
 * EditorUIState: 编辑器的 UI 相关状态
 *
 * 这层数据：
 * - 不需要持久化
 * - 频繁变化（光标移动、选中文本等）
 * - UI 组件直接订阅这层数据
 */
export interface EditorUIState {
  // 文本选中信息（频繁变化）
  selection: SelectionInfo

  // 保存状态
  isSaving: boolean // 是否正在保存中
  isDirty: boolean // 是否有未保存的改动

  // 编辑器焦点
  isFocused: boolean // 编辑器是否获得焦点
}

// ============================================================================
// 第四层：错误状态（临时状态，出现错误时设置）
// ============================================================================

/**
 * EditorErrorInfo: 错误信息
 *
 * 用途：当操作失败时，记录错误详情
 */
export interface EditorErrorInfo {
  code: string // 错误代码（如 'SAVE_FAILED'）
  message: string // 用户可读的错误信息
  originalError?: Error // 原始错误对象（用于日志）
  timestamp: number // 错误发生的时间
  recoverable: boolean // 是否可以恢复（比如重试）
}

/**
 * EditorErrorState: 错误状态管理
 */
export interface EditorErrorState {
  hasError: boolean // 是否有错误

  error?: EditorErrorInfo // 错误详情
}

// ============================================================================
// 完整状态：组合以上所有层次
// ============================================================================

/**
 * EditorState: 编辑器的完整状态
 *
 * 这是一个组合类型，包含：
 * - 内容层：content + title
 * - 历史层：actions + currentIndex
 * - UI 层：selection, isSaving, isDirty, isFocused
 * - 错误层：hasError, error
 * - 额外信息：lastSaved, canUndo, canRedo（计算属性的缓存）
 */
export interface EditorState extends EditorContent, EditorHistory, EditorUIState, EditorErrorState {
  // 额外的元信息
  lastSaved?: Date // 上次保存的时间

  // 计算属性的缓存（为了避免频繁计算）
  // 实际上这些可以从 history 中计算出来，但为了性能，缓存在这里
  canUndo: boolean
  canRedo: boolean
}

// ============================================================================
// 自动保存配置
// ============================================================================

/**
 * AutoSaveConfig: 自动保存的配置选项（混合方案）
 *
 * 设计原理：采用分层保存策略
 * 1. 本地保存（localStorage）：快速、同步、高频（2秒）
 * 2. 服务器保存（API）：可靠、异步、低频（10秒）
 * 3. 两者配合：本地快速备份 + 服务器安全存储
 *
 * 示例（推荐配置）：
 * ```
 * autoSave: {
 *   enabled: true,
 *   storage: 'both',                    // 同时用两个存储
 *   localStorageInterval: 2000,         // 2秒保存到 localStorage
 *   apiUrl: '/api/articles/auto-save',
 *   apiInterval: 10000,                 // 10秒保存到服务器（异步）
 *   maxRetries: 3,
 *   retryDelay: 5000,
 *   draftKey: 'article-draft',
 *   saveOnBeforeUnload: true,
 * }
 * ```
 */
export interface AutoSaveConfig {
  // ===== 启用开关 =====
  enabled: boolean // 是否启用自动保存

  // ===== 本地保存（localStorage）=====
  localStorageInterval?: number // 本地保存间隔（毫秒，默认 2000）
  draftKey?: string // localStorage 的键名（默认 'editor-draft'）

  // ===== 服务器保存（API）=====
  apiUrl?: string // API 保存端点（当 storage 为 'api' 或 'both' 时需要）
  apiInterval?: number // 服务器保存间隔（毫秒，默认 10000，异步非阻塞）

  // ===== 重试配置 =====
  maxRetries?: number // 服务器保存失败时最多重试次数（默认 3）
  retryDelay?: number // 重试等待时间（毫秒，默认 1000）

  // ===== 保存策略选择 =====
  storage: 'localStorage' | 'api' | 'both'
  //        - 'localStorage'：只用本地存储
  //        - 'api'：只用服务器存储
  //        - 'both'：同时用两个存储（推荐）

  // ===== 页面卸载处理 =====
  saveOnBeforeUnload?: boolean // 用户关闭页面前是否强制保存（默认 true）
}

// ============================================================================
// 工具栏操作类型定义（分细类）
// ============================================================================

/**
 * InlineFormatType: 行内格式类型,需要用户选中文本才能应用
 */
export type InlineFormatType =
  | 'bold' // 加粗：**文字**
  | 'italic' // 斜体：*文字*
  | 'code' // 行内代码：`文字`
  | 'highlight' // 高亮：==文字==
  | 'link' // 链接：[文字](url)

/**
 * ParagraphFormatType: 段落目标格式类型
 *
 * 这些操作应用于整个段落，不需要选中全文
 * 比如用户光标在任何地方，点击"H1"按钮，整行都会变成 H1
 */
export type ParagraphFormatType =
  | 'heading1' // 一级标题：# 文字
  | 'heading2' // 二级标题：## 文字
  | 'heading3' // 三级标题：### 文字
  | 'quote' // 引用：> 文字

/**
 * BlockInsertType: 块级插入操作（插入新内容）
 *
 * 用于插入代码块、图片、表格等块级元素
 */
export type BlockInsertType =
  | 'codeBlock' // 代码块：```language ...code... ```
  | 'image' // 图片：![alt](url)
  | 'table' // 表格：| col1 | col2 |
  | 'video' // 视频：嵌入视频
  | 'embedLink' // 内嵌链接：嵌入外链预览
  | 'divider' // 分割线：---

/**
 * FloatingToolbarType: 浮动工具栏支持的所有操作类型
 *
 * 组合：行内格式操作 + 段落格式操作
 */
export type FloatingToolbarType = InlineFormatType | ParagraphFormatType

/**
 * ToolbarType: 所有工具栏支持的操作类型
 *
 * 包含：浮动工具栏操作 + 块级插入操作
 */
export type ToolbarType = FloatingToolbarType | BlockInsertType

// ============================================================================
// 工具栏配置类型
// ============================================================================

/**
 * ToolbarItem 基础接口
 */
interface ToolbarItemBase {
  id: string // 按钮唯一 ID
  icon?: string // 图标名称（Lucide Icons）
  title?: string // 鼠标悬停提示
  hotkey?: string // 快捷键（如 "Ctrl+B"）
  disabled?: boolean // 是否禁用
  // 注意：label 和 description 会从 ActionRegistry 获取
}

/**
 * 行内格式工具栏项（需要选中文本）
 */
interface InlineToolbarItem extends ToolbarItemBase {
  action: InlineFormatType
  requiresSelection: true
}

/**
 * 段落格式工具栏项（作用于整个段落）
 */
interface ParagraphToolbarItem extends ToolbarItemBase {
  action: ParagraphFormatType
  requiresSelection: false
}

/**
 * 浮动工具栏项：行内格式 + 段落格式
 *
 * 使用 discriminated union，TypeScript 会强制类型安全
 */
export type FloatingToolbarItem = InlineToolbarItem | ParagraphToolbarItem

/**
 * 块级插入工具栏项
 */
export interface BlockToolbarItem extends ToolbarItemBase {
  action: BlockInsertType
}

/**
 * 所有工具栏项的通用类型
 */
export type ToolbarItem = FloatingToolbarItem | BlockToolbarItem

/**
 * ToolbarConfig: 工具栏配置
 *
 * 使用 discriminated union：
 * - position 为 'floating' 时，items 必须是 FloatingToolbarItem[]
 * - position 为 'blockMenu' 时，items 必须是 BlockToolbarItem[]
 */
export type ToolbarConfig =
  | {
      position: 'floating'
      items: FloatingToolbarItem[]
    }
  | {
      position: 'blockMenu'
      items: BlockToolbarItem[]
    }

// ============================================================================
// Markdown 格式状态类型
// ============================================================================

/**
 * FormatState: 当前光标位置的格式状态
 *
 * 用途：
 * - 检测光标所在位置已应用的格式
 * - 用于工具栏按钮的高亮显示
 * - 帮助用户了解当前编辑位置的格式状态
 *
 * 示例：
 * 光标在 "**加粗文本**" 内部时：
 * { isBold: true, isItalic: false, ... }
 */
export interface FormatState {
  isBold: boolean // 是否在加粗文本内
  isItalic: boolean // 是否在斜体文本内
  isCode: boolean // 是否在行内代码内
  isHighlight: boolean // 是否在高亮文本内
  headingLevel: 0 | 1 | 2 | 3 // 标题级别（0 = 非标题）
  isQuote: boolean // 是否在引用块内
}

// ============================================================================
// 插件系统
// ============================================================================

/**
 * EditorPlugin: 编辑器插件接口
 *
 * 允许第三方扩展编辑器功能
 */
export interface EditorPlugin {
  name: string // 插件名称
  version?: string // 插件版本

  // 生命周期 Hooks
  hooks?: {
    beforeParse?: (markdown: string) => string
    afterParse?: (html: string) => string
    onToolbarAction?: (action: string) => void
  }

  // 自定义命令
  commands?: Record<string, (args: any) => void>
}

// ============================================================================
// 编辑器配置
// ============================================================================

/**
 * EditorLocales: 国际化文本
 *
 * 用于自定义编辑器的所有 UI 文本
 */
export interface EditorLocales {
  // 操作名称
  bold?: string
  italic?: string
  code?: string
  link?: string
  heading1?: string
  heading2?: string
  heading3?: string
  quote?: string
  codeBlock?: string
  image?: string
  table?: string
  video?: string
  embedLink?: string
  newpart?: string

  // 提示信息
  selectTextToFormat?: string
  savingDraft?: string
  saveSuccess?: string
  saveFailed?: string
  [key: string]: string | undefined
}

/**
 * PermissionConfig: 权限配置
 */
export interface PermissionConfig {
  canEdit?: boolean // 是否可编辑
  canUndo?: boolean // 是否可撤销
  canRedo?: boolean // 是否可重做
  // allowedActions?: (ToolbarType)[];       // 允许的操作白名单
  // deniedActions?: (ToolbarType)[];        // 禁止的操作黑名单
}

/**
 * ToolbarStyleConfig: 工具栏样式配置
 */
export interface ToolbarStyleConfig {
  floating?: {
    maxWidth?: number
    direction?: 'horizontal' | 'vertical'
    offset?: { x: number; y: number }
  }
  blockMenu?: {
    width?: number
    side?: 'left' | 'right'
  }
}

/**
 * ErrorHandlerConfig: 错误处理配置
 */
export interface ErrorHandlerConfig {
  onError?: (error: EditorErrorInfo) => void
  logErrors?: boolean
  retryStrategies?: {
    [code: string]: {
      maxRetries: number
      backoffMs: number
    }
  }
}

/**
 * EditorConfig: 编辑器的完整配置对象
 */
export interface EditorConfig {
  // ===== 基础配置 =====
  title?: string // 初始标题
  content?: string // 初始内容
  placeholder?: string // 占位符文本

  // ===== 功能开关 =====
  readOnly?: boolean // 只读模式
  spellCheck?: boolean // 拼写检查

  // ===== 工具栏配置 =====
  toolbars?: {
    floating?: ToolbarConfig
    blockMenu?: ToolbarConfig
  }

  // ===== 自动保存 =====
  autoSave?: AutoSaveConfig

  // ===== 撤销重做 =====
  historySize?: number // 最多保留多少个操作（默认 50）

  // ===== 插件 =====
  plugins?: EditorPlugin[]

  // ===== 国际化 =====
  locale?: EditorLocales

  // ===== 权限 =====
  permissions?: PermissionConfig

  // ===== 样式 =====
  toolbarStyle?: ToolbarStyleConfig

  // ===== 错误处理 =====
  errorHandling?: ErrorHandlerConfig

  // ===== 事件回调 =====
  callbacks?: {
    onContentChange?: (content: string) => void
    onSave?: (state: EditorState) => void
    onError?: (error: EditorErrorInfo) => void
  }
}
