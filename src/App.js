import React from 'react';
import './App.css';
import ArgumentDAG from './ArgumentDAG';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Rational-Onion DAG Visualization</h1>
      </header>
      <main>
        <ArgumentDAG />
      </main>
    </div>
  );
}

export default App; 