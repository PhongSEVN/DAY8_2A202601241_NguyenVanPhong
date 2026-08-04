import React from 'react';

interface ChatBubbleProps {
  isUser: boolean;
  children: React.ReactNode;
}

const ChatBubble: React.FC<ChatBubbleProps> = ({ isUser, children }) => {
  return (
    <div 
      className={`animate-fade-in-up flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}
      style={{ marginBottom: '32px' }}
    >
      {!isUser && (
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          marginRight: '16px',
          marginTop: '4px',
          backgroundColor: 'var(--primary-container)',
        }}>
          <span
            className="material-symbols-outlined"
            style={{ fontSize: '20px', color: 'var(--on-primary)' }}
          >
            school
          </span>
        </div>
      )}
      
      <div 
        className={isUser ? 'font-body-md' : 'font-body-md'}
        style={{
          maxWidth: '85%',
          backgroundColor: isUser ? 'var(--surface-container-high)' : 'transparent',
          borderRadius: isUser ? '28px' : '0',
          padding: isUser ? '16px 24px' : '0',
          color: 'var(--on-surface)'
        }}
      >
        {children}
      </div>
    </div>
  );
};

export default ChatBubble;
