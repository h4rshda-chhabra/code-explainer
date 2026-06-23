import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import {
  Send, UploadCloud, Folder, FileCode2, Command, Bot, User,
  CheckCircle2, AlertCircle, Github, HardDrive, Database,
  ChevronDown, ChevronRight, FileText, Trash2, Plus, LogOut,
  MessageSquare, Pin, PinOff, Pencil, Check, X, BookOpen,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './App.css';
import { useNavigate } from 'react-router-dom';

const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://codesense-backend-a472.onrender.com';

const INIT_MSG = {
  role: 'assistant',
  content: 'Hi! I\'m your AI Codebase Explainer. Upload a project folder or GitHub repo, then ask me anything about it.',
  id: 'init',
};

const SUMMARY_PROMPT =
  'Give me a comprehensive summary of this codebase: what it does, its overall architecture, the main components and their responsibilities, and how they interact with each other.';

function App() {
  const navigate = useNavigate();

  // Chat
  const [messages, setMessages] = useState([INIT_MSG]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Conversations
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);

  // Inline rename state
  const [editingConvId, setEditingConvId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');

  // Index + upload
  const [indexedData, setIndexedData] = useState({ repo_name: null, files: [] });
  const [isFilesExpanded, setIsFilesExpanded] = useState(false);
  const [uploadMode, setUploadMode] = useState('local');
  const [githubUrl, setGithubUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const renameInputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    fetchIndexStatus();
    fetchConversations();
  }, []);

  // Focus rename input when entering edit mode
  useEffect(() => {
    if (editingConvId !== null) {
      setTimeout(() => renameInputRef.current?.focus(), 0);
    }
  }, [editingConvId]);

  // ── Data fetching ──────────────────────────────────────────────────────────

  const fetchIndexStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/index-status`);
      setIndexedData(res.data);
    } catch (err) {
      if (err.response?.status === 401) navigate('/auth');
    }
  };

  const fetchConversations = async () => {
    try {
      const res = await axios.get(`${API_BASE}/conversations`);
      setConversations(res.data);
    } catch (err) {
      if (err.response?.status === 401) navigate('/auth');
    }
  };

  // ── Conversations ──────────────────────────────────────────────────────────

  const loadConversation = async (convId) => {
    if (editingConvId !== null) return; // don't switch while renaming
    try {
      const res = await axios.get(`${API_BASE}/conversations/${convId}/messages`);
      const msgs = res.data.map(m => ({ role: m.role, content: m.content, id: String(m.id) }));
      setMessages(msgs.length > 0 ? msgs : [INIT_MSG]);
      setActiveConvId(convId);
    } catch (err) {
      console.error('Failed to load conversation', err);
    }
  };

  const startNewConversation = () => {
    setMessages([INIT_MSG]);
    setActiveConvId(null);
    setEditingConvId(null);
  };

  const handleDeleteConversation = async (convId, e) => {
    e.stopPropagation();
    try {
      await axios.delete(`${API_BASE}/conversations/${convId}`);
      setConversations(prev => prev.filter(c => c.id !== convId));
      if (activeConvId === convId) startNewConversation();
    } catch (err) {
      console.error('Failed to delete', err);
    }
  };

  const handleTogglePin = async (conv, e) => {
    e.stopPropagation();
    const newPinned = !conv.pinned;
    try {
      await axios.put(`${API_BASE}/conversations/${conv.id}`, { pinned: newPinned });
      setConversations(prev => {
        const updated = prev.map(c => c.id === conv.id ? { ...c, pinned: newPinned } : c);
        return [...updated.filter(c => c.pinned), ...updated.filter(c => !c.pinned)];
      });
    } catch (err) {
      console.error('Failed to pin', err);
    }
  };

  const startRename = (conv, e) => {
    e.stopPropagation();
    setEditingConvId(conv.id);
    setEditingTitle(conv.title);
  };

  const cancelRename = (e) => {
    e?.stopPropagation?.();
    setEditingConvId(null);
    setEditingTitle('');
  };

  const saveRename = async (convId, e) => {
    e?.stopPropagation?.();
    const title = editingTitle.trim();
    if (!title) { cancelRename(); return; }
    try {
      await axios.put(`${API_BASE}/conversations/${convId}`, { title });
      setConversations(prev => prev.map(c => c.id === convId ? { ...c, title } : c));
    } catch (err) {
      console.error('Failed to rename', err);
    }
    setEditingConvId(null);
  };

  // ── Upload / Index ─────────────────────────────────────────────────────────

  const handleUploadLocal = async (e) => {
    e.preventDefault();
    const files = fileInputRef.current?.files;
    if (!files || files.length === 0) return;
    setUploading(true); setUploadStatus(null);
    try {
      const formData = new FormData();
      let fileCount = 0;
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const path = file.webkitRelativePath || file.name;
        if (path.includes('.git/') || path.includes('node_modules/') || path.includes('__pycache__/')) continue;
        formData.append('files', file);
        formData.append('paths', path);
        fileCount++;
      }
      if (fileCount === 0) throw new Error('No valid files found after filtering.');
      const res = await axios.post(`${API_BASE}/upload-local`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadStatus({ type: 'success', message: `Indexed ${res.data.files_indexed} files!` });
      if (fileInputRef.current) fileInputRef.current.value = '';
      const el = document.getElementById('file-count-label');
      if (el) el.innerText = '';
      fetchIndexStatus();
      startNewConversation();
    } catch (err) {
      setUploadStatus({ type: 'error', message: err.response?.data?.detail || err.message });
    } finally {
      setUploading(false);
      setTimeout(() => setUploadStatus(null), 5000);
    }
  };

  const handleUploadGithub = async (e) => {
    e.preventDefault();
    if (!githubUrl.trim()) return;
    setUploading(true); setUploadStatus(null);
    try {
      const res = await axios.post(`${API_BASE}/upload-github`, { github_url: githubUrl.trim() });
      setUploadStatus({ type: 'success', message: `Indexed ${res.data.files_indexed} files from GitHub!` });
      setGithubUrl('');
      fetchIndexStatus();
      startNewConversation();
    } catch (err) {
      setUploadStatus({ type: 'error', message: err.response?.data?.detail || err.message });
    } finally {
      setUploading(false);
      setTimeout(() => setUploadStatus(null), 8000);
    }
  };

  const handleUnindex = async () => {
    if (!window.confirm('Unindex the current codebase?')) return;
    setUploading(true); setUploadStatus(null);
    try {
      await axios.post(`${API_BASE}/clear`);
      setUploadStatus({ type: 'success', message: 'Unindexed successfully.' });
      fetchIndexStatus();
      fetchConversations();
      startNewConversation();
    } catch (err) {
      setUploadStatus({ type: 'error', message: 'Failed to unindex.' });
    } finally {
      setUploading(false);
      setTimeout(() => setUploadStatus(null), 5000);
    }
  };

  // ── Auth ───────────────────────────────────────────────────────────────────

  const handleLogout = async () => {
    try { await axios.post(`${API_BASE}/logout`); } catch (_) {}
    navigate('/auth');
  };

  // ── Chat ───────────────────────────────────────────────────────────────────

  const sendMessage = async (question) => {
    if (!question.trim() || loading) return;

    const userMsg = { role: 'user', content: question, id: Date.now().toString() };
    setMessages(prev => [...prev.filter(m => m.id !== 'init'), userMsg]);
    setInput('');
    setLoading(true);

    try {
      let convId = activeConvId;
      if (!convId && indexedData.repo_name) {
        const convRes = await axios.post(`${API_BASE}/conversations`, {
          title: question.slice(0, 80),
        });
        convId = convRes.data.id;
        setActiveConvId(convId);
        setConversations(prev => [convRes.data, ...prev.filter(c => !c.pinned)].map(c => c));
        // Re-sort: pinned first
        setConversations(prev => {
          const allWithNew = [convRes.data, ...prev.filter(c => c.id !== convRes.data.id)];
          return [...allWithNew.filter(c => c.pinned), ...allWithNew.filter(c => !c.pinned)];
        });
      }

      const res = await axios.post(`${API_BASE}/ask`, {
        question,
        conversation_id: convId || undefined,
      });

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: res.data.answer,
          context: res.data.context_chunks?.length || 0,
          id: (Date.now() + 1).toString(),
        },
      ]);

      if (convId) {
        setConversations(prev =>
          prev.map(c => c.id === convId ? { ...c, updated_at: new Date().toISOString() } : c)
        );
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${err.response?.data?.detail || err.message}`,
          isError: true,
          id: (Date.now() + 1).toString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = (e) => {
    e.preventDefault();
    sendMessage(input.trim());
  };

  const handleSummarize = () => {
    sendMessage(SUMMARY_PROMPT);
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  const pinnedConvs = conversations.filter(c => c.pinned);
  const unpinnedConvs = conversations.filter(c => !c.pinned);

  const ConvItem = ({ conv }) => {
    const isActive = activeConvId === conv.id;
    const isEditing = editingConvId === conv.id;

    return (
      <div
        onClick={() => loadConversation(conv.id)}
        style={{
          display: 'flex', alignItems: 'center', gap: '4px',
          padding: '7px 8px', borderRadius: '6px', cursor: 'pointer', marginBottom: '3px',
          background: isActive ? '#374151' : 'transparent',
          border: `1px solid ${isActive ? '#4b5563' : 'transparent'}`,
        }}
      >
        {conv.pinned && <Pin size={10} style={{ color: '#60a5fa', flexShrink: 0 }} />}

        {isEditing ? (
          <input
            ref={renameInputRef}
            value={editingTitle}
            onChange={e => setEditingTitle(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') saveRename(conv.id, e);
              if (e.key === 'Escape') cancelRename(e);
            }}
            onClick={e => e.stopPropagation()}
            style={{
              flex: 1, background: '#111827', border: '1px solid #4b5563', color: '#f3f4f6',
              borderRadius: '4px', padding: '2px 6px', fontSize: '13px', minWidth: 0,
            }}
          />
        ) : (
          <span style={{ flex: 1, fontSize: '13px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {conv.title}
          </span>
        )}

        <div style={{ display: 'flex', gap: '2px', flexShrink: 0 }} onClick={e => e.stopPropagation()}>
          {isEditing ? (
            <>
              <button onClick={e => saveRename(conv.id, e)} style={iconBtnStyle('#34d399')}>
                <Check size={11} />
              </button>
              <button onClick={cancelRename} style={iconBtnStyle('#6b7280')}>
                <X size={11} />
              </button>
            </>
          ) : (
            <>
              <button onClick={e => startRename(conv, e)} title="Rename" style={iconBtnStyle('#6b7280')}>
                <Pencil size={11} />
              </button>
              <button onClick={e => handleTogglePin(conv, e)} title={conv.pinned ? 'Unpin' : 'Pin'} style={iconBtnStyle(conv.pinned ? '#60a5fa' : '#6b7280')}>
                {conv.pinned ? <PinOff size={11} /> : <Pin size={11} />}
              </button>
              <button onClick={e => handleDeleteConversation(conv.id, e)} title="Delete" style={iconBtnStyle('#6b7280')}>
                <Trash2 size={11} />
              </button>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar" style={{ display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <div className="sidebar-header" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Command className="logo-icon" />
          <h2 style={{ flex: 1 }}>CodeSense AI</h2>
          <button onClick={handleLogout} title="Logout" style={iconBtnStyle('#9ca3af')}>
            <LogOut size={16} />
          </button>
        </div>

        {/* Upload section */}
        <div className="upload-section">
          <h3><Folder size={16} /> Index Codebase</h3>

          <div className="source-tabs">
            <button className={`tab-btn ${uploadMode === 'local' ? 'active' : ''}`} onClick={() => setUploadMode('local')}>
              <HardDrive size={13} /> Local
            </button>
            <button className={`tab-btn ${uploadMode === 'github' ? 'active' : ''}`} onClick={() => setUploadMode('github')}>
              <Github size={13} /> GitHub
            </button>
          </div>

          {uploadMode === 'local' ? (
            <form onSubmit={handleUploadLocal}>
              <div style={{ marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <label style={{ cursor: 'pointer', padding: '7px 10px', background: '#374151', borderRadius: '4px', fontSize: '13px', border: '1px solid #4b5563' }}>
                  Choose Folder
                  <input
                    type="file"
                    webkitdirectory="true"
                    directory="true"
                    multiple
                    ref={fileInputRef}
                    disabled={uploading}
                    style={{ display: 'none' }}
                    onChange={e => {
                      const el = document.getElementById('file-count-label');
                      if (el) el.innerText = e.target.files?.length > 0 ? `${e.target.files.length} files` : '';
                    }}
                  />
                </label>
                <span id="file-count-label" style={{ fontSize: '11px', color: '#9ca3af' }} />
              </div>
              <button type="submit" className={`upload-btn ${uploading ? 'loading' : ''}`} disabled={uploading}>
                {uploading ? <div className="spinner-small" /> : <UploadCloud size={16} />}
                <span>{uploading ? 'Indexing...' : 'Upload Folder'}</span>
              </button>
            </form>
          ) : (
            <form onSubmit={handleUploadGithub}>
              <input
                type="text"
                className="github-input"
                value={githubUrl}
                onChange={e => setGithubUrl(e.target.value)}
                placeholder="https://github.com/user/repo"
                disabled={uploading}
              />
              <button type="submit" className={`upload-btn ${uploading ? 'loading' : ''}`} disabled={uploading || !githubUrl.trim()}>
                {uploading ? <div className="spinner-small" /> : <Github size={16} />}
                <span>{uploading ? 'Indexing...' : 'Index Repo'}</span>
              </button>
            </form>
          )}

          {uploadStatus && (
            <div className={`status-toast ${uploadStatus.type}`}>
              {uploadStatus.type === 'success' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
              <span>{uploadStatus.message}</span>
            </div>
          )}
        </div>

        {/* Active repo */}
        {indexedData.repo_name && (
          <div className="indexed-files-section">
            <div className="indexed-header" onClick={() => setIsFilesExpanded(v => !v)}>
              <div className="indexed-title">
                <Database size={14} />
                <h4 style={{ margin: 0, fontSize: '13px' }}>Active: {indexedData.repo_name.split('/').pop()}</h4>
              </div>
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                <button
                  onClick={e => { e.stopPropagation(); handleUnindex(); }}
                  disabled={uploading}
                  title="Unindex"
                  style={{ background: 'transparent', border: '1px solid #ef4444', color: '#ef4444', padding: '2px 6px', borderRadius: '4px', cursor: 'pointer', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '3px' }}
                >
                  <Trash2 size={11} /> Unindex
                </button>
                {isFilesExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </div>
            </div>
            {isFilesExpanded && (
              <div className="indexed-content">
                <div className="file-tree">
                  {indexedData.files.map((file, idx) => {
                    const segments = file.split(/[/\\]/);
                    const repoIdx = segments.findIndex(s => s === indexedData.repo_name);
                    const display = repoIdx !== -1 ? segments.slice(repoIdx + 1).join('/') : segments.slice(-3).join('/');
                    return (
                      <div key={idx} className="tree-item" title={file}>
                        <FileText size={12} className="file-icon" style={{ minWidth: '12px' }} />
                        <span className="file-name" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {display}
                        </span>
                      </div>
                    );
                  })}
                </div>
                <div className="file-count">{indexedData.files.length} files embedded</div>
              </div>
            )}
          </div>
        )}

        {/* Conversation history */}
        <div style={{ flex: 1, overflowY: 'auto', marginTop: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', padding: '0 2px' }}>
            <span style={{ fontSize: '12px', color: '#9ca3af', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              <MessageSquare size={11} style={{ display: 'inline', marginRight: '4px' }} />
              History
            </span>
            <button
              onClick={startNewConversation}
              title="New conversation"
              style={{ background: '#374151', border: 'none', color: '#f3f4f6', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              <Plus size={12} /> New
            </button>
          </div>

          {conversations.length === 0 ? (
            <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>No conversations yet.</p>
          ) : (
            <>
              {pinnedConvs.length > 0 && (
                <>
                  <div style={{ fontSize: '10px', color: '#60a5fa', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 4px 2px' }}>Pinned</div>
                  {pinnedConvs.map(conv => <ConvItem key={conv.id} conv={conv} />)}
                  {unpinnedConvs.length > 0 && (
                    <div style={{ fontSize: '10px', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '8px 0 4px 2px' }}>Recent</div>
                  )}
                </>
              )}
              {unpinnedConvs.map(conv => <ConvItem key={conv.id} conv={conv} />)}
            </>
          )}
        </div>

        <div className="sidebar-footer">
          <div className="tech-badge"><FileCode2 size={13} /> Py, JS, TS, Go, YAML</div>
        </div>
      </aside>

      {/* ── Main chat ── */}
      <main className="chat-container">
        <header className="chat-header">
          <div className="header-info">
            <h1>Codebase Assistant</h1>
            <span className="badge">RAG Powered</span>
          </div>
          {activeConvId && (
            <span style={{ fontSize: '12px', color: '#6b7280' }}>
              {conversations.find(c => c.id === activeConvId)?.title}
            </span>
          )}
        </header>

        <div className="messages-area">
          {messages.map(msg => (
            <div key={msg.id} className={`message-wrapper ${msg.role}`}>
              <div className="avatar">
                {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
              </div>
              <div className={`message-bubble ${msg.isError ? 'error' : ''}`}>
                <div className="message-content">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
                {msg.context > 0 && (
                  <div className="message-meta">Retrieved {msg.context} code chunks.</div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message-wrapper assistant">
              <div className="avatar"><Bot size={20} /></div>
              <div className="typing-indicator"><span /><span /><span /></div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <div style={{ display: 'flex', gap: '8px', marginBottom: '10px', flexWrap: 'wrap' }}>
            <button
              onClick={handleSummarize}
              disabled={!indexedData.repo_name || loading}
              title={!indexedData.repo_name ? 'Index a codebase first' : 'Generate a project summary'}
              style={{
                background: indexedData.repo_name ? '#1e3a5f' : '#1f2937',
                color: indexedData.repo_name ? '#93c5fd' : '#4b5563',
                border: `1px solid ${indexedData.repo_name ? '#2563eb' : '#374151'}`,
                padding: '6px 12px', borderRadius: '6px', cursor: indexedData.repo_name ? 'pointer' : 'not-allowed',
                fontSize: '13px', display: 'flex', alignItems: 'center', gap: '5px',
              }}
            >
              <BookOpen size={13} /> Summarize Project
            </button>
            {['Explain the main entry point', 'How does ingestion work?', 'List all API endpoints'].map((q, i) => (
              <button
                key={i}
                onClick={() => setInput(q)}
                type="button"
                style={{ background: '#374151', color: '#f3f4f6', border: 'none', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' }}
                onMouseOver={e => e.currentTarget.style.background = '#4b5563'}
                onMouseOut={e => e.currentTarget.style.background = '#374151'}
              >
                {q}
              </button>
            ))}
          </div>
          <form onSubmit={handleSend} className="input-form">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={indexedData.repo_name ? 'Ask about your codebase...' : 'Upload a codebase first, then ask questions...'}
              disabled={loading}
              autoFocus
            />
            <button type="submit" disabled={!input.trim() || loading} className="send-btn">
              <Send size={20} />
            </button>
          </form>
          <div className="input-footer">AI can make mistakes. Verify critical code explanations.</div>
        </div>
      </main>
    </div>
  );
}

const iconBtnStyle = (color) => ({
  background: 'none', border: 'none', color, cursor: 'pointer', padding: '2px', display: 'flex', alignItems: 'center',
});

export default App;
