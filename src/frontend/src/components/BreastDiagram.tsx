import { AbnormalFinding } from '../types'

interface BreastDiagramProps {
  findings: AbnormalFinding[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export default function BreastDiagram({ findings, selectedId, onSelect }: BreastDiagramProps) {
  // 计算钟点位置的角度（12点为90度，顺时针递减）
  const getClockPositionAngle = (clockPosition: string): number => {
    // 12点=90度(上), 3点=0度(右), 6点=-90度(下), 9点=180度(左)
    if (clockPosition.includes('12点')) return 90.0
    if (clockPosition.includes('1点')) return 60.0
    if (clockPosition.includes('2点')) return 30.0
    if (clockPosition.includes('3点')) return 0.0
    if (clockPosition.includes('4点')) return -30.0
    if (clockPosition.includes('5点')) return -60.0
    if (clockPosition.includes('6点')) return -90.0
    if (clockPosition.includes('7点')) return -120.0
    if (clockPosition.includes('8点')) return -150.0
    if (clockPosition.includes('9点')) return 180.0
    if (clockPosition.includes('10点')) return 150.0
    if (clockPosition.includes('11点')) return 120.0
    return 90.0 // 默认12点方向
  }

  // 计算钟点位置的坐标（参考Streamlit版本的逻辑）
  const getClockPositionCoords = (
    clockPosition: string,
    distanceFromNipple: number | undefined,
    breast: 'left' | 'right',
    diagramRadius: number = 85 // SVG坐标中的半径（0-100范围，对应Streamlit的0.85）
  ) => {
    const angleDegrees = getClockPositionAngle(clockPosition)
    const angleRadians = (angleDegrees * Math.PI) / 180
    const centerX = 150
    const centerY = 150
    
    // 计算半径（参考Streamlit逻辑）
    // 实际乳腺半径约7.5cm，示意图半径85（相对坐标，对应Streamlit的0.85）
    const actualBreastRadius = 7.5 // cm
    let r = diagramRadius * 0.45 // 默认半径（对应Streamlit的0.45）
    
    if (distanceFromNipple && distanceFromNipple > 0) {
      // 根据距离计算在示意图中的位置
      const ratio = Math.min(distanceFromNipple / actualBreastRadius, 0.9) // 限制在90%以内
      r = diagramRadius * ratio
    }
    
    // 计算基础坐标（极坐标转直角坐标）
    // 使用标准极坐标：x = r*cos(angle), y = r*sin(angle)
    const xPosBase = r * Math.cos(angleRadians)
    const yPos = r * Math.sin(angleRadians)
    
    // 对于左乳：直接使用
    // 对于右乳：镜像x坐标（参考Streamlit逻辑）
    const xPos = breast === 'left' ? xPosBase : -xPosBase
    
    return {
      x: centerX + xPos,
      y: centerY - yPos, // 注意：SVG的Y轴向下，所以用减号
    }
  }

  const renderBreast = (breast: 'left' | 'right', findings: AbnormalFinding[]) => {
    const breastFindings = findings.filter((f) => f.location.breast === breast)
    const riskColors = {
      High: '#ef4444',
      Medium: '#f59e0b',
      Low: '#10b981',
    }

    return (
      <div key={breast} className="flex flex-col items-center">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">
          {breast === 'left' ? '左乳' : '右乳'}
        </h4>
        <svg width="300" height="300" viewBox="0 0 300 300" className="border border-gray-200 rounded-lg bg-white">
          {/* 绘制乳腺轮廓（正圆形，参考Streamlit版本） */}
          <circle cx="150" cy="150" r="85" fill="#fef3c7" stroke="#1F2937" strokeWidth="2" />
          
          {/* 绘制钟点标记 */}
          {[12, 3, 6, 9].map((hour) => {
            const angle = ((hour * 30 - 90) * Math.PI) / 180
            const x = 150 + 110 * Math.cos(angle)
            const y = 150 + 110 * Math.sin(angle)
            return (
              <text
                key={hour}
                x={x}
                y={y}
                textAnchor="middle"
                dominantBaseline="middle"
                className="text-xs fill-gray-500"
              >
                {hour}点
              </text>
            )
          })}

          {/* 绘制异常发现标记 */}
          {breastFindings.map((finding) => {
            const coords = getClockPositionCoords(
              finding.location.clockPosition,
              finding.location.distanceFromNipple,
              breast
            )
            const isSelected = finding.id === selectedId
            const riskColor = riskColors[finding.risk]
            
            // 根据大小计算标记大小
            let markerSize = 8
            if (finding.size) {
              const longAxis = finding.size.length
              // 实际乳腺半径约7.5cm，示意图半径85（相对坐标）
              const scale = 85 / 7.5
              markerSize = Math.min(Math.max(longAxis * scale * 0.5, 6), 16)
            }

            return (
              <g key={finding.id}>
                <circle
                  cx={coords.x}
                  cy={coords.y}
                  r={isSelected ? markerSize + 2 : markerSize}
                  fill={riskColor}
                  stroke={isSelected ? '#4f46e5' : '#fff'}
                  strokeWidth={isSelected ? 3 : 2}
                  className="cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => onSelect(finding.id)}
                />
                <text
                  x={coords.x}
                  y={coords.y + markerSize + 15}
                  textAnchor="middle"
                  className="text-xs fill-gray-700 font-medium pointer-events-none"
                >
                  {finding.name}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
    )
  }

  if (findings.length === 0) {
    return (
      <div className="glass rounded-2xl shadow-elegant p-6">
        <h3 className="text-lg md:text-xl font-bold text-gray-800 mb-4">胸部示意图</h3>
        <div className="text-center text-gray-500 py-8">暂无异常发现</div>
      </div>
    )
  }

  const leftFindings = findings.filter((f) => f.location.breast === 'left')
  const rightFindings = findings.filter((f) => f.location.breast === 'right')

  return (
    <div className="glass rounded-2xl shadow-elegant p-4 md:p-6">
      <h3 className="text-lg md:text-xl font-bold text-gray-800 mb-4">胸部示意图</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {leftFindings.length > 0 && renderBreast('left', findings)}
        {rightFindings.length > 0 && renderBreast('right', findings)}
        {leftFindings.length === 0 && rightFindings.length === 0 && (
          <div className="col-span-2 text-center text-gray-500 py-8">暂无异常发现</div>
        )}
      </div>
    </div>
  )
}

