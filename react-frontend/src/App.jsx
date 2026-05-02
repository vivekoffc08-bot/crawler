import { Routes, Route } from 'react-router-dom'
import SearchPage from './pages/SearchPage'
import ResultsPage from './pages/ResultsPage'

function App() {
  return (
    <div className="min-h-screen bg-dark-900 grid-bg">
      {/* Top Nav Bar */}
      <header className="sticky top-0 z-50 border-b border-dark-400/50 bg-dark-900/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <a href="/" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-electric-500 to-accent-cyan flex items-center justify-center shadow-lg shadow-electric-500/20">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"/>
                  <path d="m21 21-4.3-4.3"/>
                </svg>
              </div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-lg font-bold text-white tracking-tight">JobHunt</span>
                <span className="text-[10px] font-mono font-semibold text-electric-400 tracking-widest uppercase">CMD</span>
              </div>
            </a>
            <div className="flex items-center gap-4">
              <span className="hidden sm:flex items-center gap-1.5 text-xs font-mono text-dark-100">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse"></span>
                SYSTEM ONLINE
              </span>
              <div className="h-6 w-px bg-dark-400 hidden sm:block"></div>
              <span className="text-xs text-dark-100 font-mono hidden sm:block">v1.0.0</span>
            </div>
          </div>
        </div>
      </header>

      {/* Routes */}
      <main>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/results" element={<ResultsPage />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="border-t border-dark-400/30 mt-20 py-6">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-xs text-dark-200 font-mono">
            JOBHUNT COMMAND CENTER — Aggregating jobs from 8+ sources in real-time
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
