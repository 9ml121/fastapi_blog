import {type ToolbarConfig} from '@/components/editor/types/editor.ts';

const floatingConfig: ToolbarConfig = {
  position: 'floating',
  items: [
    {
      id: 'bold',
      action: 'bold',         // ✅ SelectionRequiredActionType
      requiresSelection: true,
    },
    {
      id: 'heading1',
      action: 'heading1',     // 这个是什么类型？
      requiresSelection: false,
    },
  ]
}
