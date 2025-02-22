import React, { useEffect } from 'react';
import cytoscape from 'cytoscape';
import tippy from 'tippy.js';
import 'tippy.js/dist/tippy.css';
import './ArgumentDAG.css'; // If you want separate styling

const ArgumentDAG = () => {
  useEffect(() => {
    // Replace with your local or deployed API address
    fetch('http://localhost:8000/visualize-argument-dag')
      .then(response => response.json())
      .then(data => {
        const cy = cytoscape({
          container: document.getElementById('cy'),
          elements: [
            ...data.nodes.map(node => ({
              data: {
                id: node.id,
                label: node.text,
                type: node.label,
                details: node.details
              }
            })),
            ...data.edges.map(edge => ({
              data: {
                source: edge.source,
                target: edge.target,
                label: edge.type,
                relationship: edge.type
              }
            }))
          ],
          style: [
            {
              selector: 'node',
              style: {
                'background-color': '#0074D9',
                'label': 'data(label)',
                'text-valign': 'center',
                'color': '#fff',
                'font-size': '12px',
                'border-width': 2,
                'border-color': '#fff'
              }
            },
            {
              selector: '[type = "Claim"]',
              style: {
                'background-color': '#FF4136'
              }
            },
            {
              selector: '[type = "Warrant"]',
              style: {
                'background-color': '#2ECC40'
              }
            },
            {
              selector: '[type = "Rebuttal"]',
              style: {
                'background-color': '#FF851B'
              }
            },
            {
              selector: 'edge',
              style: {
                'width': 2,
                'line-color': '#ccc',
                'target-arrow-shape': 'triangle',
                'target-arrow-color': '#ccc',
                'curve-style': 'bezier'
              }
            },
            {
              selector: '.highlighted',
              style: {
                'line-color': '#FFD700',
                'target-arrow-color': '#FFD700',
                'width': 4
              }
            }
          ],
          layout: {
            name: 'cose',
            animate: true
          }
        });

        // Node tooltips (Tippy.js)
        cy.nodes().forEach(node => {
          const ref = node.popperRef();
          tippy(ref, {
            content: `Type: ${node.data('type')}\nDetails: ${node.data('details') || 'N/A'}`,
            trigger: 'mouseenter',
            placement: 'top',
            arrow: true,
            theme: 'light',
          });
        });

        // Edge hover highlight
        cy.on('mouseover', 'edge', evt => {
          evt.target.addClass('highlighted');
        });
        cy.on('mouseout', 'edge', evt => {
          evt.target.removeClass('highlighted');
        });

        // Clickable edge interactions
        cy.on('tap', 'edge', evt => {
          const edge = evt.target;
          alert(`Relationship: ${edge.data('relationship')}\nSource: ${edge.data('source')}\nTarget: ${edge.data('target')}`);
        });

        // Node filtering example
        document.getElementById('filter-claims').addEventListener('click', () => {
          cy.nodes().forEach(node => {
            node.style('display', node.data('type') === 'Claim' ? 'element' : 'none');
          });
        });

        document.getElementById('reset-filter').addEventListener('click', () => {
          cy.nodes().forEach(node => {
            node.style('display', 'element');
          });
        });
      })
      .catch(error => console.error('Error fetching DAG:', error));
  }, []);

  return (
    <>
      <div id="cy" style={{ width: '100%', height: '600px' }}></div>
      <button id="filter-claims">Show Only Claims</button>
      <button id="reset-filter">Reset Filter</button>
    </>
  );
};

export default ArgumentDAG;