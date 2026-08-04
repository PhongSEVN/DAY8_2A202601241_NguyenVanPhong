import React, { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import gsap from 'gsap';
import ChatBubble from '../components/chat/ChatBubble';
import CitationList from '../components/chat/CitationList';
import MarkdownContent from '../components/chat/MarkdownContent';
import SuggestionChip from '../components/shared/SuggestionChip';
import PromptBar from '../components/shared/PromptBar';
import { queryUniversityAssistant, ApiError, type Citation } from '../lib/api';
import './ChatPage.css';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  isError?: boolean;
}

const STARTER_QUESTIONS = [
  'Học phí tại RMIT Vietnam là bao nhiêu?',
  'Điều kiện xin học bổng Academic Achievement?',
  'Cách đăng ký học phần qua myRMIT?',
];

function createMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const previousMessageCount = useRef(0);

  useEffect(() => {
    if (!containerRef.current) return;
    if (messages.length === previousMessageCount.current) return;
    previousMessageCount.current = messages.length;

    const newest = containerRef.current.querySelectorAll('.message-enter');
    const lastMessage = newest[newest.length - 1];
    if (lastMessage) {
      gsap.fromTo(
        lastMessage,
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.5, ease: 'power2.out' },
      );
    }
    containerRef.current.scrollTo({ top: containerRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (question: string) => {
    const userMessage: ChatMessage = { id: createMessageId(), role: 'user', content: question };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const conversationHistory = messages.map((message) => ({
        role: message.role,
        content: message.content,
      }));
      const result = await queryUniversityAssistant(question, conversationHistory);
      setMessages((prev) => [
        ...prev,
        {
          id: createMessageId(),
          role: 'assistant',
          content: result.answer,
          citations: result.citations,
        },
      ]);
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : 'Không thể kết nối tới máy chủ. Vui lòng thử lại.';
      setMessages((prev) => [
        ...prev,
        { id: createMessageId(), role: 'assistant', content: message, isError: true },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const location = useLocation();
  const hasConsumedInitialQuestion = useRef(false);

  useEffect(() => {
    const initialQuestion = (location.state as { initialQuestion?: string } | null)
      ?.initialQuestion;
    if (initialQuestion && !hasConsumedInitialQuestion.current) {
      hasConsumedInitialQuestion.current = true;
      handleSend(initialQuestion);
    }
    // Runs once on mount to consume the question passed from HomePage's navigation
    // state; handleSend is intentionally omitted since re-running on every render
    // would keep re-sending the same initial question.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const hasMessages = messages.length > 0;

  return (
    <div className="chat-page-container">
      <div className="chat-header">
        <div className="chat-title">
          <span className="font-headline-md font-medium text-on-surface">Trợ lý Dịch vụ Đại học AI</span>
        </div>
      </div>

      <div className="chat-scroll-area custom-scrollbar" ref={containerRef}>
        <div className="chat-content">
          {!hasMessages && (
            <div className="chat-empty-state">
              <p className="font-body-md text-on-surface-variant">
                Đặt câu hỏi về chính sách và dịch vụ đại học để bắt đầu.
              </p>
              <div className="chip-row">
                {STARTER_QUESTIONS.map((question) => (
                  <SuggestionChip
                    key={question}
                    label={question}
                    onClick={() => handleSend(question)}
                  />
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div className="message-enter" key={message.id}>
              <ChatBubble isUser={message.role === 'user'}>
                {message.role === 'assistant' ? (
                  <div style={{ color: message.isError ? 'var(--error)' : undefined }}>
                    <MarkdownContent content={message.content} />
                  </div>
                ) : (
                  <p style={{ lineHeight: 1.6 }}>{message.content}</p>
                )}
                {message.citations && message.citations.length > 0 && (
                  <CitationList citations={message.citations} />
                )}
              </ChatBubble>
            </div>
          ))}

          {isLoading && (
            <div className="message-enter">
              <ChatBubble isUser={false}>
                <p className="font-body-md text-on-surface-variant">Đang tra cứu...</p>
              </ChatBubble>
            </div>
          )}
        </div>
      </div>

      <div className="chat-prompt-area">
        <PromptBar onSend={handleSend} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default ChatPage;
