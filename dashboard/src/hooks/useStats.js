import { useState, useEffect, useCallback } from 'react'
import { fetchStats } from '../api'

export function useStats() {
  const [stats, setStats] = useState({ cpu: 0, ram: 0, disk: 0, gpu: null })

  const poll = useCallback(async () => {
    try {
      const d = await fetchStats()
      setStats(d)
    } catch {}
  }, [])

  useEffect(() => {
    poll()
    const id = setInterval(poll, 2000)
    return () => clearInterval(id)
  }, [poll])

  return stats
}
