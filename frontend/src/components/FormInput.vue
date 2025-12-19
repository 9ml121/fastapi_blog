<script lang="ts" setup>
/**
 * 通用表单输入框组件
 * 1. v-model 支持双向绑定，任何表单都能用
 * 2. type	支持 text、password、email 等
 * 3. placeholder	自定义占位符文字
 * 4. slots	 自定义前缀/后缀图标
 */

// 禁用属性自动继承，手动通过 v-bind="$attrs" 绑定到 input 上
defineOptions({
  inheritAttrs: false,
})

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

const modelValue = defineModel<string>({ required: true })
</script>

<template>
  <div class="input-wrapper">
    <!-- 前缀插槽容器 -->
    <div v-if="$slots.prefix" class="input-prefix">
      <slot name="prefix"></slot>
    </div>

    <!-- 输入框 -->
    <input
      class="input-inner"
      v-bind="$attrs"
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
  display: flex;
  align-items: center;
  width: 100%;
  height: 45px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background-color: var(--color-bg-input);
  transition: all 0.3s ease;
}

/*子元素获得焦点时 ：边框变蓝 + 浅蓝光晕 */
.input-wrapper:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
  background-color: transparent;
}

.input-inner {
  flex: 1; /* 占满剩余空间 */
  height: 100%;
  border: none;
  outline: none;
  padding: 0.75rem 1rem;
  background-color: transparent; /* 关键：设为透明，让 wrapper 的背景色透出来 */
}

.input-prefix {
  padding-left: 1rem;
  display: flex;
  align-items: center;
  color: var(--color-text-secondary);
}

.input-suffix {
  padding-right: 1rem;
  display: flex;
  align-items: center;
  color: var(--color-text-secondary);
}
</style>
