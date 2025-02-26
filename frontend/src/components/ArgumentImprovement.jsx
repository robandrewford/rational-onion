import React, { useState } from 'react';
import './ArgumentImprovement.css';

const ArgumentImprovement = () => {
  const [argumentId, setArgumentId] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
      const API_KEY = process.env.REACT_APP_API_KEY || 'test_api_key_123';
      
      const url = argumentId 
        ? `${API_BASE_URL}/suggest-improvements?argument_id=${argumentId}`
        : `${API_BASE_URL}/suggest-improvements`;
      
      console.log('Getting improvement suggestions');
      console.log('API URL:', url);
      
      const response = await fetch(url, {
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
        throw new Error(errorData.detail?.message || 'Failed to get improvement suggestions');
      }
      
      const data = await response.json();
      console.log('Success response:', data);
      setSuggestions(data);
    } catch (err) {
      console.error('Error getting improvement suggestions:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="improvement-container">
      <h2>Argument Improvement</h2>
      <p className="description">
        Get AI-powered suggestions to improve your arguments using structured reasoning principles.
        Our system analyzes your arguments for logical consistency, evidence strength, and adherence to the Toulmin model.
      </p>
      
      <form onSubmit={handleSubmit} className="improvement-form">
        <div className="form-group">
          <label htmlFor="argumentId">Argument ID (optional)</label>
          <input
            type="text"
            id="argumentId"
            value={argumentId}
            onChange={(e) => setArgumentId(e.target.value)}
            placeholder="Leave empty to analyze all arguments"
          />
          <small className="input-help">
            Enter a specific argument ID to get targeted suggestions, or leave blank to analyze all arguments.
          </small>
        </div>
        
        <button type="submit" disabled={loading} className="submit-button">
          {loading ? 'Analyzing...' : 'Get Improvement Suggestions'}
        </button>
      </form>
      
      {error && (
        <div className="error-message">
          <h3>Error</h3>
          <p>{error}</p>
        </div>
      )}
      
      {suggestions && (
        <div className="suggestions-container">
          <h3>Improvement Suggestions</h3>
          
          <div className="quality-score">
            <h4>Overall Quality Score</h4>
            <div className="score-display">
              <div 
                className="score-bar"
                style={{ width: `${suggestions.quality_score * 100}%` }}
              ></div>
              <span>{(suggestions.quality_score * 10).toFixed(1)}/10</span>
            </div>
          </div>
          
          {suggestions.missing_components && suggestions.missing_components.length > 0 && (
            <div className="missing-components">
              <h4>Missing Components</h4>
              <ul>
                {suggestions.missing_components.map((component, index) => (
                  <li key={index}>{component}</li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="improvement-list">
            <h4>Specific Suggestions</h4>
            {suggestions.improvement_suggestions && suggestions.improvement_suggestions.map((suggestion, index) => (
              <div key={index} className="suggestion-item">
                <h5>For: {suggestion.claim}</h5>
                <ul>
                  {suggestion.improvement_suggestions && suggestion.improvement_suggestions.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          
          {suggestions.external_references && suggestions.external_references.length > 0 && (
            <div className="references">
              <h4>Recommended References</h4>
              <ul>
                {suggestions.external_references.map((ref, index) => (
                  <li key={index}>
                    {ref.author} ({ref.year}). <em>{ref.title}</em>. {ref.source}.
                    {ref.url && <a href={ref.url} target="_blank" rel="noopener noreferrer"> Link</a>}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="message-box">
            <p>{suggestions.message}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ArgumentImprovement; 