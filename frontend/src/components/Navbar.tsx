import { useState } from 'react'
import Logo from './Logo'
import PatientEducationModal from './PatientEducationModal'

export default function Navbar() {
  const [showEducationModal, setShowEducationModal] = useState(false)
  const [showAnalysisMenu, setShowAnalysisMenu] = useState(false)
  const [showEducationMenu, setShowEducationMenu] = useState(false)

  return (
    <>
      <nav className="glass shadow-elegant sticky top-0 z-50">
        <div className="container mx-auto px-4 py-3 md:py-4 max-w-7xl">
          <div className="flex items-center justify-between">
            <Logo />
            <div className="flex items-center gap-2 md:gap-4">
              {/* 智能分析菜单 */}
              <div className="relative">
                <button
                  onClick={() => {
                    setShowAnalysisMenu(!showAnalysisMenu)
                    setShowEducationMenu(false)
                  }}
                  className="flex items-center gap-1 md:gap-2 px-2 md:px-4 py-2 text-sm md:text-base text-gray-700 hover:text-purple-600 transition-colors"
                >
                  智能分析
                  <svg
                    className={`w-4 h-4 transition-transform ${showAnalysisMenu ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {showAnalysisMenu && (
                  <div className="absolute right-0 mt-2 w-40 md:w-48 glass rounded-lg shadow-lg py-2">
                    <a
                      href="#"
                      className="block px-3 md:px-4 py-2 text-sm md:text-base text-gray-700 hover:bg-purple-50 hover:text-purple-600 transition-colors"
                    >
                      乳腺超声报告分析
                    </a>
                  </div>
                )}
              </div>

              {/* 科普教育菜单 */}
              <div className="relative">
                <button
                  onClick={() => {
                    setShowEducationMenu(!showEducationMenu)
                    setShowAnalysisMenu(false)
                  }}
                  className="flex items-center gap-1 md:gap-2 px-2 md:px-4 py-2 text-sm md:text-base text-gray-700 hover:text-purple-600 transition-colors"
                >
                  科普教育
                  <svg
                    className={`w-4 h-4 transition-transform ${showEducationMenu ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {showEducationMenu && (
                  <div className="absolute right-0 mt-2 w-40 md:w-48 glass rounded-lg shadow-lg py-2">
                    <button
                      onClick={() => {
                        setShowEducationModal(true)
                        setShowEducationMenu(false)
                      }}
                      className="block w-full text-left px-3 md:px-4 py-2 text-sm md:text-base text-gray-700 hover:bg-purple-50 hover:text-purple-600 transition-colors"
                    >
                      BI-RADS分级说明
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>

      <PatientEducationModal
        isOpen={showEducationModal}
        onClose={() => setShowEducationModal(false)}
      />

      {/* 点击外部关闭菜单 */}
      {(showAnalysisMenu || showEducationMenu) && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => {
            setShowAnalysisMenu(false)
            setShowEducationMenu(false)
          }}
        />
      )}
    </>
  )
}

