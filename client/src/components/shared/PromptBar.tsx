import React, { useState } from 'react';
import './PromptBar.css';

interface PromptBarProps {
  variant?: 'premium' | 'default';
  onSend: (message: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

const PromptBar: React.FC<PromptBarProps> = ({
  variant = 'default',
  onSend,
  isLoading = false,
  placeholder = 'Hỏi về học phí, học bổng, ký túc xá, đăng ký học phần...',
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [inputValue, setInputValue] = useState('');

  const isPremium = variant === 'premium';

  const handleSend = () => {
    const trimmed = inputValue.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setInputValue('');
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={`prompt-bar-wrapper ${isFocused ? 'focused' : ''} ${isPremium ? 'premium-variant' : 'default-variant'}`}>
      <div className="prompt-bar-container">
        
        {/* Render premium layers only if variant is premium */}
        {isPremium && (
          <>
            {/* Layer 2: Blurred rainbow glow following the border */}
            <div className="prompt-bar-glow-container">
              <div className="prompt-bar-glow"></div>
            </div>

            {/* Layer 1: Animated conic rainbow border */}
            <div className="prompt-bar-border-container">
              <div className="prompt-bar-border"></div>
            </div>
          </>
        )}
        
        {/* Content (Layer 3 & 4 styling depends on variant class) */}
        <div className={`prompt-bar-inner ${!isPremium ? 'default-style' : ''}`}>
          <input
            type="text"
            className="prompt-input"
            placeholder={placeholder}
            value={inputValue}
            disabled={isLoading}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
          />

          <div className="prompt-actions">
            <button
              type="button"
              className={`prompt-btn send-btn ${inputValue.trim() && !isLoading ? 'active-text' : ''}`}
              onClick={handleSend}
              disabled={!inputValue.trim() || isLoading}
              aria-label="Gửi câu hỏi"
            >
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
                {isLoading ? 'hourglass_empty' : 'send'}
              </span>
            </button>
          </div>
        </div>
      </div>

      <div className="prompt-footer-container">
        <p className="prompt-footer font-label-sm">
          Trợ lý AI có thể mắc sai sót. Không thay thế thông báo chính thức từ trường.
        </p>
      </div>
    </div>
  );
};

export default PromptBar;
