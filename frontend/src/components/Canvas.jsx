import React, { useState, useCallback } from "react";
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  addEdge,
} from '@reactflow/core';
import { MiniMap } from '@reactflow/minimap';
import { Controls } from '@reactflow/controls';
import { Background } from '@reactflow/background';
import '@reactflow/core/dist/style.css';
import '@reactflow/controls/dist/style.css';
import '@reactflow/minimap/dist/style.css';
import PalettePanel from "./PalettePanel";
import ConfigPanel from "./ConfigPanel";

const initialNodes = [];
const initialEdges = [];

export default function Canvas({ onSave }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  const [notification, setNotification] = useState('');
  const [notificationType, setNotificationType] = useState('success'); // 'success', 'error', 'info'

  const showNotification = (message, type = 'info') => {
    setNotification(message);
    setNotificationType(type);
    setTimeout(() => setNotification(''), 4000);
  };

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeUpdate = useCallback((nodeId, updatedNode) => {
    setNodes((nds) => 
      nds.map((node) => 
        node.id === nodeId ? updatedNode : node
      )
    );
  }, [setNodes]);

  const validateWorkflow = () => {
    const errors = [];
    
    // Check if workflow has required components
    const hasUserQuery = nodes.some(n => n.data?.type === 'UserQuery');
    const hasOutput = nodes.some(n => n.data?.type === 'Output');
    
    if (nodes.length === 0) {
      errors.push('Add at least one component to start building your workflow');
      setValidationErrors(errors);
      return false;
    }
    
    if (!hasUserQuery) {
      errors.push('Workflow must include a User Query component (starting point)');
    }
    
    if (!hasOutput) {
      errors.push('Workflow must include an Output component (ending point)');
    }
    
    // Check if nodes are connected
    if (nodes.length > 1 && edges.length === 0) {
      errors.push('Components must be connected with lines to create a valid workflow');
    }
    
    // Check for isolated nodes
    const nodeIds = new Set(nodes.map(n => n.id));
    const connectedNodes = new Set();
    edges.forEach(edge => {
      connectedNodes.add(edge.source);
      connectedNodes.add(edge.target);
    });
    
    const isolatedNodes = [...nodeIds].filter(id => !connectedNodes.has(id));
    if (isolatedNodes.length > 0 && nodes.length > 1) {
      errors.push(`${isolatedNodes.length} component(s) are not connected to the workflow`);
    }
    
    setValidationErrors(errors);
    return errors.length === 0;
  };

  const buildDefinition = () => {
    return { 
      nodes: nodes.map(node => ({
        id: node.id,
        type: node.data?.type || 'default',
        data: node.data || {},
        position: node.position
      })), 
      edges: edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target
      }))
    };
  };

  const handleSave = () => {
    if (validateWorkflow()) {
      const definition = buildDefinition();
      onSave(definition);
      showNotification('💾 Workflow saved successfully!', 'success');
    } else {
      showNotification('❌ Cannot save invalid workflow. Fix errors first.', 'error');
    }
  };

  const handleBuildStack = () => {
    if (validateWorkflow()) {
      showNotification('✅ Workflow is valid and ready for execution!', 'success');
    } else {
      showNotification('❌ Workflow validation failed. Check the errors panel.', 'error');
    }
  };

  const clearWorkflow = () => {
    setNodes([]);
    setEdges([]);
    setSelectedNode(null);
    setValidationErrors([]);
    showNotification('🗑️ Workflow cleared successfully', 'info');
  };

  return (
    <div className="canvas-container">
      <PalettePanel setNodes={setNodes} />
      <div className="react-flow-container">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={(event, node) => setSelectedNode(node)}
          onPaneClick={() => setSelectedNode(null)}
          fitView
          className="workflow-canvas"
        >
          <MiniMap 
            nodeColor={(node) => node.data?.color || '#94a3b8'}
            nodeStrokeWidth={3}
            className="workflow-minimap"
          />
          <Controls className="workflow-controls" />
          <Background variant="dots" gap={12} size={1} className="workflow-background" />
        </ReactFlow>
        
        {/* Notification */}
        {notification && (
          <div className={`canvas-notification ${notificationType}`}>
            {notification}
          </div>
        )}
        
        {validationErrors.length > 0 && (
          <div className="validation-errors">
            <h4>⚠️ Validation Errors:</h4>
            {validationErrors.map((error, index) => (
              <div key={index} className="error-item">• {error}</div>
            ))}
          </div>
        )}
      </div>
      
      <ConfigPanel 
        node={selectedNode} 
        onNodeUpdate={onNodeUpdate}
      />
      
      <div className="canvas-toolbar">
        <div className="toolbar-section">
          <button onClick={handleBuildStack} className="build-stack-btn">
            🔧 Build Check
          </button>
          <button onClick={handleSave} className="save-workflow-btn">
            💾 Save Workflow
          </button>
          <button onClick={clearWorkflow} className="clear-workflow-btn">
            🗑️ Clear All
          </button>
        </div>
        
        <div className="workflow-stats">
          <span className="stat-item">
            📊 {nodes.length} Components
          </span>
          <span className="stat-item">
            🔗 {edges.length} Connections
          </span>
          {validationErrors.length === 0 && nodes.length > 0 && (
            <span className="stat-item valid">
              ✅ Valid Workflow
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
