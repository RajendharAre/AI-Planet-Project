import React from 'react';

export default function ConfigPanel({ node }) {
  if (!node) {
    return (
      <div className="config-panel">
        <h3>Configuration</h3>
        <p>Select a node to configure its properties</p>
      </div>
    );
  }

  return (
    <div className="config-panel">
      <h3>Configure: {node.data?.label || 'Node'}</h3>
      <div className="config-content">
        <div className="form-group">
          <label>Node Type:</label>
          <span>{node.type || 'default'}</span>
        </div>
        <div className="form-group">
          <label>Label:</label>
          <input 
            type="text" 
            defaultValue={node.data?.label || ''} 
            placeholder="Enter node label"
            className="config-input"
          />
        </div>
        {node.type === 'LLM' && (
          <div className="form-group">
            <label>Model:</label>
            <select className="config-input">
              <option value="gpt-4o-mini">GPT-4O Mini</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </select>
          </div>
        )}
        {node.type === 'KnowledgeBase' && (
          <div className="form-group">
            <label>Collection Name:</label>
            <input 
              type="text" 
              placeholder="Enter collection name"
              className="config-input"
            />
          </div>
        )}
      </div>
    </div>
  );
}