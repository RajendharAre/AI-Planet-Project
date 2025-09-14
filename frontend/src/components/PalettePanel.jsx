import React from 'react';

const nodeTypes = [
  { type: 'UserQuery', label: '👤 User Query', description: 'Input from user' },
  { type: 'KnowledgeBase', label: '📚 Knowledge Base', description: 'Search documents' },
  { type: 'LLM', label: '🤖 LLM', description: 'AI language model' },
  { type: 'Output', label: '📝 Output', description: 'Final response' },
];

export default function PalettePanel({ setNodes }) {
  const addNode = (nodeType) => {
    const newNode = {
      id: `${nodeType.type}_${Date.now()}`,
      type: nodeType.type === 'UserQuery' ? 'input' : 
            nodeType.type === 'Output' ? 'output' : 'default',
      data: { 
        label: nodeType.label,
        nodeType: nodeType.type
      },
      position: { 
        x: Math.random() * 400 + 100, 
        y: Math.random() * 300 + 100 
      },
    };

    setNodes((nodes) => [...nodes, newNode]);
  };

  return (
    <div className="palette-panel">
      <h3>Workflow Components</h3>
      <div className="node-types">
        {nodeTypes.map((nodeType) => (
          <div
            key={nodeType.type}
            className="node-item"
            onClick={() => addNode(nodeType)}
            title={nodeType.description}
          >
            <div className="node-label">{nodeType.label}</div>
            <div className="node-description">{nodeType.description}</div>
          </div>
        ))}
      </div>
      
      <div className="palette-instructions">
        <h4>Instructions:</h4>
        <ul>
          <li>Click on components to add them to the canvas</li>
          <li>Drag nodes to position them</li>
          <li>Connect nodes by dragging from one to another</li>
          <li>Click nodes to configure their properties</li>
        </ul>
      </div>
    </div>
  );
}
