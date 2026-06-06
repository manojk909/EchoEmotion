import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { MicrophoneIcon, BoltIcon, ChartBarIcon, ShieldCheckIcon } from '@heroicons/react/24/outline'
import { useQuery } from '@tanstack/react-query'
import { healthCheck } from '../services/api'

const FEATURES = [
  {
    icon: MicrophoneIcon,
    title: 'Real-Time Detection',
    desc: 'Record your voice directly in the browser and get instant emotion analysis.',
  },
  {
    icon: BoltIcon,
    title: 'Multi-Model Pipeline',
    desc: 'MLP, Random Forest, SVM, XGBoost, and LightGBM compete; the best wins automatically.',
  },
  {
    icon: ChartBarIcon,
    title: 'Rich Analytics',
    desc: 'Probability charts, radar profiles, and a full dashboard to track prediction history.',
  },
  {
    icon: ShieldCheckIcon,
    title: 'Production-Ready',
    desc: 'FastAPI + PostgreSQL + Docker + JWT auth. Ready for deployment on any cloud.',
  },
]

const EMOTIONS = [
  { emoji: '😌', label: 'Calm',    color: 'text-blue-300' },
  { emoji: '😄', label: 'Happy',   color: 'text-yellow-300' },
  { emoji: '😨', label: 'Fearful', color: 'text-purple-300' },
  { emoji: '🤢', label: 'Disgust', color: 'text-red-300' },
]

export default function LandingPage() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => healthCheck().then(r => r.data),
    retry: false,
  })

  return (
    <div className="min-h-screen gradient-mesh">
      {/* Hero */}
      <section className="pt-32 pb-20 px-4 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto"
        >
          {/* Status badge */}
          {health && (
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 ring-1 ring-emerald-500/30 text-emerald-300 text-xs font-medium mb-8">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              API Online · Model {health.model_loaded ? 'Loaded' : 'Not trained'}
            </div>
          )}

          {/* Animated mic icon */}
          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
            className="inline-flex items-center justify-center w-24 h-24 rounded-3xl bg-brand-500/15 ring-2 ring-brand-500/30 mb-8"
          >
            <MicrophoneIcon className="w-12 h-12 text-brand-400" />
          </motion.div>

          <h1 className="font-display text-6xl md:text-7xl font-extrabold text-white leading-tight mb-6">
            Hear what voices<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-purple-400">
              truly feel
            </span>
          </h1>

          <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10">
            EchoEmotion detects human emotions from speech using a multi-model ML pipeline
            trained on the RAVDESS dataset. Upload audio or speak live.
          </p>

          <div className="flex flex-wrap gap-4 justify-center">
            <Link to="/predict" className="btn-primary text-base px-8 py-3.5 flex items-center gap-2">
              <MicrophoneIcon className="w-5 h-5" />
              Try it now
            </Link>
            <Link to="/dashboard" className="btn-ghost text-base px-8 py-3.5 ring-1 ring-surface-border">
              View Dashboard
            </Link>
          </div>
        </motion.div>

        {/* Emotion chips */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="flex justify-center gap-4 mt-14 flex-wrap"
        >
          {EMOTIONS.map(({ emoji, label, color }, i) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 + i * 0.1 }}
              className="flex items-center gap-2 px-5 py-3 card text-sm font-medium"
            >
              <span className="text-xl">{emoji}</span>
              <span className={color}>{label}</span>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* Features */}
      <section className="py-20 px-4 border-t border-surface-border">
        <div className="max-w-6xl mx-auto">
          <motion.h2
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="font-display text-3xl font-bold text-white text-center mb-14"
          >
            Everything you need
          </motion.h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map(({ icon: Icon, title, desc }, i) => (
              <motion.div
                key={title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="card hover:border-brand-500/30 transition-colors duration-300 group"
              >
                <div className="w-10 h-10 rounded-xl bg-brand-500/10 flex items-center justify-center mb-4 group-hover:bg-brand-500/20 transition-colors">
                  <Icon className="w-5 h-5 text-brand-400" />
                </div>
                <h3 className="font-display font-semibold text-white mb-2">{title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
