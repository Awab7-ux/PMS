import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { searchApi } from '../services/api';

export default function SearchPage() {
  const { orgId } = useAuth();
  const [params, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(params.get('q') || '');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const q = params.get('q');
    if (!q || !orgId) return;
    setLoading(true);
    setError('');
    searchApi.global({ organization_id: orgId, q, per_page: 20 })
      .then(r => setResults(r.data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [params, orgId]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) setSearchParams({ q: query.trim() });
  };

  const sections = [
    { key: 'projects', label: 'Projects', link: (id) => `/projects/${id}` },
    { key: 'tasks', label: 'Tasks', link: (id) => `/tasks/${id}` },
    { key: 'teams', label: 'Teams', link: (id) => `/teams/${id}` },
    { key: 'users', label: 'Users', link: () => '/users' },
  ];

  return (
    <div>
      <div className="page-header">
        <div><h1>Search</h1><p>Find projects, tasks, teams, and users</p></div>
      </div>

      <form onSubmit={handleSearch} style={{ marginBottom: 24, display: 'flex', gap: 8 }}>
        <input className="input" placeholder="Search..." value={query} onChange={e => setQuery(e.target.value)} style={{ maxWidth: 500 }} />
        <button className="btn btn-primary">Search</button>
      </form>

      {loading && <div className="loader">Searching...</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {results && !loading && (
        <div>
          {sections.map(({ key, label, link }) => {
            const items = results[key] || [];
            if (!items.length) return null;
            return (
              <div key={key} className="card" style={{ marginBottom: 16 }}>
                <h3 style={{ marginBottom: 12 }}>{label}</h3>
                {items.map(item => (
                  <div key={item.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                    <Link to={link(item.id)}>{item.name || item.title || item.full_name || item.email}</Link>
                    {item.description && <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{item.description}</p>}
                  </div>
                ))}
              </div>
            );
          })}
          {sections.every(s => !(results[s.key]?.length)) && (
            <div className="card empty-state">No results for "{params.get('q')}"</div>
          )}
        </div>
      )}
    </div>
  );
}
