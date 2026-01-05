import { useState, lazy, Suspense } from 'react'

const PrivacyModal = lazy(() => import('./PrivacyModal'))

export default function Footer() {
  const [showPrivacyModal, setShowPrivacyModal] = useState(false)
  const currentYear = new Date().getFullYear()

  return (
    <>
      <footer className="glass border-t border-gray-200 mt-8 md:mt-12">
        <div className="container mx-auto px-4 py-6 md:py-8 max-w-7xl">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
            {/* Copyright */}
            <div>
              <p className="text-sm text-gray-600">
                © {currentYear} Nauta. All rights reserved.
              </p>
              <p className="text-xs text-gray-500 mt-2">
                MedCrux v1.3.0
              </p>
            </div>

            {/* Links */}
            <div className="flex flex-col gap-2">
              <a
                href="https://github.com/riverbii/MedCrux/blob/main/LICENSE"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-600 hover:text-purple-600 transition-colors"
              >
                License: Apache License 2.0
              </a>
              <button
                onClick={() => setShowPrivacyModal(true)}
                className="text-sm text-gray-600 hover:text-purple-600 transition-colors text-left"
              >
                Privacy
              </button>
              <a
                href="https://github.com/riverbii/MedCrux/issues"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-600 hover:text-purple-600 transition-colors"
              >
                Issues
              </a>
            </div>

            {/* Empty column for layout */}
            <div></div>
          </div>
        </div>
      </footer>

      <Suspense fallback={null}>
        <PrivacyModal
          isOpen={showPrivacyModal}
          onClose={() => setShowPrivacyModal(false)}
        />
      </Suspense>
    </>
  )
}

