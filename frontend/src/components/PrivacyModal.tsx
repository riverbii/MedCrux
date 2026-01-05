interface PrivacyModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function PrivacyModal({ isOpen, onClose }: PrivacyModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose} />
      <div className="relative glass rounded-2xl shadow-elegant max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-800">数据隐私政策</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-4 text-gray-700">
            <section>
              <h3 className="font-semibold text-gray-800 mb-2">数据处理</h3>
              <p className="text-sm">
                所有数据处理在本地完成，不会上传到服务器。您的医学影像报告图片和识别结果仅存储在您的设备本地。
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-gray-800 mb-2">数据安全</h3>
              <p className="text-sm">
                我们采用行业标准的安全措施来保护您的数据。所有数据传输均使用加密连接。
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-gray-800 mb-2">数据使用</h3>
              <p className="text-sm">
                我们不会收集、存储或分享您的个人健康信息。所有分析功能均在您的设备上本地执行。
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-gray-800 mb-2">第三方服务</h3>
              <p className="text-sm">
                本系统使用 DeepSeek API 进行 AI 分析。API 调用仅传输 OCR 识别的文本内容，不包含图片数据。
                请参考 DeepSeek 的隐私政策了解其数据处理方式。
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-gray-800 mb-2">联系我们</h3>
              <p className="text-sm">
                如有任何关于数据隐私的问题，请通过 GitHub Issues 联系我们。
              </p>
            </section>
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

