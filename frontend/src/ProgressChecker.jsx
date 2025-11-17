import React, { useState } from 'react';
import './ProgressChecker.css';

function ProgressChecker() {
  const [repoLink, setRepoLink] = useState('');
  const [progress, setProgress] = useState(null);
  const [stats, setStats] = useState(null);
  const [lastCommit, setLastCommit] = useState(null);
  const [conciseSummary, setConciseSummary] = useState(null);
  const [commitsLog, setCommitsLog] = useState(null);
  const [readmeContent, setReadmeContent] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Handle scroll event for sticky nav styling
  React.useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setProgress(null);
    setStats(null);
    setConciseSummary(null);
    setCommitsLog(null);
    setReadmeContent(null);

    try {
      // Validate repo link
      if (!repoLink.trim()) {
        throw new Error('Please enter a repository link');
      }

      // Normalize GitHub URL
      let repoUrl = repoLink.trim();
      if (!repoUrl.startsWith('https://')) {
        repoUrl = `https://github.com/${repoUrl}`;
      }

      console.log('📌 Fetching progress for:', repoUrl);

      // Call backend API
      const response = await fetch('http://localhost:8000/api/progress/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repo_url: repoUrl
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Error: ${response.status}`);
      }

      const data = await response.json();
      
      setProgress(data.summary);
      setStats(data.statistics);
      setLastCommit(data.last_commit || null);
      setConciseSummary(data.concise_summary || null);
      setCommitsLog(data.commits_log || null);
      setReadmeContent(data.readme_content || null);
      
    } catch (err) {
      console.error('❌ Error:', err);
      setError(err.message || 'An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClearForm = () => {
    setRepoLink('');
    setProgress(null);
    setStats(null);
    setLastCommit(null);
    setConciseSummary(null);
    setCommitsLog(null);
    setReadmeContent(null);
    setError(null);
  };

  return (
    <div className="progress-checker">
      {/* Sticky Top Navigation */}
      <nav className={`sticky-nav ${scrolled ? 'scrolled' : ''}`}>
        <div className="nav-container">
          <div className="nav-logo">
            <span className="nav-icon">📊</span>
            <h2 className="nav-title">Progress Analyzer</h2>
          </div>
          <ul className="nav-links">
            <li><a href="#home">Home</a></li>
            <li><a href="#upload">Upload</a></li>
            <li><a href="#stats">Stats</a></li>
            <li><a href="#contributors">Contributors</a></li>
          </ul>
        </div>
      </nav>

      <div className="progress-container">
        {/* Header */}
        <div className="progress-header">
          <h1>📊 Repository Progress Analyzer</h1>
          <p className="progress-subtitle">Enter a GitHub repository URL to analyze its progress, track commits, and monitor team contributions</p>
        </div>

        <div className="content-wrapper">
          {/* Upload & Control Card - Full Width */}
          <div className="upload-card">
            <div className="upload-card-header">
              <h2>🔍 Analyze Repository</h2>
              <p className="upload-subtitle">Paste your GitHub repository link below</p>
            </div>
            
            <form onSubmit={handleSubmit} className="progress-form">
              <div className="form-group">
                <label htmlFor="repo-link">GitHub Repository URL</label>
                <div className="input-wrapper">
                  <input
                    id="repo-link"
                    type="text"
                    value={repoLink}
                    onChange={(e) => setRepoLink(e.target.value)}
                    placeholder="https://github.com/username/repo-name"
                    disabled={loading}
                    className="repo-input"
                  />
                  <span className="input-hint">Full URL or username/repo</span>
                </div>
              </div>

              <div className="form-actions">
                <button
                  type="submit"
                  disabled={loading}
                  className="btn btn-primary"
                >
                  {loading ? '🔄 Analyzing...' : '📈 Analyze Progress'}
                </button>
                <button
                  type="button"
                  onClick={handleClearForm}
                  disabled={loading}
                  className="btn btn-secondary"
                >
                  Clear
                </button>
              </div>
            </form>
          </div>

          {/* Concise Progress Summary Card (NEW FEATURE) */}
          {conciseSummary && (
            <div className="result-card concise-summary-card">
              <div className="card-header">
                <h3>⚡ Progress Update</h3>
                <div className="header-divider"></div>
              </div>
              <div className="concise-summary-content">
                <p className="concise-summary-text">{conciseSummary}</p>
              </div>
              <div className="concise-summary-footer">
                <span className="footer-badge">Auto-generated Summary</span>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="alert alert-error">
              <span className="alert-icon">❌</span>
              <div className="alert-content">
                <h3>Error</h3>
                <p>{error}</p>
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="loading-overlay">
              <div className="loading-spinner">
                <div className="spinner"></div>
                <p className="loading-text">Analyzing repository...</p>
                <div className="loading-bar">
                  <div className="loading-progress"></div>
                </div>
              </div>
            </div>
          )}

          {/* Two-Column Layout for Results */}
          {progress && (
            <div className="results-grid">
              {/* Left Column */}
              <div className="results-column left-column">
                {/* Progress Summary */}
                <div className="result-card summary-card">
                  <div className="card-header">
                    <h3>📋 Progress Summary</h3>
                    <div className="header-divider"></div>
                  </div>
                  <div className="summary-content">
                    {progress.split('\n').map((line, idx) => {
                      if (line.startsWith('##')) {
                        return (
                          <h4 key={idx} className="summary-heading">
                            {line.replace(/^##\s*/, '')}
                          </h4>
                        );
                      } else if (line.startsWith('-')) {
                        return (
                          <li key={idx} className="summary-bullet">
                            {line.replace(/^-\s*/, '')}
                          </li>
                        );
                      } else if (line.startsWith('**') && line.includes(':')) {
                        return (
                          <div key={idx} className="summary-stat">
                            {line}
                          </div>
                        );
                      } else if (line.startsWith('1.') || line.startsWith('2.') || line.startsWith('3.')) {
                        return (
                          <div key={idx} className="summary-step">
                            {line}
                          </div>
                        );
                      } else if (line.trim()) {
                        return (
                          <p key={idx} className="summary-text">
                            {line}
                          </p>
                        );
                      }
                      return null;
                    })}
                  </div>
                </div>

                {/* Key Metrics */}
                {stats && (
                  <div className="result-card metrics-card">
                    <div className="card-header">
                      <h3>📊 Key Metrics</h3>
                      <div className="header-divider"></div>
                    </div>
                    <div className="metrics-compact">
                      <div className="metric-item">
                        <span className="metric-label">Total Commits</span>
                        <div className="metric-value-box">
                          <span className="metric-value">{stats.total_commits}</span>
                          <span className="metric-badge">commits</span>
                        </div>
                      </div>
                      <div className="metric-item">
                        <span className="metric-label">Files Changed</span>
                        <div className="metric-value-box">
                          <span className="metric-value">{stats.total_files_changed}</span>
                          <span className="metric-badge">files</span>
                        </div>
                      </div>
                      <div className="metric-item">
                        <span className="metric-label">Contributors</span>
                        <div className="metric-value-box">
                          <span className="metric-value">{stats.total_contributors}</span>
                          <span className="metric-badge">team members</span>
                        </div>
                      </div>
                      {stats.top_contributor && (
                        <div className="metric-item">
                          <span className="metric-label">Top Contributor</span>
                          <div className="metric-value-box">
                            <span className="metric-tag">{stats.top_contributor}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Future Steps */}
                <div className="result-card future-steps-card">
                  <div className="card-header">
                    <h3>🎯 Next Steps</h3>
                    <div className="header-divider"></div>
                  </div>
                  <div className="future-steps-list">
                    <div className="step-item">
                      <span className="step-number">1</span>
                      <span className="step-text">Review the progress summary above</span>
                    </div>
                    <div className="step-item">
                      <span className="step-number">2</span>
                      <span className="step-text">Check contributor breakdown below</span>
                    </div>
                    <div className="step-item">
                      <span className="step-number">3</span>
                      <span className="step-text">Analyze latest commit changes</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column */}
              <div className="results-column right-column">
                {/* Repository Statistics Card */}
                {stats && (
                  <div className="result-card stats-card">
                    <div className="card-header">
                      <h3>📈 Repository Statistics</h3>
                      <div className="header-divider"></div>
                    </div>
                    
                    <div className="stats-grid-inline">
                      <div className="stat-card-inline">
                        <div className="stat-top-bar"></div>
                        <div className="stat-value">{stats.total_commits}</div>
                        <div className="stat-label">Commits</div>
                      </div>

                      <div className="stat-card-inline">
                        <div className="stat-top-bar"></div>
                        <div className="stat-value">{stats.total_contributors}</div>
                        <div className="stat-label">Contributors</div>
                      </div>

                      <div className="stat-card-inline">
                        <div className="stat-top-bar"></div>
                        <div className="stat-value">{stats.total_files_changed}</div>
                        <div className="stat-label">Files Changed</div>
                      </div>

                      {stats.top_contributor && (
                        <div className="stat-card-inline">
                          <div className="stat-top-bar"></div>
                          <div className="stat-value-small">{stats.top_contributor}</div>
                          <div className="stat-label">Top Contributor</div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Contributors Breakdown */}
                {stats && Object.keys(stats.contributors).length > 0 && (
                  <div className="result-card contributors-card">
                    <div className="card-header">
                      <h3>👥 Contributors</h3>
                      <div className="header-divider"></div>
                    </div>
                    <div className="contributors-list-enhanced">
                      {Object.entries(stats.contributors).slice(0, 6).map(([name, data]) => (
                        <div key={name} className="contributor-item-enhanced">
                          <div className="contributor-avatar">{name.charAt(0).toUpperCase()}</div>
                          <div className="contributor-info">
                            <div className="contributor-name">{name}</div>
                            <div className="contributor-badge">{data.commits} commits</div>
                          </div>
                        </div>
                      ))}
                      {Object.keys(stats.contributors).length > 6 && (
                        <div className="contributor-more">
                          +{Object.keys(stats.contributors).length - 6} more contributors
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Commit Breakdown */}
                {lastCommit && (
                  <div className="result-card commit-card">
                    <div className="card-header">
                      <h3>🔨 Latest Commit</h3>
                      <div className="header-divider"></div>
                    </div>
                    
                    <div className="commit-details">
                      <div className="commit-detail-row">
                        <span className="detail-label">Author:</span>
                        <span className="detail-value">{lastCommit.author}</span>
                      </div>
                      
                      {lastCommit.timestamp && (
                        <div className="commit-detail-row">
                          <span className="detail-label">Date:</span>
                          <span className="detail-value">{new Date(lastCommit.timestamp).toLocaleDateString()}</span>
                        </div>
                      )}

                      <div className="commit-message-box">
                        <span className="detail-label">Message:</span>
                        <p className="commit-message-text">{lastCommit.message}</p>
                      </div>

                      {lastCommit.files_changed && lastCommit.files_changed.length > 0 && (
                        <div className="commit-files-box">
                          <span className="detail-label">Files Changed: {lastCommit.files_changed.length}</span>
                          <div className="files-count-badge">{lastCommit.files_changed.length}</div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Empty State */}
          {!progress && !error && !loading && (
            <div className="empty-state">
              <div className="empty-icon">📊</div>
              <h3>No Repository Analyzed Yet</h3>
              <p>Enter a GitHub repository URL above to analyze its progress and track team contributions</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProgressChecker;
