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
  const aiResult = response.ai_result || {}

  // 处理错误情况
  if (aiResult.ai_risk_assessment === 'Error' || aiResult.error) {
    return {
      findings: [],
      overallAssessment: {
        summary: aiResult.advice || 'AI分析失败，请稍后重试。',
        facts: [],
        suggestions: [],
      },
    }
  }

  // 优先使用新格式
  if (aiResult._new_format) {
    const newFormat = aiResult._new_format
      const findings: AbnormalFinding[] = (newFormat.nodules || []).map((nodule: any, index: number) => {
      // 解析size字符串（格式：长径×横径×前后径 cm）
      let sizeObj: { length: number; width: number; depth: number } | undefined
      if (nodule.morphology?.size) {
        const sizeStr = nodule.morphology.size
        const match = sizeStr.match(/([\d.]+)\s*×\s*([\d.]+)\s*×\s*([\d.]+)/)
        if (match) {
          sizeObj = {
            length: parseFloat(match[1]),
            width: parseFloat(match[2]),
            depth: parseFloat(match[3]),
          }
        }
      }

      return {
        id: nodule.id || `finding_${index + 1}`,
        name: nodule.name || `异常发现${index + 1}`,
        risk: (nodule.risk_assessment === 'High' ? 'High' : nodule.risk_assessment === 'Medium' ? 'Medium' : 'Low') as 'Low' | 'Medium' | 'High',
        location: {
          breast: (nodule.location?.breast === 'right' ? 'right' : 'left') as 'left' | 'right',
          clockPosition: nodule.location?.clock_position || nodule.location?.clockPosition || '12点',
          distanceFromNipple: nodule.location?.distance_from_nipple || nodule.location?.distanceFromNipple,
        },
        size: sizeObj || nodule.size,
        morphology: nodule.morphology,
        birads: nodule.birads_class,
        inconsistencyAlerts: nodule.inconsistency_reasons || [],
      }
    })

    const overallAssessment: OverallAssessment = {
      summary: typeof newFormat.overall_assessment?.summary === 'string' 
        ? newFormat.overall_assessment.summary 
        : Array.isArray(newFormat.overall_assessment?.summary)
        ? newFormat.overall_assessment.summary.join(' ')
        : '',
      facts: Array.isArray(newFormat.overall_assessment?.summary) 
        ? newFormat.overall_assessment.summary 
        : newFormat.overall_assessment?.facts || [],
      suggestions: newFormat.overall_assessment?.suggestions || [],
      birads: newFormat.overall_assessment?.birads,
    }

    return { findings, overallAssessment }
  }

  // 使用旧格式（向后兼容）
  if (aiResult.nodules && aiResult.nodules.length > 0) {
    const findings: AbnormalFinding[] = aiResult.nodules.map((nodule, index) => {
      // 解析size字符串（格式：长径×横径×前后径 cm）
      let sizeObj: { length: number; width: number; depth: number } | undefined
      if (nodule.morphology?.size) {
        const sizeStr = nodule.morphology.size
        const match = sizeStr.match(/([\d.]+)\s*×\s*([\d.]+)\s*×\s*([\d.]+)/)
        if (match) {
          sizeObj = {
            length: parseFloat(match[1]),
            width: parseFloat(match[2]),
            depth: parseFloat(match[3]),
          }
        }
      }

      return {
        id: nodule.id || `finding_${index + 1}`,
        name: nodule.name || `异常发现${index + 1}`,
        risk: (nodule.risk_assessment === 'High' ? 'High' : nodule.risk_assessment === 'Medium' ? 'Medium' : 'Low') as 'Low' | 'Medium' | 'High',
        location: {
          breast: (nodule.location?.breast === 'right' ? 'right' : 'left') as 'left' | 'right',
          clockPosition: nodule.location?.clock_position || nodule.location?.clockPosition || '12点',
          distanceFromNipple: nodule.location?.distance_from_nipple || nodule.location?.distanceFromNipple,
        },
        size: sizeObj || nodule.size,
        morphology: nodule.morphology,
        birads: nodule.birads_class,
        inconsistencyAlerts: nodule.inconsistency_reasons || [],
      }
    })

    const overallAssessment: OverallAssessment = {
      summary: typeof aiResult.overall_assessment?.summary === 'string' 
        ? aiResult.overall_assessment.summary 
        : Array.isArray(aiResult.overall_assessment?.summary)
        ? aiResult.overall_assessment.summary.join(' ')
        : '',
      facts: Array.isArray(aiResult.overall_assessment?.summary) 
        ? aiResult.overall_assessment.summary 
        : aiResult.overall_assessment?.facts || [],
      suggestions: aiResult.overall_assessment?.suggestions || [],
      birads: aiResult.overall_assessment?.birads,
    }

    return { findings, overallAssessment }
  }

  // 无异常发现或格式不匹配
  return {
    findings: [],
    overallAssessment: {
      summary: aiResult.overall_assessment?.summary || aiResult.advice || '未发现异常',
      facts: Array.isArray(aiResult.overall_assessment?.summary) 
        ? aiResult.overall_assessment.summary 
        : aiResult.overall_assessment?.facts || [],
      suggestions: aiResult.overall_assessment?.suggestions || [],
      birads: aiResult.overall_assessment?.birads || aiResult.birads_class,
    },
  }
}

export interface AnalyzeReportResponse {
  result: AnalysisResult
  ocrText: string
}

export const analyzeReport = async (file: File): Promise<AnalyzeReportResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await api.post<AnalysisResponse>('/analyze/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    return {
      result: convertToAnalysisResult(response.data),
      ocrText: response.data.ocr_text || '',
    }
  } catch (error: any) {
    console.error('API调用失败:', error)
    // 返回错误结果
    return {
      result: {
        findings: [],
        overallAssessment: {
          summary: error.response?.data?.detail || error.message || '分析失败，请重试',
          facts: [],
          suggestions: [],
        },
      },
      ocrText: '',
    }
  }
}

export const getHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>('/health')
  return response.data
}

