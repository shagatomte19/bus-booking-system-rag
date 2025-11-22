import React, { useState } from 'react';
import { askProviderQuestion } from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const ProviderChat = () => {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const exampleQuestions = [
    // Route and price queries
    "Are there any buses from Dhaka to Rajshahi under 500 taka?",
    "Show all bus providers operating from Chattogram to Sylhet",
    "Which buses go from Dhaka to Barishal?",
    "What's the cheapest bus from Khulna to Rajshahi?",
    
    // Provider information queries
    "What are the contact details of Hanif Bus?",
    "Show me Green Line's address",
    "Give me information about Desh Travel",
    "What is Ena Transport's privacy policy?",
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!question.trim()) {
      return;
    }

    const userMessage = {
      type: 'user',
      content: question,
    };

    setMessages([...messages, userMessage]);
    setQuestion('');
    setLoading(true);

    try {
      const response = await askProviderQuestion(question);
      
      const assistantMessage = {
        type: 'assistant',
        content: response.answer,
        sources: response.sources,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = {
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        error: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (exampleQuestion) => {
    setQuestion(exampleQuestion);
  };

  return (
    <div className="container">
      <div className="card">
        <h2 style={{ marginBottom: '24px', color: '#667eea' }}>
          🤖 AI Assistant - Ask Anything!
        </h2>
        <p style={{ marginBottom: '20px', color: '#666' }}>
          Ask me about bus routes, prices, availability, or provider information. 
          I'll search the database and documents to give you the best answer!
        </p>

        <div style={{ 
          background: '#f0f7ff', 
          padding: '15px', 
          borderRadius: '8px',
          marginBottom: '20px',
          borderLeft: '4px solid #667eea'
        }}>
          <strong style={{ color: '#667eea' }}>💡 I can help you with:</strong>
          <ul style={{ marginTop: '10px', marginLeft: '20px', color: '#555' }}>
            <li>Finding buses between cities and checking prices</li>
            <li>Comparing bus operators on specific routes</li>
            <li>Getting contact details and addresses of bus companies</li>
            <li>Learning about privacy policies and company information</li>
          </ul>
        </div>

        {messages.length === 0 && (
          <div style={{ marginBottom: '30px' }}>
            <h4 style={{ marginBottom: '15px', color: '#333' }}>
              Try these example questions:
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
              {exampleQuestions.map((example, index) => (
                <button
                  key={index}
                  className="btn btn-secondary"
                  style={{ fontSize: '14px', padding: '8px 16px' }}
                  onClick={() => handleExampleClick(example)}
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.length > 0 && (
          <div className="chat-container">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`chat-message ${
                  message.type === 'user' ? 'chat-user' : 'chat-assistant'
                }`}
              >
                <div style={{ fontWeight: '600', marginBottom: '8px' }}>
                  {message.type === 'user' ? '👤 You' : '🤖 AI Assistant'}
                </div>
                <div className="markdown-content">
                  {message.type === 'user' ? (
                    <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
                  ) : (
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        // Style different markdown elements
                        p: ({node, ...props}) => <p style={{ marginBottom: '10px' }} {...props} />,
                        ul: ({node, ...props}) => <ul style={{ marginLeft: '20px', marginBottom: '10px' }} {...props} />,
                        ol: ({node, ...props}) => <ol style={{ marginLeft: '20px', marginBottom: '10px' }} {...props} />,
                        li: ({node, ...props}) => <li style={{ marginBottom: '5px' }} {...props} />,
                        strong: ({node, ...props}) => <strong style={{ fontWeight: '700', color: '#667eea' }} {...props} />,
                        table: ({node, ...props}) => (
                          <table style={{ 
                            width: '100%', 
                            borderCollapse: 'collapse', 
                            marginTop: '10px',
                            marginBottom: '10px'
                          }} {...props} />
                        ),
                        thead: ({node, ...props}) => (
                          <thead style={{ 
                            backgroundColor: '#667eea', 
                            color: 'white' 
                          }} {...props} />
                        ),
                        th: ({node, ...props}) => (
                          <th style={{ 
                            padding: '8px', 
                            border: '1px solid #ddd',
                            textAlign: 'left'
                          }} {...props} />
                        ),
                        td: ({node, ...props}) => (
                          <td style={{ 
                            padding: '8px', 
                            border: '1px solid #ddd' 
                          }} {...props} />
                        ),
                        tr: ({node, ...props}) => (
                          <tr style={{ 
                            borderBottom: '1px solid #ddd' 
                          }} {...props} />
                        ),
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  )}
                </div>
                {message.sources && message.sources.length > 0 && (
                  <div className="chat-sources">
                    <strong>📚 Sources:</strong> {message.sources.join(', ')}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="chat-message chat-assistant">
                <div style={{ fontWeight: '600', marginBottom: '8px' }}>
                  🤖 AI Assistant
                </div>
                <div>Searching database and documents...</div>
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ marginTop: '20px' }}>
          <div className="form-group">
            <label className="form-label">Your Question</label>
            <input
              type="text"
              className="form-input"
              placeholder="Ask about routes, prices, or provider details..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !question.trim()}
          >
            {loading ? 'Processing...' : 'Ask Question'}
          </button>
        </form>

        {messages.length > 0 && (
          <button
            className="btn btn-secondary"
            style={{ marginTop: '15px' }}
            onClick={() => {
              setMessages([]);
              setQuestion('');
            }}
          >
            Clear Chat
          </button>
        )}
      </div>
    </div>
  );
};

export default ProviderChat;