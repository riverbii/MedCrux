import { AbnormalFinding } from '../types'

interface BreastDiagramProps {
  findings: AbnormalFinding[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export default function BreastDiagram({ findings, selectedId, onSelect }: BreastDiagramProps) {
  // 计算钟点位置的角度（按照layout v2原型和医学标准）
  // SVG坐标系：Y轴向下，角度从右侧(3点)开始为0度，逆时针增加
  // 根据原型验证：3点(180,105)→0度，9点(20,105)→180度，11点(70,60)→-127度
  const getClockPositionAngle = (clockPosition: string): number => {
    // 转换为SVG坐标系角度（从3点开始为0度，逆时针）
    // 改为精确匹配，先归一化，再查表，避免“11点”被“1点”误匹配
    const normalized = clockPosition
      .replace(/(钟方向|钟)/g, '')
      .trim()

    const angleMap: Record<string, number> = {
      '12点': -90.0, // 顶部
      '11点': -120.0, // 左上方
      '10点': -150.0, // 左上方
      '9点': 180.0, // 左侧
      '8点': 150.0, // 左下方
      '7点': 120.0, // 左下方
      '6点': 90.0, // 底部
      '5点': 60.0, // 右下方
      '4点': 30.0, // 右下方
      '3点': 0.0, // 右侧
      '2点': -30.0, // 右上方
      '1点': -60.0, // 右上方
    }

    const angle = angleMap[normalized]
    if (angle === undefined) {
      console.warn(`[BreastDiagram] 未知钟点: ${clockPosition} (归一化后: ${normalized})，使用默认12点`)
      return -90.0 // 默认12点方向
    }
    return angle
  }

  // 计算钟点位置的坐标（按照layout v2原型）
  // 钟点方向是相对于每个乳房的乳头位置，左右乳房不需要镜像
  // 必须使用真实的distanceFromNipple数据，不能使用默认值
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

    // 计算半径：必须使用真实的distanceFromNipple数据
    const actualBreastRadius = 7.5 // cm（实际乳腺半径）

    let r: number
    if (distanceFromNipple !== undefined && distanceFromNipple !== null && distanceFromNipple > 0) {
      // 使用真实距离数据计算半径
      // 比例：实际距离 / 实际乳腺半径，限制在90%以内
      const ratio = Math.min(distanceFromNipple / actualBreastRadius, 0.9)
      r = diagramRadius * ratio
      // 调试信息
      console.log(`[BreastDiagram] ${breast === 'left' ? '左' : '右'}乳${clockPosition}: 距离=${distanceFromNipple}cm, ratio=${ratio.toFixed(3)}, r=${r.toFixed(1)}`)
    } else {
      // 如果没有距离数据，使用默认值（但应该尽量避免这种情况）
      // 默认使用中等距离（约45%半径，对应约3.4cm）
      r = diagramRadius * 0.45
      console.warn(`警告：${breast === 'left' ? '左' : '右'}乳${clockPosition}缺少距离数据，使用默认值r=${r.toFixed(1)}`)
    }

    // 计算坐标（SVG坐标系，Y轴向下）
    // 钟点方向是相对于每个乳房的乳头位置，左右乳房不需要镜像
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
              // 调试信息：输出距离数据
              if (finding.location.distanceFromNipple === undefined || finding.location.distanceFromNipple === null) {
                console.warn(`警告：${breast === 'left' ? '左' : '右'}乳${finding.location.clockPosition}的${finding.name}缺少距离数据`)
              }

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
