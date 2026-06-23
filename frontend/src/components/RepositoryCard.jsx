import React from 'react';
import { Trash2, RefreshCw } from 'lucide-react';

export default function RepositoryCard({ repo, onReindex, onDelete }) {
  const {
    id,
    name,
    branch,
    file_count,
    chunk_count,
    embedding_count,
    size_bytes,
    last_indexed_at,
    indexing_status,
  } = repo;

  const formattedDate = last_indexed_at ? new Date(last_indexed_at).toLocaleString() : 'Never';
  const sizeMB = (size_bytes / (1024 * 1024)).toFixed(2);

  return (
    <div className="repo-card" style={{
      border: '1px solid #374151',
      borderRadius: '8px',
      padding: '12px',
      marginBottom: '12px',
      background: '#1f2937',
      color: '#f3f4f6',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
    }}>
      <div className="repo-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>{name}</h3>
        <span style={{ fontSize: '0.9rem', opacity: 0.8 }}>{branch || 'main'}</span>
      </div>
      <div className="repo-stats" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '4px' }}>
        <div>Files: {file_count}</div>
        <div>Chunks: {chunk_count}</div>
        <div>Embeddings: {embedding_count}</div>
        <div>Size: {sizeMB} MB</div>
        <div>Last indexed: {formattedDate}</div>
        <div>Status: {indexing_status}</div>
      </div>
      <div className="repo-actions" style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
        <button
          onClick={() => onReindex(id)}
          style={{
            flex: 1,
            background: '#2563eb',
            border: 'none',
            color: '#fff',
            padding: '6px 8px',
            borderRadius: '4px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          <RefreshCw size={14} /> Re‑index
        </button>
        <button
          onClick={() => onDelete(id)}
          style={{
            flex: 1,
            background: '#dc2626',
            border: 'none',
            color: '#fff',
            padding: '6px 8px',
            borderRadius: '4px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          <Trash2 size={14} /> Delete
        </button>
      </div>
    </div>
  );
}
