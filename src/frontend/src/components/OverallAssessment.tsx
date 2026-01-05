import { OverallAssessment as OverallAssessmentType } from '../types'

interface OverallAssessmentProps {
  assessment: OverallAssessmentType
}

export default function OverallAssessment({ assessment }: OverallAssessmentProps) {
  const riskColors = {
    High: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-300', emoji: '🔴' },
    Medium: { bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-300', emoji: '🟡' },
    Low: { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-300', emoji: '🟢' },
  }

  const highestRisk = assessment.highestRisk || 'Low'
  const riskColor = riskColors[highestRisk]

  return (
    <div className="glass rounded-2xl shadow-elegant p-4 md:p-6">
      <h3 className="text-lg md:text-xl font-bold text-gray-800 mb-4">整体评估</h3>
      <div className="space-y-6">
        {/* 整体风险评估 */}
        <div>
          <h4 className="font-semibold text-gray-700 mb-3">📊 整体风险评估</h4>
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-gray-700">结节总数：</span>
              <span className="font-semibold text-gray-800">{assessment.totalNodules || 0}个</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">最高风险等级：</span>
              <span className={`font-semibold ${riskColor.text} flex items-center gap-2`}>
                <span>{riskColor.emoji}</span>
                <span>{highestRisk === 'High' ? '高' : highestRisk === 'Medium' ? '中' : '低'}</span>
              </span>
            </div>
            {assessment.riskDistribution && assessment.totalNodules && assessment.totalNodules > 1 && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="text-sm font-medium text-gray-700 mb-2">风险分布：</div>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  <div className="text-center">
                    <div className="text-green-600 font-semibold">{assessment.riskDistribution.Low}</div>
                    <div className="text-gray-600">低风险</div>
                  </div>
                  <div className="text-center">
                    <div className="text-yellow-600 font-semibold">{assessment.riskDistribution.Medium}</div>
                    <div className="text-gray-600">中风险</div>
                  </div>
                  <div className="text-center">
                    <div className="text-red-600 font-semibold">{assessment.riskDistribution.High}</div>
                    <div className="text-gray-600">高风险</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 不一致预警总结 */}
        {assessment.inconsistencyCount && assessment.inconsistencyCount > 0 && (
          <div>
            <h4 className="font-semibold text-gray-700 mb-3">⚠️ 不一致预警总结</h4>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-yellow-800 mb-2">
                检测到 <strong>{assessment.inconsistencyCount}个结节</strong> 存在描述与结论不一致的情况，建议重新评估或咨询专业医生。
              </p>
              {assessment.inconsistencySummary && assessment.inconsistencySummary.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {assessment.inconsistencySummary.map((item, index) => (
                    <li key={index} className="text-yellow-700 text-sm">• {item}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}

        {/* 事实摘要 */}
        {assessment.facts && assessment.facts.length > 0 && (
          <div>
            <h4 className="font-semibold text-gray-700 mb-3">📋 事实摘要</h4>
            <ul className="bg-gray-50 rounded-lg p-4 space-y-2">
              {assessment.facts.map((fact, index) => (
                <li key={index} className="text-gray-700 text-sm flex items-start">
                  <span className="text-blue-600 mr-2 font-bold">•</span>
                  <span>{fact}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* 综合建议 */}
        {(assessment.advice || (assessment.suggestions && assessment.suggestions.length > 0)) && (
          <div>
            <h4 className="font-semibold text-gray-700 mb-3">💡 MedCrux 建议</h4>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              {assessment.advice ? (
                <p className="text-blue-800">{assessment.advice}</p>
              ) : (
                <ul className="space-y-2">
                  {assessment.suggestions?.map((suggestion, index) => (
                    <li key={index} className="text-blue-800 text-sm flex items-start">
                      <span className="text-blue-600 mr-2">•</span>
                      <span>{suggestion}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}

        {/* BI-RADS分类 */}
        {assessment.birads && (
          <div>
            <h4 className="font-semibold text-gray-700 mb-3">📊 BI-RADS分类</h4>
            <div className="bg-purple-100 border border-purple-200 rounded-lg p-4">
              <span className="inline-block px-4 py-2 bg-purple-600 text-white rounded-lg font-semibold text-lg">
                BI-RADS {assessment.birads}类
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

