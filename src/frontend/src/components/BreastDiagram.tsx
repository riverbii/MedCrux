import { AbnormalFinding } from '../types'

interface BreastDiagramProps {
  findings: AbnormalFinding[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export default function BreastDiagram({ findings, selectedId, onSelect }: BreastDiagramProps) {
  // 计算钟点位置的角度（按照layout v2原型和医学标准）
  // SVG坐标系：Y轴向下，角度从右侧(3点)开始为0度，逆时针增加
  // 3点 = 0度，6点 = 90度，9点 = 180度，12点 = 270度(或-90度)
  const getClockPositionAngle = (clockPosition: string): number => {
    // 转换为SVG坐标系角度（从3点开始为0度，逆时针）
    if (clockPosition.includes('12点')) return -90.0  // 或 270度
    if (clockPosition.includes('1点')) return -60.0   // 或 300度
    if (clockPosition.includes('2点')) return -30.0   // 或 330度
    if (clockPosition.includes('3点')) return 0.0
    if (clockPosition.includes('4点')) return 30.0
    if (clockPosition.includes('5点')) return 60.0
    if (clockPosition.includes('6点')) return 90.0
    if (clockPosition.includes('7点')) return 120.0
    if (clockPosition.includes('8点')) return 150.0
    if (clockPosition.includes('9点')) return 180.0
    if (clockPosition.includes('10点')) return -150.0  // 或 210度
    if (clockPosition.includes('11点')) return -120.0  // 或 240度
    return -90.0 // 默认12点方向
  }

  // 计算钟点位置的坐标（按照layout v2原型）
  // 左右乳房钟点方向一致，不需要镜像
  // 原型示例：左乳3点在(150,100)，右乳9点在(50,100)，右乳11点在(70,60)
  // 验证：3点=0度→(150,100)，9点=180度→(50,100)，11点=-120度→(70,60)
  const getClockPositionCoords = (
    clockPosition: string,
    distanceFromNipple: number | undefined,
    breast: 'left' | 'right',
    centerX: number = 100,
    centerY: number = 100,
    diagramRadius: number = 85 // SVG viewBox="0 0 200 200"中的半径
  ) => {
    const angleDegrees = getClockPositionAngle(clockPosition)
    const angleRadians = (angleDegrees * Math.PI) / 180
    
    // 计算半径（根据距离或使用默认值）
    const actualBreastRadius = 7.5 // cm
    let r = diagramRadius * 0.59 // 默认半径约50，对应原型中的3点(150,100)和9点(50,100)
    
    if (distanceFromNipple && distanceFromNipple > 0) {
      const ratio = Math.min(distanceFromNipple / actualBreastRadius, 0.9)
      r = diagramRadius * ratio
    } else {
      // 根据钟点位置调整默认半径
      // 11点钟位置在(70,60)，计算：dx=30, dy=40, r=sqrt(30^2+40^2)=50
      // 但角度-120度，r=50时：x=100+50*cos(-120°)=100+50*(-0.5)=75, y=100+50*sin(-120°)=100+50*(-0.866)=56.7
      // 实际需要r约35才能得到(70,60)
      if (clockPosition.includes('11点') || clockPosition.includes('10点') || 
          clockPosition.includes('1点') || clockPosition.includes('2点')) {
        // 对于11点，需要调整半径使其更接近(70,60)
        // 从(70,60)反推：角度-120度，需要r约35
        r = diagramRadius * 0.41 // 约35
      }
    }
    
    // 计算坐标（SVG坐标系，Y轴向下）
    // 左右乳房钟点方向一致，直接使用计算出的坐标，不镜像
    // x = centerX + r*cos(angle)
    // y = centerY + r*sin(angle)
    const xPos = r * Math.cos(angleRadians)
    const yPos = r * Math.sin(angleRadians)
    
    return {
      x: centerX + xPos,
      y: centerY + yPos, // SVG的Y轴向下，所以用加号
    }
  }

  const renderBreast = (breast: 'left' | 'right', findings: AbnormalFinding[]) => {
    const breastFindings = findings.filter((f) => f.location.breast === breast)
    const riskColors = {
      High: '#EF4444',
      Medium: '#F59E0B',
      Low: '#10B981',
    }

    return (
      <div key={breast} className="flex flex-col items-center">
        <div className="text-center text-sm font-semibold text-gray-700 mb-4">
          {breast === 'left' ? '左乳' : '右乳'}
        </div>
        <div className="relative w-full aspect-square max-w-xs mx-auto">
          <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
            {/* 圆形轮廓 - 按照layout v2原型 */}
            <circle cx="100" cy="100" r="85" fill="none" stroke="#4F46E5" strokeWidth="3" opacity="0.3" />
            
            {/* 钟点标注 - 按照layout v2原型 */}
            <text x="100" y="20" textAnchor="middle" fontSize="14" fill="#6366F1" fontWeight="600">12</text>
            <text x="180" y="105" textAnchor="middle" fontSize="14" fill="#6366F1" fontWeight="600">3</text>
            <text x="100" y="190" textAnchor="middle" fontSize="14" fill="#6366F1" fontWeight="600">6</text>
            <text x="20" y="105" textAnchor="middle" fontSize="14" fill="#6366F1" fontWeight="600">9</text>

            {/* 绘制异常发现标记 */}
            {breastFindings.map((finding, index) => {
              const coords = getClockPositionCoords(
                finding.location.clockPosition,
                finding.location.distanceFromNipple,
                breast,
                100, // centerX
                100, // centerY
                85   // diagramRadius
              )
              const isSelected = finding.id === selectedId
              const riskColor = riskColors[finding.risk]
              
              // 根据大小计算标记大小
              let markerSize = 8
              if (finding.size) {
                const longAxis = finding.size.length
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
                    stroke={isSelected ? '#4F46E5' : riskColor === '#EF4444' ? '#DC2626' : riskColor === '#F59E0B' ? '#D97706' : '#059669'}
                    strokeWidth={isSelected ? 3 : 2}
                    opacity="0.9"
                    className="cursor-pointer hover:opacity-100 transition-opacity"
                    onClick={() => onSelect(finding.id)}
                  >
                    {isSelected && (
                      <animate attributeName="r" values={`${markerSize + 2};${markerSize + 4};${markerSize + 2}`} dur="2s" repeatCount="indefinite" />
                    )}
                  </circle>
                  <text
                    x={coords.x}
                    y={coords.y + markerSize + 15}
                    textAnchor="middle"
                    fontSize={finding.risk === 'High' ? '12' : finding.risk === 'Medium' ? '11' : '10'}
                    fill={riskColor}
                    fontWeight="700"
                    className="pointer-events-none"
                  >
                    {index + 1}
                  </text>
                </g>
              )
            })}
          </svg>
        </div>
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
    <div className="breast-diagram-container rounded-2xl">
      <div className="grid grid-cols-2 gap-8 max-w-2xl mx-auto">
        {leftFindings.length > 0 && renderBreast('left', findings)}
        {rightFindings.length > 0 && renderBreast('right', findings)}
        {leftFindings.length === 0 && rightFindings.length === 0 && (
          <div className="col-span-2 text-center text-gray-500 py-8">暂无异常发现</div>
        )}
      </div>
    </div>
  )
}

