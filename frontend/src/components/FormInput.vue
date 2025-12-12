<script lang="ts" setup>
/**
 * 通用表单输入框组件
 * 1. v-model 支持双向绑定，任何表单都能用
 * 2. type	支持 text、password、email 等
 * 3. placeholder	自定义占位符文字
 * 4. slots	 自定义前缀/后缀图标
 */

// 1. 定义 Props
// defineProps<{
//   modelValue: string
// }>()

const props = withDefaults(
  defineProps<{
    type?: string
    placeholder?: string
  }>(),
  {
    type: 'text',
    placeholder: '请输入内容',
  },
)

// 2. 定义 Emits - 发射更新事件
// const emit = defineEmits<{
//   (e:'update:modelValue', value: string): void;
// }>();

// const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

// 3. 处理输入事件
// const handleInput = (event: Event) => {
//   const target = event.target as HTMLInputElement
//   emit('update:modelValue', target.value)
// }

const modelValue = defineModel<string>({ required: true })
</script>

<template>
  <div class="input-wrapper">
    <!-- 前缀插槽容器 -->
    <div v-if="$slots.prefix" class="input-prefix">
      <slot name="prefix"></slot>
    </div>

    <!-- 输入框 -->
    <!-- <input class="input-inner" :value="modelValue" @input="handleInput" /> -->
    <input
      class="input-inner"
      v-model="modelValue"
      :type="props.type"
      :placeholder="props.placeholder"
    />

    <!-- 后缀插槽容器 -->
    <div v-if="$slots.suffix" class="input-suffix">
      <slot name="suffix"></slot>
    </div>
  </div>
</template>

<style scoped>
.input-wrapper {
  display: flex; /* 水平排列 */
  align-items: center; /* 垂直居中 */
  width: 100%;
  height: 48px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

/* 聚焦状态：边框变蓝 + 浅蓝光晕 */
.input-wrapper:focus-within {
  border-color: #3b82f6; /* 聚焦时边框变蓝 */
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-inner {
  flex: 1; /* 占满剩余空间 */
  height: 100%;
  border: none;
  outline: none;
  padding: 0 16px;
}

.input-prefix {
  padding-left: 16px;
  display: flex;
  align-items: center;
  color: #6b7280;
}

.input-suffix {
  padding-right: 16px;
  display: flex;
  align-items: center;
  color: #6b7280;
}
</style>
