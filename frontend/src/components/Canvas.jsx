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

const initialNodes = [
  {
    id: '1',
    type: 'input',
    data: { label: 'User Query' },
    position: { x: 250, y: 25 },
  },
];

const initialEdges = [];

export default function Canvas({ onSave }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState(null);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const buildDefinition = () => {
    return { nodes, edges };
  };

  const handleSave = () => {
    const definition = buildDefinition();
    onSave(definition);
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
          fitView
        >
          <MiniMap />
          <Controls />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
      </div>
      <ConfigPanel node={selectedNode} />
      <div className="canvas-toolbar">
        <button onClick={handleSave} className="save-workflow-btn">
          💾 Save Workflow
        </button>
      </div>
    </div>
  );
}
