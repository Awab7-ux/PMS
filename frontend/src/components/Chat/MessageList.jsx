import React, { useState, useEffect, useRef } from 'react';
import '../Chat/ChatPage.css';

export default function MessageList({ messages, loading, onEditMessage, onDeleteMessage }) {
  const [editingId, setEditingId] = useState(null);
  const [editContent, setEditContent] = useState('');
  const endRef = useRef(null);
  const messageListRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (endRef.current) {
      endRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [messages]);

  const formatTime = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleEditClick = (message) => {
    setEditingId(message.id);
    setEditContent(message.content);
  };

  const handleSaveEdit = async (messageId) => {
    if (!editContent.trim()) {
      setEditingId(null);
      return;
    }
    await onEditMessage(messageId, editContent);
    setEditingId(null);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditContent('');
  };

  return (
    <div className="message-list" ref={messageListRef}>
      {loading ? (
        <div className="loading">Loading messages...</div>
      ) : messages.length === 0 ? (
        <div className="empty-messages">
          <div className="empty-icon">💬</div>
          <p>No messages yet. Start a conversation!</p>
        </div>
      ) : (
        messages.map((message, _index) => (
          <div key={message.id} className="message-group">
            <div className="message">
              <div className="message-avatar">
                {message.sender_avatar_url ? (
                  <img src={message.sender_avatar_url} alt={message.sender_name} />
                ) : (
                  <div className="avatar-placeholder">{message.sender_name?.[0]?.toUpperCase() || '?'}</div>
                )}
              </div>
              <div className="message-content-wrapper">
                <div className="message-header">
                  <div className="message-sender">{message.sender_name}</div>
                  <div className="message-time">{formatTime(message.created_at)}</div>
                </div>
                {editingId === message.id ? (
                  <div className="message-edit-form">
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      placeholder="Edit message..."
                    />
                    <div className="edit-actions">
                      <button onClick={() => handleSaveEdit(message.id)} className="btn-save">
                        Save
                      </button>
                      <button onClick={handleCancelEdit} className="btn-cancel">
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="message-text">
                      {message.is_deleted ? (
                        <em className="deleted-message">This message was deleted</em>
                      ) : (
                        message.content
                      )}
                    </div>
                    {message.updated_at !== message.created_at && !message.is_deleted && (
                      <div className="message-edited">(edited)</div>
                    )}
                  </>
                )}
              </div>
              {!message.is_deleted && editingId !== message.id && (
                <div className="message-actions">
                  <button
                    className="btn-icon"
                    onClick={() => handleEditClick(message)}
                    title="Edit message"
                  >
                    ✏️
                  </button>
                  <button
                    className="btn-icon"
                    onClick={() => onDeleteMessage(message.id)}
                    title="Delete message"
                  >
                    🗑️
                  </button>
                </div>
              )}
            </div>
          </div>
        ))
      )}
      <div ref={endRef} />
    </div>
  );
}
