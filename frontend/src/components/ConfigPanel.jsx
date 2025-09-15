import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function ConfigPanel({ node, onNodeUpdate }) {
  const [config, setConfig] = useState({});
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showTips, setShowTips] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    if (node) {
      setConfig(node.data?.config || {});
      if (node.type === 'KnowledgeBase') {
        fetchDocuments();
      }
    }
  }, [node]);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8001/api/v1/documents/public');
      setDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = (key, value) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
    
    if (onNodeUpdate && node) {
      onNodeUpdate(node.id, {
        ...node,
        data: {
          ...node.data,
          config: newConfig
        }
      });
    }
  };

  const handleDocumentToggle = (docId) => {
    const currentDocs = config.selectedDocuments || [];
    const newDocs = currentDocs.includes(docId)
      ? currentDocs.filter(id => id !== docId)
      : [...currentDocs, docId];
    
    handleConfigChange('selectedDocuments', newDocs);
  };

  if (!node) {
    return null; // Don't render anything when no component is selected
  }

  const renderUserQueryConfig = () => (
    <div className="config-content">
      <div className="form-group">
        <label>Placeholder Text</label>
        <input
          type="text"
          className="config-input"
          value={config.placeholder || ''}
          onChange={(e) => handleConfigChange('placeholder', e.target.value)}
          placeholder="Enter your question..."
        />
      </div>
      <div className="form-group">
        <label>Label</label>
        <input
          type="text"
          className="config-input"
          value={config.label || ''}
          onChange={(e) => handleConfigChange('label', e.target.value)}
          placeholder="User Query"
        />
      </div>
    </div>
  );

  const renderKnowledgeBaseConfig = () => (
    <div className="config-content">
      <div className="form-group">
        <label>📄 Select Documents</label>
        {loading ? (
          <div className="loading-docs">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="no-documents">
            <p>No documents uploaded yet.</p>
            <p>Upload documents first to use them in your workflow.</p>
          </div>
        ) : (
          <div className="document-list">
            {documents.map((doc) => (
              <div key={doc.id} className="document-item">
                <label className="document-label">
                  <input
                    type="checkbox"
                    checked={(config.selectedDocuments || []).includes(doc.id)}
                    onChange={() => handleDocumentToggle(doc.id)}
                  />
                  <div className="document-info">
                    <div className="document-title">{doc.title}</div>
                    <div className="document-meta">
                      {doc.file_type?.toUpperCase()} • {Math.round(doc.file_size / 1024)}KB
                      {doc.processing_status === 'completed' && (
                        <span className="status-badge">✅ Processed</span>
                      )}
                    </div>
                  </div>
                </label>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="form-group">
        <label>🎯 Similarity Threshold</label>
        <input
          type="range"
          min="0.1"
          max="0.9"
          step="0.1"
          value={config.similarityThreshold || 0.3}
          onChange={(e) => handleConfigChange('similarityThreshold', parseFloat(e.target.value))}
          className="range-input"
        />
        <div className="range-value">{(config.similarityThreshold || 0.3).toFixed(1)} - Higher = More Precise</div>
      </div>
      
      <div className="form-group">
        <label>📊 Max Results</label>
        <select
          value={config.maxResults || 5}
          onChange={(e) => handleConfigChange('maxResults', parseInt(e.target.value))}
          className="config-input"
        >
          <option value={3}>3 results</option>
          <option value={5}>5 results</option>
          <option value={10}>10 results</option>
          <option value={15}>15 results</option>
        </select>
      </div>
    </div>
  );

  const renderLLMEngineConfig = () => (
    <div className="config-content">
      <div className="form-group">
        <label>🤖 AI Model</label>
        <select
          value={config.model || 'gemini-1.5-flash'}
          onChange={(e) => handleConfigChange('model', e.target.value)}
          className="config-input"
        >
          <option value="gemini-1.5-flash">Gemini 1.5 Flash (Fast)</option>
          <option value="gemini-1.5-pro">Gemini 1.5 Pro (Advanced)</option>
        </select>
      </div>
      
      <div className="form-group">
        <label>🎭 Custom System Prompt</label>
        <textarea
          value={config.customPrompt || ''}
          onChange={(e) => handleConfigChange('customPrompt', e.target.value)}
          className="config-textarea"
          rows={4}
          placeholder="You are a helpful assistant specialized in..."
        />
        <div className="help-text">
          Define the AI's role, expertise, and response style. This shapes how the AI interprets and responds to queries.
        </div>
      </div>
      
      <div className="form-group">
        <label>🌡️ Temperature</label>
        <input
          type="range"
          min="0.1"
          max="1.0"
          step="0.1"
          value={config.temperature || 0.7}
          onChange={(e) => handleConfigChange('temperature', parseFloat(e.target.value))}
          className="range-input"
        />
        <div className="range-value">{(config.temperature || 0.7).toFixed(1)} - Higher = More Creative</div>
      </div>
      
      <div className="form-group">
        <label>📏 Max Response Length</label>
        <select
          value={config.maxTokens || 2048}
          onChange={(e) => handleConfigChange('maxTokens', parseInt(e.target.value))}
          className="config-input"
        >
          <option value={512}>Short (512 tokens)</option>
          <option value={1024}>Medium (1024 tokens)</option>
          <option value={2048}>Long (2048 tokens)</option>
          <option value={4096}>Very Long (4096 tokens)</option>
        </select>
      </div>
      
      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.useWebSearch || false}
            onChange={(e) => handleConfigChange('useWebSearch', e.target.checked)}
          />
          🌐 Enable Web Search (Coming Soon)
        </label>
      </div>
    </div>
  );

  const renderOutputConfig = () => (
    <div className="config-content">
      <div className="form-group">
        <label>📋 Output Format</label>
        <select
          value={config.format || 'text'}
          onChange={(e) => handleConfigChange('format', e.target.value)}
          className="config-input"
        >
          <option value="text">Text (Human-readable)</option>
          <option value="json">JSON (Structured data)</option>
          <option value="markdown">Markdown (Formatted text)</option>
        </select>
      </div>
      
      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.includeSources !== false}
            onChange={(e) => handleConfigChange('includeSources', e.target.checked)}
          />
          📚 Include Source References
        </label>
        <div className="help-text">
          Show which documents were used to generate the response
        </div>
      </div>
      
      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.includeMetadata || false}
            onChange={(e) => handleConfigChange('includeMetadata', e.target.checked)}
          />
          🔍 Include Metadata
        </label>
        <div className="help-text">
          Show processing time, confidence scores, and technical details
        </div>
      </div>
    </div>
  );

  const getComponentIcon = (type) => {
    switch (type) {
      case 'UserQuery': return '❓';
      case 'KnowledgeBase': return '📚';
      case 'LLMEngine': return '🤖';
      case 'Output': return '💬';
      default: return '⚙️';
    }
  };

  const getComponentDescription = (type) => {
    switch (type) {
      case 'UserQuery': return 'Entry point for user questions';
      case 'KnowledgeBase': return 'Document search and context retrieval';
      case 'LLMEngine': return 'AI processing and response generation';
      case 'Output': return 'Final response formatting and display';
      default: return 'Component configuration';
    }
  };

  return (
    <div className="config-panel">
      {/* Collapsible Header */}
      <div className="config-section">
        <button 
          className="config-toggle-btn"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          <div className="config-title">
            {getComponentIcon(node.type)} {node.type} Configuration
          </div>
          <span className={`chevron ${isCollapsed ? '' : 'open'}`}>▼</span>
        </button>
        
        {!isCollapsed && (
          <div className="config-content-wrapper">
            <p className="component-description">
              {getComponentDescription(node.type)}
            </p>
            
            {node.type === 'UserQuery' && renderUserQueryConfig()}
            {node.type === 'KnowledgeBase' && renderKnowledgeBaseConfig()}
            {node.type === 'LLMEngine' && renderLLMEngineConfig()}
            {node.type === 'Output' && renderOutputConfig()}
            
            <div className="config-footer">
              <div className="selected-count">
                {node.type === 'KnowledgeBase' && config.selectedDocuments && (
                  <span>📄 {config.selectedDocuments.length} document(s) selected</span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}