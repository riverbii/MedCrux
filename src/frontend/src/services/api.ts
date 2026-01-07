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

// 从OCR文本中提取原报告事实性摘要和结论
function extractOriginalReportSummary(
  ocrText: string,
  reportStructure?: { findings?: string | null; diagnosis?: string | null; recommendation?: string | null } | null
): {
  factualSummary?: { findings?: string }
  conclusion?: { diagnosis?: string; recommendation?: string }
} {
  // 优先使用后端LLM解析的报告结构结果
  if (reportStructure) {
    const result: {
      factualSummary?: { findings?: string }
      conclusion?: { diagnosis?: string; recommendation?: string }
    } = {}

    // 使用后端解析的findings作为事实性摘要
    if (reportStructure.findings) {
      result.factualSummary = {
        findings: reportStructure.findings
      }
    }

    // 使用后端解析的diagnosis和recommendation作为结论
    if (reportStructure.diagnosis || reportStructure.recommendation) {
      result.conclusion = {}
      if (reportStructure.diagnosis) {
        result.conclusion.diagnosis = reportStructure.diagnosis
      }
      if (reportStructure.recommendation) {
        result.conclusion.recommendation = reportStructure.recommendation
      }
    }

    // 如果后端解析结果存在，直接返回
    if (result.factualSummary || result.conclusion) {
      return result
    }
  }

  // Fallback：如果后端解析失败或不存在，使用正则表达式从OCR文本中提取
  if (!ocrText || ocrText.trim().length === 0) {
    return {}
  }

  const text = ocrText.trim()
  const result: {
    factualSummary?: { findings?: string }
    conclusion?: { diagnosis?: string; recommendation?: string }
  } = {}

  // 提取"检查所见"或"检查结果"部分（事实性摘要）
  const findingsMatch = text.match(/(?:检查所见|检查结果|所见)[:：]?\s*([^影像学诊断诊断建议]*?)(?=影像学诊断|诊断|建议|$)/s)
  if (findingsMatch && findingsMatch[1]) {
    result.factualSummary = {
      findings: findingsMatch[1].trim()
    }
  }

  // 提取"影像学诊断"或"诊断"部分（结论）
  const diagnosisMatch = text.match(/(?:影像学诊断|诊断|诊断意见)[:：]?\s*([^建议]*?)(?=建议|$)/s)
  const recommendationMatch = text.match(/(?:建议|处理建议|临床建议)[:：]?\s*(.+?)(?=报告医师|审核医师|报告日期|$)/s)

  if (diagnosisMatch || recommendationMatch) {
    result.conclusion = {}
    if (diagnosisMatch && diagnosisMatch[1]) {
      result.conclusion.diagnosis = diagnosisMatch[1].trim()
    }
    if (recommendationMatch && recommendationMatch[1]) {
      result.conclusion.recommendation = recommendationMatch[1].trim()
    }
  }

  // 如果上述方法都没提取到，尝试提取整个文本的关键部分
  if (!result.factualSummary && !result.conclusion) {
    const lines = text.split('\n').filter(line => line.trim().length > 0)
    const findingsEnd = Math.floor(lines.length * 0.6)
    const diagnosisEnd = Math.floor(lines.length * 0.8)

    result.factualSummary = {
      findings: lines.slice(0, findingsEnd).join('\n')
    }
    result.conclusion = {
      diagnosis: lines.slice(findingsEnd, diagnosisEnd).join('\n'),
      recommendation: lines.slice(diagnosisEnd).join('\n')
    }
  }

  return result
}

export interface HealthResponse {
  status: string
  version: string
}

