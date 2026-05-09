import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { ArrowRight, ShieldCheck, ShieldAlert, Shield } from 'lucide-react';

export default function Dashboard() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('http://localhost:5001/api/candidates')
      .then(res => {
        setCandidates(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const getRiskBadge = (risk) => {
    if (risk === 'Low Risk') return <span className="flex w-fit items-center gap-1.5 px-3 py-1.5 bg-green-50 text-green-700 border border-green-200 rounded-lg text-xs font-bold"><ShieldCheck className="w-3.5 h-3.5"/> LOW RISK</span>;
    if (risk === 'Medium Risk') return <span className="flex w-fit items-center gap-1.5 px-3 py-1.5 bg-yellow-50 text-yellow-700 border border-yellow-200 rounded-lg text-xs font-bold"><Shield className="w-3.5 h-3.5"/> MEDIUM RISK</span>;
    return <span className="flex w-fit items-center gap-1.5 px-3 py-1.5 bg-red-50 text-red-700 border border-red-200 rounded-lg text-xs font-bold"><ShieldAlert className="w-3.5 h-3.5"/> HIGH RISK</span>;
  };

  return (
    <div className="p-10 max-w-7xl mx-auto">
      <h2 className="text-4xl font-black mb-8 text-gray-900 tracking-tight">Active Pipeline</h2>
      
      <div className="bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="p-20 text-center text-gray-500 font-medium animate-pulse">Loading assessments...</div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-50/80">
              <tr>
                <th className="p-5 font-bold text-gray-500 text-xs uppercase tracking-wider border-b border-gray-100">Candidate Profile</th>
                <th className="p-5 font-bold text-gray-500 text-xs uppercase tracking-wider border-b border-gray-100">XAI Risk Category</th>
                <th className="p-5 font-bold text-gray-500 text-xs uppercase tracking-wider border-b border-gray-100 w-1/4">Algorithm Trust Score</th>
                <th className="p-5 font-bold text-gray-500 text-xs uppercase tracking-wider border-b border-gray-100 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {candidates.map(candidate => (
                <tr key={candidate._id} className="hover:bg-blue-50/30 transition-colors group">
                  <td className="p-5">
                    <div className="font-bold text-gray-900 text-lg">{candidate.name}</div>
                    <div className="text-gray-500 text-sm font-medium mt-0.5">@{candidate.github_username}</div>
                  </td>
                  <td className="p-5">
                    {getRiskBadge(candidate.risk_category)}
                  </td>
                  <td className="p-5">
                    <div className="flex items-center gap-4">
                      <div className="font-black text-2xl text-gray-700 w-10">{candidate.trust_score}</div>
                      <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full transition-all duration-1000 ${candidate.trust_score > 70 ? 'bg-gradient-to-r from-green-400 to-green-500' : candidate.trust_score > 40 ? 'bg-gradient-to-r from-yellow-400 to-yellow-500' : 'bg-gradient-to-r from-red-400 to-red-500'}`} 
                          style={{ width: `${candidate.trust_score}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="p-5 text-right">
                    <Link to={`/candidates/${candidate._id}`} className="inline-flex items-center gap-1.5 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-bold text-gray-700 hover:border-blue-300 hover:text-blue-700 transition-all shadow-sm hover:shadow">
                      View Report <ArrowRight className="w-4 h-4"/>
                    </Link>
                  </td>
                </tr>
              ))}
              {candidates.length === 0 && (
                <tr>
                  <td colSpan="4" className="p-20 text-center">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-50 mb-4">
                      <ShieldAlert className="w-8 h-8 text-gray-400" />
                    </div>
                    <div className="text-gray-500 font-medium text-lg">Pipeline is empty.</div>
                    <Link to="/" className="text-blue-600 font-bold hover:underline mt-2 inline-block">Evaluate your first candidate</Link>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
