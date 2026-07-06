import { useMemo } from 'react'
import { marked } from 'marked'

export default function Message({ msg }) {
  const { role, content, meta } = msg

  const html = useMemo(() => {
    if (role === 'assistant') {
      try { return marked.parse(content) } catch {}
    }
    return null
  }, [role, content])

  return (
    <div className={`message ${role}`}>
      {html ? (
        <div dangerouslySetInnerHTML={{ __html: html }} />
      ) : (
        <p>{content}</p>
      )}
      {meta && (
        <span className="meta-info">
          [{meta.model} | {meta.task}] used {meta.ctx} memories
        </span>
      )}
    </div>
  )
}
