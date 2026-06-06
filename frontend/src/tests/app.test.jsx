import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// ── Helpers ────────────────────────────────────────────────────────────────────

const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })

function Wrapper({ children }) {
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

// ── Mock API ───────────────────────────────────────────────────────────────────

vi.mock('../src/services/api', () => ({
  healthCheck: vi.fn(() => Promise.resolve({ data: { status: 'ok', model_loaded: true } })),
  getDashboard: vi.fn(() =>
    Promise.resolve({
      data: {
        total_predictions: 42,
        avg_confidence: 78.5,
        emotion_distribution: { happy: 20, calm: 12, fearful: 6, disgust: 4 },
        recent_predictions: [],
      },
    })
  ),
  getModelInfo: vi.fn(() =>
    Promise.resolve({ data: { loaded: true, algorithm: 'MLPClassifier', n_features: 180 } })
  ),
  getMetrics: vi.fn(() => Promise.resolve({ data: { best_model: 'MLP', best_accuracy: 72.4 } })),
  getEmotions: vi.fn(() =>
    Promise.resolve({
      data: {
        observed_emotions: ['calm', 'happy', 'fearful', 'disgust'],
        emoji_map: { calm: '😌', happy: '😄' },
      },
    })
  ),
}))

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('EmotionResult', () => {
  it('renders emotion label and confidence', async () => {
    const { default: EmotionResult } = await import('../src/components/ui/EmotionResult')
    const colors = { bg: 'bg-yellow-400/20', text: 'text-yellow-300', ring: 'ring-yellow-400/40', emoji: '😄' }
    const result = {
      predicted_emotion: 'happy',
      confidence: 82.5,
      all_probabilities: { calm: 5, happy: 82.5, fearful: 8, disgust: 4.5 },
    }
    render(<Wrapper><EmotionResult result={result} colors={colors} /></Wrapper>)
    expect(screen.getByText('happy')).toBeDefined()
    expect(screen.getByText('82.5%')).toBeDefined()
  })
})

describe('API service', () => {
  it('healthCheck resolves with status ok', async () => {
    const { healthCheck } = await import('../src/services/api')
    const res = await healthCheck()
    expect(res.data.status).toBe('ok')
  })
})
