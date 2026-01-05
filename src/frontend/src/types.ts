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
}

export interface AnalysisResult {
  findings: AbnormalFinding[]
  overallAssessment: OverallAssessment
}

export type AnalysisStatus = 'idle' | 'uploading' | 'ocr' | 'rag' | 'llm' | 'consistency' | 'completed' | 'error'


