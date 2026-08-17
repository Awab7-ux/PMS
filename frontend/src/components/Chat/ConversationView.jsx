import React, { useState, useEffect, useRef, useCallback } from 'react';
import { conversationApi } from '../../services/api';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import '../Chat/ChatPage.css';

export default function ConversationView({
  conversation,
  _organizationId,
  _onConversationUpdated,
  _onConversationDeleted,
}) {
  const [messages, setMessages] = useState([]);
  const [_members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sending, setSending] = useState(false);
  const pollingTimeoutRef = useRef(null);
  const lastMessageIdRef = useRef(null);
  const isVisibleRef = useRef(true);
  const conversationIdRef = useRef(conversation.id);

  // Handle visibility changes (tab focus)
  useEffect(() => {
    const handleVisibilityChange = () => {
      isVisibleRef.current = !document.hidden;
      if (isVisibleRef.current) {
        // Poll immediately when tab becomes visible
        pollMessages();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load initial messages and members
  useEffect(() => {
    conversationIdRef.current = conversation.id;
    loadConversation();
    loadMembers();
    
    // Start polling
    pollMessages();

    return () => {
      if (pollingTimeoutRef.current) {
        clearTimeout(pollingTimeoutRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversation.id]);

  const loadConversation = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await conversationApi.getMessages(conversation.id, { limit: 50, offset: 0 });
      const messages = response.data || [];
      setMessages(messages);
      if (messages.length > 0) {
        lastMessageIdRef.current = messages[messages.length - 1].id;
      }
      // Mark as read
      try {
        await conversationApi.markAsRead(conversation.id);
      } catch (_err) {
        // Ignore read status errors
      }
    } catch (err) {
      setError(err.message || 'Failed to load messages');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadMembers = async () => {
    try {
      const response = await conversationApi.listMembers(conversation.id);
      setMembers(response.data || []);
    } catch (err) {
      console.error('Failed to load members:', err);
    }
  };

  const pollMessages = useCallback(() => {
    // Clear any existing timeout
    if (pollingTimeoutRef.current) {
      clearTimeout(pollingTimeoutRef.current);
    }

    // Only poll if conversation is active and we haven't unmounted
    if (!isVisibleRef.current || !conversationIdRef.current) {
      // Schedule next poll at longer interval when not visible
      const nextPoll = setTimeout(pollMessages, 10000);
      pollingTimeoutRef.current = nextPoll;
      return;
    }

    const fetchNewMessages = async () => {
      try {
        if (lastMessageIdRef.current) {
          const response = await conversationApi.getMessagesSince(
            conversationIdRef.current,
            lastMessageIdRef.current,
            50
          );
          const newMessages = response.data || response.items || [];
          if (newMessages.length > 0) {
            setMessages((prev) => [...prev, ...newMessages]);
            lastMessageIdRef.current = newMessages[newMessages.length - 1].id;
          }
        }
      } catch (_err) {
        // Silently ignore polling errors to avoid spam
      }

      // Schedule next poll (every 3 seconds when visible, every 10 seconds when hidden)
      const interval = isVisibleRef.current ? 3000 : 10000;
      const nextPoll = setTimeout(pollMessages, interval);
      pollingTimeoutRef.current = nextPoll;
    };

    fetchNewMessages();
  }, []);

  const handleSendMessage = async (content) => {
    if (!content.trim()) return;

    try {
      setSending(true);
      const response = await conversationApi.sendMessage(conversation.id, content);
      const newMessage = response.data || response;
      
      // Add message optimistically
      setMessages((prev) => [...prev, newMessage]);
      lastMessageIdRef.current = newMessage.id;
      
      // Mark as read
      try {
        await conversationApi.markAsRead(conversation.id);
      } catch (_err) {
        // Ignore read status errors
      }
    } catch (err) {
      alert('Failed to send message: ' + (err.message || 'Unknown error'));
      console.error(err);
    } finally {
      setSending(false);
    }
  };

  const handleEditMessage = async (messageId, content) => {
    try {
      const response = await conversationApi.editMessage(messageId, content);
      const updated = response.data || response;
      setMessages((prev) =>
        prev.map((m) => (m.id === messageId ? updated : m))
      );
    } catch (_err) {
      alert('Failed to edit message: ' + (_err.message || 'Unknown error'));
      console.error(_err);
    }
  };

  const handleDeleteMessage = async (messageId) => {
    try {
      await conversationApi.deleteMessage(messageId);
      setMessages((prev) => prev.map((m) =>
        m.id === messageId ? { ...m, is_deleted: true } : m
      ));
    } catch (_err) {
      alert('Failed to delete message: ' + (_err.message || 'Unknown error'));
      console.error(_err);
    }
  };

  return (
    <div className="conversation-view">
      <div className="conversation-header">
        <div className="header-content">
          <h2>{conversation.name || 'Conversation'}</h2>
          <div className="header-info">
            {conversation.type === 'direct' && <span className="badge-type">Direct Message</span>}
            {conversation.type === 'group' && <span className="badge-type">Group • {conversation.members_count} members</span>}
            {conversation.type === 'project' && <span className="badge-type">Project Chat</span>}
            {conversation.type === 'team' && <span className="badge-type">Team Chat</span>}
          </div>
        </div>
        <div className="header-actions">
          {/* Future: Add settings button */}
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <MessageList
        messages={messages}
        loading={loading}
        onEditMessage={handleEditMessage}
        onDeleteMessage={handleDeleteMessage}
      />

      <MessageInput
        onSendMessage={handleSendMessage}
        disabled={sending}
        conversationType={conversation.type}
      />
    </div>
  );
}
