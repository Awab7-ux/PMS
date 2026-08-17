import React, { useState, useRef } from 'react';
import '../Chat/ChatPage.css';

export default function MessageInput({ onSendMessage, disabled, _conversationType }) {
  const [content, setContent] = useState('');
  const textareaRef = useRef(null);

  const handleSend = async () => {
    if (!content.trim() || disabled) return;
    
    const messageContent = content.trim();
    setContent('');
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    
    await onSendMessage(messageContent);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextChange = (e) => {
    setContent(e.target.value);
    
    // Auto-expand textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  };

  return (
    <div className="message-input-container">
      <div className="message-input-wrapper">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={handleTextChange}
          onKeyDown={handleKeyDown}
          placeholder="Type a message... (Shift+Enter for new line)"
          disabled={disabled}
          className="message-textarea"
        />
        <button
          onClick={handleSend}
          disabled={!content.trim() || disabled}
          className="btn-send"
          title="Send message (Enter)"
        >
          {disabled ? '⏳' : '➤'}
        </button>
      </div>
      <div className="input-footer">
        <small>Press Enter to send, Shift+Enter for new line</small>
      </div>
    </div>
  );
}
