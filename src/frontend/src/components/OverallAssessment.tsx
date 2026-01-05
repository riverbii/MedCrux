import { OverallAssessment as OverallAssessmentType } from '../types'

interface OverallAssessmentProps {
  assessment: OverallAssessmentType
}

export default function OverallAssessment({ assessment }: OverallAssessmentProps) {
  return (
    <div className="glass rounded-2xl shadow-elegant p-4 md:p-6">
      <h3 className="text-lg md:text-xl font-bold text-gray-800 mb-4">整体评估</h3>
      <div className="space-y-6">
        {/* 摘要 */}
        <div>
          <h4 className="font-semibold text-gray-700 mb-2">摘要</h4>
          <p className="text-gray-700 bg-gray-50 rounded-lg p-4">{assessment.summary}</p>
        </div>

        {/* 事实摘要 */}
        {assessment.facts && assessment.facts.length > 0 && (
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">事实摘要</h4>
            <ul className="bg-gray-50 rounded-lg p-4 space-y-2">
              {assessment.facts.map((fact, index) => (
                <li key={index} className="text-gray-700 text-sm flex items-start">
                  <span className="text-purple-600 mr-2">•</span>
                  <span>{fact}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* 建议 */}
        {assessment.suggestions && assessment.suggestions.length > 0 && (
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">建议</h4>
            <ul className="bg-purple-50 rounded-lg p-4 space-y-2">
              {assessment.suggestions.map((suggestion, index) => (
                <li key={index} className="text-purple-700 text-sm flex items-start">
                  <span className="text-purple-600 mr-2">•</span>
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* BI-RADS分类 */}
        {assessment.birads && (
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">BI-RADS分类</h4>
            <div className="bg-purple-100 rounded-lg p-4">
              <span className="px-4 py-2 bg-purple-600 text-white rounded-lg font-semibold">
                {assessment.birads}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

