import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, CheckCircle, User, Mail } from 'lucide-react';

const Github = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.24c3-.34 6-1.53 6-6.76a5.2 5.2 0 0 0-1.5-3.78c.15-.38.65-1.8-0.15-3.72a2 2 0 0 0-1.8-1.28c-1.54.4-3.1 1.7-4.1 2.3A14 14 0 0 0 12 4a14 14 0 0 0-4 1.1c-1-.6-2.56-1.9-4.1-2.3a2 2 0 0 0-1.8 1.28c-.8 1.92-.3 3.34-.15 3.72A5.2 5.2 0 0 0 4.5 9c0 5.23 3 6.42 6 6.76a4.8 4.8 0 0 0-1 3.24v4" />
    <path d="M9 18c-3.5 1-4-2-6-2" />
  </svg>
);
import axios from 'axios';

export default function EntryForm() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [github, setGithub] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleDragOver = (e) => e.preventDefault();
  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !github || !name) return;
    
    setLoading(true);
    const formData = new FormData();
    formData.append('name', name);
    formData.append('email', email);
    formData.append('github_username', github);
    formData.append('resume', file);

    try {
      const res = await axios.post('http://localhost:5001/api/candidates/evaluate', formData);
      navigate(`/candidates/${res.data._id}`);
    } catch (err) {
      console.error(err);
      alert('Analysis failed. Make sure Node.js and FastAPI are running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-10 lg:p-16 max-w-3xl mx-auto h-full flex flex-col justify-center">
      <div className="mb-10">
        <h2 className="text-4xl font-black mb-2 text-gray-900 tracking-tight">Evaluate Candidate</h2>
        <p className="text-gray-500 font-medium text-lg">Cross-analyze Github repositories & Resumes simultaneously using Explainable AI.</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white p-8 lg:p-10 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2 uppercase tracking-wide">Candidate Name</label>
            <div className="relative">
               <User className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5"/>
               <input type="text" value={name} onChange={(e) => setName(e.target.value)} required className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none font-medium text-gray-800" placeholder="Jane Doe" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2 uppercase tracking-wide">Email</label>
            <div className="relative">
               <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5"/>
               <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none font-medium text-gray-800" placeholder="jane@company.com" />
            </div>
          </div>
        </div>
        
        <div className="mb-8">
          <label className="block text-sm font-bold text-gray-700 mb-2 uppercase tracking-wide">GitHub Username</label>
          <div className="relative">
             <Github className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5"/>
             <input type="text" value={github} onChange={(e) => setGithub(e.target.value)} required className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none font-medium text-gray-800" placeholder="janedoe123" />
          </div>
        </div>

        <div className="mb-10">
          <label className="block text-sm font-bold text-gray-700 mb-2 uppercase tracking-wide">Resume Upload</label>
          <div 
            onDragOver={handleDragOver} 
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200 ${file ? 'border-green-500 bg-green-50/50 scale-[1.02]' : 'border-gray-200 hover:border-blue-400 hover:bg-blue-50/30'}`}
            onClick={() => document.getElementById('file-upload').click()}
          >
            {file ? (
              <div className="flex flex-col items-center text-green-600 animate-in fade-in zoom-in duration-300">
                <CheckCircle className="w-12 h-12 mb-3 drop-shadow-sm" />
                <span className="font-bold text-lg">{file.name} ready</span>
                <span className="text-sm font-medium mt-1 text-green-600/70">Click to change file</span>
              </div>
            ) : (
              <div className="flex flex-col items-center text-gray-400">
                <div className="w-16 h-16 mb-4 rounded-full bg-blue-50 flex items-center justify-center">
                  <UploadCloud className="w-8 h-8 text-blue-500" />
                </div>
                <span className="font-bold text-gray-600 text-lg">Drop PDF to Upload</span>
                <span className="text-sm mt-1">or browse your computer</span>
              </div>
            )}
            <input id="file-upload" type="file" accept=".pdf" className="hidden" onChange={(e) => setFile(e.target.files[0])} />
          </div>
        </div>

        <button 
          type="submit" 
          disabled={loading || !file || !github} 
          className={`w-full py-4 rounded-xl font-bold text-white text-lg tracking-wide transition-all duration-300 ${loading ? 'bg-indigo-400 cursor-not-allowed animate-pulse shadow-inner' : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:shadow-lg hover:-translate-y-0.5'}`}
        >
          {loading ? 'Evaluating Model Path...' : 'Initialize Analysis'}
        </button>
      </form>
    </div>
  );
}
