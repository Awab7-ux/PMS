import React, { useEffect, useState } from 'react';
import { conversationApi, userApi } from '../../services/api';
import '../Chat/ChatPage.css';

export default function ConversationList({
  conversations,
  selectedConversation,
  onSelectConversation,
  onConversationCreated,
  organizationId,
  loading,
  error,
  _onRefresh,
}) {
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [dialogType, setDialogType] = useState('direct');
  const [formData, setFormData] = useState({ otherUserId: '', name: '', memberIds: [] });
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [userError, setUserError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!showNewDialog || !organizationId) return;

    let cancelled = false;
    const loadOrgUsers = async () => {
      setLoadingUsers(true);
      setUserError('');
      try {
        const response = await userApi.list({ organization_id: organizationId, per_page: 100 });
        if (!cancelled) {
          setUsers(response.data || []);
        }
      } catch (err) {
        if (!cancelled) {
          setUserError(err.message || 'Unable to load organization users.');
          setUsers([]);
        }
      } finally {
        if (!cancelled) {
          setLoadingUsers(false);
        }
      }
    };

    loadOrgUsers();
    return () => { cancelled = true; };
  }, [showNewDialog, organizationId]);

  const handleCreateDirect = async () => {
    if (!formData.otherUserId) return;
    try {
      setSubmitting(true);
      const data = await conversationApi.createDirect({
        other_user_id: formData.otherUserId,
        organization_id: organizationId,
      });
      onConversationCreated(data.data || data);
      setFormData({ otherUserId: '', name: '', memberIds: [] });
      setShowNewDialog(false);
    } catch (err) {
      alert('Failed to create conversation: ' + (err.message || 'Unknown error'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateGroup = async () => {
    if (!formData.name || formData.memberIds.length === 0) return;
    try {
      setSubmitting(true);
      const data = await conversationApi.createGroup({
        organization_id: organizationId,
        name: formData.name,
        member_ids: formData.memberIds,
      });
      onConversationCreated(data.data || data);
      setFormData({ otherUserId: '', name: '', memberIds: [] });
      setShowNewDialog(false);
    } catch (err) {
      alert('Failed to create conversation: ' + (err.message || 'Unknown error'));
    } finally {
      setSubmitting(false);
    }
  };

  const toggleGroupMember = (userId) => {
    setFormData((prev) => {
      const next = prev.memberIds.includes(userId)
        ? prev.memberIds.filter((id) => id !== userId)
        : [...prev.memberIds, userId];
      return { ...prev, memberIds: next };
    });
  };

  const formatTime = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getConversationName = (conv) => {
    if (conv.name) return conv.name;
    if (conv.type === 'direct') {
      return 'Direct Message';
    }
    return `Conversation (${conv.type})`;
  };

  return (
    <div className="conversation-list">
      <div className="list-header">
        <h2>Messages</h2>
        <button
          type="button"
          className="btn-new"
          onClick={() => setShowNewDialog(true)}
          title="New conversation"
          aria-label="Create new conversation"
        >
          <i className="bi bi-pencil-square" aria-hidden="true"></i>
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="loading">Loading conversations...</div>
      ) : conversations.length === 0 ? (
        <div className="empty-list">No conversations yet</div>
      ) : (
        <div className="list-items">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${selectedConversation?.id === conv.id ? 'active' : ''}`}
              onClick={() => onSelectConversation(conv)}
            >
              <div className="item-avatar">
                {conv.type === 'direct' && '👤'}
                {conv.type === 'group' && '👥'}
                {conv.type === 'project' && '📊'}
                {conv.type === 'team' && '👨‍💼'}
              </div>
              <div className="item-content">
                <div className="item-name">{getConversationName(conv)}</div>
                <div className="item-preview">
                  {conv.last_message ? conv.last_message.content.substring(0, 40) : 'No messages yet'}
                </div>
              </div>
              <div className="item-meta">
                <div className="item-time">
                  {conv.last_message ? formatTime(conv.last_message.created_at) : ''}
                </div>
                {conv.unread_count > 0 && (
                  <div className="badge unread">{conv.unread_count}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {showNewDialog && (
        <div className="chat-modal-overlay" onClick={() => setShowNewDialog(false)}>
          <div className="chat-modal" onClick={(e) => e.stopPropagation()}>
            <div className="chat-modal-header">
              <h3>{dialogType === 'direct' ? 'New Conversation' : 'New Group Conversation'}</h3>
              <button type="button" className="chat-modal-close" onClick={() => setShowNewDialog(false)} aria-label="Close new conversation dialog">
                <i className="bi bi-x-lg" aria-hidden="true"></i>
              </button>
            </div>

            <div className="chat-modal-tabs">
              <button
                type="button"
                className={`chat-modal-tab ${dialogType === 'direct' ? 'active' : ''}`}
                onClick={() => {
                  setDialogType('direct');
                  setFormData({ otherUserId: '', name: '', memberIds: [] });
                }}
              >
                Direct
              </button>
              <button
                type="button"
                className={`chat-modal-tab ${dialogType === 'group' ? 'active' : ''}`}
                onClick={() => {
                  setDialogType('group');
                  setFormData({ otherUserId: '', name: '', memberIds: [] });
                }}
              >
                Group
              </button>
            </div>

            {dialogType === 'direct' && (
              <div className="chat-modal-body">
                <label className="chat-field-label">Select a user</label>
                {loadingUsers ? (
                  <div className="chat-empty-state small">Loading users...</div>
                ) : userError ? (
                  <div className="error-banner small">{userError}</div>
                ) : (
                  <div className="chat-user-list">
                    {users.length === 0 ? (
                      <div className="chat-empty-state small">No organization members found.</div>
                    ) : (
                      users.map((user) => (
                        <button
                          key={user.id}
                          type="button"
                          className={`chat-user-option ${formData.otherUserId === user.id ? 'selected' : ''}`}
                          onClick={() => setFormData({ ...formData, otherUserId: user.id })}
                        >
                          <span className="chat-user-radio" aria-hidden="true" />
                          <span className="chat-user-meta">
                            <strong>{user.full_name || user.username}</strong>
                            <small>{user.email}</small>
                          </span>
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
            )}

            {dialogType === 'group' && (
              <div className="chat-modal-body">
                <div className="form-group compact">
                  <label className="chat-field-label">Group name</label>
                  <input
                    type="text"
                    placeholder="Enter group name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    disabled={submitting}
                  />
                </div>

                <label className="chat-field-label">Select members</label>
                {loadingUsers ? (
                  <div className="chat-empty-state small">Loading members...</div>
                ) : userError ? (
                  <div className="error-banner small">{userError}</div>
                ) : (
                  <div className="chat-user-list checkbox-list">
                    {users.length === 0 ? (
                      <div className="chat-empty-state small">No members available.</div>
                    ) : (
                      users.map((user) => (
                        <label key={user.id} className={`chat-user-option checkbox ${formData.memberIds.includes(user.id) ? 'selected' : ''}`}>
                          <input
                            type="checkbox"
                            checked={formData.memberIds.includes(user.id)}
                            onChange={() => toggleGroupMember(user.id)}
                            disabled={submitting}
                          />
                          <span className="chat-user-meta">
                            <strong>{user.full_name || user.username}</strong>
                            <small>{user.email}</small>
                          </span>
                        </label>
                      ))
                    )}
                  </div>
                )}
              </div>
            )}

            <div className="modal-actions chat-modal-actions">
              <button type="button" onClick={() => setShowNewDialog(false)} disabled={submitting}>
                Cancel
              </button>
              <button
                type="button"
                onClick={dialogType === 'direct' ? handleCreateDirect : handleCreateGroup}
                disabled={
                  submitting ||
                  (dialogType === 'direct' && !formData.otherUserId) ||
                  (dialogType === 'group' && (!formData.name || formData.memberIds.length === 0))
                }
                className="primary"
              >
                {submitting ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
