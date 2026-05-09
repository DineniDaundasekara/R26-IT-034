import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { Fingerprint, ArrowLeft, Terminal, FileText, CheckCircle2 } from 'lucide-react';

export default function CandidateDetail() {
  const { id } = useParams();
  const [candidate, setCandidate] = useState(null);

  useEffect(() => {
    // Standard workaround since we don't have a single GET endpoint
    axios.get('http://localhost:5001/api/candidates')
      .then(res => {
        const found = res.data.find(c => c._id === id);
        setCandidate(found);
      })
      .catch(err => console.error(err));
  }, [id]);

  if (!candidate) return <div className="p-20 text-center animate-pulse text-gray-400 font-bold text-xl">Reconstructing Decision Tree Paths...</div>;

  const f = candidate.extracted_features || {};
  
  const radarData = [
    { subject: 'Exp. Years', A: Math.min((f.years_of_experience || 0) / 10 * 100, 100) },
    { subject: 'Skills Match', A: Math.min((f.matched_skills?.length || 0) / 8 * 100, 100) },
    { subject: 'Repo Quality', A: (f.repo_quality_score || 0) * 10 },
    { subject: 'Activity', A: (f.commit_frequency || 0) * 10 },
    { subject: 'Collaboration', A: (f.collaboration_score || 0) * 10 },
    { subject: 'OS Presence', A: Math.min((f.github_followers || 0) / 100 * 100, 100) },
  ];

  return (
    <div className="p-10 max-w-7xl mx-auto space-y-8">
      <Link to="/candidates" className="inline-flex items-center gap-2 text-gray-500 font-bold hover:text-blue-600 transition-colors mb-4">
        <ArrowLeft className="w-5 h-5"/> Back to Pipeline
      </Link>

      {/* Header Profile - Premium aesthetic */}
      <div className="bg-white p-10 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100 flex flex-col md:flex-row justify-between items-center relative overflow-hidden bg-gradient-to-r from-white to-gray-50/50">
        <div className="absolute top-0 left-0 w-3 h-full bg-gradient-to-b from-blue-500 to-indigo-600"></div>
        <div className="mb-6 md:mb-0">
          <div className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-2 flex items-center gap-2"><CheckCircle2 className="w-4 h-4"/> Assessment Completed</div>
          <h2 className="text-5xl font-black text-gray-900 tracking-tight">{candidate.name}</h2>
          <p className="text-gray-500 font-medium mt-2 flex items-center gap-4">
            <span className="flex items-center gap-1.5"><Terminal className="w-4 h-4"/> @{candidate.github_username}</span>
            <span className="flex items-center gap-1.5"><FileText className="w-4 h-4"/> {candidate.email}</span>
          </p>
        </div>
        <div className="md:text-right bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <div className="text-xs font-black uppercase tracking-widest text-gray-400 mb-1">Algorithm Trust Score</div>
          <div className="text-7xl font-black tracking-tighter leading-none bg-clip-text text-transparent bg-gradient-to-br from-blue-600 to-indigo-700">
            {candidate.trust_score}
          </div>
          <div className={`mt-3 px-4 py-1.5 inline-block text-sm font-bold uppercase tracking-wider rounded-lg ${candidate.risk_category === 'Low Risk' ? 'bg-green-100 text-green-700' : candidate.risk_category === 'Medium Risk' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
            {candidate.risk_category} CATEGORY
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        
        {/* XAI Insights */}
        <div className="xl:col-span-2 space-y-8">
          <div className="bg-white p-8 lg:p-10 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600">
                <Fingerprint className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-2xl font-black text-gray-900 tracking-tight">Explainable AI Trace Logic</h3>
                <p className="text-sm font-medium text-gray-500 mt-1 uppercase tracking-wide">DecisionTreeClassifier Path Evaluation</p>
              </div>
            </div>
            
            <p className="text-gray-600 font-medium mb-8 leading-relaxed">
              This score was generated securely without black-box LLMs. The model evaluated the candidate's exact feature vectors against a trained decision threshold. Below is the deterministic trace pathway that led to the final assessment output.
            </p>
            
            <div className="space-y-4">
              {candidate.explanations?.map((exp, idx) => (
                <div key={idx} className="flex items-start gap-5 p-5 rounded-2xl bg-gray-50/80 border border-gray-100 hover:bg-gray-50 transition-colors">
                  <div className="shrink-0 w-10 h-10 rounded-full bg-white flex items-center justify-center font-black text-indigo-600 shadow-sm border border-gray-200">
                    {idx + 1}
                  </div>
                  <div className="pt-2">
                    <h4 className="font-bold text-gray-800 text-lg leading-snug">{exp}</h4>
                    <div className="flex gap-2 mt-3">
                       <span className="px-2 py-0.5 rounded bg-white border border-gray-200 text-[10px] font-mono text-gray-400">NODE_{idx}_PASSED</span>
                    </div>
                  </div>
                </div>
              ))}
              {(!candidate.explanations || candidate.explanations.length === 0) && (
                <div className="p-5 rounded-2xl bg-gray-50/80 border border-gray-100 text-gray-500 font-medium text-center">No explicit path extracted. Raw baseline classification match.</div>
              )}
            </div>
          </div>
          
          <div className="bg-white p-8 lg:p-10 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100">
            <h3 className="text-2xl font-black text-gray-900 tracking-tight mb-2">Technical Lexicon Alignment</h3>
            <p className="text-sm font-medium text-gray-500 mb-8 uppercase tracking-wide">Extracted Resume Skill Match</p>
            
            <div className="flex flex-wrap gap-3">
              {f.matched_skills?.map(skill => (
                <span key={skill} className="px-5 py-2.5 bg-blue-50/80 text-blue-700 font-black tracking-wide uppercase rounded-xl border border-blue-100/50 shadow-sm">
                  {skill}
                </span>
              ))}
              {(!f.matched_skills || f.matched_skills.length === 0) && (
                <span className="text-gray-400 font-medium italic">No direct technical skill ontology matched.</span>
              )}
            </div>
          </div>

          <div className="bg-white p-8 lg:p-10 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100">
            <h3 className="text-2xl font-black text-gray-900 tracking-tight mb-2">Preferred Technologies</h3>
            <p className="text-sm font-medium text-gray-500 mb-8 uppercase tracking-wide">GitHub Language Breakdown</p>
            
            <div className="flex flex-wrap gap-3">
              {f.preferred_languages?.map(lang => (
                <span key={lang} className="px-5 py-2.5 bg-indigo-50/80 text-indigo-700 font-black tracking-wide uppercase rounded-xl border border-indigo-100/50 shadow-sm">
                  {lang}
                </span>
              ))}
              {(!f.preferred_languages || f.preferred_languages.length === 0) && (
                <span className="text-gray-400 font-medium italic">No primary languages detected.</span>
              )}
            </div>
          </div>
        </div>

        {/* Visualizations & Raw Data - Sidebar format */}
        <div className="space-y-8">
          <div className="bg-white p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100 h-[400px] flex flex-col">
            <h3 className="text-xl font-black text-gray-900 tracking-tight mb-2">Multivariate Assessment</h3>
            <p className="text-xs font-bold text-gray-400 mb-6 uppercase tracking-wider">Normalized Feature Vectors</p>
            
            <div className="flex-1 -mx-4 -mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="65%" data={radarData}>
                  <PolarGrid stroke="#f3f4f6" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 10, fontWeight: 'bold' }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar name="Candidate" dataKey="A" stroke="#4f46e5" strokeWidth={3} fill="#4f46e5" fillOpacity={0.25} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100">
            <h3 className="text-xl font-black text-gray-900 tracking-tight mb-2">GitHub Performance Metrics</h3>
            <p className="text-xs font-bold text-gray-400 mb-8 uppercase tracking-wider">Advanced Behavioral Extraction</p>
            
            <div className="space-y-6">
              <div>
                <div className="flex justify-between items-end mb-2">
                  <span className="text-gray-500 font-bold text-xs uppercase">Coding Activity</span>
                  <span className="font-black text-lg text-gray-900 leading-none">{(f.commit_frequency || 0).toFixed(1)}/10</span>
                </div>
                <div className="w-full h-2 bg-gray-50 border border-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full" style={{width: `${(f.commit_frequency || 0) * 10}%`}}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-end mb-2">
                  <span className="text-gray-500 font-bold text-xs uppercase">Repo Quality</span>
                  <span className="font-black text-lg text-gray-900 leading-none">{(f.repo_quality_score || 0).toFixed(1)}/10</span>
                </div>
                <div className="w-full h-2 bg-gray-50 border border-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full" style={{width: `${(f.repo_quality_score || 0) * 10}%`}}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-end mb-2">
                  <span className="text-gray-500 font-bold text-xs uppercase">Collaboration</span>
                  <span className="font-black text-lg text-gray-900 leading-none">{(f.collaboration_score || 0).toFixed(1)}/10</span>
                </div>
                <div className="w-full h-2 bg-gray-50 border border-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-teal-400 to-emerald-500 rounded-full" style={{width: `${(f.collaboration_score || 0) * 10}%`}}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-end mb-2">
                  <span className="text-gray-500 font-bold text-xs uppercase">OS Contributions</span>
                  <span className="font-black text-lg text-gray-900 leading-none">{(f.open_source_contributions || 0).toFixed(1)}/10</span>
                </div>
                <div className="w-full h-2 bg-gray-50 border border-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-orange-400 to-red-500 rounded-full" style={{width: `${(f.open_source_contributions || 0) * 10}%`}}></div>
                </div>
              </div>
              
              <div className="pt-4 mt-2 border-t border-gray-50 grid grid-cols-2 gap-4">
                 <div>
                   <span className="text-gray-400 font-bold text-[10px] uppercase block mb-1">Followers</span>
                   <span className="font-black text-gray-900">{f.github_followers || 0}</span>
                 </div>
                 <div>
                   <span className="text-gray-400 font-bold text-[10px] uppercase block mb-1">Public Repos</span>
                   <span className="font-black text-gray-900">{f.github_public_repos || 0}</span>
                 </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
