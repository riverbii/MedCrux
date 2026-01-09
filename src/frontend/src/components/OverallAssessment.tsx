import { OverallAssessment as OverallAssessmentType } from '../types'

interface OverallAssessmentProps {
  assessment: OverallAssessmentType
}

export default function OverallAssessment({ assessment }: OverallAssessmentProps) {
  // 卡片1：原报告结论摘要
  const originalReport = assessment.originalReport
  const factualSummary = assessment.originalReport?.factualSummary
  const conclusion = assessment.originalReport?.conclusion

  // 卡片2：一致性校验结果（原有：形态学特征一致性检查）
  const consistencyCheck = assessment.consistencyCheck

  // 卡片2.5：一致性校验结果（BL-009新增：报告分类结果和AI分类结果的一致性）
  const consistencyCheckNew = assessment.consistencyCheckNew

  // 卡片3：评估紧急程度（BL-009新增）
  const assessmentUrgency = assessment.assessmentUrgency

  // 卡片4：风险评估（原有：基于一致性校验的风险评估）
  const consistencyBasedRisk = assessment.consistencyBasedRisk

  return (
    <div className="detail-card rounded-3xl shadow-elegant p-8 card-hover">
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

        {/* 卡片2：一致性校验结果（核心，重点展示） */}
        {consistencyCheck && (
          <div>
            <div className="text-sm font-semibold text-gray-600 mb-3">一致性校验结果</div>
            <div
              className={`rounded-xl p-6 text-white ${
                consistencyCheck.status === 'has_inconsistency'
                  ? 'bg-gradient-to-r from-yellow-500 to-orange-500'
                  : 'bg-gradient-to-r from-green-500 to-green-600'
              }`}
            >
              <div className="flex items-center space-x-2 mb-3">
                <span className="text-2xl">
                  {consistencyCheck.status === 'has_inconsistency' ? '⚠️' : '✅'}
                </span>
                <div className="text-xl font-bold">
                  {consistencyCheck.status === 'has_inconsistency' ? '发现不一致' : '全部一致'}
                </div>
              </div>
              <div className="text-sm opacity-90 mb-4">
                一致性统计：<strong>
                  {consistencyCheck.consistentCount}个一致，{consistencyCheck.inconsistentCount}个不一致
                </strong>
              </div>
              {(consistencyCheck.inconsistentDetails && consistencyCheck.inconsistentDetails.length > 0) ||
              (consistencyCheck.consistentDetails && consistencyCheck.consistentDetails.length > 0) ? (
                <div className="bg-white/20 rounded-lg p-4 space-y-3">
                  {consistencyCheck.inconsistentDetails && consistencyCheck.inconsistentDetails.length > 0 && (
                    <div className="border-b border-white/30 pb-2">
                      <div className="text-sm font-semibold mb-1">⚠️ 不一致详情：</div>
                      {consistencyCheck.inconsistentDetails.map((detail, index) => (
                        <div key={index} className="text-xs opacity-90 mb-1">
                          <strong>{detail.findingName}：</strong>原报告BI-RADS {detail.originalBirads}类，{detail.reasons.join('；')}
                        </div>
                      ))}
                    </div>
                  )}
                  {consistencyCheck.consistentDetails && consistencyCheck.consistentDetails.length > 0 && (
                    <div>
                      <div className="text-sm font-semibold mb-1">✅ 一致详情：</div>
                      {consistencyCheck.consistentDetails.map((detail, index) => (
                        <div key={index} className="text-xs opacity-90 mb-1">
                          <strong>{detail.findingName}：</strong>原报告BI-RADS {detail.originalBirads}类，与形态学特征描述一致。
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          </div>
        )}

        {/* 卡片2.5：一致性校验结果（BL-009新增：报告分类结果和AI分类结果的一致性） */}
        {consistencyCheckNew && (
          <div>
            <div className="text-sm font-semibold text-gray-600 mb-3">一致性校验结果（报告分类结果和AI分类结果的一致性）</div>
            <div
              className={`rounded-xl p-6 text-white ${
                consistencyCheckNew.consistent
                  ? 'bg-gradient-to-r from-green-500 to-green-600'
                  : 'bg-gradient-to-r from-yellow-500 to-orange-500'
              }`}
            >
              <div className="flex items-center space-x-2 mb-3">
                <span className="text-2xl">
                  {consistencyCheckNew.consistent ? '✅' : '⚠️'}
                </span>
                <div className="text-xl font-bold">
                  {consistencyCheckNew.consistent ? '分类结果一致' : '分类结果不一致'}
                </div>
              </div>
              <div className="text-sm opacity-90 mb-4">
                {consistencyCheckNew.description}
              </div>
              <div className="bg-white/20 rounded-lg p-4 space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs font-semibold mb-1">报告BI-RADS分类集合：</div>
                    <div className="text-sm">
                      {consistencyCheckNew.reportBiradsSet.length > 0
                        ? `{${consistencyCheckNew.reportBiradsSet.sort().join(', ')}}`
                        : '无'}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold mb-1">AI BI-RADS分类集合：</div>
                    <div className="text-sm">
                      {consistencyCheckNew.aiBiradsSet.length > 0
                        ? `{${consistencyCheckNew.aiBiradsSet.sort().join(', ')}}`
                        : '无'}
                    </div>
                  </div>
                </div>
                {(consistencyCheckNew.missingInAi.length > 0 || consistencyCheckNew.extraInAi.length > 0) && (
                  <div className="border-t border-white/30 pt-3 space-y-2">
                    {consistencyCheckNew.missingInAi.length > 0 && (
                      <div>
                        <div className="text-xs font-semibold mb-1">AI缺少的分类：</div>
                        <div className="text-sm">
                          {consistencyCheckNew.missingInAi.sort().join(', ')}
                        </div>
                      </div>
                    )}
                    {consistencyCheckNew.extraInAi.length > 0 && (
                      <div>
                        <div className="text-xs font-semibold mb-1">AI额外的分类：</div>
                        <div className="text-sm">
                          {consistencyCheckNew.extraInAi.sort().join(', ')}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 卡片3：评估紧急程度（BL-009新增） */}
        {assessmentUrgency && (
          <div>
            <div className="text-sm font-semibold text-gray-600 mb-3">
              评估紧急程度
              <span className="text-xs text-gray-500 ml-2 font-normal">（当医生给出了更低的风险评级，而患者实际的风险评级更高）</span>
            </div>
            <div
              className={`rounded-xl p-6 text-white ${
                assessmentUrgency.urgencyLevel === 'High'
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
              <div className="bg-white/20 rounded-lg p-4 mt-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-xs font-semibold mb-1 opacity-75">医生最高BI-RADS分类：</div>
                    <div className="text-lg font-bold">{assessmentUrgency.doctorHighestBirads}类</div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold mb-1 opacity-75">AI最高BI-RADS分类：</div>
                    <div className="text-lg font-bold">{assessmentUrgency.llmHighestBirads}类</div>
                  </div>
                </div>
              </div>
              <div className="text-xs opacity-75 border-t border-white/30 pt-3 mt-3">
                这是基于报告文本的提示，不是医疗诊断。所有分析结果仅供参考，不能替代专业医生的诊断和治疗建议。
              </div>
            </div>
          </div>
        )}

        {/* 卡片4：风险评估（原有：基于一致性校验的风险评估） */}
        {consistencyBasedRisk && (
          <div>
            <div className="text-sm font-semibold text-gray-600 mb-3">
              风险评估
              <span className="text-xs text-gray-500 ml-2 font-normal">（基于报告描述的特征，提示需要进一步评估的紧急程度）</span>
            </div>
            <div
              className={`rounded-xl p-6 text-white ${
                consistencyBasedRisk.level === 'High'
                  ? 'bg-gradient-to-r from-red-500 to-red-600'
                  : consistencyBasedRisk.level === 'Medium'
                  ? 'bg-gradient-to-r from-yellow-500 to-yellow-600'
                  : 'bg-gradient-to-r from-green-500 to-green-600'
              }`}
            >
              <div className="text-2xl font-bold mb-2">
                评估紧急程度：{consistencyBasedRisk.level === 'High' ? 'High' : consistencyBasedRisk.level === 'Medium' ? 'Medium' : 'Low'}
              </div>
              <div className="text-sm opacity-90 mb-3">{consistencyBasedRisk.description}</div>
              <div className="text-xs opacity-75 border-t border-white/30 pt-3 mt-3">
                这是基于报告文本的提示，不是医疗诊断。所有分析结果仅供参考，不能替代专业医生的诊断和治疗建议。
              </div>
            </div>
          </div>
        )}

        {/* 卡片5：综合建议 */}
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
