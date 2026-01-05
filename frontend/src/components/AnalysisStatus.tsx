import { AnalysisStatus as StatusType } from '../types'

interface AnalysisStatusProps {
  status: StatusType
  progress: number
}

const statusConfig: Record<StatusType, { label: string; color: string }> = {
  idle: { label: '待开始', color: 'gray' },
  uploading: { label: '上传中', color: 'blue' },
  ocr: { label: 'OCR识别中', color: 'blue' },
  rag: { label: 'RAG检索中', color: 'purple' },
  llm: { label: '大模型分析中', color: 'purple' },
  consistency: { label: '一致性检查中', color: 'yellow' },
  completed: { label: '分析完成', color: 'green' },
  error: { label: '分析失败', color: 'red' },
}

const stages: StatusType[] = ['uploading', 'ocr', 'rag', 'llm', 'consistency', 'completed']

export default function AnalysisStatus({ status, progress }: AnalysisStatusProps) {
  const currentStageIndex = stages.indexOf(status)
  const config = statusConfig[status]

  return (
    <div className="glass rounded-2xl shadow-elegant p-4 md:p-6 animate-fade-in-up">
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <h3 className="text-base md:text-lg font-semibold text-gray-800">分析状态</h3>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            config.color === 'blue' ? 'bg-blue-100 text-blue-700' :
            config.color === 'purple' ? 'bg-purple-100 text-purple-700' :
            config.color === 'yellow' ? 'bg-yellow-100 text-yellow-700' :
            config.color === 'green' ? 'bg-green-100 text-green-700' :
            config.color === 'red' ? 'bg-red-100 text-red-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            {config.label}
          </span>
        </div>

        {/* 进度条 */}
        <div className="space-y-2">
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                config.color === 'blue' ? 'bg-blue-500' :
                config.color === 'purple' ? 'bg-purple-500' :
                config.color === 'yellow' ? 'bg-yellow-500' :
                config.color === 'green' ? 'bg-green-500' :
                config.color === 'red' ? 'bg-red-500' :
                'bg-gray-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 text-right">{progress}%</p>
        </div>

        {/* 阶段列表 - 响应式：移动端单列，桌面端5列 */}
        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-2 mt-4">
          {stages.map((stage, index) => {
            const stageConfig = statusConfig[stage]
            const isActive = index === currentStageIndex
            const isCompleted = index < currentStageIndex
            const isPending = index > currentStageIndex

            return (
              <div
                key={stage}
                className={`text-center p-2 rounded-lg ${
                  isActive ? 'bg-purple-100 text-purple-700 font-semibold' :
                  isCompleted ? 'bg-green-100 text-green-700' :
                  'bg-gray-100 text-gray-400'
                }`}
              >
                <div className="text-xs font-medium">{stageConfig.label}</div>
                {isCompleted && (
                  <svg className="w-4 h-4 mx-auto mt-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

