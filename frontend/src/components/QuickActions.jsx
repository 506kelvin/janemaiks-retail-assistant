import { Link } from 'react-router-dom';
import { Plus, MessageSquare, BarChart3 } from 'lucide-react';

export default function QuickActions() {
  return (
    <div className="fixed bottom-6 right-6 z-40 flex flex-col gap-2">
      <Link
        to="/chatbot"
        className="w-12 h-12 rounded-full bg-accent-500 text-white shadow-lg hover:shadow-xl hover:bg-accent-600
                   flex items-center justify-center transition-all duration-200 hover:scale-105 active:scale-95"
        aria-label="Ask AI Assistant"
      >
        <MessageSquare size={20} />
      </Link>
    </div>
  );
}
