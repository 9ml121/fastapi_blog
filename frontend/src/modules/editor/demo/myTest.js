const fruits = ['apple', 'banana', 'cherry', 'date']
// 要求：找到第一个长度大于 5 的水果
const result = fruits.find(fruit => fruit.length > 5)
console.log(result)
// 预期输出: 'banana'

const users = [
  { id: 1, name: 'Alice', age: 25 },
  { id: 2, name: 'Bob', age: 30 },
  { id: 3, name: 'Charlie', age: 35 },
]
// 要求：找到 id 为 2 的用户
const user = users.find(user => user.id === 2)
console.log(user)
// 预期输出: { id: 2, name: 'Bob', age: 30 }

const numbers = [1, 3, 5, 7, 9]

// 要求：找到第一个偶数，如果找不到返回默认值 0
const evenNumber = numbers.find(number => number % 2 === 0) ?? 0

console.log(evenNumber)
// 预期输出: 0（因为数组中没有偶数）



const tocItems= [
  { id: 'toc-0', text: '简介', level: 2 },
  { id: 'toc-1', text: '安装', level: 2 },
  { id: 'toc-2', text: '配置选项', level: 3 },
]

// 要求：写一个函数，根据 id 查找目录项
// 如果找到返回该项，找不到返回 null
function findTocItem(id) {
  return tocItems.find(item => item.id === id) ?? null
}

console.log(findTocItem('toc-1'))
// 预期输出: { id: 'toc-1', text: '安装', level: 2 }

console.log(findTocItem('toc-999'))
// 预期输出: null
