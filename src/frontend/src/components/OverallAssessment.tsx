import { OverallAssessment as OverallAssessmentType } from '../types'

interface OverallAssessmentProps {
  assessment: OverallAssessmentType
}

export default function OverallAssessment({ assessment }: OverallAssessmentProps) {
  // 卡片1：原报告结论摘要
  const originalReport = assessment.originalReport
  const factualSummary = assessment.originalReport?.factualSummary
  const conclusion = assessment.originalReport?.conclusion

  // 卡片2：评估紧急程度（BL-009新增，包含一致性校验结果）
  const assessmentUrgency = assessment.assessmentUrgency

  // 注意：consistencyCheck（原有的形态学特征一致性检查）仅在综合建议中使用，不再单独显示卡片
  const consistencyCheck = assessment.consistencyCheck

  return (
    <div className="detail-card rounded-3xl shadow-elegant p-8 card-hover" style={{ position: 'relative', zIndex: 0 }}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-800">整体评估</h3>
        {originalReport?.highestBirads && (
          <div className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold">
            原报告：BI-RADS {originalReport.highestBirads}类
          </div>
        )}
      </div>

      <div className="space-y-6">
        {/* 卡片1：原报告结论摘要 */}
        {originalReport && (
          <div>
            <div className="text-sm font-semibold text-gray-600 mb-3">原报告结论摘要</div>
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 space-y-3">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-blue-700">原报告最高BI-RADS分类：</span>
                {originalReport.highestBirads ? (
                  <>
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-semibold">
                      {originalReport.highestBirads}类
                    </span>
                    <span className="text-xs text-gray-600">（从报告中提取）</span>
                  </>
                ) : (
                  <span className="text-xs text-gray-500">未提取到</span>
                )}
              </div>
              {originalReport.totalFindings !== undefined && (
                <div className="text-xs text-gray-600">
                  <span className="font-semibold">原报告异常发现数量：</span>
                  {originalReport.totalFindings}个
                </div>
              )}
              {(factualSummary || conclusion) && (
                <div className="border-t border-blue-200 pt-3 space-y-3">
                  {/* 事实性摘要 */}
                  {factualSummary?.findings && (
                    <div>
                      <div className="text-xs font-semibold text-gray-700 mb-2">事实性摘要：</div>
                      <div className="text-xs text-gray-700 leading-relaxed">
                        {factualSummary.findings}
                      </div>
                    </div>
                  )}
                  {/* 结论 */}
                  {(conclusion?.diagnosis || conclusion?.recommendation) && (
                    <div>
                      <div className="text-xs font-semibold text-gray-700 mb-2">结论：</div>
                      <div className="text-xs text-gray-700 leading-relaxed space-y-1">
                        {conclusion.diagnosis && (
                          <div>{conclusion.diagnosis}</div>
                        )}
                        {conclusion.recommendation && (
                          <div>{conclusion.recommendation}</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 注意：一致性校验结果已集成在"评估紧急程度"卡片中，不再单独显示 */}

        {/* 卡片2：评估紧急程度（BL-009新增，包含一致性校验结果） */}
        {assessmentUrgency && (
          <div>
            <div className="text-sm font-semibold text-gray-600 mb-3">
              评估紧急程度
              <span className="text-xs text-gray-500 ml-2 font-normal">（当AI判断的风险评级高于医生判断，或识别到需要关注的风险征兆时）</span>
            </div>
            <div
              className={`rounded-xl p-6 text-white ${assessmentUrgency.urgencyLevel === 'High'
                ? 'bg-gradient-to-r from-red-500 to-red-600'
                : assessmentUrgency.urgencyLevel === 'Medium'
                  ? 'bg-gradient-to-r from-yellow-500 to-orange-500'
                  : 'bg-gradient-to-r from-green-500 to-green-600'
                }`}
            >
              <div className="text-2xl font-bold mb-2">
                评估紧急程度：{assessmentUrgency.urgencyLevel}
              </div>
              <div className="text-sm opacity-90 mb-3">{assessmentUrgency.reason}</div>
              <div className="bg-white/20 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-4 text-sm">
                  {/* 医生最高BI-RADS分类 */}
                  <div className="flex-1">
                    <div className="text-xs font-semibold mb-1 opacity-75">医生最高BI-RADS分类：</div>
                    <div className="text-xl font-bold">{assessmentUrgency.doctorHighestBirads}类</div>
                  </div>
                  {/* AI最高BI-RADS分类 */}
                  <div className="flex-1">
                    <div className="text-xs font-semibold mb-1 opacity-75">AI最高BI-RADS分类：</div>
                    <div className="text-xl font-bold">{assessmentUrgency.llmHighestBirads}类</div>
                  </div>
                  {/* 一致性检查结果 */}
                  {assessment.consistencyCheckNew && (
                    <div className="flex-shrink-0">
                      <div className="text-xs font-semibold mb-1 opacity-75">一致性检查：</div>
                      <div className={`bg-white/40 border rounded-lg px-4 py-2 flex items-center gap-2 ${assessment.consistencyCheckNew.consistent
                        ? 'border-green-500/60 text-green-800'
                        : 'border-yellow-500/60 text-yellow-800'
                        }`}>
                        <span className={assessment.consistencyCheckNew.consistent ? 'text-green-700' : 'text-yellow-700'}>
                          {assessment.consistencyCheckNew.consistent ? '✅' : '⚠️'}
                        </span>
                        <span className="text-sm font-semibold">
                          {assessment.consistencyCheckNew.consistent ? '一致' : '不一致'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* 风险征兆汇总 - BL-010新增 */}
              {assessment.riskSignsSummary &&
                (assessment.riskSignsSummary.strongEvidence.length > 0 || assessment.riskSignsSummary.weakEvidence.length > 0) && (
                  <div className="bg-white/20 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-lg">⚠️</span>
                      <span className="text-sm font-semibold">风险征兆汇总</span>
                      <span className="text-xs opacity-75">
                        （共 {assessment.riskSignsSummary.strongEvidence.length + assessment.riskSignsSummary.weakEvidence.length} 个）
                      </span>
                    </div>

                    {/* 风险征兆列表 */}
                    <div className="space-y-2">
                      {assessment.riskSignsSummary.strongEvidence.map((riskSign, index) => (
                        <div key={`strong-${index}`} className="bg-white/10 rounded-lg p-2 text-xs flex items-center gap-2">
                          <span>🔴</span>
                          <span className="flex-1">{riskSign.sign}</span>
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-white/40 border border-orange-600/70 text-orange-900">
                            <span>强证据</span>
                          </span>
                        </div>
                      ))}
                      {assessment.riskSignsSummary.weakEvidence.map((riskSign, index) => (
                        <div key={`weak-${index}`} className="bg-white/10 rounded-lg p-2 text-xs flex items-center gap-2">
                          <span>🟡</span>
                          <span className="flex-1">{riskSign.sign}</span>
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-white/30 border border-yellow-500/60 text-yellow-900">
                            <span>弱证据</span>
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              <div className="text-xs opacity-75 border-t border-white/30 pt-3 mt-4">
                这是基于报告文本的提示，不是医疗诊断。所有分析结果仅供参考，不能替代专业医生的诊断和治疗建议。
              </div>
            </div>
          </div>
        )}

        {/* 卡片3：综合建议 */}
        {(assessment.advice || assessment.suggestions?.length > 0) && (
          <div>
            <div className="text-sm font-semibold text-gray-600 mb-3">综合建议</div>
            <div className="bg-green-50 border border-green-200 rounded-xl p-4">
              <ul className="text-sm text-gray-700 leading-relaxed space-y-2">
                {consistencyCheck?.inconsistentDetails && consistencyCheck.inconsistentDetails.length > 0 && (
                  <li>
                    • 对不一致的异常发现，<strong>建议咨询专业医生确认BI-RADS分类</strong>，原报告分类可能不准确。这是基于报告文本的提示，不是医疗诊断。
                  </li>
                )}
                {consistencyCheck?.status === 'has_inconsistency' && (
                  <li>
                    • <strong>建议咨询专业医生</strong>，确认正确的BI-RADS分类，特别是对不一致的异常发现。
                  </li>
                )}
                {assessment.advice && (
                  <li>• {assessment.advice}</li>
                )}
                {assessment.suggestions?.map((suggestion, index) => (
                  <li key={index}>• {suggestion}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
