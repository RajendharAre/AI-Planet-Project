import React, { useState, useRef, useEffect } from "react";

export default function ChatModal({ onClose, onRunWorkflow }) {
  const [query, setQuery] = useState("");
  const [customPrompt, setCustomPrompt] = useState("");
  const [chat, setChat] = useState([]);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive - Enhanced
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ 
        behavior: "smooth", 
        block: "end",
        inline: "nearest"
      });
    }
  }, [chat, loading]);

  // Focus input on component mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const submit = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    const currentQuery = query;
    setQuery(""); // Clear input immediately for better UX
    
    // Add user message immediately
    setChat(c => [...c, { user: currentQuery, bot: null, timestamp: new Date() }]);
    
    try {
      const answer = await onRunWorkflow(currentQuery, customPrompt || null);
      setChat(c => c.map((msg, i) => 
        i === c.length - 1 ? { ...msg, bot: answer } : msg
      ));
      
      // Force scroll to bottom after response
      setTimeout(() => {
        if (chatEndRef.current) {
          chatEndRef.current.scrollIntoView({ 
            behavior: "smooth", 
            block: "end" 
          });
        }
      }, 100);
    } catch (error) {
      setChat(c => c.map((msg, i) => 
        i === c.length - 1 ? { 
          ...msg, 
          bot: "I apologize, but I encountered an error while processing your request. Please try again or check if the AI service is properly configured."
        } : msg
      ));
    }
    setLoading(false);
    inputRef.current?.focus(); // Refocus input
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const clearChat = () => {
    setChat([]);
    setQuery("");
    inputRef.current?.focus();
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content enhanced-modal">
        <div className="modal-header">
          <div className="header-content">
            <h2>🤖 AI Workflow Chat</h2>
            <p className="header-subtitle">Powered by your custom workflow</p>
          </div>
          <div className="header-actions">
            {chat.length > 0 && (
              <button onClick={clearChat} className="clear-chat-btn" title="Clear Chat">
                🗑️
              </button>
            )}
            <button onClick={onClose} className="close-btn" title="Close Chat">×</button>
          </div>
        </div>
        
        <div className="chat-container">
          {chat.length === 0 ? (
            <div className="empty-chat">
              <div className="empty-chat-icon">🚀</div>
              <h3>Ready to Chat!</h3>
              <p>Start a conversation with your AI workflow. Ask questions, get insights, and explore the possibilities!</p>
              <div className="chat-suggestions">
                <button onClick={() => setQuery("What can you help me with?")}>What can you help me with?</button>
                <button onClick={() => setQuery("Explain how workflows work")}>Explain how workflows work</button>
                <button onClick={() => setQuery("Show me an example")}>Show me an example</button>
              </div>
            </div>
          ) : (
            <>
              {chat.map((m, i) => (
                <div key={i} className="message-pair">
                  <div className="user-message">
                    <div className="message-avatar user-avatar">👤</div>
                    <div className="message-content">
                      <div className="message-text">{m.user}</div>
                      <div className="message-time">
                        {m.timestamp?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                  {m.bot && (
                    <div className="bot-message">
                      <div className="message-avatar bot-avatar">🤖</div>
                      <div className="message-content">
                        <div className="message-text">{m.bot}</div>
                        <div className="message-actions">
                          <button onClick={() => navigator.clipboard.writeText(m.bot)} title="Copy response">
                            📋
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="bot-message loading">
                  <div className="message-avatar bot-avatar">🤖</div>
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <div className="message-text loading-text">AI is thinking...</div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </>
          )}
        </div>
        
        <div className="chat-input-section">
          <div className="input-group">
            <label>🎨 Custom Instructions (optional):</label>
            <textarea
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="Add specific instructions to customize AI responses (e.g., 'Be concise', 'Use simple language', 'Focus on technical details')..."
              className="custom-prompt-input"
              rows="2"
            />
          </div>
          
          <div className="input-group">
            <div className="query-input-container">
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message here..."
                className="query-input"
                disabled={loading}
                maxLength={500}
              />
              <div className="input-actions">
                <span className="char-count">{query.length}/500</span>
                <button 
                  onClick={submit} 
                  disabled={loading || !query.trim()}
                  className="send-btn"
                  title="Send message (Enter)"
                >
                  {loading ? '🔄' : '➤'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
