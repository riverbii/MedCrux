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

  const riskColor = selectedFinding.risk === 'High' ? 'red' : selectedFinding.risk === 'Medium' ? 'yellow' : 'green'
  const riskText = selectedFinding.risk === 'High' ? '高' : selectedFinding.risk === 'Medium' ? '中' : '低'

  return (
    <div className="detail-card rounded-3xl shadow-elegant p-8 card-hover w-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-800">异常发现详情</h3>
        <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
          riskColor === 'red' ? 'bg-red-100 text-red-700' :
          riskColor === 'yellow' ? 'bg-yellow-100 text-yellow-700' :
          'bg-green-100 text-green-700'
        }`}>
          可疑程度：{riskText}
        </div>
      </div>

      <div className="space-y-4">
        {/* 关键信息网格 - 按照layout v2原型 */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4">
            <div className="text-xs text-gray-600 mb-1">位置</div>
            <div className="text-sm font-semibold text-gray-800">
              {selectedFinding.location.breast === 'left' ? '左' : '右'}乳 {selectedFinding.location.clockPosition}
              {selectedFinding.location.distanceFromNipple && `，距乳头${selectedFinding.location.distanceFromNipple}cm`}
            </div>
          </div>
          {selectedFinding.size && (
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-4">
              <div className="text-xs text-gray-600 mb-1">大小</div>
              <div className="text-sm font-semibold text-gray-800">
                {selectedFinding.size.length}×{selectedFinding.size.width}
                {selectedFinding.size.depth > 0 ? `×${selectedFinding.size.depth}` : ''} cm
              </div>
            </div>
          )}
          {selectedFinding.morphology?.shape && (
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4">
              <div className="text-xs text-gray-600 mb-1">形状</div>
              <div className="text-sm font-semibold text-gray-800">{selectedFinding.morphology.shape}</div>
            </div>
          )}
          {selectedFinding.birads && (
            <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-xl p-4">
              <div className="text-xs text-gray-600 mb-1">AI评估 BI-RADS</div>
              <div className="text-sm font-semibold text-red-600">{selectedFinding.birads}类</div>
              <div className="text-xs text-gray-500 mt-1">（仅供参考）</div>
            </div>
          )}
        </div>

        {/* 不一致预警 - 按照layout v2原型 */}
        {selectedFinding.inconsistencyAlerts && selectedFinding.inconsistencyAlerts.length > 0 && (
          <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <span className="text-xl">⚠️</span>
              <div>
                <div className="text-sm font-semibold text-red-800 mb-1">检测到不一致</div>
                {selectedFinding.inconsistencyAlerts.map((alert, index) => (
                  <div key={index} className="text-xs text-red-700">{alert}</div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
  }

  // 显示列表
  return (
    <div className="glass rounded-3xl shadow-elegant p-6 w-full flex flex-col">
      <h3 className="text-lg font-bold text-gray-800 mb-4">异常发现列表</h3>
      <div className="space-y-3">
        {findings.length === 0 ? (
          <p className="text-gray-500 text-center py-8">暂无异常发现</p>
        ) : (
          findings.map((finding) => {
            const isSelected = finding.id === selectedId

            return (
              <button
                key={finding.id}
                onClick={() => onSelect(finding.id)}
                className={`w-full text-left p-4 rounded-2xl transition-all nodule-btn ${
                  isSelected
                    ? 'selected bg-gradient-to-br from-indigo-500 to-purple-600 text-white border-2 border-transparent shadow-lg'
                    : 'bg-white/50 hover:bg-white/70 border-2 border-white/30'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className={`font-semibold ${isSelected ? 'text-white' : 'text-gray-800'}`}>
                    {finding.name}
                  </span>
                  <span className="text-2xl">
                    {finding.risk === 'High' ? '🔴' : finding.risk === 'Medium' ? '🟡' : '🟢'}
                  </span>
                </div>
                <div className={`text-xs ${isSelected ? 'text-white/80' : 'text-gray-600'}`}>
                  {finding.birads && <span>🤖 BI-RADS {finding.birads}类 · </span>}
                  {finding.location.breast === 'left' ? '左' : '右'}乳 {finding.location.clockPosition}
                </div>
                {finding.size && (
                  <div className={`mt-2 text-xs ${isSelected ? 'text-white/70' : 'text-gray-500'}`}>
                    {finding.size.length}×{finding.size.width}×{finding.size.depth} cm
                  </div>
                )}
              </button>
            )
          })
        )}
      </div>
    </div>
  )
}
