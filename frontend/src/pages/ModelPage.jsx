import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { getModelInfo, getMetrics } from '../services/api'
import { TrophyIcon, CpuChipIcon } from '@heroicons/react/24/outline'

export default function ModelPage() {
  const { data: info }    = useQuery({ queryKey: ['model-info'],    queryFn: () => getModelInfo().then(r => r.data),  retry: false })
  const { data: metrics } = useQuery({ queryKey: ['model-metrics'], queryFn: () => getMetrics().then(r => r.data),   retry: false })

  return (
    <div className="min-h-screen gradient-mesh pt-24 pb-16 px-4">
      <div className="max-w-5xl mx-auto space-y-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-display text-4xl font-bold text-white mb-2">Model Info</h1>
          <p className="text-slate-400">Details about the trained model and performance metrics.</p>
        </motion.div>

        {/* Model card */}
        {info ? (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card">
            <div className="flex items-center gap-3 mb-6">
              <CpuChipIcon className="w-6 h-6 text-brand-400" />
              <h2 className="font-display font-semibold text-white text-xl">Active Model</h2>
              <span className="ml-auto badge bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/30">Loaded</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Algorithm',  value: info.algorithm || '—' },
                { label: 'Features',   value: info.n_features ?? '—' },
                { label: 'Emotions',   value: info.emotions?.join(', ') || '—' },
                { label: 'Loss',       value: info.loss ?? '—' },
              ].map(({ label, value }) => (
                <div key={label} className="bg-surface rounded-xl p-4">
                  <p className="text-slate-400 text-xs mb-1">{label}</p>
                  <p className="text-white font-semibold text-sm break-words">{String(value)}</p>
                </div>
              ))}
            </div>
          </motion.div>
        ) : (
          <div className="card text-center py-12">
            <p className="text-slate-400">No model loaded. POST to <code className="text-brand-400 font-mono">/api/v1/train</code> to train.</p>
          </div>
        )}

        {/* Comparison table */}
        {metrics?.model_comparison && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card">
            <div className="flex items-center gap-3 mb-6">
              <TrophyIcon className="w-6 h-6 text-yellow-400" />
              <h2 className="font-display font-semibold text-white text-xl">Model Comparison</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-400 border-b border-surface-border text-xs uppercase tracking-wider">
                    <th className="pb-3 pr-6 font-medium">Model</th>
                    <th className="pb-3 pr-6 font-medium">Accuracy</th>
                    <th className="pb-3 pr-6 font-medium">F1 (weighted)</th>
                    <th className="pb-3 pr-6 font-medium">CV F1 ± std</th>
                    <th className="pb-3 font-medium">Time (s)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border/50">
                  {Object.entries(metrics.model_comparison).map(([name, m]) => {
                    const isBest = name === metrics.best_model
                    return (
                      <tr key={name} className={`${isBest ? 'bg-brand-500/5' : ''} hover:bg-white/2 transition-colors`}>
                        <td className="py-3 pr-6 font-medium text-white flex items-center gap-2">
                          {isBest && <TrophyIcon className="w-4 h-4 text-yellow-400" />}
                          {name}
                        </td>
                        <td className="py-3 pr-6 text-slate-200">{m.accuracy}%</td>
                        <td className="py-3 pr-6">
                          <span className={`font-semibold ${isBest ? 'text-brand-400' : 'text-slate-200'}`}>
                            {(m.f1_weighted * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-3 pr-6 text-slate-400 font-mono text-xs">
                          {(m.cv_f1_mean * 100).toFixed(1)}% ± {(m.cv_f1_std * 100).toFixed(1)}%
                        </td>
                        <td className="py-3 text-slate-400">{m.training_time_s}s</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}
