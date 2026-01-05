import { useState } from 'react'

interface ImageDisplayProps {
  imageUrl: string | null
  ocrText?: string
  onRemove?: () => void
}

export default function ImageDisplay({ imageUrl, ocrText, onRemove }: ImageDisplayProps) {
  const [showOcrText, setShowOcrText] = useState(false)

  if (!imageUrl) return null

  return (
    <div className="relative group">
      {/* 图片预览区域 */}
      <div className="relative rounded-2xl overflow-hidden bg-gray-900 min-h-[400px] flex items-center justify-center">
        <img
          src={imageUrl}
          alt="预览图像"
          className="w-full h-full object-contain"
        />
        {onRemove && (
          <button
            onClick={onRemove}
            className="absolute top-4 right-4 bg-white/90 hover:bg-white px-3 py-2 rounded-lg shadow-lg text-sm font-medium text-gray-700 transition-all"
          >
            ✕ 移除
          </button>
        )}
        
        {/* OCR展开按钮 - 悬浮显示（分析后显示） */}
        {ocrText && (
          <button
            onClick={() => setShowOcrText(!showOcrText)}
            className="absolute bottom-4 right-4 bg-white/90 hover:bg-white px-4 py-2 rounded-xl shadow-lg text-sm font-medium text-gray-700 transition-all"
          >
            📄 查看OCR原文
          </button>
        )}
      </div>
      
      {/* OCR原文展示区域（可展开/收起） */}
      {ocrText && showOcrText && (
        <div className="mt-4 glass rounded-2xl shadow-elegant p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-semibold text-gray-800">OCR识别原文</h4>
            <button
              onClick={() => setShowOcrText(false)}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              收起
            </button>
          </div>
          <div className="bg-gray-50 rounded-xl p-4 max-h-64 overflow-y-auto">
            <pre className="text-xs text-gray-700 font-mono whitespace-pre-wrap">{ocrText}</pre>
          </div>
        </div>
      )}
    </div>
  )
}

