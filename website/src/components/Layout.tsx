import { Link, useLocation } from 'react-router-dom'
import { Database, Menu, X, Github } from 'lucide-react'
import { useState } from 'react'
import type { ReactNode } from 'react'
import { DATASET_METRICS, REPO_URL } from '../data/generatedData'

interface LayoutProps {
  children: ReactNode
}

const navItems = [
  { path: '/', label: 'Home' },
  { path: '/data-quality', label: 'Data Quality' },
  { path: '/signal-analysis', label: 'Signal Analysis' },
  { path: '/time-trends', label: 'Time Trends' },
  { path: '/technical', label: 'Technical' },
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-bg border-b border-comment/30 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2 group">
              <Database className="w-6 h-6 text-yellow group-hover:text-green transition-colors" />
              <span className="font-mono font-bold text-white text-lg tracking-wider">
                SECOM
              </span>
            </Link>

            <div className="hidden md:flex items-center gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                    location.pathname === item.path
                      ? 'text-yellow bg-comment/20'
                      : 'text-white/70 hover:text-white hover:bg-comment/10'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </div>

            <div className="hidden md:flex items-center gap-4">
              <a
                href={REPO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-white/70 hover:text-yellow transition-colors"
              >
                <Github className="w-5 h-5" />
              </a>
            </div>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-white/70 hover:text-white"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="md:hidden border-t border-comment/30 bg-bg">
            <div className="px-4 py-2 space-y-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`block px-4 py-3 rounded text-sm font-medium transition-colors ${
                    location.pathname === item.path
                      ? 'text-yellow bg-comment/20'
                      : 'text-white/70 hover:text-white hover:bg-comment/10'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
              <a
                href={REPO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-3 text-white/70 hover:text-yellow transition-colors"
              >
                <Github className="w-5 h-5" />
                View on GitHub
              </a>
            </div>
          </div>
        )}
      </nav>

      <main className="flex-1">
        {children}
      </main>

      <footer className="bg-bg border-t border-comment/30 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-yellow" />
              <span className="font-mono text-white font-medium">SECOM</span>
              <span className="text-comment text-sm">Manufacturing Data Quality Platform</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-comment">
              <span>UCI SECOM Dataset</span>
              <span>-</span>
              <span>{DATASET_METRICS.entityCount.toLocaleString()} entities</span>
              <span>-</span>
              <span>{DATASET_METRICS.featureCount} features</span>
            </div>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-white/70 hover:text-yellow transition-colors"
            >
              <Github className="w-4 h-4" />
              <span className="text-sm">View Source</span>
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
