/**
 * useMarkdownEditor - 编辑器核心 Composable
 * 
 * 功能：
 * - 管理编辑器的核心状态（内容、标题、保存状态）
 * - 提供编辑操作接口（撤销、重做、内容修改）
 * - 集成自动保存机制
 * - 管理选中文本信息
 * - 管理操作历史
 * 
 * 使用示例：
 * const editor = useMarkdownEditor({
 *   content: '# 初始内容',
 *   autoSave: { enabled: true, interval: 2000 }
 * });
 */

import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue';
import type { EditorState, EditorConfig, EditAction, SelectionInfo, AutoSaveConfig } from '../types/editor';

/**
 * useMarkdownEditor - 编辑器主 Hook
 * 
 * @param config 编辑器配置对象
 * @returns 编辑器的状态、计算属性和操作方法
 */
export function useMarkdownEditor(config: EditorConfig = {}) {
  // ============================================================================
  // 1. 初始化状态
  // ============================================================================

  /**
   * 核心编辑器状态
   * 这就是编辑器在任何时刻的"快照"
   */
  const state = reactive<EditorState>({
    title: config.title ?? '',
    content: config.content ?? '',
    isDirty: false,
    isSaving: false,
    lastSaved: undefined,
    canUndo: false,
    canRedo: false,
    selectedText: undefined,
  });

  /**
   * 选中文本信息（用于工具栏）
   */
  const selection = reactive<SelectionInfo>({
    start: 0,
    end: 0,
    selectedText: '',
    isEmpty: true,
  });

  /**
   * 操作历史栈（用于撤销/重做）
   * - undoStack: 可以撤销的操作
   * - redoStack: 可以重做的操作
   */
  const undoStack = ref<EditAction[]>([]);
  const redoStack = ref<EditAction[]>([]);

  /**
   * 自动保存配置
   */
  const autoSaveConfig = reactive<AutoSaveConfig>(
    config.autoSave ?? {
      enabled: true,
      interval: 3000,  // 默认 3 秒保存一次
      storage: 'both',
      draftKey: 'markdown-editor-draft',
    }
  );

  /**
   * 自动保存定时器 ID
   */
  let autoSaveTimer: ReturnType<typeof setTimeout> | null = null;

  // ============================================================================
  // 2. 计算属性
  // ============================================================================

  /**
   * 是否可以撤销
   */
  const canUndo = computed(() => undoStack.value.length > 0);

  /**
   * 是否可以重做
   */
  const canRedo = computed(() => redoStack.value.length > 0);

  /**
   * 是否有未保存的改动
   */
  const isDirty = computed(() => state.isDirty);

  /**
   * 历史记录数量
   */
  const historySize = computed(() => undoStack.value.length);

  // ============================================================================
  // 3. 核心编辑操作
  // ============================================================================

  /**
   * 更新内容并标记为已修改
   * 
   * @param newContent 新的内容
   */
  function updateContent(newContent: string): void {
    // 记录变更前的内容（用于撤销）
    const previousContent = state.content;

    // 创建编辑操作记录
    const action: EditAction = {
      type: 'replace',
      timestamp: Date.now(),
      content: newContent,
      start: 0,
      end: state.content.length,
      previousContent,
    };

    // 执行操作：更新内容
    state.content = newContent;
    state.isDirty = true;

    // 将操作推入撤销栈
    undoStack.value.push(action);

    // 清空重做栈（新操作后，重做历史失效）
    redoStack.value = [];

    // 限制历史记录大小
    const maxHistory = config.historySize ?? 50;
    if (undoStack.value.length > maxHistory) {
      undoStack.value.shift();
    }
  }

  /**
   * 更新标题
   * 
   * @param newTitle 新的标题
   */
  function updateTitle(newTitle: string): void {
    state.title = newTitle;
    state.isDirty = true;
  }

  /**
   * 撤销上一步操作
   */
  function undo(): void {
    if (!canUndo.value) return;

    // 从撤销栈弹出最后一个操作
    const action = undoStack.value.pop();
    if (!action) return;

    // 恢复操作前的内容
    if (action.previousContent !== undefined) {
      state.content = action.previousContent;
    }

    // 将此操作推入重做栈（以便用户可以重做）
    redoStack.value.push(action);
  }

  /**
   * 重做撤销的操作
   */
  function redo(): void {
    if (!canRedo.value) return;

    // 从重做栈弹出最后一个操作
    const action = redoStack.value.pop();
    if (!action) return;

    // 重新应用操作
    if (action.content !== undefined) {
      state.content = action.content;
    }

    // 将此操作推回撤销栈
    undoStack.value.push(action);
  }

  /**
   * 清空所有历史记录
   * （用于保存后重置状态）
   */
  function clearHistory(): void {
    undoStack.value = [];
    redoStack.value = [];
  }

  // ============================================================================
  // 4. 选中文本管理
  // ============================================================================

  /**
   * 更新选中文本信息
   * 
   * @param start 选中开始位置
   * @param end 选中结束位置
   */
  function updateSelection(start: number, end: number): void {
    // 确保 start <= end
    const normalizedStart = Math.min(start, end);
    const normalizedEnd = Math.max(start, end);

    // 从内容中截取选中的文字
    const selectedText = state.content.substring(normalizedStart, normalizedEnd);

    // 更新选中信息
    selection.start = normalizedStart;
    selection.end = normalizedEnd;
    selection.selectedText = selectedText;
    selection.isEmpty = normalizedStart === normalizedEnd;

    // 同步到主状态
    state.selectedText = selectedText;
  }

  /**
   * 清空选中
   */
  function clearSelection(): void {
    selection.start = 0;
    selection.end = 0;
    selection.selectedText = '';
    selection.isEmpty = true;
    state.selectedText = undefined;
  }

  // ============================================================================
  // 5. 自动保存机制
  // ============================================================================

  /**
   * 立即保存当前内容
   * 
   * @param force 是否强制保存（即使没有改动）
   */
  async function save(force: boolean = false): Promise<void> {
    // 如果没有改动且非强制保存，则跳过
    if (!state.isDirty && !force) return;

    // 设置保存状态
    state.isSaving = true;

    try {
      // TODO: 实现具体的保存逻辑
      // 这里应该调用 API 或保存到 localStorage
      // 根据 autoSaveConfig.storage 的值决定保存位置

      // 模拟网络延迟（后续替换为真实的保存逻辑）
      await new Promise((resolve) => setTimeout(resolve, 300));

      // 更新保存时间和状态
      state.lastSaved = new Date();
      state.isDirty = false;
      clearHistory();  // 保存后清空历史
    } catch (error) {
      // TODO: 处理保存错误
      console.error('保存失败:', error);
      // 在此处调用 config.callbacks?.onError?.(error)
    } finally {
      state.isSaving = false;
    }
  }

  /**
   * 启动自动保存机制
   */
  function startAutoSave(): void {
    if (!autoSaveConfig.enabled) return;

    // 监听内容变化，定时触发保存
    autoSaveTimer = setInterval(() => {
      if (state.isDirty) {
        save();
      }
    }, autoSaveConfig.interval);
  }

  /**
   * 停止自动保存机制
   */
  function stopAutoSave(): void {
    if (autoSaveTimer) {
      clearInterval(autoSaveTimer);
      autoSaveTimer = null;
    }
  }

  /**
   * 处理页面卸载前的保存
   */
  function handleBeforeUnload(event: BeforeUnloadEvent): void {
    if (state.isDirty && autoSaveConfig.saveOnBeforeUnload !== false) {
      // 同步保存（某些浏览器可能不支持异步）
      save(true);

      // 显示确认对话框
      event.preventDefault();
      event.returnValue = '';
    }
  }

  // ============================================================================
  // 6. 生命周期钩子
  // ============================================================================

  /**
   * 组件挂载时：初始化自动保存和事件监听
   */
  onMounted(() => {
    startAutoSave();
    window.addEventListener('beforeunload', handleBeforeUnload);
  });

  /**
   * 组件卸载时：清理定时器和事件监听
   */
  onUnmounted(() => {
    stopAutoSave();
    window.removeEventListener('beforeunload', handleBeforeUnload);
  });

  // ============================================================================
  // 7. 返回公共接口
  // ============================================================================

  return {
    // 状态
    state,
    selection,

    // 计算属性
    canUndo,
    canRedo,
    isDirty,
    historySize,

    // 编辑操作
    updateContent,
    updateTitle,
    undo,
    redo,
    clearHistory,

    // 选中管理
    updateSelection,
    clearSelection,

    // 保存操作
    save,
    startAutoSave,
    stopAutoSave,
  };
}
