import { useState } from 'react'
import UploadScreen from './components/UploadScreen'
import InterviewScreen from './components/InterviewScreen'
import SummaryScreen from './components/SummaryScreen'

const STEPS = ['Setup', 'Interview', 'Report']

const BrainIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
  </svg>
)

const SettingsIcon = ({ className = "w-4.5 h-4.5" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
)

const CloseIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
)

const CheckIcon = () => (
  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
  </svg>
)

function StepNav({ screen }) {
  const activeIdx = screen === 'upload' ? 0 : screen === 'interview' ? 1 : 2
  return (
    <div className="flex items-center gap-1">
      {STEPS.map((step, i) => (
        <div key={step} className="flex items-center gap-1">
          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 ${
            i === activeIdx
              ? 'bg-blue-50 text-blue-700 ring-1 ring-blue-200'
              : i < activeIdx
              ? 'text-emerald-700 bg-emerald-50 ring-1 ring-emerald-200'
              : 'text-gray-400 bg-transparent'
          }`}>
            {i < activeIdx ? (
              <span className="w-4 h-4 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0">
                <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              </span>
            ) : (
              <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold flex-shrink-0 ${
                i === activeIdx ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
              }`}>{i + 1}</span>
            )}
            <span className="hidden sm:inline">{step}</span>
          </div>
          {i < STEPS.length - 1 && (
            <div className={`w-5 h-px mx-0.5 transition-colors duration-200 ${i < activeIdx ? 'bg-emerald-300' : 'bg-gray-200'}`} />
          )}
        </div>
      ))}
    </div>
  )
}

