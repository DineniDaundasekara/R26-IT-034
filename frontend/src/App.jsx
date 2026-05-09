import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import EntryForm from './pages/EntryForm';
import Dashboard from './pages/Dashboard';
import CandidateDetail from './pages/CandidateDetail';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<EntryForm />} />
          <Route path="/candidates" element={<Dashboard />} />
          <Route path="/candidates/:id" element={<CandidateDetail />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
