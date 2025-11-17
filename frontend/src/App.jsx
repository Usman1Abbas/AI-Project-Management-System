import React, { useState } from 'react';
import { createProject } from './api';
import ProgressChecker from './ProgressChecker';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('create');
  const [formData, setFormData] = useState({
    project_name: '',
    project_type: 'web',
    assignees: '',
    requirements: ''
  });
  
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const assigneesList = formData.assignees
        .split(',')
        .map(a => a.trim())
        .filter(a => a);

      const response = await createProject({
        project_name: formData.project_name,
        project_type: formData.project_type,
        assignees: assigneesList,
        requirements: formData.requirements || null
      });

      setResult(response);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="app">
      <div className="container">
        <h1>🚀 AI Project Automation</h1>
        <p className="subtitle">Generate production-ready projects instantly with AI</p>
        
        {/* Tab Navigation */}
        <div className="tab-navigation">
          <button 
            className={`tab-button ${activeTab === 'create' ? 'active' : ''}`}
            onClick={() => setActiveTab('create')}
          >
            ✨ Create Project
          </button>
          <button 
            className={`tab-button ${activeTab === 'analyze' ? 'active' : ''}`}
            onClick={() => setActiveTab('analyze')}
          >
            📊 Analyze Repository
          </button>
        </div>

        {/* Create Project Tab */}
        {activeTab === 'create' && (
          <>
            <form onSubmit={handleSubmit} className="project-form">
              <div className="form-group">
                <label>Project Name</label>
                <input
                  type="text"
                  name="project_name"
                  value={formData.project_name}
                  onChange={handleChange}
                  required
                  placeholder="my-awesome-project"
                />
              </div>

              <div className="form-group">
                <label>Project Type</label>
                <select
                  name="project_type"
                  value={formData.project_type}
                  onChange={handleChange}
                  required
                >
                  <option value="web">Web Application</option>
                  <option value="api">REST API</option>
                  <option value="mobile">Mobile App</option>
                  <option value="cli">CLI Tool</option>
                  <option value="library">Library</option>
                  <option value="data">Data Science</option>
                </select>
              </div>

              <div className="form-group">
                <label>Assignees (GitHub usernames, comma-separated)</label>
                <input
                  type="text"
                  name="assignees"
                  value={formData.assignees}
                  onChange={handleChange}
                  placeholder="user1, user2, user3"
                />
              </div>

              <div className="form-group">
                <label>Requirements (optional)</label>
                <textarea
                  name="requirements"
                  value={formData.requirements}
                  onChange={handleChange}
                  placeholder="Describe your project requirements, features, tech stack preferences, etc."
                  rows="4"
                />
              </div>

              <button type="submit" disabled={loading} className="submit-btn">
                {loading ? 'Creating Project...' : 'Create Project'}
              </button>
            </form>

            {error && (
              <div className="error-box">
                <h3>❌ Error</h3>
                <p>{error}</p>
              </div>
            )}

            {result && (
              <div className="success-box">
                <h3>✅ Project Created Successfully!</h3>
                <div className="result-details">
                  <p><strong>Project:</strong> {result.name}</p>
                  <p><strong>Type:</strong> {result.type}</p>
                  {result.requirements && (
                    <p><strong>Requirements:</strong> {result.requirements}</p>
                  )}
                  <p>
                    <strong>Repository:</strong>{' '}
                    <a href={result.repo_url} target="_blank" rel="noopener noreferrer">
                      {result.repo_url}
                    </a>
                  </p>
                  <p><strong>Created:</strong> {new Date(result.created_at).toLocaleString()}</p>
                </div>
              </div>
            )}
          </>
        )}

        {/* Analyze Repository Tab */}
        {activeTab === 'analyze' && (
          <div className="progress-checker-wrapper">
            <ProgressChecker />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

