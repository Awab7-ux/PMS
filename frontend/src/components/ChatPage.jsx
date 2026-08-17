import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { conversationApi } from '../services/api';
import ConversationList from './Chat/ConversationList';
import ConversationView from './Chat/ConversationView';
import './Chat/ChatPage.css';

export default function ChatPage() {
  const { orgId: organizationId } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!organizationId) return;
    loadConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [organizationId]);

  const loadConversations = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await conversationApi.list(organizationId);
      setConversations(response.data || []);
    } catch (err) {
      setError(err.message || 'Failed to load conversations');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectConversation = (conversation) => {
    setSelectedConversation(conversation);
  };

  const handleConversationCreated = (newConversation) => {
    setConversations([newConversation, ...conversations]);
    setSelectedConversation(newConversation);
  };

  const handleConversationUpdated = (updatedConversation) => {
    setConversations(
      conversations.map((c) => (c.id === updatedConversation.id ? updatedConversation : c))
    );
    if (selectedConversation?.id === updatedConversation.id) {
      setSelectedConversation(updatedConversation);
    }
  };

  const handleConversationDeleted = (conversationId) => {
    setConversations(conversations.filter((c) => c.id !== conversationId));
    if (selectedConversation?.id === conversationId) {
      setSelectedConversation(null);
    }
  };

  return (
    <div className="chat-page">
      <div className="chat-sidebar">
        <ConversationList
          conversations={conversations}
          selectedConversation={selectedConversation}
          onSelectConversation={handleSelectConversation}
          onConversationCreated={handleConversationCreated}
          organizationId={organizationId}
          loading={loading}
          error={error}
          onRefresh={loadConversations}
        />
      </div>
      <div className="chat-main">
        {selectedConversation ? (
          <ConversationView
            conversation={selectedConversation}
            organizationId={organizationId}
            onConversationUpdated={handleConversationUpdated}
            onConversationDeleted={handleConversationDeleted}
          />
        ) : (
          <div className="chat-empty-state">
            <div className="empty-icon">💬</div>
            <h3>No conversation selected</h3>
            <p>Select a conversation or create a new one to start chatting</p>
          </div>
        )}
      </div>
    </div>
  );
}
