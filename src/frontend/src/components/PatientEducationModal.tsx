interface PatientEducationModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function PatientEducationModal({ isOpen, onClose }: PatientEducationModalProps) {
  if (!isOpen) return null

  const biradsInfo = [
    { class: '0', title: '不完整评估', desc: '需要进一步影像学检查才能完成评估', suggestion: '追加影像评估' },
    { class: '1', title: '阴性', desc: '无异常发现', suggestion: '常规筛查' },
    { class: '2', title: '良性', desc: '明确的良性发现', suggestion: '常规筛查' },
    { class: '3', title: '可能良性', desc: '可能为良性，恶性可能性>0%但≤2%', suggestion: '短期随访（通常6个月）' },
    { class: '4', title: '可疑异常', desc: '可疑异常，需要活检，恶性可能性>2%且<95%。可细分为4A（2%-10%）、4B（10%-50%）、4C（50%-95%）', suggestion: '建议活检' },
    { class: '5', title: '高度可疑恶性', desc: '高度怀疑恶性，恶性可能性≥95%', suggestion: '强烈建议活检' },
    { class: '6', title: '已证实恶性', desc: '已通过活检证实为恶性', suggestion: '治疗' },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose} />
      <div className="relative glass rounded-2xl shadow-elegant max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-800">BI-RADS 分级说明</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-6">
            {/* 介绍说明 - 按照layout v2原型 */}
            <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-xl">
              <p className="text-sm text-blue-700">
                <strong>BI-RADS</strong>（Breast Imaging Reporting and Data System）是由美国放射学会（ACR）制定的标准化乳腺影像报告系统。
                本系统用于标准化描述和评估乳腺影像检查结果。
              </p>
            </div>

            {/* BI-RADS分级说明 - 按照layout v2原型，使用网格布局和渐变背景卡片 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {biradsInfo.map((item) => (
                <div key={item.class} className="bg-gradient-to-br rounded-xl p-4 hover:shadow-md transition-shadow card-hover"
                  style={{
                    background: item.class === '0' ? 'linear-gradient(to bottom right, #f3f4f6, #e5e7eb)' :
                      item.class === '1' || item.class === '2' ? 'linear-gradient(to bottom right, #d1fae5, #a7f3d0)' :
                      item.class === '3' ? 'linear-gradient(to bottom right, #fef3c7, #fde68a)' :
                      item.class === '4' ? 'linear-gradient(to bottom right, #fed7aa, #fdba74)' :
                      item.class === '5' ? 'linear-gradient(to bottom right, #fee2e2, #fecaca)' :
                      'linear-gradient(to bottom right, #e9d5ff, #ddd6fe)'
                  }}
                >
                  <div className="flex items-start gap-4">
                    <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center font-bold text-white shadow-lg ${
                      item.class === '0' ? 'bg-gray-500' :
                      item.class === '1' || item.class === '2' ? 'bg-green-500' :
                      item.class === '3' ? 'bg-yellow-500' :
                      item.class === '4' ? 'bg-orange-500' :
                      item.class === '5' ? 'bg-red-500' :
                      'bg-purple-500'
                    }`}>
                      {item.class}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-800 mb-2">{item.title}</h3>
                      <p className="text-sm text-gray-600 mb-3">{item.desc}</p>
                      <div className="bg-white/60 rounded-lg px-3 py-2">
                        <p className="text-sm text-purple-600 font-medium">建议：{item.suggestion}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* 重要提示 - 按照layout v2原型 */}
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-xl">
              <p className="text-sm text-yellow-700">
                <strong>重要提示：</strong>BI-RADS 分级仅供参考，不能替代专业医生的诊断。如有任何疑问，请咨询专业医生。
              </p>
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
