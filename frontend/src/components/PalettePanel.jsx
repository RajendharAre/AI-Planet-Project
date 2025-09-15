import React, { useState } from 'react';

const COMPONENTS = [
  {
    type: 'UserQuery',
    name: 'User Query',
    icon: '❓',
    color: '#3B82F6',
    category: 'Input'
  },
  {
    type: 'KnowledgeBase', 
    name: 'Knowledge Base',
    icon: '📚',
    color: '#10B981',
    category: 'Data'
  },
  {
    type: 'LLMEngine',
    name: 'LLM Engine', 
    icon: '🤖',
    color: '#8B5CF6',
    category: 'Processing'
  },
  {
    type: 'Output',
    name: 'Output',
    icon: '💬',
    color: '#F59E0B',
    category: 'Output'
  }
];

export default function PalettePanel({ setNodes }) {
  const [showGuide, setShowGuide] = useState(false);
  const [showTips, setShowTips] = useState(false);

  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const addComponent = (component) => {
    const newNode = {
      id: `${component.type.toLowerCase()}-${Date.now()}`,
      type: 'default',
      data: { 
        label: component.name,
        type: component.type,
        icon: component.icon,
        color: component.color,
        config: {}
      },
      position: { 
        x: Math.random() * 250 + 100, 
        y: Math.random() * 250 + 100 
      },
      style: {
        background: component.color,
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        padding: '10px',
        minWidth: '120px',
        textAlign: 'center',
        fontSize: '12px',
        fontWeight: '500'
      }
    };

    setNodes((nds) => nds.concat(newNode));
  };

  return (
    <div className="palette-panel">
      <div className="palette-header">
        <h3>🎨 Component Library</h3>
        <p>Drag components to build your workflow</p>
      </div>
      
      <div className="component-categories">
        {['Input', 'Data', 'Processing', 'Output'].map(category => {
          const categoryComponents = COMPONENTS.filter(c => c.category === category);
          return (
            <div key={category} className="component-category">
              <h4 className="category-title">{category}</h4>
              <div className="component-grid">
                {categoryComponents.map((component) => (
                  <div
                    key={component.type}
                    className="component-card"
                    draggable
                    onDragStart={(event) => onDragStart(event, component.type)}
                    onClick={() => addComponent(component)}
                    style={{
                      borderLeft: `4px solid ${component.color}`
                    }}
                  >
                    <div className="component-icon" style={{ color: component.color }}>
                      {component.icon}
                    </div>
                    <div className="component-details">
                      <div className="component-name">{component.name}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Quick Start Guide Button */}
      <div className="help-section">
        <button 
          className="help-toggle-btn"
          onClick={() => setShowGuide(!showGuide)}
        >
          🚀 Quick Start Guide
          <span className={`chevron ${showGuide ? 'open' : ''}`}>▼</span>
        </button>
        {showGuide && (
          <div className="help-content">
            <div className="guide-steps">
              <div className="guide-step">
                <span className="step-number">1</span>
                <span>Drag components to canvas</span>
              </div>
              <div className="guide-step">
                <span className="step-number">2</span>
                <span>Connect components with lines</span>
              </div>
              <div className="guide-step">
                <span className="step-number">3</span>
                <span>Configure each component</span>
              </div>
              <div className="guide-step">
                <span className="step-number">4</span>
                <span>Save and test your workflow</span>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Pro Tips Button */}
      <div className="help-section">
        <button 
          className="help-toggle-btn"
          onClick={() => setShowTips(!showTips)}
        >
          💡 Pro Tips
          <span className={`chevron ${showTips ? 'open' : ''}`}>▼</span>
        </button>
        {showTips && (
          <div className="help-content">
            <div className="tips-list">
              <div className="tip-item">
                • Start with User Query component
              </div>
              <div className="tip-item">
                • End with Output component
              </div>
              <div className="tip-item">
                • Upload documents before using Knowledge Base
              </div>
              <div className="tip-item">
                • Configure custom prompts in LLM Engine
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
