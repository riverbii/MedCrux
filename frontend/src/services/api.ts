import axios from 'axios'
import { AnalysisResult, AbnormalFinding, OverallAssessment } from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000, // 5分钟超时，因为分析可能需要较长时间
})

export interface HealthResponse {
  status: string
  version: string
}

export interface AnalysisResponse {
  filename: string
  ocr_text: string
  ai_result: {
    nodules?: Array<{
      id: string
      name: string
      risk_assessment: 'Low' | 'Medium' | 'High'
      location: {
        breast: 'left' | 'right'
        clock_position: string
        distance_from_nipple?: number
      }
      size?: {
        length: number
        width: number
        depth: number
      }
      morphology?: {
        shape?: string
        boundary?: string
        echo?: string
        orientation?: string
        posterior_features?: string
        calcification?: string
        blood_flow?: string
      }
      birads_class?: string
      inconsistency_alert?: boolean
      inconsistency_reasons?: string[]
    }>
    overall_assessment?: {
      summary: string
      facts: string[]
      suggestions: string[]
      highest_risk: 'Low' | 'Medium' | 'High'
      birads?: string
    }
    _new_format?: {
      nodules: any[]
      overall_assessment: any
    }
  }
  message: string
}

// 转换后端响应为前端格式
function convertToAnalysisResult(response: AnalysisResponse): AnalysisResult {
  const aiResult = response.ai_result

  // 优先使用新格式
  if (aiResult._new_format) {
    const newFormat = aiResult._new_format
    const findings: AbnormalFinding[] = (newFormat.nodules || []).map((nodule: any, index: number) => ({
      id: nodule.id || `finding_${index + 1}`,
      name: nodule.name || `异常发现${index + 1}`,
      risk: nodule.risk_assessment || 'Low',
      location: nodule.location || { breast: 'left', clockPosition: '12点' },
      size: nodule.size,
      morphology: nodule.morphology,
      birads: nodule.birads_class,
      inconsistencyAlerts: nodule.inconsistency_reasons || [],
    }))

    const overallAssessment: OverallAssessment = {
      summary: newFormat.overall_assessment?.summary || '',
      facts: newFormat.overall_assessment?.facts || [],
      suggestions: newFormat.overall_assessment?.suggestions || [],
      birads: newFormat.overall_assessment?.birads,
    }

    return { findings, overallAssessment }
  }

  // 使用旧格式（向后兼容）
  if (aiResult.nodules && aiResult.nodules.length > 0) {
    const findings: AbnormalFinding[] = aiResult.nodules.map((nodule, index) => ({
      id: nodule.id || `finding_${index + 1}`,
      name: nodule.name || `异常发现${index + 1}`,
      risk: nodule.risk_assessment || 'Low',
      location: nodule.location || { breast: 'left', clockPosition: '12点' },
      size: nodule.size,
      morphology: nodule.morphology,
      birads: nodule.birads_class,
      inconsistencyAlerts: nodule.inconsistency_reasons || [],
    }))

    const overallAssessment: OverallAssessment = {
      summary: aiResult.overall_assessment?.summary || '',
      facts: aiResult.overall_assessment?.facts || [],
      suggestions: aiResult.overall_assessment?.suggestions || [],
      birads: aiResult.overall_assessment?.birads,
    }

    return { findings, overallAssessment }
  }

  // 无异常发现
  return {
    findings: [],
    overallAssessment: {
      summary: aiResult.overall_assessment?.summary || '未发现异常',
      facts: [],
      suggestions: [],
    },
  }
}

export const analyzeReport = async (file: File): Promise<AnalysisResult> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post<AnalysisResponse>('/analyze/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return convertToAnalysisResult(response.data)
}

export const getHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>('/health')
  return response.data
}

