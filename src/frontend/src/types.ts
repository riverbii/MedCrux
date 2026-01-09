export interface AbnormalFinding {
  id: string
  name: string
  risk: 'Low' | 'Medium' | 'High'
  location: {
    breast: 'left' | 'right'
    clockPosition: string
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
    posteriorFeatures?: string
    calcification?: string
    bloodFlow?: string
  }
  birads?: string
  inconsistencyAlerts?: string[]
}

export interface OverallAssessment {
  summary: string
  facts: string[]
  suggestions: string[]
  birads?: string
  totalNodules?: number
  highestRisk?: 'Low' | 'Medium' | 'High'
  riskDistribution?: {
    Low: number
    Medium: number
    High: number
  }
  advice?: string
  inconsistencyCount?: number
  inconsistencySummary?: string[]
  // 新增：原报告结论摘要
  originalReport?: {
    highestBirads?: string
    totalFindings?: number
    // 事实性摘要：检查所见（描述性的，客观的）
    factualSummary?: {
      findings?: string  // 检查所见
    }
    // 结论：影像学诊断和建议（判断性的，结论性的）
    conclusion?: {
      diagnosis?: string  // 影像学诊断
      recommendation?: string  // 建议
    }
  }
  // 新增：一致性校验结果
  consistencyCheck?: {
    status: 'all_consistent' | 'has_inconsistency'
    consistentCount: number
    inconsistentCount: number
    inconsistentDetails?: Array<{
      findingName: string
      originalBirads: string
      reasons: string[]
    }>
    consistentDetails?: Array<{
      findingName: string
      originalBirads: string
    }>
  }
  // 新增：基于一致性校验的风险评估
  consistencyBasedRisk?: {
    level: 'Low' | 'Medium' | 'High'
    description: string
  }
  // 新增：评估紧急程度（BL-009）
  assessmentUrgency?: {
    urgencyLevel: 'Low' | 'Medium' | 'High'
    reason: string
    doctorHighestBirads: string
    llmHighestBirads: string
    comparison: 'llm_exceeds' | 'llm_equal_or_lower' | 'unknown'
  }
  // 新增：一致性校验结果（BL-009，报告分类结果和AI分类结果的一致性）
  consistencyCheckNew?: {
    consistent: boolean
    reportBiradsSet: string[]
    aiBiradsSet: string[]
    missingInAi: string[]
    extraInAi: string[]
    description: string
  }
}

export interface AnalysisResult {
  findings: AbnormalFinding[]
  overallAssessment: OverallAssessment
}

export type AnalysisStatus = 'idle' | 'uploading' | 'ocr' | 'rag' | 'llm' | 'consistency' | 'completed' | 'error'
