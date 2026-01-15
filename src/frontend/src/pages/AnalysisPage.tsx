import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import FileUpload from '../components/FileUpload'
import ImageDisplay from '../components/ImageDisplay'
import AnalysisStatus from '../components/AnalysisStatus'
import AbnormalFindings from '../components/AbnormalFindings'
import OverallAssessment from '../components/OverallAssessment'
import BreastDiagram from '../components/BreastDiagram'
import Disclaimer from '../components/Disclaimer'
import Footer from '../components/Footer'
import { AnalysisResult, AnalysisStatus as StatusType } from '../types'
import { analyzeReport, getHealth } from '../services/api'

export default function AnalysisPage() {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [ocrText, setOcrText] = useState<string>('')
  const [analysisStatus, setAnalysisStatus] = useState<StatusType>('idle')
  const [analysisProgress, setAnalysisProgress] = useState<number>(0)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  // 当文件上传时，创建预览URL
  useEffect(() => {
    if (uploadedFile) {
      const url = URL.createObjectURL(uploadedFile)
      setImageUrl(url)
      return () => URL.revokeObjectURL(url)
    } else {
      setImageUrl(null)
    }
  }, [uploadedFile])

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

      const response = await analyzeReport(uploadedFile)
      clearInterval(progressInterval)
      setAnalysisResult(response.result)
      setOcrText(response.ocrText || '')
      setAnalysisStatus('completed')
      setAnalysisProgress(100)

      // 自动选择第一个异常发现
      if (response.result.findings.length > 0) {
        setSelectedFindingId(response.result.findings[0].id)
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
      <main className="flex-1 pt-24 pb-12">
        <div className="container mx-auto px-8">
          {/* 顶部区域：图像和分析 - 按照layout v2原型 */}
          <div className="mb-8 animate-fade-in-up">
            <div className="glass rounded-3xl shadow-elegant p-8">
              <div className="grid grid-cols-12 gap-6">
                {/* 左侧：图像展示区 - 占据7列 */}
                <div className="col-span-12 lg:col-span-7">
                  {imageUrl ? (
                    <ImageDisplay
                      imageUrl={imageUrl}
                      ocrText={ocrText}
                      onRemove={() => {
                        setUploadedFile(null)
                        setImageUrl(null)
                        setOcrText('')
                        setAnalysisResult(null)
                        setSelectedFindingId(null)
                      }}
                    />
                  ) : (
                    <FileUpload
                      onFileSelect={setUploadedFile}
                      uploadedFile={uploadedFile}
                    />
                  )}
                </div>

                {/* 右侧：分析控制区 - 占据5列 */}
                <div className="col-span-12 lg:col-span-5 flex flex-col justify-between">
                  {/* 分析状态区域 */}
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-600 mb-3 uppercase tracking-wide">分析状态</h3>
                      <AnalysisStatus
                        status={analysisStatus}
                        progress={analysisProgress}
                      />
                    </div>
                  </div>

                  {/* 分析按钮 */}
                  <div>
                    <button
                      onClick={handleAnalyze}
                      disabled={isAnalyzing || !uploadedFile}
                      className="analyze-btn w-full py-5 px-6 rounded-2xl text-white font-semibold text-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <span className="flex items-center justify-center space-x-2">
                        <span>{isAnalyzing ? '⏳' : '🚀'}</span>
                        <span>{isAnalyzing ? '分析中...' : '开始智能分析'}</span>
                      </span>
                    </button>
                    <p className="text-xs text-gray-500 text-center mt-3">预计耗时 15-20 秒</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 中间区域：胸部示意图 - 全宽展示（按照layout v2原型） */}
          {analysisResult && analysisResult.findings.length > 0 && (
            <div className="mb-8 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
              <div className="glass rounded-3xl shadow-elegant p-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-gray-800">异常发现可视化分析</h2>
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <span>发现</span>
                    <span className="font-bold text-gray-800">{analysisResult.findings.length}</span>
                    <span>个异常发现</span>
                  </div>
                </div>
                <BreastDiagram
                  findings={analysisResult.findings}
                  selectedId={selectedFindingId}
                  onSelect={setSelectedFindingId}
                />
              </div>
            </div>
          )}

          {/* 中间区域：异常发现列表和详情 - 左右分栏布局（按照layout v2原型） */}
          {analysisResult && (
            <div className="mb-8 animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
              <div className="grid grid-cols-12 gap-6 items-stretch">
                {/* 左侧：异常发现列表 - 3列 */}
                <div className="col-span-12 lg:col-span-3 flex">
                  <AbnormalFindings
                    findings={analysisResult.findings}
                    selectedId={selectedFindingId}
                    onSelect={setSelectedFindingId}
                  />
                </div>

                {/* 右侧：异常发现详情 - 9列 */}
                <div className="col-span-12 lg:col-span-9 flex">
                  <AbnormalFindings
                    findings={analysisResult.findings}
                    selectedId={selectedFindingId}
                    onSelect={setSelectedFindingId}
                    showDetails={true}
                  />
                </div>
              </div>
            </div>
          )}

          {/* 底部区域：整体评估 - 独立展示（按照layout v2原型） */}
          {analysisResult && (
            <div className="mb-8 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
              <OverallAssessment assessment={analysisResult.overallAssessment} />
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  )
}
