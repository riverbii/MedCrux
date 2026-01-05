interface LogoProps {
  size?: 'small' | 'medium' | 'large'
  variant?: 'compact' | 'full'
}

export default function Logo({ size = 'medium', variant = 'compact' }: LogoProps) {
  if (variant === 'compact') {
    // 导航栏使用的紧凑版本
    return (
      <div className="flex items-center space-x-3">
        <svg width="36" height="36" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
          <circle cx="20" cy="20" r="12" fill="none" stroke="#4F46E5" strokeWidth="2" />
          <circle cx="20" cy="20" r="6" fill="none" stroke="#4F46E5" strokeWidth="1.5" />
          <line x1="20" y1="2" x2="20" y2="8" stroke="#4F46E5" strokeWidth="2" strokeLinecap="round" />
          <line x1="20" y1="32" x2="20" y2="38" stroke="#4F46E5" strokeWidth="2" strokeLinecap="round" />
          <line x1="2" y1="20" x2="8" y2="20" stroke="#4F46E5" strokeWidth="2" strokeLinecap="round" />
          <line x1="32" y1="20" x2="38" y2="20" stroke="#4F46E5" strokeWidth="2" strokeLinecap="round" />
          <circle cx="20" cy="20" r="2" fill="#6366F1" />
        </svg>
        <span className="text-xl font-bold text-gray-800">MedCrux</span>
      </div>
    )
  }

  // 完整版本
  const width = size === 'small' ? 80 : size === 'large' ? 120 : 100
  const height = size === 'small' ? 30 : size === 'large' ? 40 : 35
  const fontSize = size === 'small' ? 14 : size === 'large' ? 18 : 16

  return (
    <svg width={width} height={height} viewBox="0 0 120 40" xmlns="http://www.w3.org/2000/svg">
      <circle cx="20" cy="20" r="12" fill="none" stroke="#4F46E5" strokeWidth="2" />
      <circle cx="20" cy="20" r="6" fill="none" stroke="#4F46E5" strokeWidth="1.5" />
      <line x1="20" y1="2" x2="20" y2="8" stroke="#4F46E5" strokeWidth="2" strokeLinecap="round" />
      <line x1="20" y1="32" x2="20" y2="38" stroke="#4F46E5" strokeWidth="2" strokeLinecap="round" />
      <line x1="2" y1="20" x2="8" y2="20" stroke="#4F46E5" strokeWidth="2" strokeLinecap="round" />
      <line x1="32" y1="20" x2="38" y2="20" stroke="#4F46E5" strokeWidth="2" strokeLinecap="round" />
      <circle cx="20" cy="20" r="2" fill="#6366F1" />
      <text x="45" y="25" fontFamily="Inter, sans-serif" fontSize={fontSize} fontWeight="600" fill="#1F2937">
        MedCrux
      </text>
    </svg>
  )
}


