import React, { useState } from "react";

export default function ChatModal({ onClose, onRunWorkflow }) {
  const [query, setQuery] = useState("");
  const [customPrompt, setCustomPrompt] = useState("");
  const [chat, setChat] = useState([]);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const answer = await onRunWorkflow(query, customPrompt || null);
      setChat(c => [...c, { user: query, bot: answer }]);
      setQuery("");
    } catch (error) {
      setChat(c => [...c, { user: query, bot: "Sorry, there was an error processing your request." }]);
    }
    setLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Chat with AI Workflow</h2>
          <button onClick={onClose} className="close-btn">×</button>
        </div>
        
        <div className="chat-container">
          {chat.length === 0 ? (
            <div className="empty-chat">
              <p>Start a conversation with your AI workflow!</p>
            </div>
          ) : (
            chat.map((m, i) => (
              <div key={i} className="message-pair">
                <div className="user-message">
                  <strong>You:</strong> {m.user}
                </div>
                <div className="bot-message">
                  <strong>AI:</strong> {m.bot}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="loading-message">
              <strong>AI:</strong> <span className="loading-dots">Thinking...</span>
            </div>
          )}
        </div>
        
        <div className="chat-input-section">
          <div className="input-group">
            <label>Custom Prompt (optional):</label>
            <textarea
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="Add custom instructions for the AI..."
              className="custom-prompt-input"
              rows="2"
            />
          </div>
          
          <div className="input-group">
            <div className="query-input-container">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask your question..."
                className="query-input"
                disabled={loading}
              />
              <button 
                onClick={submit} 
                disabled={loading || !query.trim()}
                className="send-btn"
              >
                {loading ? '...' : 'Send'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
