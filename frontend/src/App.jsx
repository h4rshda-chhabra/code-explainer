import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, UploadCloud, Folder, FileCode2, Command, Bot, User, CheckCircle2, AlertCircle, Github, HardDrive, Database, ChevronDown, ChevronRight, FileText, Trash2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './App.css';

const API_BASE = window.location.hostname === 'localhost' ? 'http://localhost:8000' : 'https://codesense-backend-a472.onrender.com';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi! I am your AI Codebase Explainer. Upload your project folder or files, and ask me anything about how the code works.', id: 'init' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadMode, setUploadMode] = useState('local'); // 'local' or 'github'

  const [githubUrl, setGithubUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // { type: 'success' | 'error', message: '' }
  const [indexedData, setIndexedData] = useState({ repo_name: 'None', files: [] });
  const [isTreeExpanded, setIsTreeExpanded] = useState(true);
  const [allowedExtensions, setAllowedExtensions] = useState('');
  
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchIndexStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/index-status`);
      setIndexedData(res.data);
    } catch (err) {
      console.error("Failed to fetch index status", err);
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetchIndexStatus();
  }, []);

  const handleUploadLocal = async (e) => {
    e.preventDefault();
    if (!uploadPaths.trim()) return;
  const fileInputRef = useRef(null);

  const handleUploadLocal = async (e) => {
    e.preventDefault();
    const files = fileInputRef.current?.files;
    if (!files || files.length === 0) return;
    
    setUploading(true);
    setUploadStatus(null);
    
    try {
      const formData = new FormData();
      let fileCount = 0;
      
      const exts = allowedExtensions.split(',').map(e => e.trim().toLowerCase()).filter(Boolean);

      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const path = file.webkitRelativePath || file.name;
        
        // Exclude common heavy directories to save upload bandwidth
        if (path.includes('.git/') || path.includes('node_modules/') || path.includes('__pycache__/')) {
          continue;
        }

        // Filter by extensions if provided
        if (exts.length > 0) {
          const fileExt = '.' + file.name.split('.').pop().toLowerCase();
          if (!exts.includes(fileExt)) {
            continue;
          }
        }

        formData.append('files', file);
        formData.append('paths', path);
        fileCount++;
      }

      if (fileCount === 0) {
        throw new Error("No valid files found after filtering.");
      }

      const res = await axios.post(`${API_BASE}/upload-local`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setUploadStatus({ 
        type: 'success', 
        message: `Indexed ${res.data.files_indexed} local files!` 
      });
      
      // Reset file input
      if (fileInputRef.current) fileInputRef.current.value = '';
      
      fetchIndexStatus();
    } catch (err) {
      setUploadStatus({ 
        type: 'error', 
        message: err.response?.data?.detail || err.message || 'Failed to upload and index files.' 
      });
    } finally {
      setUploading(false);
      setTimeout(() => setUploadStatus(null), 5000);
    }
  };

  const handleUploadGithub = async (e) => {
    e.preventDefault();
    if (!githubUrl.trim()) return;
    
    setUploading(true);
    setUploadStatus(null);
    
    try {
      const res = await axios.post(`${API_BASE}/upload-github`, { github_url: githubUrl.trim() });
      setUploadStatus({ 
        type: 'success', 
        message: `Indexed ${res.data.files_indexed} files from GitHub!` 
      });
      setGithubUrl('');
      fetchIndexStatus();
    } catch (err) {
      setUploadStatus({ 
        type: 'error', 
        message: err.response?.data?.detail || err.message || 'Failed to index GitHub repo.' 
      });
    } finally {
      setUploading(false);
      setTimeout(() => setUploadStatus(null), 8000);
    }
  };



  const handleUnindex = async () => {
    if (!window.confirm("Are you sure you want to unindex the current codebase? This guarantees no two codebases will merge.")) return;
    setUploading(true);
    setUploadStatus(null);
    try {
      await axios.post(`${API_BASE}/clear`);
      setUploadStatus({ type: 'success', message: 'Successfully unindexed codebase!' });
      fetchIndexStatus();
    } catch (err) {
      setUploadStatus({ type: 'error', message: 'Failed to unindex codebase.' });
    } finally {
      setUploading(false);
      setTimeout(() => setUploadStatus(null), 5000);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = { role: 'user', content: input.trim(), id: Date.now().toString() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/ask`, { question: userMsg.content });
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: res.data.answer, 
        context: res.data.context_chunks?.length || 0,
        id: (Date.now() + 1).toString() 
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Error: ${err.message}. Make sure the backend is running and you have uploaded files.`, 
        isError: true,
        id: (Date.now() + 1).toString() 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="layout">
      {/* Sidebar for Uploads */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <Command className="logo-icon" />
          <h2>CodeSense AI</h2>
        </div>
        
        <div className="upload-section">
          <h3><Folder size={16} /> Index Codebase</h3>
          
          <div className="source-tabs">
            <button 
              className={`tab-btn ${uploadMode === 'local' ? 'active' : ''}`}
              onClick={() => setUploadMode('local')}
            >
              <HardDrive size={14} /> Local
            </button>
            <button 
              className={`tab-btn ${uploadMode === 'github' ? 'active' : ''}`}
              onClick={() => setUploadMode('github')}
            >
              <Github size={14} /> GitHub
            </button>
          </div>

          {uploadMode === 'local' ? (
            <div className="tab-pane">
              <p className="upload-desc">Select a project folder to upload and index its code.</p>
              <form onSubmit={handleUploadLocal}>
                <div style={{ marginBottom: '12px' }}>
                  <input 
                    type="file" 
                    webkitdirectory="true" 
                    directory="true" 
                    multiple 
                    ref={fileInputRef}
                    disabled={uploading}
                    className="file-picker-input"
                  />
                </div>
                <input 
                  type="text"
                  value={allowedExtensions}
                  onChange={(e) => setAllowedExtensions(e.target.value)}
                  placeholder="Extensions: .py, .js (optional)"
                  style={{ background: '#374151', color: '#f3f4f6', border: '1px solid #4b5563', padding: '8px', borderRadius: '4px', width: '100%', marginBottom: '8px' }}
                />
                <button 
                  type="submit" 
                  className={`upload-btn ${uploading ? 'loading' : ''}`}
                  disabled={uploading}
                >
                  {uploading ? <div className="spinner-small" /> : <UploadCloud size={18} />}
                  <span>{uploading ? 'Uploading & Indexing...' : 'Upload Local Folder'}</span>
                </button>
              </form>
            </div>
          ) : (
            <div className="tab-pane">
              <p className="upload-desc">Paste a public GitHub repository URL to clone and index it automatically.</p>
              <form onSubmit={handleUploadGithub}>
                <input 
                  type="text"
                  className="github-input"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/user/repo"
                  disabled={uploading}
                />
                <button 
                  type="submit" 
                  className={`upload-btn ${uploading ? 'loading' : ''}`}
                  disabled={uploading || !githubUrl.trim()}
                >
                  {uploading ? <div className="spinner-small" /> : <Github size={18} />}
                  <span>{uploading ? 'Cloning & Indexing...' : 'Index Repository'}</span>
                </button>
              </form>
            </div>
          )}

          {uploadStatus && (
            <div className={`status-toast ${uploadStatus.type}`}>
              {uploadStatus.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
              <span>{uploadStatus.message}</span>
            </div>
          )}
        </div>

        {/* Dynamic File Tree Section */}
        <div className="indexed-files-section">
          <div className="indexed-header" onClick={() => setIsTreeExpanded(!isTreeExpanded)}>
            <div className="indexed-title">
              <Database size={15} />
              <h4>Active Repository</h4>
            </div>
            {isTreeExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </div>
          
          {isTreeExpanded && (
            <div className="indexed-content">
              {indexedData.repo_name !== 'None' ? (
                <>
                  <div className="repo-badge-container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <div className="repo-badge" title={indexedData.repo_name} style={{overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '140px'}}>
                      {indexedData.repo_name}
                    </div>
                    <button onClick={handleUnindex} disabled={uploading} title="Remove to prevent merging codebases" style={{ background: 'transparent', border: '1px solid #ef4444', color: '#ef4444', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Trash2 size={12} /> Unindex
                    </button>
                  </div>
                  <div className="file-tree">
                    {indexedData.files.map((file, idx) => {
                      // Display the full project structure relative to repo to show internal folders and files
                      const segments = file.split(/[/\\]/);
                      const repoIndex = segments.findIndex(s => s === indexedData.repo_name);
                      let displayPath = file;
                      if (repoIndex !== -1 && repoIndex < segments.length - 1) {
                         displayPath = segments.slice(repoIndex + 1).join('/');
                      } else if (segments.length > 2) {
                         displayPath = segments.slice(-3).join('/');
                      }
                      return (
                        <div key={idx} className="tree-item" title={file}>
                          <FileText size={13} className="file-icon" style={{ minWidth: '13px' }} />
                          <span className="file-name" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', direction: 'rtl', textAlign: 'left' }}>
                            &lrm;{displayPath}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  <div className="file-count">{indexedData.files.length} files embedded</div>
                </>
              ) : (
                <div className="empty-state">
                  No codebase indexed yet.
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className="sidebar-footer">
          <div className="tech-badge">
            <FileCode2 size={14} /> Supports Py, JS, YML, Docker
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="chat-container">
        <header className="chat-header">
          <div className="header-info">
            <h1>Codebase Assistant</h1>
            <span className="badge">RAG Powered</span>
          </div>
        </header>

        <div className="messages-area">
          {messages.map((msg) => (
            <div key={msg.id} className={`message-wrapper ${msg.role}`}>
              <div className="avatar">
                {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
              </div>
              <div className={`message-bubble ${msg.isError ? 'error' : ''}`}>
                <div className="message-content">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
                {msg.context > 0 && (
                  <div className="message-meta">
                    Retrieved {msg.context} code chunks as context.
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message-wrapper assistant">
              <div className="avatar"><Bot size={20} /></div>
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <div style={{ display: 'flex', gap: '10px', marginBottom: '12px', flexWrap: 'wrap' }}>
            {['Explain main entry point', 'How does ingestion work?', 'List API endpoints'].map((q, idx) => (
              <button 
                key={idx} 
                onClick={() => setInput(q)} 
                type="button"
                style={{ background: '#374151', color: '#f3f4f6', border: 'none', padding: '8px 14px', borderRadius: '6px', cursor: 'pointer', fontSize: '14px', fontWeight: '500', transition: 'background-color 0.2s' }}
                onMouseOver={(e) => e.target.style.background = '#4b5563'}
                onMouseOut={(e) => e.target.style.background = '#374151'}
              >
                {q}
              </button>
            ))}
          </div>
          <form onSubmit={handleSend} className="input-form">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g. How does the ingestion logic work?"
              disabled={loading}
              autoFocus
            />
            <button type="submit" disabled={!input.trim() || loading} className="send-btn">
              <Send size={20} />
            </button>
          </form>
          <div className="input-footer">
            AI can make mistakes. Verify critical code explanations.
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
