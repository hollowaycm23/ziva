import { useState, useEffect, useCallback } from 'react'
import { fetchMemory } from '../api'

export function useMemory() {
  const [items, setItems] = useState([])

  const poll = useCallback(async () => {
    try {
      const d = await fetchMemory()
      setItems(d.items || [])
    } catch {}
  }, [])

  useEffect(() => {
    poll()
    const id = setInterval(poll, 5000)
    return () => clearInterval(id)
  }, [poll])

  return items
}
