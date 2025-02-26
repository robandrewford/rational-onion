import React, { useState } from 'react';
import './ArgumentVerification.css';

const ArgumentVerification = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const verifyAllArguments = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
      const API_KEY = process.env.REACT_APP_API_KEY || 'test_api_key_123';
      
      console.log('Verifying all arguments');
      console.log('API URL:', `${API_BASE_URL}/verify-argument-structure`);
      
      const response = await fetch(`${API_BASE_URL}/verify-argument-structure`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY
        }
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        throw new Error(errorData.detail?.message || 'Verification failed');
      }
      
      const data = await response.json();
      console.log('Success response:', data);
      setResults(data);
    } catch (err) {
      console.error('Error verifying arguments:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="verification-container">
      <h2>Argument Verification</h2>
      <p className="description">
        Verify the logical structure and consistency of all arguments in the system.
        This process checks for cycles, orphaned nodes, and invalid relationships.
      </p>
      
      <button 
        onClick={verifyAllArguments}
        disabled={loading}
        className="verify-button"
      >
        {loading ? 'Verifying...' : 'Verify All Arguments'}
      </button>
      
      {error && (
        <div className="error-message">
          <h3>Verification Error</h3>
          <p>{error}</p>
        </div>
      )}
      
      {results && (
        <div className="verification-results">
          <h3>Verification Results</h3>
          <div className="result-item">
            <span className="result-label">Status:</span>
            <span className={`result-value ${results.is_valid ? 'valid' : 'invalid'}`}>
              {results.is_valid ? 'Valid' : 'Invalid'}
            </span>
          </div>
          
          <div className="result-item">
            <span className="result-label">Cycles Detected:</span>
            <span className={`result-value ${results.has_cycles ? 'invalid' : 'valid'}`}>
              {results.has_cycles ? 'Yes' : 'No'}
            </span>
          </div>
          
          {results.orphaned_nodes && results.orphaned_nodes.length > 0 && (
            <div className="result-item">
              <span className="result-label">Orphaned Nodes:</span>
              <ul className="orphaned-list">
                {results.orphaned_nodes.map((node, index) => (
                  <li key={index}>{node}</li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="result-message">
            <p>{results.message}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ArgumentVerification; 