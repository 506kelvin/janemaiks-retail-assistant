import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Trash2, Sparkles, Package } from 'lucide-react';
import { chatApi } from '../services/api';
import EmptyState from '../components/EmptyState';

function formatResponse(text) {
  let html = text
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
    .replace(/\n/g, '<br/>');

  html = html.replace(
    /(📦|📊|💡|🔄|🏷️|💰|⚠️|⚡)\s*/g,
    '<span class="inline-block mr-0.5">$1</span>'
  );

  html = html.replace(
    /<br\/><br\/>(📦|📊|💡|🔄|🏷️|💰)\s\*\*(.*?)\*\*:\s\*\*(.*?)\*\*/g,
    (match, emoji, label, value) => {
      return `</p><div class="pricing-card"><div class="pricing-item"><span class="pricing-label">${emoji} ${label}</span><span class="pricing-value">${value}</span></div></div><p class="text-sm markdown-response leading-relaxed">`;
    }
  );

  return html;
}

const SUGGESTIONS = [
  'How much is Arimis Petroleum Jelly?',
  'What is the wholesale price of Arimis?',
  'How much profit per unit on Arimis?',
  'How much do we buy a dozen at?',
  'Suggest selling price for this item',
  'What is the unit cost of cooking oil?',
  'How many sweets are remaining?',
  'Bei gani ya sukari?',
];

function ProductCard({ product, onSelect }) {
  return (
    <button
      onClick={() => onSelect(product)}
      className="flex items-center gap-3 w-full p-3 rounded-xl border border-gray-200 dark:border-dark-border
                 bg-white dark:bg-dark-card hover:bg-gray-50 dark:hover:bg-dark-surface
                 hover:border-primary-300 dark:hover:border-primary-500/30
                 transition-all duration-200 text-left cursor-pointer"
    >
      <div className="w-10 h-10 rounded-lg bg-primary-50 dark:bg-primary-900/20 flex items-center justify-center flex-shrink-0">
        <Package size={18} className="text-primary-500" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-dark-text truncate">{product.name}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {product.category}{product.supplier ? ` \u00B7 ${product.supplier}` : ''}
        </p>
      </div>
      <span className="text-xs font-medium text-primary-500 dark:text-primary-400 whitespace-nowrap">
        Select &rarr;
      </span>
    </button>
  );
}

function ClarificationMessage({ msg, onSelectProduct }) {
  return (
    <div className="space-y-3">
      <div className="chat-bubble-bot">
        <p className="text-sm markdown-response leading-relaxed" dangerouslySetInnerHTML={{ __html: formatResponse(msg.text) }} />
      </div>
      <div className="space-y-2 pl-2">
        {msg.matches.map((product) => (
          <ProductCard key={product.id} product={product} onSelect={onSelectProduct} />
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ msg, onSelectProduct }) {
  const isUser = msg.role === 'user';

  if (!isUser && msg.type === 'clarification_required') {
    return (
      <div className={`flex gap-3 items-start`}>
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-50 to-blue-50 dark:from-primary-500/20 dark:to-blue-500/20 flex items-center justify-center flex-shrink-0">
          <Bot size={16} className="text-primary-600 dark:text-primary-400" />
        </div>
        <ClarificationMessage msg={msg} onSelectProduct={onSelectProduct} />
      </div>
    );
  }

  return (
    <div className={`flex gap-3 items-start ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
        isUser
          ? 'bg-primary-500 text-white'
          : 'bg-gradient-to-br from-primary-50 to-blue-50 dark:from-primary-500/20 dark:to-blue-500/20 text-primary-600 dark:text-primary-400'
      }`}>
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {isUser ? (
        <div className="chat-bubble-user">
          <p className="text-sm leading-relaxed">{msg.text}</p>
        </div>
      ) : (
        <div className="chat-bubble-bot">
          <p className="text-sm markdown-response leading-relaxed" dangerouslySetInnerHTML={{ __html: formatResponse(msg.text) }} />
        </div>
      )}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex gap-3 items-start">
      <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-50 to-blue-50 dark:from-primary-500/20 dark:to-blue-500/20 flex items-center justify-center flex-shrink-0">
        <Bot size={16} className="text-primary-500" />
      </div>
      <div className="chat-bubble-bot">
        <div className="flex gap-1.5 py-1">
          <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}

export default function Chatbot() {
  const [messages, setMessages] = useState([
    {
      role: 'bot',
      type: 'normal',
      text: "👋 **Karibu!** Welcome to **JaneMaiks Retail Assistant**. I'm your AI pricing manager.\n\nI can help with:\n• **Retail prices** — \"How much is Arimis?\"\n• **Wholesale prices** — \"What is the wholesale price?\"\n• **Unit costs** — \"How much do we buy a dozen at?\"\n• **Profit analysis** — \"How much profit per unit?\"\n• **Stock levels** — \"How many sweets remaining?\"\n• **Swahili support** — \"Bei gani ya sukari?\"\n\nHow can I help you at JaneMaiks today?",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendMessage = async (query, selectedProductId) => {
    if (!query?.trim() && !selectedProductId) return;
    if (loading) return;

    if (query?.trim()) {
      setMessages((prev) => [...prev, { role: 'user', text: query }]);
    }
    setInput('');
    setLoading(true);

    try {
      const res = await chatApi.query({
        query: query?.trim() || '',
        session_id: sessionId,
        selected_product_id: selectedProductId || undefined,
      });
      const data = res.data;
      if (!sessionId) setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        {
          role: 'bot',
          type: data.type || 'normal',
          text: data.response,
          matches: data.clarification_matches || [],
        },
      ]);
    } catch {
      setMessages((prev) => [...prev, { role: 'bot', type: 'normal', text: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleSelectProduct = (product) => {
    sendMessage('', product.id);
  };

  const clearChat = () => {
    setMessages([{ role: 'bot', type: 'normal', text: 'Chat cleared! How can I help you at JaneMaiks?' }]);
    setSessionId(null);
  };

  const hasClarification = messages.some(
    (m) => m.role === 'bot' && m.type === 'clarification_required'
  );

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
            <Sparkles size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-dark-text">JaneMaiks AI Assistant</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Pricing intelligence & inventory management</p>
          </div>
        </div>
        <button onClick={clearChat} className="btn-ghost btn-sm" title="Clear conversation">
          <Trash2 size={14} />
          Clear
        </button>
      </div>

      {/* Chat Container */}
      <div className="flex-1 card overflow-hidden flex flex-col p-0 !shadow-card-hover">
        <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className="animate-slide-up">
              <MessageBubble msg={msg} onSelectProduct={handleSelectProduct} />
            </div>
          ))}
          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-100 dark:border-dark-border p-4 bg-gray-50/50 dark:bg-dark-surface/50">
          {/* Suggestion Chips */}
          {!hasClarification && (
            <div className="flex flex-wrap gap-2 mb-3">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(s)}
                  disabled={loading}
                  className="text-xs bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border
                           hover:bg-gray-50 dark:hover:bg-dark-surface hover:border-primary-300 dark:hover:border-primary-500/30
                           text-gray-600 dark:text-gray-300 px-3 py-1.5 rounded-full transition-all duration-200
                           disabled:opacity-50"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              ref={inputRef}
              className="input-field flex-1"
              placeholder={hasClarification ? 'Type a number or name to select...' : 'Ask JaneMaiks about prices, stock, profit...'}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              aria-label="Chat message"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="btn-primary px-5"
              aria-label="Send message"
            >
              {loading ? <div className="spinner !w-4 !h-4" /> : <Send size={18} />}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
