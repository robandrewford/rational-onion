import React from 'react';
import ReactDOM from 'react-dom/client';
import ArgumentDAG from './ArgumentDAG';

function App() {
  return (
    <div>
      <h1>Rational-Onion DAG Visualization</h1>
      <ArgumentDAG />
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);