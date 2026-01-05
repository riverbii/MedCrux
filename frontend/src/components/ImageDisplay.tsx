import { useState } from 'react'

interface ImageDisplayProps {
  imageUrl: string | null
  ocrText?: string
}

export default function ImageDisplay({ imageUrl, ocrText }: ImageDisplayProps) {
  const [showOcrText, setShowOcrText] = useState(false)

  if (!imageUrl) return null

  return (
    <div className="glass rounded-2xl shadow-elegant p-4 md:p-6 animate-fade-in-up">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        {/* 原始图像 */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">原始图像</h3>
          <div className="bg-gray-100 rounded-lg p-2 md:p-4 flex items-center justify-center min-h-[200px] md:min-h-[300px]">
            <img
              src={imageUrl}
              alt="医学报告"
              className="max-w-full max-h-[300px] md:max-h-[500px] object-contain rounded-lg"
            />
          </div>
        </div>

        {/* OCR原文 */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">OCR原文</h3>
            <button
              onClick={() => setShowOcrText(!showOcrText)}
              className="text-sm text-purple-600 hover:text-purple-700 font-medium"
            >
              {showOcrText ? '收起' : '展开'}
            </button>
          </div>
          {showOcrText && ocrText && (
            <div className="bg-gray-50 rounded-lg p-4 max-h-[500px] overflow-y-auto">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
                {ocrText}
              </pre>
            </div>
          )}
          {!ocrText && (
            <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-500">
              暂无OCR文本
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

