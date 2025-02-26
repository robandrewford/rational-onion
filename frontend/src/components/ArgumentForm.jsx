import React, { useState } from 'react';
import './ArgumentForm.css';

const ArgumentForm = () => {
  const [argument, setArgument] = useState({
    claim: '',
    grounds: '',
    warrant: '',
    backing: '',
    rebuttal: '',
    qualifier: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => {
    setArgument({
      ...argument,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);
    
    try {
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
      const API_KEY = process.env.REACT_APP_API_KEY || 'test_api_key_123';
      
      console.log('Submitting argument:', argument);
      console.log('API URL:', `${API_BASE_URL}/insert-argument`);
      
      const response = await fetch(`${API_BASE_URL}/insert-argument`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY
        },
        body: JSON.stringify(argument)
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        throw new Error(errorData.detail?.message || 'Failed to create argument');
      }
      
      const data = await response.json();
      console.log('Success response:', data);
      
      setSuccess(true);
      setArgument({
        claim: '',
        grounds: '',
        warrant: '',
        backing: '',
        rebuttal: '',
        qualifier: ''
      });
    } catch (err) {
      console.error('Error creating argument:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="argument-form-container">
      <h2>Create New Argument</h2>
      {success && <div className="success-message">Argument created successfully!</div>}
      {error && <div className="error-message">Error: {error}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="claim">Claim</label>
          <textarea 
            id="claim"
            name="claim"
            value={argument.claim}
            onChange={handleChange}
            required
            placeholder="The main point you're trying to make"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="grounds">Grounds</label>
          <textarea 
            id="grounds"
            name="grounds"
            value={argument.grounds}
            onChange={handleChange}
            required
            placeholder="Evidence supporting your claim"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="warrant">Warrant</label>
          <textarea 
            id="warrant"
            name="warrant"
            value={argument.warrant}
            onChange={handleChange}
            required
            placeholder="Explanation of how the grounds support the claim"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="backing">Backing (Optional)</label>
          <textarea 
            id="backing"
            name="backing"
            value={argument.backing}
            onChange={handleChange}
            placeholder="Additional support for the warrant"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="rebuttal">Rebuttal (Optional)</label>
          <textarea 
            id="rebuttal"
            name="rebuttal"
            value={argument.rebuttal}
            onChange={handleChange}
            placeholder="Conditions under which the claim might not hold"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="qualifier">Qualifier (Optional)</label>
          <textarea 
            id="qualifier"
            name="qualifier"
            value={argument.qualifier}
            onChange={handleChange}
            placeholder="Words like 'probably', 'possibly' that limit the claim"
          />
        </div>
        
        <button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create Argument'}
        </button>
      </form>
    </div>
  );
};

export default ArgumentForm; 