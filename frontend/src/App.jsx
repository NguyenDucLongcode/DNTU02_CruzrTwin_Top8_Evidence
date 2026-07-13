import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import AdminControl from './pages/AdminControl';

function App() {
  return (
    <Router>
      <div className="w-screen h-screen overflow-hidden bg-[#0a0a0c] text-white">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/admin" element={<AdminControl />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
