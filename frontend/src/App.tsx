import { useState, useEffect } from 'react'
import Navbar from './components/Navbar'
import FileUpload from './components/FileUpload'
import AnalysisStatus from './components/AnalysisStatus'
import AbnormalFindings from './components/AbnormalFindings'
import OverallAssessment from './components/OverallAssessment'
import Disclaimer from './components/Disclaimer'
import Footer from './components/Footer'
import { AnalysisResult, AnalysisStatus as StatusType } from './types'
import { analyzeReport, getHealth } from './services/api'

function App() {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [analysisStatus, setAnalysisStatus] = useState<StatusType>('idle')
  const [analysisProgress, setAnalysisProgress] = useState<number>(0)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  // 检查后端健康状态
  useEffect(() => {
    getHealth().catch(() => {
      console.warn('无法连接到后端服务')
    })
  }, [])

  // 开始分析（直接上传文件并分析）
  const handleAnalyze = async () => {
    if (!uploadedFile) return

    setIsAnalyzing(true)
    setAnalysisStatus('uploading')
    setAnalysisProgress(10)

    try {
      // 模拟进度更新
      const progressInterval = setInterval(() => {
        setAnalysisProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return prev
          }
          return prev + 5
        })
      }, 1000)

      // 更新状态
      setTimeout(() => {
        setAnalysisStatus('ocr')
        setAnalysisProgress(30)
      }, 2000)
      setTimeout(() => {
        setAnalysisStatus('rag')
        setAnalysisProgress(50)
      }, 4000)
      setTimeout(() => {
        setAnalysisStatus('llm')
        setAnalysisProgress(70)
      }, 6000)
      setTimeout(() => {
        setAnalysisStatus('consistency')
        setAnalysisProgress(85)
      }, 8000)

      const result = await analyzeReport(uploadedFile)
      clearInterval(progressInterval)
      setAnalysisResult(result)
      setAnalysisStatus('completed')
      setAnalysisProgress(100)

      // 自动选择第一个异常发现
      if (result.findings.length > 0) {
        setSelectedFindingId(result.findings[0].id)
      }
    } catch (error) {
      console.error('分析失败:', error)
      setAnalysisStatus('error')
      alert('分析失败，请重试')
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Disclaimer />
      <Navbar />
      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl">
        <div className="space-y-6">
          {/* 文件上传区域 */}
          <FileUpload
            onFileSelect={setUploadedFile}
            uploadedFile={uploadedFile}
          />

          {/* 分析按钮 */}
          {uploadedFile && !analysisResult && (
            <div className="flex justify-center">
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="analyze-btn px-8 py-4 text-white font-semibold rounded-xl text-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAnalyzing ? '分析中...' : '开始分析 🚀'}
              </button>
            </div>
          )}

          {/* 分析状态 */}
          {analysisStatus !== 'idle' && analysisStatus !== 'error' && (
            <AnalysisStatus
              status={analysisStatus}
              progress={analysisProgress}
            />
          )}

          {/* 异常发现和整体评估 */}
          {analysisResult && (
            <div className="grid grid-cols-12 gap-6">
              <div className="col-span-12 lg:col-span-3">
                <AbnormalFindings
                  findings={analysisResult.findings}
                  selectedId={selectedFindingId}
                  onSelect={setSelectedFindingId}
                />
              </div>
              <div className="col-span-12 lg:col-span-9">
                <AbnormalFindings
                  findings={analysisResult.findings}
                  selectedId={selectedFindingId}
                  onSelect={setSelectedFindingId}
                  showDetails={true}
                />
              </div>
              <div className="col-span-12">
                <OverallAssessment assessment={analysisResult.overallAssessment} />
              </div>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  )
}

export default App

