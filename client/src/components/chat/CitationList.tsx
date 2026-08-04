import { useState } from 'react'
import type { Citation } from '../../lib/api'
import './CitationList.css'

interface CitationListProps {
  citations: Citation[]
}

function CitationList({ citations }: CitationListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  if (citations.length === 0) {
    return null
  }

  return (
    <div className="citation-list">
      {citations.map((citation, index) => {
        const key = `${citation.documentId}-${index}`
        const isExpanded = expandedId === key
        return (
          <div key={key} className="citation-card">
            <button
              type="button"
              className="citation-header"
              onClick={() => setExpandedId(isExpanded ? null : key)}
            >
              <span className="material-symbols-outlined citation-icon">description</span>
              <span className="citation-label">{citation.label}</span>
              <span className="material-symbols-outlined citation-chevron">
                {isExpanded ? 'expand_less' : 'expand_more'}
              </span>
            </button>
            {isExpanded && <p className="citation-content">{citation.content}</p>}
          </div>
        )
      })}
    </div>
  )
}

export default CitationList
