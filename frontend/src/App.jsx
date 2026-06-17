import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import AdminControl from './pages/AdminControl';

function Navigation() {
  const location = useLocation();
  const isDashboard = location.pathname === '/';

  return (
    <nav className="absolute top-4 left-1/2 -translate-x-1/2 z-50 flex gap-4 pointer-events-auto">
      <Link 
        to="/" 
        className={`px-4 py-2 rounded-full backdrop-blur-md font-mono text-sm uppercase tracking-wider transition-all duration-300 border ${
          isDashboard 
            ? 'bg-blue-600/80 text-white border-blue-400 shadow-[0_0_15px_rgba(37,99,235,0.5)]' 
            : 'bg-black/50 text-gray-300 border-gray-700 hover:bg-black/70 hover:border-blue-500'
        }`}
      >
        Dashboard 3D
      </Link>
      <Link 
        to="/admin" 
        className={`px-4 py-2 rounded-full backdrop-blur-md font-mono text-sm uppercase tracking-wider transition-all duration-300 border ${
          !isDashboard 
            ? 'bg-amber-600/80 text-white border-amber-400 shadow-[0_0_15px_rgba(217,119,6,0.5)]' 
            : 'bg-black/50 text-gray-300 border-gray-700 hover:bg-black/70 hover:border-amber-500'
        }`}
      >
        Admin Control
      </Link>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="w-screen h-screen overflow-hidden bg-[#0a0a0c] text-white">
        <Navigation />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/admin" element={<AdminControl />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
