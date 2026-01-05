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
          onFileSelect(file)
        } else {
          alert('文件大小不能超过10MB')
        }
      } else {
        alert('只支持JPG/PNG格式的图片')
      }
    }
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
    <div className="glass rounded-2xl shadow-elegant p-8 animate-fade-in-up">
      <div
        className="border-2 border-dashed border-purple-300 rounded-xl p-12 text-center cursor-pointer hover:border-purple-400 transition-colors"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/jpg"
          onChange={handleFileChange}
          className="hidden"
        />
        {uploadedFile ? (
          <div className="space-y-4">
            <div className="text-green-600">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-lg font-semibold text-gray-800">{uploadedFile.name}</p>
            <p className="text-sm text-gray-600">{(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</p>
            <button
              onClick={(e) => {
                e.stopPropagation()
                fileInputRef.current?.click()
              }}
              className="text-purple-600 hover:text-purple-700 text-sm font-medium"
            >
              重新选择文件
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-purple-400">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <div>
              <p className="text-lg font-semibold text-gray-800 mb-2">
                点击或拖拽文件到此处上传
              </p>
              <p className="text-sm text-gray-600">
                支持 JPG/PNG 格式，最大 10MB
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

