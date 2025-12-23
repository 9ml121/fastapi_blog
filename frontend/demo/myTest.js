
const arr = ['A', 'B', 'C', 'D']

// 删除 1 个元素
arr.splice(1, 1)  // 删除索引 1 的元素
console.log(arr)  // ['A', 'C', 'D']

// 删除并替换
arr.splice(1, 1, 'X', 'Y')
console.log(arr)  // ['A', 'X', 'Y', 'D']

// 任务：实现一个购物车管理系统
let cart = [
  { id: 1, name: 'iPhone', price: 999 },
  { id: 2, name: 'iPad', price: 599 },
  { id: 3, name: 'AirPods', price: 199 },
  { id: 4, name: 'mac', price: 9999 }
]

// 1: 删除 id 为 2 的商品
const index = cart.findIndex(item => item.id === 2)
cart.splice(index, 1)
console.log(cart)

// 2: 删除价格 > 500 的所有商品
cart = cart.filter(item => item.price > 500)
console.log(cart)

// 3: 删除第一个商品
cart.shift()
console.log(cart)


// 4: 删除最后一个商品
cart.pop()
console.log(cart)


// 任务：实现一个更复杂的 Toast 管理器
let toasts = [
  { id: 1, type: 'success', message: 'Login success' },
  { id: 2, type: 'error', message: 'Network error' },
  { id: 3, type: 'warning', message: 'Low storage' },
  { id: 4, type: 'error', message: 'Server down' }
]

// 1: 删除所有 type 为 'error' 的 toast
// toasts = toasts.filter(toast => toast.type !== 'error')
// console.log(toasts)

// 2: 只保留最新的 2 条 toast（删除旧的）
// toasts.splice(0, toasts.length - 2)
// toasts = toasts.slice(-2)
// console.log(toasts)


// 3: 批量删除多个 id：[1, 3]
toasts = toasts.filter(toast => ![1, 3].includes(toast.id))
console.log(toasts)

// 4: 清空所有 toast
// toasts.length = 0
// toasts.splice(0)
toasts = []
console.log(toasts)
