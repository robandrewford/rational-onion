import React, { useEffect, useRef, useState, useCallback } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import './ArgumentDAG.css';

// Register dagre layout
cytoscape.use(dagre);

// Use environment variable or fallback to default
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
const API_KEY = process.env.REACT_APP_API_KEY || 'test_api_key_123';

const ArgumentDAG = () => {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [graphStats, setGraphStats] = useState({
    nodeCount: 0,
    edgeCount: 0,
    lastUpdated: null
  });

  const fetchData = useCallback(async () => {
    if (!containerRef.current) {
      console.error('Container ref is not available');
      setError('Visualization container is not ready');
      setLoading(false);
      return;
    }

    try {
      console.log('Starting data fetch - Container ref is available');
      setLoading(true);
      setError(null);

      const visualizationUrl = `${API_BASE_URL}/visualize-argument-dag`;

      // Detailed logging for fetch configuration
      console.log('Fetch Configuration:', {
        url: visualizationUrl,
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY
        }
      });

      const response = await fetch(visualizationUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY
        }
      });

      console.log('Fetch Response:', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Fetch Error Response:', errorText);
        console.error('API Key used:', API_KEY);
        console.error('API URL used:', visualizationUrl);
        setError(`HTTP error! status: ${response.status}, message: ${errorText}`);
        setLoading(false);
        return;
      }

      const data = await response.json();
      console.log('Parsed JSON Data:', data);

      // Validate data structure
      if (!data || !data.nodes || !data.edges) {
        console.warn('Received invalid data structure:', data);
        setError('Invalid graph data received');
        setLoading(false);
        return;
      }

      // Log node and edge details
      console.log('Nodes:', data.nodes);
      console.log('Edges:', data.edges);

      // Prepare Cytoscape elements
      const cytoscapeElements = [
        ...data.nodes.map(node => ({
          data: {
            id: node.id,
            label: node.label || node.text || 'Unnamed Node',
            type: node.type || 'unknown',
            details: node.details || ''
          }
        })),
        ...data.edges.map(edge => ({
          data: {
            source: edge.source,
            target: edge.target,
            type: edge.type || 'unspecified'
          }
        }))
      ];

      console.log('Cytoscape Elements:', cytoscapeElements);

      // Update graph statistics
      setGraphStats({
        nodeCount: data.nodes.length,
        edgeCount: data.edges.length,
        lastUpdated: new Date().toISOString()
      });

      // Initialize or update Cytoscape
      if (cyRef.current) {
        cyRef.current.destroy();
      }

      // Make sure container is properly sized before initializing Cytoscape
      console.log('Container dimensions:', {
        width: containerRef.current.offsetWidth,
        height: containerRef.current.offsetHeight
      });

      cyRef.current = cytoscape({
        container: containerRef.current,
        elements: cytoscapeElements,
        style: [
          {
            selector: 'node',
            style: {
              'background-color': (ele) => {
                switch(ele.data('type')) {
                  case 'claim': return '#3498db';  // Blue for claims
                  case 'ground': return '#2ecc71';  // Green for grounds
                  case 'warrant': return '#e74c3c';  // Red for warrants
                  default: return '#666';  // Default gray
                }
              },
              'shape': 'rectangle',  // Change from default ellipse to rectangle
              'label': 'data(label)',
              'color': '#fff',
              'text-valign': 'center',
              'text-halign': 'center',
              'width': 140,  // Slightly increased for squares
              'height': 80,  // Adjusted height for square-ish shape
              'font-size': '12px',
              'text-wrap': 'wrap',
              'text-max-width': 120,
              'border-width': 2,
              'border-color': '#2c3e50',
              'border-opacity': 0.7,
              'border-radius': 5  // Add slight rounding to corners
            }
          },
          {
            selector: 'edge',
            style: {
              'width': 3,
              'line-color': '#95a5a6',
              'target-arrow-color': '#7f8c8d',
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
              'arrow-scale': 1.5,
              'label': 'data(type)'
            }
          }
        ],
        layout: {
          name: 'dagre',  // More structured layout for DAGs
          rankDir: 'TB',  // Top to Bottom direction
          spacingFactor: 1.5,  // More spacing between nodes
          nodeSep: 60,  // Separation between nodes
          edgeSep: 40,  // Separation between edges
          rankSep: 120,  // Separation between ranks (levels)
          fit: true,     // Fit the graph to the container
          padding: 50    // Padding around the graph
        },
        minZoom: 0.5,
        maxZoom: 2.0,
        wheelSensitivity: 0.2
      });

      // Force a resize after initialization
      setTimeout(() => {
        if (cyRef.current) {
          cyRef.current.resize();
          cyRef.current.fit();
        }
      }, 100);

      setLoading(false);
    } catch (err) {
      console.error('Comprehensive Fetch Error:', {
        message: err.message,
        name: err.name,
        stack: err.stack
      });
      setError(`Error loading visualization: ${err.message}`);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();

    // Add resize handler to ensure responsiveness
    const handleResize = () => {
      if (cyRef.current) {
        cyRef.current.resize();
        cyRef.current.fit();
      }
    };

    window.addEventListener('resize', handleResize);

    // Cleanup function
    return () => {
      window.removeEventListener('resize', handleResize);
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [fetchData]);

  return (
    <div className="dag-container">
      {loading && (
        <div className="loading-message">
          <div className="loading-spinner"></div>
          Initializing visualization...
        </div>
      )}
      
      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
          <br />
          <small>Please check the console for more details.</small>
        </div>
      )}
      
      <div className="filter-controls">
        <button 
          id="filter-claims" 
          className="filter-btn"
          onClick={() => {
            if (cyRef.current) {
              cyRef.current.nodes().forEach(node => {
                node.style('opacity', node.data('type') === 'claim' ? 1 : 0.3);
              });
            }
          }}
        >
          Filter Claims
        </button>
        <button 
          id="reset-filter" 
          className="filter-btn"
          onClick={() => {
            if (cyRef.current) {
              cyRef.current.nodes().style('opacity', 1);
            }
          }}
        >
          Reset Filter
        </button>
      </div>

      <div 
        ref={containerRef} 
        className="cytoscape-container"
        style={{ 
          display: loading || error ? 'none' : 'block',
          height: '500px', // Explicit height
          border: '1px solid #ddd',
          borderRadius: '5px',
          overflow: 'hidden',
          margin: '10px 0'
        }}
      ></div>
      
      {!loading && !error && (
        <div className="graph-stats">
          <p>Nodes: {graphStats.nodeCount} | Edges: {graphStats.edgeCount}</p>
          <p>Last Updated: {new Date(graphStats.lastUpdated).toLocaleString()}</p>
        </div>
      )}
    </div>
  );
};

export default ArgumentDAG;