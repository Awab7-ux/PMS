import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { teamApi, orgApi } from '../services/api';
import { joinRoom, leaveRoom, onRealtime } from '../services/realtime';
import { PageHeader, Card, Modal, LoadingState, EmptyState, Alert, Badge, Input, Textarea, FormGroup, FormSection } from '../components';

export default function TeamsPage() {
  const { orgId, user } = useAuth();
  const [members, setMembers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ name: '', description: '' });
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true);
    Promise.all([teamApi.list(), orgId ? orgApi.members(orgId) : Promise.resolve({ data: [] })])
      .then(([r, membership]) => { setTeams(r.data || []); setMembers(membership.data || []); })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);
  useEffect(() => {
    if (!orgId) return undefined;
    joinRoom('organization', orgId);
    const upsert = team => { if (String(team.organization_id) !== String(orgId)) return; setTeams(current => current.some(item => item.id === team.id) ? current.map(item => item.id === team.id ? { ...item, ...team } : item) : [team, ...current]); };
    const remove = payload => { if (String(payload.organization_id) === String(orgId)) setTeams(current => current.filter(team => String(team.id) !== String(payload.team_id))); };
    const adjustMemberCount = (payload, delta) => { if (String(payload.organization_id) !== String(orgId)) return; setTeams(current => current.map(team => String(team.id) === String(payload.team_id) ? { ...team, member_count: Math.max(0, Number(team.member_count || 0) + delta) } : team)); };
    const off = [onRealtime('team.created', upsert), onRealtime('team.updated', upsert), onRealtime('team.deleted', remove), onRealtime('team.member_added', event => adjustMemberCount(event, 1)), onRealtime('team.member_removed', event => adjustMemberCount(event, -1))];
    return () => { leaveRoom('organization', orgId); off.forEach(stop => stop()); };
  }, [orgId]);
  const canManage = ['Organization Owner', 'Project Manager'].includes(members.find(m => m.user_id === user?.id)?.role);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await teamApi.create({ ...form, organization_id: orgId });
      setShowModal(false);
      setForm({ name: '', description: '' });
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Archive this team?')) return;
    await teamApi.delete(id);
    load();
  };

  if (loading) return <LoadingState message="Loading teams..." />;

  return (
    <div>
      <PageHeader
        title="Teams"
        description="Bring the right people together around shared work."
        icon="👥"
        action={
          canManage && (
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              + New Team
            </button>
          )
        }
      />

      {error && <Alert type="error" title="Error" message={error} onClose={() => setError('')} />}

      {teams.length === 0 ? (
        <EmptyState
          icon="👥"
          title="No teams yet"
          message="Create your first team to collaborate with colleagues."
          action={
            canManage && (
              <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                Create First Team
              </button>
            )
          }
        />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {teams.map(t => (
            <Card key={t.id}>
              <h3 style={{ marginTop: 0, marginBottom: 8 }}>
                <Link to={`/teams/${t.id}`} className="btn-link">
                  {t.name}
                </Link>
              </h3>
              <p style={{ color: 'var(--text-muted)', margin: '8px 0 16px', fontSize: '0.9rem' }}>
                {t.description || 'No description'}
              </p>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between', alignItems: 'center' }}>
                <Badge variant="secondary">{t.member_count ?? 0} members</Badge>
                {canManage && (
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete(t.id)}>
                    Archive
                  </button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Create New Team"
        size="md"
      >
        <form onSubmit={handleCreate}>
          <FormSection>
            <FormGroup label="Team Name" required>
              <Input
                value={form.name}
                onChange={e => setForm({ ...form, name: e.target.value })}
                placeholder="Enter team name"
                required
              />
            </FormGroup>
            <FormGroup label="Description">
              <Textarea
                value={form.description}
                onChange={e => setForm({ ...form, description: e.target.value })}
                placeholder="Describe your team..."
                rows={4}
              />
            </FormGroup>
          </FormSection>

          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 24 }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowModal(false)}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Create Team
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