function SettingsModal({ questionCount, setQuestionCount, personality, setPersonality, enableTTS, setEnableTTS, enableSTT, setEnableSTT, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-6 animate-fade-in">
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative card-elevated max-w-md w-full p-7 animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="icon-box icon-box-sm bg-blue-50 border border-blue-100">
              <SettingsIcon className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <h3 className="text-base font-bold text-gray-900 font-display">Interview Settings</h3>
              <p className="text-xs text-gray-500 mt-0.5">Customize your screening session</p>
            </div>
          </div>
          <button onClick={onClose} className="btn-ghost w-8 h-8 rounded-lg flex items-center justify-center p-0">
            <CloseIcon />
          </button>
        </div>

        <div className="space-y-5">
          {/* Question Count */}
          <div>
            <label className="section-label block mb-2.5">Number of Questions</label>
            <div className="grid grid-cols-4 gap-2">
              {[3, 5, 7, 10].map(n => (
                <button
                  key={n}
                  onClick={() => setQuestionCount(n)}
                  className={`py-2.5 rounded-lg text-sm font-semibold transition-all cursor-pointer border ${
                    questionCount === n
                      ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                      : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300 hover:text-blue-700'
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          {/* Personality */}
          <div>
            <label className="section-label block mb-2.5">Interviewer Persona</label>
            <div className="space-y-2">
              {[
                { value: 'Professional Mentor', label: 'Professional Mentor', desc: 'Warm, structured & thorough', icon: '🎯' },
                { value: 'Rude Stress Interviewer', label: 'Stress Interviewer', desc: 'High-pressure, critical edge-cases', icon: '🔥' },
                { value: 'Academic Professor', label: 'Academic Professor', desc: 'Rigorous, theory-first', icon: '📚' },
              ].map(p => (
                <button
                  key={p.value}
                  onClick={() => setPersonality(p.value)}
                  className={`w-full flex items-center gap-3 p-3.5 rounded-xl border text-left cursor-pointer transition-all ${
                    personality === p.value
                      ? 'border-blue-300 bg-blue-50 ring-1 ring-blue-200'
                      : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <span className="text-xl">{p.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-semibold font-display ${personality === p.value ? 'text-blue-800' : 'text-gray-800'}`}>{p.label}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{p.desc}</p>
                  </div>
                  {personality === p.value && (
                    <span className="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                      <CheckIcon />
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Voice Toggles */}
          <div>
            <label className="section-label block mb-2.5">Voice Features</label>
            <div className="space-y-2">
              {[
                { label: 'Voice Readout (TTS)', desc: 'Questions read aloud by AI', value: enableTTS, set: setEnableTTS },
                { label: 'Dictation Input (STT)', desc: 'Speak your answers', value: enableSTT, set: setEnableSTT },
              ].map(({ label, desc, value, set }) => (
                <div key={label} className="flex items-center justify-between p-3.5 rounded-xl bg-gray-50 border border-gray-200">
                  <div>
                    <p className="text-sm font-semibold text-gray-800">{label}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
                  </div>
                  <label className="toggle cursor-pointer">
                    <input type="checkbox" checked={value} onChange={e => set(e.target.checked)} />
                    <div className="toggle-track" />
                  </label>
                </div>
              ))}
            </div>
          </div>
        </div>

        <button onClick={onClose} className="btn-primary w-full py-3 mt-6 text-sm">
          Save & Close
        </button>
      </div>
    </div>
  )
}

function App() {
  const [screen, setScreen] = useState('upload')
  const [sessionId, setSessionId] = useState(null)
  const [role, setRole] = useState('')
  const [skills, setSkills] = useState([])
  const [experienceLevel, setExperienceLevel] = useState('mid')
  const [questionCount, setQuestionCount] = useState(5)
  const [personality, setPersonality] = useState('Professional Mentor')
  const [enableTTS, setEnableTTS] = useState(true)
  const [enableSTT, setEnableSTT] = useState(true)
  const [showSettings, setShowSettings] = useState(false)

  return (
    <div className="min-h-screen page-bg">
      {showSettings && (
        <SettingsModal
          questionCount={questionCount} setQuestionCount={setQuestionCount}
          personality={personality} setPersonality={setPersonality}
          enableTTS={enableTTS} setEnableTTS={setEnableTTS}
          enableSTT={enableSTT} setEnableSTT={setEnableSTT}
          onClose={() => setShowSettings(false)}
        />
      )}

      {/* ===== HEADER ===== */}
      <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-5 py-3.5 flex items-center justify-between gap-4">
          {/* Logo */}
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-sm flex-shrink-0">
              <BrainIcon />
            </div>
            <div className="hidden sm:block min-w-0">
              <h1 className="text-sm font-bold text-gray-900 font-display leading-none">
                PGAGI Interview <span className="text-blue-600">AI</span>
              </h1>
              <p className="text-[9px] text-gray-400 font-semibold tracking-widest uppercase mt-0.5">RAG-Powered Screening</p>
            </div>
          </div>

          {/* Step Nav — center */}
          <div className="flex-1 flex justify-center">
            <StepNav screen={screen} />
          </div>

          {/* Right */}
          <div className="flex items-center gap-2.5 flex-shrink-0">
            {sessionId && (
              <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-100 border border-gray-200 text-xs text-gray-600 font-medium">
                <span className={`w-1.5 h-1.5 rounded-full ${
                  screen === 'summary' ? 'bg-emerald-500' :
                  screen === 'interview' ? 'bg-blue-500 animate-pulse' :
                  'bg-gray-400'
                }`} />
                {screen === 'interview' ? 'Live' : screen === 'summary' ? 'Complete' : 'Ready'}
              </div>
            )}
            {screen === 'upload' && (
              <button
                id="toggle-settings-btn"
                onClick={() => setShowSettings(true)}
                className="btn-ghost w-9 h-9 rounded-lg flex items-center justify-center p-0 border border-gray-200"
                title="Interview Settings"
              >
                <SettingsIcon className="w-4.5 h-4.5" />
              </button>
            )}
          </div>
        </div>
      </header>

      {/* ===== MAIN ===== */}
      <main className="max-w-6xl mx-auto px-5 py-10">
        {screen === 'upload' && (
          <div className="text-center mb-10 animate-slide-up">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-xs font-semibold text-blue-700 mb-5">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
              Powered by RAG · sentence-transformers · FAISS · OpenAI
            </div>
            <h2 className="text-4xl sm:text-5xl font-bold tracking-tight leading-[1.12] text-gray-900 mb-4 font-display">
              AI-Powered Technical
              <span className="block text-blue-600">Interview Screening</span>
            </h2>
            <p className="text-gray-500 text-base max-w-xl mx-auto leading-relaxed">
              Upload your resume and select a role. Our RAG pipeline retrieves domain knowledge,
              generates adaptive questions, and scores your answers in real time.
            </p>
          </div>
        )}

        <div>
          {screen === 'upload' && (
            <UploadScreen
              setScreen={setScreen} setSessionId={setSessionId}
              setRole={setRole} setSkills={setSkills}
              setExperienceLevel={setExperienceLevel}
              questionCount={questionCount} personality={personality}
            />
          )}
          {screen === 'interview' && (
            <InterviewScreen
              sessionId={sessionId} role={role} skills={skills}
              setScreen={setScreen} enableTTS={enableTTS} enableSTT={enableSTT}
            />
          )}
          {screen === 'summary' && (
            <SummaryScreen
              sessionId={sessionId} role={role}
              setScreen={setScreen} setSessionId={setSessionId}
            />
          )}
        </div>
      </main>

      {/* ===== FOOTER ===== */}
      <footer className="border-t border-gray-200 bg-white py-5 mt-16">
        <div className="max-w-6xl mx-auto px-5 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-gray-400">
          <span className="font-semibold tracking-wide text-gray-500 font-display">PGAGI Interview AI</span>
          <span>FastAPI · React · FAISS · sentence-transformers · OpenAI</span>
          <span>AI/ML &amp; Backend Intern Assignment</span>
        </div>
      </footer>
    </div>
  )
}

export default App
