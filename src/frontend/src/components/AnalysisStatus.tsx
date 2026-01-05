import { AnalysisStatus as StatusType } from '../types'

interface AnalysisStatusProps {
  status: StatusType
  progress: number
}

// 按照layout v2原型的6个阶段
const stages = [
  { id: 'ready', label: '准备就绪', statusKey: 'idle' as StatusType },
  { id: 'ocr', label: 'OCR识别中...', statusKey: 'ocr' as StatusType },
  { id: 'rag', label: '知识库检索中...', statusKey: 'rag' as StatusType },
  { id: 'llm', label: '大模型分析中...', statusKey: 'llm' as StatusType },
  { id: 'check', label: '一致性检查中...', statusKey: 'consistency' as StatusType },
  { id: 'complete', label: '分析完成', statusKey: 'completed' as StatusType },
]

export default function AnalysisStatus({ status, progress }: AnalysisStatusProps) {
  // 确定当前阶段
  const getCurrentStageIndex = () => {
    if (status === 'idle') return 0
    if (status === 'ocr') return 1
    if (status === 'rag') return 2
    if (status === 'llm') return 3
    if (status === 'consistency') return 4
    if (status === 'completed') return 5
    return 0
  }

  const currentStageIndex = getCurrentStageIndex()

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        {stages.map((stage, index) => {
          const isActive = index === currentStageIndex
          const isCompleted = index < currentStageIndex
          const isPending = index > currentStageIndex

          return (
            <div
              key={stage.id}
              className={`flex items-center space-x-3 p-3 rounded-xl border ${
                isActive
                  ? 'bg-indigo-50 border-indigo-200'
                  : isCompleted
                  ? 'bg-green-50 border-green-200'
                  : 'bg-gray-50 border-gray-200 opacity-50'
              }`}
            >
              <div
                className={`w-2 h-2 rounded-full ${
                  isActive
                    ? 'bg-indigo-500 animate-pulse'
                    : isCompleted
                    ? 'bg-green-500'
                    : 'bg-gray-300'
                }`}
              />
              <span
                className={`text-sm ${
                  isActive
                    ? 'text-gray-700'
                    : isCompleted
                    ? 'text-gray-700'
                    : 'text-gray-500'
                }`}
              >
                {stage.label}
              </span>
            </div>
          )
        })}
      </div>
      
      {/* 进度条 */}
      <div className="mt-4">
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className="bg-gradient-to-r from-indigo-500 to-purple-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-gray-500 text-center mt-2">
          {status === 'idle' ? '等待开始分析...' : stages[currentStageIndex]?.label || `${progress}%`}
        </p>
      </div>
    </div>
  )
}

