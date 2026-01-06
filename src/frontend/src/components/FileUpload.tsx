import { useRef } from 'react'

interface FileUploadProps {
  onFileSelect: (file: File) => void
  uploadedFile: File | null
}

export default function FileUpload({ onFileSelect, uploadedFile }: FileUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.type === 'image/jpeg' || file.type === 'image/png' || file.type === 'image/jpg') {
        if (file.size <= 10 * 1024 * 1024) {
          // 立即调用onFileSelect，确保文件被处理
          onFileSelect(file)
        } else {
          alert('文件大小不能超过10MB')
        }
      } else {
        alert('只支持JPG/PNG格式的图片')
      }
    }
    // 重置input的value，确保可以重复选择同一个文件
    // 必须在onChange中重置，而不是在onClick中
    setTimeout(() => {
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }, 0)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) {
      if (file.type === 'image/jpeg' || file.type === 'image/png' || file.type === 'image/jpg') {
        if (file.size <= 10 * 1024 * 1024) {
          onFileSelect(file)
        } else {
          alert('文件大小不能超过10MB')
        }
      } else {
        alert('只支持JPG/PNG格式的图片')
      }
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  return (
    <div className="relative group">
      {/* 文件上传区域 - 按照layout v2原型样式 */}
      <div
        className="bg-gradient-to-br from-gray-100 to-gray-200 rounded-2xl p-8 min-h-[400px] flex items-center justify-center overflow-hidden border-2 border-dashed border-gray-300 hover:border-indigo-400 transition-colors cursor-pointer relative"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/jpg"
          onChange={handleFileChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
        />
        {uploadedFile ? (
          <div className="text-center">
            <div className="text-green-600 mb-4">
              <svg className="w-24 h-24 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-gray-500 font-medium group-hover:text-indigo-600 transition-colors break-words">{uploadedFile.name}</p>
            <p className="text-sm text-gray-400 mt-2">{(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</p>
          </div>
        ) : (
          <div className="text-center">
            <svg className="w-24 h-24 mx-auto mb-4 text-gray-400 group-hover:text-indigo-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
            </svg>
            <p className="text-gray-500 font-medium group-hover:text-indigo-600 transition-colors">点击或拖拽上传医学影像报告</p>
            <p className="text-sm text-gray-400 mt-2">支持JPG、PNG格式，最大10MB</p>
            {/* 数据隐私提示 */}
            <p className="text-xs text-gray-400 mt-3">
              <button className="text-indigo-600 hover:text-indigo-700 underline">数据隐私说明</button>
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

