import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, UploadCloud, Folder, FileCode2, Command, Bot, User, CheckCircle2, AlertCircle, Github, HardDrive, Database, ChevronDown, ChevronRight, FileText } from 'lucide-react';
import './App.css';

const API_BASE = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi! I am your AI DevOps Codebase Explainer. Upload your project folder or files, and ask me anything about how the code works.', id: 'init' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadMode, setUploadMode] = useState('local'); // 'local' or 'github'
  const [uploadPaths, setUploadPaths] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // { type: 'success' | 'error', message: '' }
  const [indexedData, setIndexedData] = useState({ repo_name: 'None', files: [] });
  const [isTreeExpanded, setIsTreeExpanded] = useState(true);
  
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
    
    setUploading(true);
    setUploadStatus(null);
    
    // Split by comma and clean up whitespace
    const paths = uploadPaths.split(',').map(p => p.trim()).filter(Boolean);
    
    try {
      const res = await axios.post(`${API_BASE}/upload`, { files: paths });
      setUploadStatus({ 
        type: 'success', 
        message: `Indexed ${res.data.files_indexed} local files!` 
      });
      setUploadPaths('');
      fetchIndexStatus();
    } catch (err) {
      setUploadStatus({ 
        type: 'error', 
        message: err.response?.data?.detail || err.message || 'Failed to index files.' 
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

  const handleBrowseLocal = async () => {
    try {
      // Call the backend endpoint to spawn a native OS folder picker
      // This brilliantly bypasses the browser's absolute path security restriction
      const res = await axios.get(`${API_BASE}/browse`);
      if (res.data.path) {
        setUploadPaths(prev => prev ? prev + ', ' + res.data.path : res.data.path);
      }
    } catch (error) {
       console.log("Folder picker error or cancelled", error);
       alert("Failed to open local folder browser. Make sure the backend server is running.");
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
              <p className="upload-desc">Enter absolute paths to your project folders (comma separated).</p>
              <form onSubmit={handleUploadLocal}>
                <div className="input-with-browser">
                  <textarea 
                    value={uploadPaths}
                    onChange={(e) => setUploadPaths(e.target.value)}
                    placeholder="e.g. C:\Projects\MyRepo"
                    rows={3}
                    disabled={uploading}
                  />
                  <button type="button" onClick={handleBrowseLocal} className="browse-btn" disabled={uploading} title="Browse Folders">
                    <Folder size={16} />
                  </button>
                </div>
                <button 
                  type="submit" 
                  className={`upload-btn ${uploading ? 'loading' : ''}`}
                  disabled={uploading || !uploadPaths.trim()}
                >
                  {uploading ? <div className="spinner-small" /> : <UploadCloud size={18} />}
                  <span>{uploading ? 'Indexing...' : 'Index Local Files'}</span>
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
                  <div className="repo-badge">{indexedData.repo_name}</div>
                  <div className="file-tree">
                    {indexedData.files.map((file, idx) => {
                      // Extract just the filename from absolute path to save space
                      const segments = file.split(/[/\\]/);
                      const filename = segments[segments.length - 1];
                      return (
                        <div key={idx} className="tree-item" title={file}>
                          <FileText size={13} className="file-icon" />
                          <span className="file-name">{filename}</span>
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
            <h1>DevOps Assistant</h1>
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
                <div className="message-content">{msg.content}</div>
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
