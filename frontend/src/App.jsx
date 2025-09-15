import React, { useState } from 'react';
import './App.css';
import './modern-styles.css';
import Canvas from './components/Canvas';
import ChatModal from './components/ChatModal';
import { uploadDoc, runWorkflow } from './api/api';

function App() {
  const [currentView, setCurrentView] = useState('home');
  const [showChat, setShowChat] = useState(false);
  const [workflowDefinition, setWorkflowDefinition] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [notification, setNotification] = useState('');

  // Default workflow for basic chat functionality
  const defaultWorkflow = {
    nodes: [
      {
        id: '1',
        type: 'UserQuery',
        data: { 
          label: 'User Query',
          type: 'UserQuery',
          icon: '❓',
          color: '#3B82F6'
        },
        position: { x: 250, y: 25 },
      },
      {
        id: '2',
        type: 'LLMEngine',
        data: { 
          label: 'LLM Engine',
          type: 'LLMEngine',
          icon: '🤖',
          color: '#8B5CF6'
        },
        position: { x: 250, y: 125 },
      },
      {
        id: '3',
        type: 'Output',
        data: { 
          label: 'Output',
          type: 'Output',
          icon: '💬',
          color: '#F59E0B'
        },
        position: { x: 250, y: 225 },
      }
    ],
    edges: [
      {
        id: 'e1-2',
        source: '1',
        target: '2',
      },
      {
        id: 'e2-3',
        source: '2',
        target: '3',
      }
    ]
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      setNotification('Uploading document...');
      const response = await uploadDoc(file);
      setDocuments(prev => [...prev, { name: file.name, ...response.data }]);
      setNotification('Document uploaded successfully!');
      setTimeout(() => setNotification(''), 3000);
    } catch (error) {
      console.error('Upload failed:', error);
      setNotification('Upload failed. Please try again.');
      setTimeout(() => setNotification(''), 3000);
    }
  };

  const handleWorkflowSave = (definition) => {
    setWorkflowDefinition(definition);
    // Notification is now handled in Canvas component
  };

  const handleRunWorkflow = async (query, customPrompt) => {
    // Use custom workflow if available, otherwise use default
    const activeWorkflow = workflowDefinition || defaultWorkflow;
    
    if (!activeWorkflow) {
      alert('Unable to process request. Please try again.');
      return;
    }

    try {
      const response = await runWorkflow(activeWorkflow, query, customPrompt);
      return response.data.answer;
    } catch (error) {
      console.error('Workflow execution failed:', error);
      throw error;
    }
  };

  const renderHome = () => (
    <div className="App-header">
      <h1>AI Planet - Workflow Engine</h1>
      <p>
        Welcome to AI Planet! Build and execute AI workflows with ease.
      </p>
      <div className="getting-started">
        <h2>Getting Started</h2>
        <div className="action-buttons">
          <button 
            className="action-btn" 
            onClick={() => setCurrentView('upload')}
          >
            📄 Upload Documents
          </button>
          <button 
            className="action-btn" 
            onClick={() => setCurrentView('workflow')}
          >
            🔧 Build Workflow
          </button>
          <button 
            className="action-btn" 
            onClick={() => setShowChat(true)}
          >
            💬 Chat with AI
          </button>
        </div>
      </div>
      {notification && (
        <div className="notification">
          {notification}
        </div>
      )}
    </div>
  );

  const renderUpload = () => (
    <div className="App-header">
      <h1>Upload Documents</h1>
      <div className="upload-section">
        <input 
          type="file" 
          accept=".pdf" 
          onChange={handleFileUpload}
          className="file-input"
          id="file-upload"
        />
        <label htmlFor="file-upload" className="upload-btn">
          Choose PDF File
        </label>
      </div>
      
      {documents.length > 0 && (
        <div className="documents-list">
          <h3>Uploaded Documents:</h3>
          <ul>
            {documents.map((doc, index) => (
              <li key={index}>{doc.name}</li>
            ))}
          </ul>
        </div>
      )}
      
      <button className="back-btn" onClick={() => setCurrentView('home')}>
        ← Back to Home
      </button>
      
      {notification && (
        <div className="notification">
          {notification}
        </div>
      )}
    </div>
  );

  const renderWorkflow = () => (
    <div className="workflow-container">
      <div className="workflow-header">
        <h2>Workflow Builder</h2>
        <button className="back-btn" onClick={() => setCurrentView('home')}>
          ← Back to Home
        </button>
      </div>
      <Canvas onSave={handleWorkflowSave} />
    </div>
  );

  return (
    <div className="App">
      {currentView === 'home' && renderHome()}
      {currentView === 'upload' && renderUpload()}
      {currentView === 'workflow' && renderWorkflow()}
      
      {showChat && (
        <ChatModal 
          onClose={() => setShowChat(false)}
          onRunWorkflow={handleRunWorkflow}
        />
      )}
    </div>
  );
}

export default App;