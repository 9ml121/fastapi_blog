import type { EditorState, EditTransaction } from '../types/editor'
import { reactive, computed } from 'vue'

export function useHistory(state: EditorState) {
  // 1️⃣ 内部状态定义: 创建一个响应性的历史栈
  const historyState = reactive({
    transactions: [] as EditTransaction[], // 历史快照数组
    currentIndex: -1, // 当前指针位置
  })

  // 2️⃣ 辅助函数: 为每个 transaction 生成唯一 ID
  /**
   * 为每个 transaction 生成唯一 ID
   *
   * ID 格式**：`txn_1701234567890_abc123`
   *  - `Date.now()`：时间戳，保证时间上唯一
   *  - `Math.random()`：随机字符串，保证同一时间的操作唯一
   */
  const generateId = (): string => {
    return `txn_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
  }

  // 3️⃣ 核心方法：pushTransaction - 记录新操作到历史栈
  const pushTransaction = (content: string, label: string = '未命名操作'): void => {
    // 1. 创建新的 transaction 对象
    const newTransaction: EditTransaction = {
      id: generateId(),
      label,
      content,
      timestamp: Date.now(),
    }

    // 2. ⚠️ 丢弃currentIndex 之后的所有内容
    // 原因：用户在历史中间做了新操作，未来的历史就失效了
    historyState.transactions = historyState.transactions.slice(0, historyState.currentIndex + 1)

    // 3. 添加新 transaction 到栈顶
    historyState.transactions.push(newTransaction)

    // 4. 指针移动到最新位置
    historyState.currentIndex = historyState.transactions.length - 1

    // 5. 限制历史栈大小，避免内存爆炸
    const MAX_HISTORY_SIZE = 50
    if (historyState.transactions.length > MAX_HISTORY_SIZE) {
      // 删除最早的快照（FIFO 队列）
      historyState.transactions.shift()
      historyState.currentIndex--
    }
  }

  // 4️⃣ 核心方法：undo - 回到上一个历史状态
  const undo = (): string | null => {
    // 1. 检查是否可以撤销
    if (historyState.currentIndex < 0) {
      console.warn('[useHistory] 无法撤销：已经在初始状态')
      return null
    }

    // 2. 指针后退
    historyState.currentIndex--

    // 3. 返回新的内容
    if (historyState.currentIndex === -1) {
      // 回到初始空白状态
      console.log('[useHistory] 撤销到初始状态')
      return ''
    } else {
      // 返回指针位置的快照内容
      const targetTransaction = historyState.transactions[historyState.currentIndex]
      console.log(`[useHistory] 撤销到: ${targetTransaction!.label}`)
      return targetTransaction!.content
    }
  }

  // 5️⃣ 核心方法：redo - 前进到下一个历史状态
  const redo = (): string | null => {
    // 1. 检查是否可以重做
    if (historyState.currentIndex >= historyState.transactions.length - 1) {
      console.warn('[useHistory] 无法重做：已经在最新状态')
      return null
    }

    // 2. 指针前进
    historyState.currentIndex++

    // 3. 返回新的内容
    const targetTransaction = historyState.transactions[historyState.currentIndex]
    console.log(`[useHistory] 重做到: ${targetTransaction!.label}`)
    return targetTransaction!.content
  }

  // 6️⃣ 计算属性
  const canUndo = computed(() => {
    return historyState.currentIndex >= 0
  })

  const canRedo = computed(() => {
    return historyState.currentIndex < historyState.transactions.length - 1
  })

  // 7️⃣ 返回 API
  return {
    //  方法
    pushTransaction,
    undo,
    redo,

    // 计算属性
    canUndo,
    canRedo,

    // 调试用（可选）
    getHistory: () => ({
      transactions: historyState.transactions,
      currentIndex: historyState.currentIndex,
    }),
  }
}

export type UseHistoryReturn = ReturnType<typeof useHistory>
