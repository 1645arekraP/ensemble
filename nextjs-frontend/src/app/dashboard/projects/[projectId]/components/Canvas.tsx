// components/Canvas.tsx
"use client"

import React from 'react';
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowInstance,
  Node,
  Edge,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
  NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

interface CanvasProps {
  nodes: Node[];
  edges: Edge[];
  nodeTypes: NodeTypes;
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  onInit: (instance: ReactFlowInstance) => void;
  onDragOver: (event: React.DragEvent) => void;
  onDrop: (event: React.DragEvent) => void;
}

export function Canvas({
  nodes,
  edges,
  nodeTypes,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onInit,
  onDragOver,
  onDrop,
}: CanvasProps) {
  return (
    <div className="flex-1 overflow-hidden h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        onInit={onInit}
        onDragOver={onDragOver}
        onDrop={onDrop}
      >
        <Controls />
        <MiniMap />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}