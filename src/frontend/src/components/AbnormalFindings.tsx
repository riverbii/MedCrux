import { AbnormalFinding } from '../types'

interface AbnormalFindingsProps {
  findings: AbnormalFinding[]
  selectedId: string | null
  onSelect: (id: string) => void
  showDetails?: boolean
}

export default function AbnormalFindings({
  findings,
  selectedId,
  onSelect,
  showDetails = false,
}: AbnormalFindingsProps) {
  const selectedFinding = findings.find((f) => f.id === selectedId)

  if (showDetails) {
    // 显示详情
    if (!selectedFinding) {
    return (
      <div className="glass rounded-2xl shadow-elegant p-6 md:p-8 h-full flex items-center justify-center">
        <p className="text-gray-500 text-sm md:text-base">请选择一个异常发现查看详情</p>
      </div>
    )
  }

  return (
    <div className="glass rounded-2xl shadow-elegant p-4 md:p-6 h-full">
      <h3 className="text-lg md:text-xl font-bold text-gray-800 mb-4">异常发现详情</h3>
        <div className="space-y-4">
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">基本信息</h4>
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <p className="text-sm">
                <span className="font-medium">名称：</span>
                {selectedFinding.name}
              </p>
              <p className="text-sm">
                <span className="font-medium">位置：</span>
                {selectedFinding.location.breast === 'left' ? '左' : '右'}乳
                {selectedFinding.location.clockPosition}
                {selectedFinding.location.distanceFromNipple && `，距乳头${selectedFinding.location.distanceFromNipple}cm`}
              </p>
              {selectedFinding.size && (
                <p className="text-sm">
                  <span className="font-medium">大小：</span>
                  {selectedFinding.size.length} × {selectedFinding.size.width} × {selectedFinding.size.depth} cm
                </p>
              )}
              {selectedFinding.birads && (
                <p className="text-sm">
                  <span className="font-medium">BI-RADS：</span>
                  <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium ml-2">
                    {selectedFinding.birads}
                  </span>
                </p>
              )}
            </div>
          </div>

          {selectedFinding.morphology && (
            <div>
              <h4 className="font-semibold text-gray-700 mb-2">形态学特征</h4>
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                {selectedFinding.morphology.shape && (
                  <p className="text-sm">
                    <span className="font-medium">形状：</span>
                    {selectedFinding.morphology.shape}
                  </p>
                )}
                {selectedFinding.morphology.boundary && (
                  <p className="text-sm">
                    <span className="font-medium">边界：</span>
                    {selectedFinding.morphology.boundary}
                  </p>
                )}
                {selectedFinding.morphology.echo && (
                  <p className="text-sm">
                    <span className="font-medium">回声：</span>
                    {selectedFinding.morphology.echo}
                  </p>
                )}
                {selectedFinding.morphology.orientation && (
                  <p className="text-sm">
                    <span className="font-medium">方位：</span>
                    {selectedFinding.morphology.orientation}
                  </p>
                )}
              </div>
            </div>
          )}

          {selectedFinding.inconsistencyAlerts && selectedFinding.inconsistencyAlerts.length > 0 && (
            <div>
              <h4 className="font-semibold text-yellow-700 mb-2">不一致提醒</h4>
              <div className="bg-yellow-50 border-l-4 border-yellow-400 rounded-lg p-4">
                <ul className="space-y-1">
                  {selectedFinding.inconsistencyAlerts.map((alert, index) => (
                    <li key={index} className="text-sm text-yellow-700">
                      • {alert}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  // 显示列表
  return (
    <div className="glass rounded-2xl shadow-elegant p-4 md:p-6 h-full">
      <h3 className="text-lg md:text-xl font-bold text-gray-800 mb-4">异常发现列表</h3>
      <div className="space-y-2">
        {findings.length === 0 ? (
          <p className="text-gray-500 text-center py-8">暂无异常发现</p>
        ) : (
          findings.map((finding) => {
            const isSelected = finding.id === selectedId
            const riskColor =
              finding.risk === 'High' ? 'red' :
              finding.risk === 'Medium' ? 'yellow' :
              'green'

            return (
              <button
                key={finding.id}
                onClick={() => onSelect(finding.id)}
                className={`w-full text-left p-4 rounded-[20px] transition-all ${
                  isSelected
                    ? 'bg-blue-500 text-white border-2 border-blue-600 font-bold shadow-lg'
                    : 'bg-gray-50 hover:bg-gray-100 border border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className={`font-semibold ${isSelected ? 'text-white' : 'text-gray-800'}`}>
                      {finding.name}
                    </p>
                    <p className={`text-sm mt-1 ${isSelected ? 'text-blue-100' : 'text-gray-600'}`}>
                      {finding.location.breast === 'left' ? '左' : '右'}乳 {finding.location.clockPosition}
                    </p>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                    isSelected
                      ? 'bg-white text-blue-600'
                      : riskColor === 'red'
                      ? 'bg-red-100 text-red-700'
                      : riskColor === 'yellow'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-green-100 text-green-700'
                  }`}>
                    {finding.risk === 'High' ? '高风险' : finding.risk === 'Medium' ? '中风险' : '低风险'}
                  </div>
                </div>
              </button>
            )
          })
        )}
      </div>
    </div>
  )
}

