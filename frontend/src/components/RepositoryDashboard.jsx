import React, { useEffect, useState } from 'react';
import axios from 'axios';
import RepositoryCard from './RepositoryCard.jsx';
import { RefreshCw, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API_BASE = window.location.hostname === 'localhost' ? 'http://localhost:8000' : process.env.REACT_APP_API_BASE || 'https://codesense-backend-a472.onrender.com';

export default function RepositoryDashboard() {
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const fetchRepos = async () => {
    try {
      const res = await axios.get(`${API_BASE}/repositories`);
      setRepos(res.data);
    } catch (err) {
      if (err.response?.status === 401) { navigate('/auth'); return; }
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRepos();
  }, []);

  const handleReindex = async (repoId) => {
    try {
      await axios.put(`${API_BASE}/repositories/${repoId}/reindex`);
      // optimistic UI update
      setRepos((prev) =>
        prev.map((r) => (r.id === repoId ? { ...r, indexing_status: 'reindex_requested' } : r))
      );
    } catch (err) {
      alert('Failed to request re-index: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDelete = async (repoId) => {
    if (!window.confirm('Delete this repository? This action cannot be undone.')) return;
    try {
      await axios.delete(`${API_BASE}/repositories/${repoId}`);
      setRepos((prev) => prev.filter((r) => r.id !== repoId));
    } catch (err) {
      alert('Failed to delete repository: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) return <div className="loading">Loading repositories...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="repo-dashboard" style={{ padding: '20px', background: '#111827', minHeight: '100vh', color: '#f3f4f6' }}>
      <h2>Repositories</h2>
      {repos.length === 0 ? (
        <div className="empty-state">No repositories indexed yet.</div>
      ) : (
        repos.map((repo) => (
          <RepositoryCard
            key={repo.id}
            repo={repo}
            onReindex={handleReindex}
            onDelete={handleDelete}
          />
        ))
      )}
    </div>
  );
}
