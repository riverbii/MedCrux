import axios from 'axios'
import { AnalysisResult, AbnormalFinding, OverallAssessment } from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000, // 5分钟超时，因为分析可能需要较长时间
})

// 解析距离数据（可能是数字或字符串，如"3cm"或"3"）
function parseDistanceFromNipple(distance: any): number | undefined {
  if (distance === undefined || distance === null) {
    return undefined
  }
  
  // 如果是数字，直接返回
  if (typeof distance === 'number') {
    return distance > 0 ? distance : undefined
  }
  
  // 如果是字符串，尝试解析
  if (typeof distance === 'string') {
    // 移除"cm"等单位，提取数字
    const match = distance.match(/([\d.]+)/)
    if (match) {
      const num = parseFloat(match[1])
      return num > 0 ? num : undefined
    }
  }
  
  return undefined
}

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
          distanceFromNipple: parseDistanceFromNipple(nodule.location?.distance_from_nipple || nodule.location?.distanceFromNipple),
        },
        size: sizeObj || nodule.size,
        morphology: nodule.morphology,
        birads: nodule.birads_class,
        inconsistencyAlerts: nodule.inconsistency_reasons || [],
      }
    })

    // 计算风险评估信息
    const totalNodules = findings.length
    const riskLevels = findings.map(f => f.risk)
    const highestRisk = riskLevels.includes('High') ? 'High' : riskLevels.includes('Medium') ? 'Medium' : 'Low'
    const riskDistribution = {
      Low: riskLevels.filter(r => r === 'Low').length,
      Medium: riskLevels.filter(r => r === 'Medium').length,
      High: riskLevels.filter(r => r === 'High').length,
    }
    const inconsistencyCount = findings.filter(f => f.inconsistencyAlerts && f.inconsistencyAlerts.length > 0).length
    const inconsistencySummary = findings
      .filter(f => f.inconsistencyAlerts && f.inconsistencyAlerts.length > 0)
      .map(f => `${f.name}：${f.inconsistencyAlerts.join('；')}`)

    // 生成详细事实摘要（如果LLM返回的不够详细）
    const llmSummary = typeof newFormat.overall_assessment?.summary === 'string' 
      ? newFormat.overall_assessment.summary 
      : Array.isArray(newFormat.overall_assessment?.summary)
      ? newFormat.overall_assessment.summary.join(' ')
      : ''
    
    const summaryIsEmpty = !llmSummary || llmSummary.trim().length === 0
    const summaryIsInsufficient = llmSummary.length < totalNodules * 50

    let detailedFacts: string[] = []
    if (summaryIsEmpty || summaryIsInsufficient) {
      // 自动生成详细摘要
      detailedFacts = findings.map((finding, index) => {
        const parts: string[] = []
        parts.push(`${finding.name}（${finding.location.breast === 'left' ? '左乳' : '右乳'}${finding.location.clockPosition}${finding.location.distanceFromNipple ? `，距乳头${finding.location.distanceFromNipple}cm` : ''}）`)
        
        if (finding.size) {
          parts.push(`大小${finding.size.length}×${finding.size.width}×${finding.size.depth}cm`)
        }
        if (finding.morphology?.shape) {
          parts.push(`形状${finding.morphology.shape}`)
        }
        if (finding.morphology?.boundary) {
          parts.push(`边界${finding.morphology.boundary}`)
        }
        if (finding.morphology?.echo) {
          parts.push(`回声${finding.morphology.echo}`)
        }
        if (finding.morphology?.orientation) {
          parts.push(`方位${finding.morphology.orientation}`)
        }
        if (finding.birads) {
          parts.push(`BI-RADS ${finding.birads}类`)
        }
        parts.push(`风险等级${finding.risk === 'High' ? '高' : finding.risk === 'Medium' ? '中' : '低'}`)
        if (finding.inconsistencyAlerts && finding.inconsistencyAlerts.length > 0) {
          parts.push('⚠️存在不一致')
        }
        
        return parts.join('，')
      })
    } else {
      // 使用LLM返回的摘要
      if (Array.isArray(newFormat.overall_assessment?.summary)) {
        detailedFacts = newFormat.overall_assessment.summary.filter((s: string) => s && s.trim())
      } else if (llmSummary) {
        detailedFacts = [llmSummary]
      }
    }

    const overallAssessment: OverallAssessment = {
      summary: llmSummary || detailedFacts.join(' '),
      facts: detailedFacts,
      suggestions: newFormat.overall_assessment?.suggestions || [],
      birads: newFormat.overall_assessment?.birads,
      totalNodules,
      highestRisk,
      riskDistribution,
      advice: newFormat.overall_assessment?.advice || '',
      inconsistencyCount,
      inconsistencySummary: inconsistencySummary.length > 0 ? inconsistencySummary : undefined,
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
          distanceFromNipple: parseDistanceFromNipple(nodule.location?.distance_from_nipple || nodule.location?.distanceFromNipple),
        },
        size: sizeObj || nodule.size,
        morphology: nodule.morphology,
        birads: nodule.birads_class,
        inconsistencyAlerts: nodule.inconsistency_reasons || [],
      }
    })

    // 计算风险评估信息
    const totalNodules = findings.length
    const riskLevels = findings.map(f => f.risk)
    const highestRisk = riskLevels.includes('High') ? 'High' : riskLevels.includes('Medium') ? 'Medium' : 'Low'
    const riskDistribution = {
      Low: riskLevels.filter(r => r === 'Low').length,
      Medium: riskLevels.filter(r => r === 'Medium').length,
      High: riskLevels.filter(r => r === 'High').length,
    }
    const inconsistencyCount = findings.filter(f => f.inconsistencyAlerts && f.inconsistencyAlerts.length > 0).length
    const inconsistencySummary = findings
      .filter(f => f.inconsistencyAlerts && f.inconsistencyAlerts.length > 0)
      .map(f => `${f.name}：${f.inconsistencyAlerts.join('；')}`)

    // 生成详细事实摘要
    const llmSummary = typeof aiResult.overall_assessment?.summary === 'string' 
      ? aiResult.overall_assessment.summary 
      : Array.isArray(aiResult.overall_assessment?.summary)
      ? aiResult.overall_assessment.summary.join(' ')
      : ''
    
    const summaryIsEmpty = !llmSummary || llmSummary.trim().length === 0
    const summaryIsInsufficient = llmSummary.length < totalNodules * 50

    let detailedFacts: string[] = []
    if (summaryIsEmpty || summaryIsInsufficient) {
      detailedFacts = findings.map((finding, index) => {
        const parts: string[] = []
        parts.push(`${finding.name}（${finding.location.breast === 'left' ? '左乳' : '右乳'}${finding.location.clockPosition}${finding.location.distanceFromNipple ? `，距乳头${finding.location.distanceFromNipple}cm` : ''}）`)
        
        if (finding.size) {
          parts.push(`大小${finding.size.length}×${finding.size.width}×${finding.size.depth}cm`)
        }
        if (finding.morphology?.shape) {
          parts.push(`形状${finding.morphology.shape}`)
        }
        if (finding.morphology?.boundary) {
          parts.push(`边界${finding.morphology.boundary}`)
        }
        if (finding.morphology?.echo) {
          parts.push(`回声${finding.morphology.echo}`)
        }
        if (finding.morphology?.orientation) {
          parts.push(`方位${finding.morphology.orientation}`)
        }
        if (finding.birads) {
          parts.push(`BI-RADS ${finding.birads}类`)
        }
        parts.push(`风险等级${finding.risk === 'High' ? '高' : finding.risk === 'Medium' ? '中' : '低'}`)
        if (finding.inconsistencyAlerts && finding.inconsistencyAlerts.length > 0) {
          parts.push('⚠️存在不一致')
        }
        
        return parts.join('，')
      })
    } else {
      if (Array.isArray(aiResult.overall_assessment?.summary)) {
        detailedFacts = aiResult.overall_assessment.summary.filter((s: string) => s && s.trim())
      } else if (llmSummary) {
        detailedFacts = [llmSummary]
      }
    }

    const overallAssessment: OverallAssessment = {
      summary: llmSummary || detailedFacts.join(' '),
      facts: detailedFacts,
      suggestions: aiResult.overall_assessment?.suggestions || [],
      birads: aiResult.overall_assessment?.birads,
      totalNodules,
      highestRisk,
      riskDistribution,
      advice: aiResult.advice || '',
      inconsistencyCount,
      inconsistencySummary: inconsistencySummary.length > 0 ? inconsistencySummary : undefined,
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

