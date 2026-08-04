export interface Citation {
  label: string
  documentId: string
  content: string
}

export interface QueryResult {
  answer: string
  citations: Citation[]
  confidence: number
}

export interface ConversationTurn {
  role: string
  content: string
}

interface RawCitation {
  label: string
  document_id: string
  content: string
}

interface RawQueryResponse {
  answer: string
  citations: RawCitation[]
  confidence: number
}

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function queryLegalAssistant(
  question: string,
  conversationHistory: ConversationTurn[] = [],
): Promise<QueryResult> {
  const response = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, conversation_history: conversationHistory }),
  })

  if (!response.ok) {
    throw new ApiError(`Truy vấn thất bại (mã lỗi ${response.status})`, response.status)
  }

  const data: RawQueryResponse = await response.json()
  return {
    answer: data.answer,
    confidence: data.confidence,
    citations: data.citations.map((citation) => ({
      label: citation.label,
      documentId: citation.document_id,
      content: citation.content,
    })),
  }
}
