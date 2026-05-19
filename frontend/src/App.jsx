import { Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import Sidebar from './components/Sidebar';
import TopNav from './components/TopNav';
import QuickActions from './components/QuickActions';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Chatbot from './pages/Chatbot';
import Analytics from './pages/Analytics';

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen flex">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 flex flex-col min-w-0">
        <TopNav onMenuToggle={() => setSidebarOpen(true)} />

        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/products" element={<Products />} />
            <Route path="/chatbot" element={<Chatbot />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </main>
      </div>

      <QuickActions />
    </div>
  );
}
