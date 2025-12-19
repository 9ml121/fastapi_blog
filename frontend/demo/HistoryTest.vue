<template>
  <div class="history-test">
    <h1>useHistory 功能测试</h1>
    <button @click="runAllTests" class="run-btn">🧪 运行所有测试</button>

    <div class="test-results">
      <div v-for="result in testResults" :key="result.title" class="test-case">
        <h3>{{ result.title }}</h3>
        <pre>{{ result.output }}</pre>
        <div :class="['status', result.passed ? 'success' : 'error']">
          {{ result.passed ? '✅ 通过' : '❌ 失败' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useHistory } from '../composables/useHistory'
import type { EditorState } from '../composables/editor.types'

interface TestResult {
  title: string
  output: string
  passed: boolean
}

const testResults = ref<TestResult[]>([])

// 创建 mock state
const createMockState = (): EditorState => {
  return reactive({
    title: '',
    content: '',
    transactions: [],
    currentIndex: -1,
    selection: { start: 0, end: 0, selectedText: '', isEmpty: true },
    isSaving: false,
    isDirty: false,
    isFocused: false,
    hasError: false,
    canUndo: false,
    canRedo: false,
  }) as EditorState
}

const runAllTests = () => {
  testResults.value = []

  // 场景1: 初始状态
  {
    const mockState = createMockState()
    const history = useHistory(mockState)
    const state = history.getHistory()

    const output = [
      `transactions 数量: ${state.transactions.length}`,
      `currentIndex: ${state.currentIndex}`,
      `canUndo: ${history.canUndo.value}`,
      `canRedo: ${history.canRedo.value}`,
    ].join('\n')

    const passed =
      state.transactions.length === 0 &&
      state.currentIndex === -1 &&
      history.canUndo.value === false &&
      history.canRedo.value === false

    testResults.value.push({
      title: '场景1: 初始状态',
      output,
      passed,
    })
  }

  // 场景2: 第一次操作
  {
    const mockState = createMockState()
    const history = useHistory(mockState)
    history.pushTransaction('内容1', '操作1')
    const state = history.getHistory()

    const output = [
      `执行: pushTransaction("内容1", "操作1")`,
      `transactions 数量: ${state.transactions.length}`,
      `currentIndex: ${state.currentIndex}`,
      `canUndo: ${history.canUndo.value}`,
      `canRedo: ${history.canRedo.value}`,
    ].join('\n')

    const passed =
      state.currentIndex === 0 && history.canUndo.value === true && history.canRedo.value === false

    testResults.value.push({
      title: '场景2: 第一次操作',
      output,
      passed,
    })
  }

  // 场景3: 撤销到初始状态
  {
    const mockState = createMockState()
    const history = useHistory(mockState)
    history.pushTransaction('内容1', '操作1')
    const undoResult = history.undo()
    const state = history.getHistory()

    const output = [
      `执行: pushTransaction + undo()`,
      `undo() 返回值: "${undoResult}"`,
      `currentIndex: ${state.currentIndex}`,
      `canUndo: ${history.canUndo.value}`,
    ].join('\n')

    const passed = undoResult === '' && state.currentIndex === -1 && history.canUndo.value === false

    testResults.value.push({
      title: '场景3: 撤销到初始状态',
      output,
      passed,
    })
  }

  // 场景4: 历史分支（核心测试）
  {
    const mockState = createMockState()
    const history = useHistory(mockState)

    // 创建4个操作
    history.pushTransaction('内容1', '操作1')
    history.pushTransaction('内容2', '操作2')
    history.pushTransaction('内容3', '操作3')
    history.pushTransaction('内容4', '操作4')

    // 撤销2次
    history.undo()
    history.undo()

    // 新操作
    history.pushTransaction('新内容', '新操作')
    const state = history.getHistory()

    const labels = state.transactions.map((t: any) => t.label).join(', ')

    const output = [
      `步骤1: 创建4个操作`,
      `步骤2: 撤销2次`,
      `步骤3: 添加新操作`,
      ``,
      `剩余 transactions: ${labels}`,
      `transactions 数量: ${state.transactions.length}`,
      `currentIndex: ${state.currentIndex}`,
      `canRedo: ${history.canRedo.value}`,
    ].join('\n')

    const passed =
      state.transactions.length === 3 &&
      state.currentIndex === 2 &&
      history.canRedo.value === false &&
      state.transactions[2]!.label === '新操作'

    testResults.value.push({
      title: '场景4: 历史分支（核心）🔥',
      output,
      passed,
    })
  }

  // 场景5: 超过最大历史限制
  {
    const mockState = createMockState()
    const history = useHistory(mockState)

    for (let i = 1; i <= 52; i++) {
      history.pushTransaction(`内容${i}`, `操作${i}`)
    }

    const state = history.getHistory()
    const firstLabel = state.transactions[0]?.label

    const output = [
      `添加 52 个操作 (MAX_HISTORY_SIZE = 50)`,
      ``,
      `transactions 数量: ${state.transactions.length}`,
      `currentIndex: ${state.currentIndex}`,
      `第一个 transaction: ${firstLabel}`,
      `(最早的2个操作应该被删除了)`,
    ].join('\n')

    const passed =
      state.transactions.length === 50 && state.currentIndex === 49 && firstLabel === '操作3' // 操作1和操作2被删除了

    testResults.value.push({
      title: '场景5: 超过最大历史限制',
      output,
      passed,
    })
  }

  // 场景6: 边界情况 - 空栈撤销
  {
    const mockState = createMockState()
    const history = useHistory(mockState)
    const result = history.undo()

    const output = [`在空栈上调用 undo()`, `返回值: ${result}`, `(应该返回 null)`].join('\n')

    const passed = result === null

    testResults.value.push({
      title: '场景6: 空栈撤销',
      output,
      passed,
    })
  }

  // 场景7: 边界情况 - 最新状态重做
  {
    const mockState = createMockState()
    const history = useHistory(mockState)
    history.pushTransaction('内容1', '操作1')
    const result = history.redo()

    const output = [`在最新状态调用 redo()`, `返回值: ${result}`, `(应该返回 null)`].join('\n')

    const passed = result === null

    testResults.value.push({
      title: '场景7: 最新状态重做',
      output,
      passed,
    })
  }
}
</script>

<style scoped>
.history-test {
  font-family: monospace;
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

h1 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.run-btn {
  background: #42b983;
  color: white;
  border: none;
  padding: 12px 24px;
  font-size: 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 20px;
}

.run-btn:hover {
  background: #35a372;
}

.test-results {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.test-case {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  background: #f9f9f9;
}

.test-case h3 {
  margin: 0 0 12px 0;
  color: #2c3e50;
}

pre {
  background: white;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0 0 12px 0;
  border: 1px solid #eee;
}

.status {
  font-weight: bold;
  padding: 8px;
  border-radius: 4px;
  text-align: center;
}

.status.success {
  background: #d4edda;
  color: #155724;
}

.status.error {
  background: #f8d7da;
  color: #721c24;
}
</style>