export interface AnalysisResponse {
  filename: string
  ocr_text: string
  report_structure?: {
    findings?: string | null
    diagnosis?: string | null
    recommendation?: string | null
  } | null
  ai_result: {
    nodules?: Array<{
      id: string
      name: string
      risk_assessment: 'Low' | 'Medium' | 'High'
      location: {
        breast: 'left' | 'right'
        clock_position: string
        distance_from_nipple?: number
        // 兼容可能出现的驼峰命名
        clockPosition?: string
        distanceFromNipple?: number
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
        size?: string
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
    ai_risk_assessment?: string
    error?: string
    advice?: string
    birads_class?: string
    _new_format?: {
      nodules: any[]
      overall_assessment: any
    }
  }
  message: string
}

// 转换后端响应为前端格式
function convertToAnalysisResult(
  response: AnalysisResponse,
  ocrText?: string,
  reportStructure?: AnalysisResponse['report_structure']
): AnalysisResult {
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
      // 解析size字符串（格式：长径×横径×前后径 cm 或 长径×横径 cm）
      let sizeObj: { length: number; width: number; depth: number } | undefined
      if (nodule.morphology?.size) {
        const sizeStr = nodule.morphology.size
        // 先尝试匹配3个维度（长径×横径×前后径）
        let match = sizeStr.match(/([\d.]+)\s*×\s*([\d.]+)\s*×\s*([\d.]+)/)
        if (match) {
          sizeObj = {
            length: parseFloat(match[1]),
            width: parseFloat(match[2]),
            depth: parseFloat(match[3]),
          }
        } else {
          // 如果3个维度匹配失败，尝试匹配2个维度（长径×横径）
          match = sizeStr.match(/([\d.]+)\s*×\s*([\d.]+)/)
          if (match) {
            sizeObj = {
              length: parseFloat(match[1]),
              width: parseFloat(match[2]),
              depth: 0, // 2个维度时，depth设为0，前端显示时会忽略
            }
          }
        }
      }
      // 如果morphology.size解析失败，尝试使用nodule.size（直接来自后端）
      if (!sizeObj && nodule.size) {
        sizeObj = nodule.size
      }

      return {
        id: nodule.id || `finding_${index + 1}`,
        name: nodule.name || `异常发现${index + 1}`,
        risk: (nodule.risk_assessment === 'High' ? 'High' : nodule.risk_assessment === 'Medium' ? 'Medium' : 'Low') as 'Low' | 'Medium' | 'High',
        location: {
          breast: (nodule.location?.breast === 'right' ? 'right' : 'left') as 'left' | 'right',
          // LLM已标准化：象限转换统一使用4个固定钟点（1、11、5、7），单位已统一为cm
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
    const inconsistencyCount = findings.filter(f => (f.inconsistencyAlerts ?? []).length > 0).length
    const inconsistencySummary = findings
      .filter(f => (f.inconsistencyAlerts ?? []).length > 0)
      .map(f => `${f.name}：${(f.inconsistencyAlerts ?? []).join('；')}`)

    // 生成详细事实摘要（如果LLM返回的不够详细）
    const llmSummary = typeof newFormat.overall_assessment?.summary === 'string'
      ? newFormat.overall_assessment.summary
      : Array.isArray(newFormat.overall_assessment?.summary)
      ? (newFormat.overall_assessment.summary as string[]).join(' ')
      : ''

    const summaryIsEmpty = !llmSummary || llmSummary.trim().length === 0
    const summaryIsInsufficient = llmSummary.length < totalNodules * 50

    let detailedFacts: string[] = []
    if (summaryIsEmpty || summaryIsInsufficient) {
      // 自动生成详细摘要
      detailedFacts = findings.map((finding) => {
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

    // 计算一致性校验结果
    const consistentFindings = findings.filter(f => !f.inconsistencyAlerts || f.inconsistencyAlerts.length === 0)
    const inconsistentFindings = findings.filter(f => (f.inconsistencyAlerts ?? []).length > 0)

    const consistencyCheck = {
      status: (inconsistentFindings.length > 0 ? 'has_inconsistency' : 'all_consistent') as 'all_consistent' | 'has_inconsistency',
      consistentCount: consistentFindings.length,
      inconsistentCount: inconsistentFindings.length,
      inconsistentDetails: inconsistentFindings.map(f => ({
        findingName: f.name,
        originalBirads: f.birads || '未分类',
        reasons: f.inconsistencyAlerts ?? [],
      })),
      consistentDetails: consistentFindings.map(f => ({
        findingName: f.name,
        originalBirads: f.birads || '未分类',
      })),
    }

    // 计算基于一致性校验的风险评估
    const consistencyBasedRisk = {
      level: (inconsistentFindings.length > 0 ? 'High' : inconsistentFindings.length === 0 && totalNodules > 0 ? 'Medium' : 'Low') as 'Low' | 'Medium' | 'High',
      description: inconsistentFindings.length > 0
        ? `发现${inconsistentFindings.length}个不一致，原报告BI-RADS分类可能不准确，建议重新评估。不一致的异常发现可能存在风险被低估的情况。`
        : '所有异常发现的一致性校验通过，原报告BI-RADS分类与形态学特征描述一致。',
    }

    // 计算原报告最高BI-RADS分类
    const allBirads = findings.map(f => f.birads).filter((b): b is string => !!b)
    const highestBirads = allBirads.length > 0
      ? allBirads.sort((a, b) => parseInt(b) - parseInt(a))[0]
      : undefined

    // 从OCR文本中提取原报告事实性摘要和结论（优先使用后端解析结果）
    const originalReportData = ocrText ? extractOriginalReportSummary(ocrText, reportStructure) : {}

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
      originalReport: {
        highestBirads,
        totalFindings: totalNodules,
        factualSummary: originalReportData.factualSummary,
        conclusion: originalReportData.conclusion,
      },
      consistencyCheck,
      consistencyBasedRisk,
    }

    return { findings, overallAssessment }
  }

  // 使用旧格式（向后兼容）
  if (aiResult.nodules && aiResult.nodules.length > 0) {
    const findings: AbnormalFinding[] = aiResult.nodules.map((nodule, index) => {
      // 解析size字符串（格式：长径×横径×前后径 cm 或 长径×横径 cm）
      let sizeObj: { length: number; width: number; depth: number } | undefined
      if (nodule.morphology?.size) {
        const sizeStr = nodule.morphology.size
        // 先尝试匹配3个维度（长径×横径×前后径）
        let match = sizeStr.match(/([\d.]+)\s*×\s*([\d.]+)\s*×\s*([\d.]+)/)
        if (match) {
          sizeObj = {
            length: parseFloat(match[1]),
            width: parseFloat(match[2]),
            depth: parseFloat(match[3]),
          }
        } else {
          // 如果3个维度匹配失败，尝试匹配2个维度（长径×横径）
          match = sizeStr.match(/([\d.]+)\s*×\s*([\d.]+)/)
          if (match) {
            sizeObj = {
              length: parseFloat(match[1]),
              width: parseFloat(match[2]),
              depth: 0, // 2个维度时，depth设为0，前端显示时会忽略
            }
          }
        }
      }
      // 如果morphology.size解析失败，尝试使用nodule.size（直接来自后端）
      if (!sizeObj && nodule.size) {
        sizeObj = nodule.size
      }

      return {
        id: nodule.id || `finding_${index + 1}`,
        name: nodule.name || `异常发现${index + 1}`,
        risk: (nodule.risk_assessment === 'High' ? 'High' : nodule.risk_assessment === 'Medium' ? 'Medium' : 'Low') as 'Low' | 'Medium' | 'High',
        location: {
          breast: (nodule.location?.breast === 'right' ? 'right' : 'left') as 'left' | 'right',
          // LLM已标准化：象限转换统一使用4个固定钟点（1、11、5、7），单位已统一为cm
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
    const inconsistencyCount = findings.filter(f => (f.inconsistencyAlerts ?? []).length > 0).length
    const inconsistencySummary = findings
      .filter(f => (f.inconsistencyAlerts ?? []).length > 0)
      .map(f => `${f.name}：${(f.inconsistencyAlerts ?? []).join('；')}`)

    // 生成详细事实摘要
    const llmSummary = typeof aiResult.overall_assessment?.summary === 'string'
      ? aiResult.overall_assessment.summary
      : Array.isArray(aiResult.overall_assessment?.summary)
      ? (aiResult.overall_assessment.summary as string[]).join(' ')
      : ''

    const summaryIsEmpty = !llmSummary || llmSummary.trim().length === 0
    const summaryIsInsufficient = llmSummary.length < totalNodules * 50

    let detailedFacts: string[] = []
    if (summaryIsEmpty || summaryIsInsufficient) {
      detailedFacts = findings.map((finding) => {
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

    // 计算一致性校验结果（旧格式）
    const consistentFindings = findings.filter(f => !f.inconsistencyAlerts || f.inconsistencyAlerts.length === 0)
    const inconsistentFindings = findings.filter(f => (f.inconsistencyAlerts ?? []).length > 0)

    const consistencyCheck = {
      status: (inconsistentFindings.length > 0 ? 'has_inconsistency' : 'all_consistent') as 'all_consistent' | 'has_inconsistency',
      consistentCount: consistentFindings.length,
      inconsistentCount: inconsistentFindings.length,
      inconsistentDetails: inconsistentFindings.map(f => ({
        findingName: f.name,
        originalBirads: f.birads || '未分类',
        reasons: f.inconsistencyAlerts ?? [],
      })),
      consistentDetails: consistentFindings.map(f => ({
        findingName: f.name,
        originalBirads: f.birads || '未分类',
      })),
    }

    // 计算基于一致性校验的风险评估（旧格式）
    const consistencyBasedRisk = {
      level: (inconsistentFindings.length > 0 ? 'High' : inconsistentFindings.length === 0 && totalNodules > 0 ? 'Medium' : 'Low') as 'Low' | 'Medium' | 'High',
      description: inconsistentFindings.length > 0
        ? `发现${inconsistentFindings.length}个不一致，原报告BI-RADS分类可能不准确，建议重新评估。不一致的异常发现可能存在风险被低估的情况。`
        : '所有异常发现的一致性校验通过，原报告BI-RADS分类与形态学特征描述一致。',
    }

    // 计算原报告最高BI-RADS分类（旧格式）
    const allBirads = findings.map(f => f.birads).filter((b): b is string => !!b)
    const highestBirads = allBirads.length > 0
      ? allBirads.sort((a, b) => parseInt(b) - parseInt(a))[0]
      : undefined

    // 从OCR文本中提取原报告事实性摘要和结论（优先使用后端解析结果）
    const originalReportData = ocrText ? extractOriginalReportSummary(ocrText, reportStructure) : {}

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
      originalReport: {
        highestBirads,
        totalFindings: totalNodules,
        factualSummary: originalReportData.factualSummary,
        conclusion: originalReportData.conclusion,
      },
      consistencyCheck,
      consistencyBasedRisk,
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
      result: convertToAnalysisResult(response.data, response.data.ocr_text, response.data.report_structure),
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
