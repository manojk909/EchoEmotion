import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  PieChart, Pie, Cell, ResponsiveContainer, Legend,
} from 'recharts'
import { getDashboard } from '../services/api'
import { MicrophoneIcon, ChartBarIcon, SparklesIcon, ClockIcon } from '@heroicons/react/24/outline'

const COLORS = ['#0ea5e9', '#a855f7', '#f59e0b', '#ef4444', '#22c55e', '#06b6d4', '#ec4899', '#84cc16']

const EMOJI = {
  happy:'😄', calm:'😌', fearful:'😨', disgust:'🤢',
  angry:'😠', sad:'😢', neutral:'😐', surprised:'😲',
}

function StatCard({ icon: Icon, label, value, color = 'brand' }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl bg-${color}-500/15 flex items-center justify-center`}>
        <Icon className={`w-6 h-6 text-${color}-400`} />
      </div>
      <div>
        <p className="text-slate-400 text-sm">{label}</p>
        <p className="text-2xl font-display font-bold text-white">{value}</p>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => getDashboard().then((r) => r.data),
    refetchInterval: 30_000,
  })

  if (isLoading) return (
    <div className="min-h-screen gradient-mesh pt-24 flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
    </div>
  )

  if (error) return (
    <div className="min-h-screen gradient-mesh pt-24 flex items-center justify-center">
      <p className="text-slate-400">Could not load dashboard. Make sure the backend is running.</p>
    </div>
  )

  const distData = Object.entries(data.emotion_distribution || {}).map(([name, value]) => ({ name, value }))
  const recentByEmotion = distData.sort((a, b) => b.value - a.value)

  return (
    <div className="min-h-screen gradient-mesh pt-24 pb-16 px-4">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-display text-4xl font-bold text-white mb-2">Dashboard</h1>
          <p className="text-slate-400">Prediction analytics and statistics.</p>
        </motion.div>

        {/* Stat cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          <StatCard icon={MicrophoneIcon} label="Total Predictions" value={data.total_predictions} />
          <StatCard icon={SparklesIcon}   label="Avg Confidence"    value={`${data.avg_confidence}%`} color="purple" />
          <StatCard icon={ChartBarIcon}   label="Emotions Tracked"  value={distData.length} color="emerald" />
          <StatCard icon={ClockIcon}      label="Recent (10)"       value={data.recent_predictions.length} color="amber" />
        </motion.div>

        {/* Charts row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Bar chart */}
          <motion.div
            initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="card"
          >
            <h3 className="font-display font-semibold text-white mb-6">Emotion Distribution</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={recentByEmotion}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
                  cursor={{ fill: 'rgba(14,165,233,0.05)' }}
                />
                <Bar dataKey="value" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Pie chart */}
          <motion.div
            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.25 }}
            className="card"
          >
            <h3 className="font-display font-semibold text-white mb-6">Share by Emotion</h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={distData} cx="50%" cy="50%"
                  innerRadius={60} outerRadius={90}
                  dataKey="value" nameKey="name"
                  paddingAngle={3}
                >
                  {distData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Recent predictions table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card"
        >
          <h3 className="font-display font-semibold text-white mb-6">Recent Predictions</h3>
          {data.recent_predictions.length === 0 ? (
            <p className="text-slate-500 text-center py-8">No predictions yet. Go to Predict!</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-400 border-b border-surface-border">
                    <th className="pb-3 pr-4 font-medium">File</th>
                    <th className="pb-3 pr-4 font-medium">Emotion</th>
                    <th className="pb-3 pr-4 font-medium">Confidence</th>
                    <th className="pb-3 pr-4 font-medium">Duration</th>
                    <th className="pb-3 font-medium">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border/50">
                  {data.recent_predictions.map((p) => (
                    <tr key={p.id} className="hover:bg-white/2 transition-colors">
                      <td className="py-3 pr-4 text-slate-300 font-mono text-xs truncate max-w-[140px]">{p.filename}</td>
                      <td className="py-3 pr-4">
                        <span className="flex items-center gap-1.5 font-medium text-slate-200">
                          {EMOJI[p.predicted_emotion] || '🎵'} {p.predicted_emotion}
                        </span>
                      </td>
                      <td className="py-3 pr-4">
                        <span className={`font-semibold ${p.confidence > 70 ? 'text-emerald-400' : p.confidence > 50 ? 'text-amber-400' : 'text-red-400'}`}>
                          {p.confidence}%
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-slate-400">{p.audio_duration_s ? `${p.audio_duration_s}s` : '—'}</td>
                      <td className="py-3 text-slate-400 text-xs">
                        {p.created_at ? new Date(p.created_at).toLocaleTimeString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
