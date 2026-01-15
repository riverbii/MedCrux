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
      <div className="detail-card rounded-3xl shadow-elegant p-8 card-hover w-full flex flex-col" style={{ position: 'relative', zIndex: 1 }}>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-gray-800">异常发现详情</h3>
          <div className={`px-3 py-1 rounded-full text-xs font-semibold ${riskColor === 'red' ? 'bg-red-100 text-red-700' :
              riskColor === 'yellow' ? 'bg-yellow-100 text-yellow-700' :
                'bg-green-100 text-green-700'
            }`}>
            {selectedFinding.birads ? `BI-RADS ${selectedFinding.birads}类` : `评估紧急程度：${riskText}`}
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
            {/* 大小信息 - 确保始终显示，即使size数据不完整 */}
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-4">
              <div className="text-xs text-gray-600 mb-1">大小</div>
              {selectedFinding.size && selectedFinding.size.length && selectedFinding.size.width ? (
                <div className="text-sm font-semibold text-gray-800">
                  {selectedFinding.size.length}×{selectedFinding.size.width}
                  {selectedFinding.size.depth !== undefined && selectedFinding.size.depth > 0 ? `×${selectedFinding.size.depth}` : ''} cm
                </div>
              ) : (
                <div className="text-sm text-gray-500">未提供大小信息</div>
              )}
            </div>
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

          {/* 风险征兆区域 - BL-010新增 */}
          <div className="mt-6 relative z-10" style={{ overflow: 'visible' }}>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xl">⚠️</span>
              <h4 className="text-lg font-semibold text-gray-800">风险征兆</h4>
              <span className="text-xs text-gray-500">（基于形态学特征识别）</span>
            </div>

            {selectedFinding.riskSigns && selectedFinding.riskSigns.length > 0 ? (
              <div className="space-y-3 relative" style={{ overflow: 'visible' }}>
                {selectedFinding.riskSigns.map((riskSign, index) => (
                  <div key={index} className={`rounded-xl p-4 ${riskSign.evidenceLevel === 'strong'
                      ? 'bg-blue-50 border-2 border-blue-300'
                      : 'bg-yellow-50 border-2 border-yellow-300'
                    }`}>
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xl">
                        {riskSign.evidenceLevel === 'strong' ? '🔴' : '🟡'}
                      </span>
                      <span className="font-semibold text-gray-800">{riskSign.sign}</span>
                    </div>

                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm">{riskSign.evidenceLevel === 'strong' ? '📚' : '📋'}</span>
                      <span className="text-sm text-gray-600">证据来源：</span>
                      <span className="text-sm font-medium text-gray-800">{riskSign.evidenceSource}</span>
                    </div>

                    <div className="flex items-center gap-2 mb-3">
                      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold ${riskSign.evidenceLevel === 'strong'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-yellow-100 text-yellow-700'
                        }`}>
                        <span>{riskSign.evidenceLevel === 'strong' ? '✅' : '⚠️'}</span>
                        <span>{riskSign.evidenceLevel === 'strong' ? '强证据' : '弱证据（仅供参考）'}</span>
                      </span>
                    </div>

                    <div className="pt-3 border-t border-gray-200">
                      <div className="flex items-start gap-2">
                        <span>💡</span>
                        <span className="text-sm text-gray-700">建议：{riskSign.suggestion}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-center">
                <div className="text-sm text-gray-600">当前异常发现未识别到风险征兆</div>
              </div>
            )}
          </div>
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
                className={`w-full text-left p-4 rounded-2xl transition-all nodule-btn ${isSelected
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
                    {finding.size.length}×{finding.size.width}
                    {finding.size.depth > 0 ? `×${finding.size.depth}` : ''} cm
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
