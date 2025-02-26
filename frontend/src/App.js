import React, { useState } from 'react';
import './App.css';
import ArgumentDAG from './ArgumentDAG';
import ArgumentForm from './components/ArgumentForm';
import ArgumentVerification from './components/ArgumentVerification';
import ArgumentImprovement from './components/ArgumentImprovement';

function App() {
  const [activeTab, setActiveTab] = useState('visualization');

  const renderContent = () => {
    switch(activeTab) {
      case 'create':
        return <ArgumentForm />;
      case 'verify':
        return <ArgumentVerification />;
      case 'improve':
        return <ArgumentImprovement />;
      case 'visualization':
      default:
        return <ArgumentDAG />;
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Rational Onion - Structured Argument Analysis</h1>
        <nav className="main-nav">
          <button 
            className={activeTab === 'visualization' ? 'active' : ''}
            onClick={() => setActiveTab('visualization')}
          >
            Visualization
          </button>
          <button 
            className={activeTab === 'create' ? 'active' : ''}
            onClick={() => setActiveTab('create')}
          >
            Create Argument
          </button>
          <button 
            className={activeTab === 'verify' ? 'active' : ''}
            onClick={() => setActiveTab('verify')}
          >
            Verify Arguments
          </button>
          <button 
            className={activeTab === 'improve' ? 'active' : ''}
            onClick={() => setActiveTab('improve')}
          >
            Improve Arguments
          </button>
        </nav>
      </header>
      
      <main className="App-main">
        {renderContent()}
      </main>
      
      <footer className="App-footer">
        <p>Rational Onion - A tool for structured argumentation using Toulmin's model</p>
      </footer>
    </div>
  );
}

export default App; 