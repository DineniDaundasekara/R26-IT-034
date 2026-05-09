import { Link, useLocation } from 'react-router-dom';
import { Home, Users, BarChart } from 'lucide-react';

export default function Layout({ children }) {
  const location = useLocation();

  const navItems = [
    { name: 'Upload Candidate', path: '/', icon: Home },
    { name: 'Pipeline Dashboard', path: '/candidates', icon: Users },
  ];

  return (
    <div className="flex h-screen bg-gray-50 text-gray-900 font-sans">
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6">
          <h1 className="text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 tracking-tighter">
            RiskAssess AI.
          </h1>
          <p className="text-xs font-semibold text-gray-400 mt-1 uppercase tracking-widest">HR Intelligence</p>
        </div>
        <nav className="mt-6 px-4 flex-1">
          {navItems.map((item) => (
            <Link
              key={item.name}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 mb-2 rounded-xl transition-all font-medium ${
                location.pathname === item.path
                  ? 'bg-blue-50 text-blue-700 shadow-sm border border-blue-100'
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900 border border-transparent'
              }`}
            >
              <item.icon className="w-5 h-5" />
              {item.name}
            </Link>
          ))}
        </nav>
        <div className="p-6 text-xs text-center text-gray-400 font-medium">
          Rule-based XAI Core<br />No LLMs Active
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto w-full relative">
        {children}
      </main>
    </div>
  );
}
