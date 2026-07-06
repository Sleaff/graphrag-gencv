'use client';

import { useState, useEffect } from 'react';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'profile' | 'generate' | 'editor'>('profile');
  const [ingestMode, setIngestMode] = useState<'upload' | 'manual'>('upload');

  const [candidates, setCandidates] = useState<string[]>([]);
  const [candidateName, setCandidateName] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [generatedCv, setGeneratedCv] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [latexCode, setLatexCode] = useState('');
  
  const [profileData, setProfileData] = useState({
    phone_mobile: '', phone_home: '', phone_work: '',
    gender: '', nationality: '', date_of_birth: '', drivers_licence: '',
    short_description: '', long_description: '',
    city: '', country: '',
    technical_skills: [{ name: '' }],
    languages: [{ name: '', proficiency: '' }],
    instant_messaging: [{ name: '', username: '' }],
    experiences: [{ company_name: '', job_title: '', start_date: '', end_date: '', raw_skills: '', description: '', career_level: '', job_type: '' }],
    education: [{ degree: '', institution: '', start_date: '', end_date: '', field_of_study: '', description: '' }],
    courses: [{ title: '', description: '', url: '', start_date: '', finish_date: '', organized_by: '', has_certification: false }],
    patents: [{ title: '', office: '', number: '', inventor: '', url: '', description: '', issued_date: '', status: '' }],
    projects: [{ name: '', role: '', start_date: '', end_date: '', url: '', creator: '', description: '', is_current: false }],
    publications: [{ title: '', publisher: '', date: '', description: '' }],
    websites: [{ url: '', website_type: '' }],
    honors: [{ title: '', issuer: '', date: '' }],
    references: [{ name: '', relation: '' }],
    other_info: [{ type: '', description: '' }]
  });

  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/list-candidates');
        if (response.ok) {
          const data = await response.json();
          setCandidates(data);
        }
      } catch (err) {
        console.error("Failed to fetch candidates", err);
      }
    };
    fetchCandidates();
  }, []);

  const loadCandidateProfile = async (name: string) => {
    if (!name) return;
    setIsLoading(true);
    setError('');
    try {
      const response = await fetch(`http://127.0.0.1:8000/get-profile/${name}`);
      if (!response.ok) throw new Error("Failed to load profile");
      const data = await response.json();
      
      setProfileData({
        phone_mobile: data.phone_mobile || '', phone_home: data.phone_home || '', phone_work: data.phone_work || '',
        gender: data.gender || '', nationality: data.nationality || '', date_of_birth: data.date_of_birth || '', 
        drivers_licence: data.drivers_licence || '', short_description: data.short_description || '', long_description: data.long_description || '',
        city: data.address?.city || '', country: data.address?.country || '',
        technical_skills: data.skills?.length ? data.skills.map((s: string) => ({ name: s })) : [{ name: '' }],
        languages: data.languages?.length ? data.languages.map((l: string) => ({ name: l, proficiency: '' })) : [{ name: '', proficiency: '' }],
        instant_messaging: data.instant_messaging?.length ? data.instant_messaging : [{ name: '', username: '' }],
        experiences: data.jobs && Object.keys(data.jobs).length ? Object.values(data.jobs).map((job: any) => ({
              company_name: job.company || '', job_title: job.title || '', start_date: job.start || '', end_date: job.end || '', 
              career_level: job.career_level || '', job_type: job.job_type || '', raw_skills: '', description: job.description || '' 
            })) : [{ company_name: '', job_title: '', start_date: '', end_date: '', raw_skills: '', description: '', career_level: '', job_type: '' }],
        education: data.education && Object.keys(data.education).length ? Object.values(data.education).map((edu: any) => ({
              degree: edu.degree || '', institution: edu.institution || '', start_date: edu.start_date || '', end_date: edu.end_date || '', field_of_study: '', description: edu.description || ''
            })) : [{ degree: '', institution: '', start_date: '', end_date: '', field_of_study: '', description: '' }],
        courses: data.courses?.length ? data.courses : [{ title: '', description: '', url: '', start_date: '', finish_date: '', organized_by: '', has_certification: false }],
        patents: data.patents?.length ? data.patents : [{ title: '', office: '', number: '', inventor: '', url: '', description: '', issued_date: '', status: '' }],
        projects: data.projects?.length ? data.projects : [{ name: '', role: '', start_date: '', end_date: '', url: '', creator: '', description: '', is_current: false }],
        publications: data.publications?.length ? data.publications : [{ title: '', publisher: '', date: '', description: '' }],
        websites: data.websites && Object.keys(data.websites).length ? Object.values(data.websites) : [{ url: '', website_type: '' }],
        honors: data.honors?.length ? data.honors : [{ title: '', issuer: '', date: '' }],
        references: data.references?.length ? data.references : [{ name: '', relation: '' }],
        other_info: data.other_info?.length ? data.other_info : [{ type: '', description: '' }]
      });
      setCandidateName(data.name || name);
      if (data.target?.job_title) setJobDescription(data.target.job_title);
    } catch (err: any) {
      setError(`Could not load profile: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBaseChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setProfileData(prev => ({ ...prev, [name]: value }));
  };

  const handleArrayChange = (category: keyof typeof profileData, index: number, field: string, value: any) => {
    const updatedArray = [...(profileData[category] as any[])];
    updatedArray[index][field] = value;
    setProfileData(prev => ({ ...prev, [category]: updatedArray }));
  };

  const addRow = (category: keyof typeof profileData, defaultObj: any) => {
    setProfileData(prev => ({ ...prev, [category]: [...(prev[category] as any[]), defaultObj] }));
  };

  const removeRow = (category: keyof typeof profileData, index: number) => {
    setProfileData(prev => ({ ...prev, [category]: (prev[category] as any[]).filter((_, i) => i !== index) }));
  };

  const buildCompletePayload = () => {
    return {
      name: candidateName,
      phone_mobile: profileData.phone_mobile, phone_home: profileData.phone_home, phone_work: profileData.phone_work,
      gender: profileData.gender, nationality: profileData.nationality, date_of_birth: profileData.date_of_birth,
      drivers_licence: profileData.drivers_licence, short_description: profileData.short_description, long_description: profileData.long_description,
      experiences: profileData.experiences.filter(e => e.company_name).map(exp => ({ ...exp, raw_skills: typeof exp.raw_skills === 'string' ? exp.raw_skills.split(',').map(s => s.trim()).filter(Boolean) : exp.raw_skills })),
      education: profileData.education.filter(e => e.degree),
      courses: profileData.courses.filter(c => c.title),
      patents: profileData.patents.filter(p => p.title),
      projects: profileData.projects.filter(p => p.name),
      publications: profileData.publications.filter(p => p.title),
      technical_skills: profileData.technical_skills.filter(s => s.name.trim()).map(s => s.name.trim()),
      languages: profileData.languages.filter(l => l.name),
      instant_messaging: profileData.instant_messaging.filter(i => i.username),
      target: { job_title: jobDescription.substring(0, 50) || "N/A", job_mode: "N/A", relocate: false, travel: false },
      address: { city: profileData.city, country: profileData.country },
      websites: profileData.websites.filter(w => w.url),
      honors: profileData.honors.filter(h => h.title),
      references: profileData.references.filter(r => r.name),
      other_info: profileData.other_info.filter(o => o.description)
    };
  };

  const handleProfileSubmit = async () => {
    setIsLoading(true);
    setError('');
    try {
      if (ingestMode === 'manual') {
        const response = await fetch('http://127.0.0.1:8000/ingest-structured-profile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(buildCompletePayload()) });
        if (!response.ok) throw new Error("Manual submission failed");
        alert((await response.json()).message);
      } else {
        if (!cvFile) throw new Error("Please select a file first.");
        const formData = new FormData(); formData.append("file", cvFile);
        const response = await fetch('http://127.0.0.1:8000/cv-to-rdf', { method: 'POST', body: formData });
        if (!response.ok) throw new Error("File upload failed");
        alert("CV processed successfully. Check logs for RDF output.");
      }
    } catch (err: any) { setError(`Failed to save: ${err.message}`); } finally { setIsLoading(false); }
  };

  const handleGenerateHybrid = async () => {
    setIsLoading(true); setError('');
    try {
      const response = await fetch('http://127.0.0.1:8000/generate-hybrid-cv', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ candidate_name: candidateName, job_description: jobDescription }) });
      if (!response.ok) throw new Error("Generation failed");
      setGeneratedCv(JSON.stringify(await response.json(), null, 2));
    } catch (err: any) { setError(err.message); } finally { setIsLoading(false); }
  };

  const loadEditor = async (designId: number) => {
    setIsLoading(true); setError('');
    try {
        const response = await fetch(`http://127.0.0.1:8000/generate-latex/${designId}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(buildCompletePayload()) });
        if (!response.ok) throw new Error("Failed to generate LaTeX template");
        setLatexCode(await response.text()); setActiveTab('editor');
    } catch (err: any) { setError(`Failed to load editor: ${err.message}`); } finally { setIsLoading(false); }
  };

  return (
    <main className="min-h-screen bg-gray-50 p-8 text-gray-900">
      <div className="max-w-7xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold">GraphRAG CV System</h1>
        
        <div className="flex space-x-4 border-b border-gray-200 mb-6">
          <button onClick={() => setActiveTab('profile')} className={`py-2 px-4 border-b-2 font-medium text-sm ${activeTab === 'profile' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>1. Profile Setup</button>
          <button onClick={() => setActiveTab('generate')} className={`py-2 px-4 border-b-2 font-medium text-sm ${activeTab === 'generate' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>2. CV Generator</button>
          <button onClick={() => setActiveTab('editor')} className={`py-2 px-4 border-b-2 font-medium text-sm ${activeTab === 'editor' ? 'border-blue-600 text-blue-600' : 'border-transparent'}`}>3. CV Editor</button>
        </div>

        {activeTab === 'profile' && (
           <div className="bg-white p-6 border border-gray-200 rounded-md shadow-sm max-w-4xl">
           <h2 className="text-xl font-semibold mb-4">Update Candidate Knowledge Base</h2>
           
           <div className="mb-6 p-4 bg-blue-50 border border-blue-100 rounded-md flex items-end gap-4">
             <div className="flex-1">
               <label className="block text-sm font-medium text-blue-900 mb-1">Load Existing Candidate Profile</label>
               <select className="w-full p-2 border border-blue-200 rounded-md bg-white" onChange={(e) => loadCandidateProfile(e.target.value)} value={candidateName}>
                 <option value="">-- Select a saved candidate --</option>
                 {candidates.map(name => <option key={name} value={name}>{name}</option>)}
               </select>
             </div>
           </div>

           <div className="mb-4">
             <label className="block text-sm font-medium mb-1">Candidate Name (Active)</label>
             <input type="text" value={candidateName} onChange={(e) => setCandidateName(e.target.value)} className="w-full p-2 border border-gray-300 rounded-md" />
           </div>

           <div className="flex space-x-2 mb-6 bg-gray-100 p-1 rounded-md w-fit">
             <button onClick={() => setIngestMode('upload')} className={`px-4 py-1.5 rounded text-sm font-medium ${ingestMode === 'upload' ? 'bg-white shadow text-blue-600' : 'text-gray-600'}`}>Upload CV</button>
             <button onClick={() => setIngestMode('manual')} className={`px-4 py-1.5 rounded text-sm font-medium ${ingestMode === 'manual' ? 'bg-white shadow text-blue-600' : 'text-gray-600'}`}>Manual Entry</button>
           </div>

           {ingestMode === 'upload' ? (
             <div className="border-2 border-dashed border-gray-300 rounded-lg p-10 text-center hover:bg-gray-50 transition-colors">
               <input type="file" accept=".pdf,.docx,.txt" onChange={(e) => setCvFile(e.target.files?.[0] || null)} className="mx-auto block text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
             </div>
           ) : (
             <div className="space-y-8 h-[600px] overflow-y-auto pr-4">
               {/* Contact & Demographics */}
               <div className="p-4 bg-gray-50 border rounded-md">
                 <h3 className="font-semibold mb-3 border-b pb-2">Demographics & Contact</h3>
                 <div className="grid grid-cols-3 gap-4 mb-2">
                    <div><label className="block text-xs font-medium">Gender</label><input type="text" name="gender" value={profileData.gender} onChange={handleBaseChange} className="w-full p-2 text-sm border rounded" /></div>
                    <div><label className="block text-xs font-medium">Nationality</label><input type="text" name="nationality" value={profileData.nationality} onChange={handleBaseChange} className="w-full p-2 text-sm border rounded" /></div>
                    <div><label className="block text-xs font-medium">Date of Birth</label><input type="text" name="date_of_birth" value={profileData.date_of_birth} onChange={handleBaseChange} className="w-full p-2 text-sm border rounded" /></div>
                    <div><label className="block text-xs font-medium">Driver's Licence</label><input type="text" name="drivers_licence" value={profileData.drivers_licence} onChange={handleBaseChange} className="w-full p-2 text-sm border rounded" /></div>
                    <div><label className="block text-xs font-medium">Mobile Phone</label><input type="text" name="phone_mobile" value={profileData.phone_mobile} onChange={handleBaseChange} className="w-full p-2 text-sm border rounded" /></div>
                    <div><label className="block text-xs font-medium">Home Phone</label><input type="text" name="phone_home" value={profileData.phone_home} onChange={handleBaseChange} className="w-full p-2 text-sm border rounded" /></div>
                    <div><label className="block text-xs font-medium">City</label><input type="text" name="city" value={profileData.city} onChange={handleBaseChange} className="w-full p-2 text-sm border rounded" /></div>
                    <div><label className="block text-xs font-medium">Country</label><input type="text" name="country" value={profileData.country} onChange={handleBaseChange} className="w-full p-2 text-sm border rounded" /></div>
                 </div>
                 <div className="mb-2"><label className="block text-xs font-medium">Short Description / Quote</label><textarea name="short_description" value={profileData.short_description} onChange={handleBaseChange} className="w-full p-2 text-sm border rounded" rows={2} /></div>
                 <div><label className="block text-xs font-medium">Long Description / Motivation</label><textarea name="long_description" value={profileData.long_description} onChange={handleBaseChange} className="w-full p-2 text-sm border rounded" rows={3} /></div>
               </div>

               {/* Work Experience */}
               <div className="p-4 bg-gray-50 border rounded-md">
                 <h3 className="font-semibold mb-3 border-b pb-2">Work Experience</h3>
                 {profileData.experiences.map((exp, idx) => (
                   <div key={idx} className="mb-6 p-4 bg-white border rounded relative">
                     <button onClick={() => removeRow('experiences', idx)} className="absolute top-1 right-1 px-2 py-1 bg-red-100 text-red-600 rounded text-xs hover:bg-red-200">Remove</button>
                     <div className="grid grid-cols-2 gap-4 mb-2">
                       <div><label className="block text-xs font-medium">Company</label><input type="text" value={exp.company_name} onChange={(e) => handleArrayChange('experiences', idx, 'company_name', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Job Title</label><input type="text" value={exp.job_title} onChange={(e) => handleArrayChange('experiences', idx, 'job_title', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Start Date</label><input type="text" value={exp.start_date} onChange={(e) => handleArrayChange('experiences', idx, 'start_date', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">End Date</label><input type="text" value={exp.end_date} onChange={(e) => handleArrayChange('experiences', idx, 'end_date', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Career Level</label><input type="text" value={exp.career_level} onChange={(e) => handleArrayChange('experiences', idx, 'career_level', e.target.value)} placeholder="e.g., Senior, Junior" className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Job Type</label><input type="text" value={exp.job_type} onChange={(e) => handleArrayChange('experiences', idx, 'job_type', e.target.value)} placeholder="e.g., Full-time, Contractor" className="w-full p-2 text-sm border rounded" /></div>
                     </div>
                     <div className="mb-2"><label className="block text-xs font-medium">Skills (comma separated)</label><input type="text" value={exp.raw_skills} onChange={(e) => handleArrayChange('experiences', idx, 'raw_skills', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                     <div><label className="block text-xs font-medium">Description</label><textarea value={exp.description} onChange={(e) => handleArrayChange('experiences', idx, 'description', e.target.value)} rows={3} className="w-full p-2 text-sm border rounded" /></div>
                   </div>
                 ))}
                 <button onClick={() => addRow('experiences', { company_name: '', job_title: '', start_date: '', end_date: '', raw_skills: '', description: '', career_level: '', job_type: '' })} className="mt-2 text-sm text-blue-600 font-medium">+ Add Experience</button>
               </div>

               {/* Education */}
               <div className="p-4 bg-gray-50 border rounded-md">
                 <h3 className="font-semibold mb-3 border-b pb-2">Education</h3>
                 {profileData.education.map((edu, idx) => (
                   <div key={idx} className="mb-6 p-4 bg-white border rounded relative">
                     <button onClick={() => removeRow('education', idx)} className="absolute top-1 right-1 px-2 py-1 bg-red-100 text-red-600 rounded text-xs hover:bg-red-200">Remove</button>
                     <div className="grid grid-cols-2 gap-4 mb-2">
                       <div><label className="block text-xs font-medium">Degree</label><input type="text" value={edu.degree} onChange={(e) => handleArrayChange('education', idx, 'degree', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Institution</label><input type="text" value={edu.institution} onChange={(e) => handleArrayChange('education', idx, 'institution', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Field of Study</label><input type="text" value={edu.field_of_study} onChange={(e) => handleArrayChange('education', idx, 'field_of_study', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div className="flex gap-2">
                         <div className="w-1/2"><label className="block text-xs font-medium">Start</label><input type="text" value={edu.start_date} onChange={(e) => handleArrayChange('education', idx, 'start_date', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                         <div className="w-1/2"><label className="block text-xs font-medium">End</label><input type="text" value={edu.end_date} onChange={(e) => handleArrayChange('education', idx, 'end_date', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       </div>
                     </div>
                     <div><label className="block text-xs font-medium">Description</label><textarea value={edu.description} onChange={(e) => handleArrayChange('education', idx, 'description', e.target.value)} rows={2} className="w-full p-2 text-sm border rounded" /></div>
                   </div>
                 ))}
                 <button onClick={() => addRow('education', { degree: '', institution: '', start_date: '', end_date: '', field_of_study: '', description: '' })} className="mt-2 text-sm text-blue-600 font-medium">+ Add Education</button>
               </div>

               {/* Projects */}
               <div className="p-4 bg-gray-50 border rounded-md">
                 <h3 className="font-semibold mb-3 border-b pb-2">Projects</h3>
                 {profileData.projects.map((proj, idx) => (
                   <div key={idx} className="mb-6 p-4 bg-white border rounded relative">
                     <button onClick={() => removeRow('projects', idx)} className="absolute top-1 right-1 px-2 py-1 bg-red-100 text-red-600 rounded text-xs hover:bg-red-200">Remove</button>
                     <div className="grid grid-cols-2 gap-4 mb-2">
                       <div><label className="block text-xs font-medium">Name</label><input type="text" value={proj.name} onChange={(e) => handleArrayChange('projects', idx, 'name', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Role</label><input type="text" value={proj.role} onChange={(e) => handleArrayChange('projects', idx, 'role', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Start Date</label><input type="text" value={proj.start_date} onChange={(e) => handleArrayChange('projects', idx, 'start_date', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">End Date</label><input type="text" value={proj.end_date} onChange={(e) => handleArrayChange('projects', idx, 'end_date', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Creator</label><input type="text" value={proj.creator} onChange={(e) => handleArrayChange('projects', idx, 'creator', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">URL</label><input type="text" value={proj.url} onChange={(e) => handleArrayChange('projects', idx, 'url', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                     </div>
                     <div className="flex items-center gap-2 mb-2">
                         <input type="checkbox" checked={proj.is_current} onChange={(e) => handleArrayChange('projects', idx, 'is_current', e.target.checked)} className="h-4 w-4 text-blue-600" />
                         <label className="text-xs font-medium">Current Project</label>
                     </div>
                     <div><label className="block text-xs font-medium">Description</label><textarea value={proj.description} onChange={(e) => handleArrayChange('projects', idx, 'description', e.target.value)} rows={3} className="w-full p-2 text-sm border rounded" /></div>
                   </div>
                 ))}
                 <button onClick={() => addRow('projects', { name: '', role: '', start_date: '', end_date: '', url: '', creator: '', description: '', is_current: false })} className="mt-2 text-sm text-blue-600 font-medium">+ Add Project</button>
               </div>

               {/* Courses */}
               <div className="p-4 bg-gray-50 border rounded-md">
                 <h3 className="font-semibold mb-3 border-b pb-2">Courses & Certifications</h3>
                 {profileData.courses.map((crs, idx) => (
                   <div key={idx} className="mb-6 p-4 bg-white border rounded relative">
                     <button onClick={() => removeRow('courses', idx)} className="absolute top-1 right-1 px-2 py-1 bg-red-100 text-red-600 rounded text-xs hover:bg-red-200">Remove</button>
                     <div className="grid grid-cols-2 gap-4 mb-2">
                       <div><label className="block text-xs font-medium">Title</label><input type="text" value={crs.title} onChange={(e) => handleArrayChange('courses', idx, 'title', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Organized By</label><input type="text" value={crs.organized_by} onChange={(e) => handleArrayChange('courses', idx, 'organized_by', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Start Date</label><input type="text" value={crs.start_date} onChange={(e) => handleArrayChange('courses', idx, 'start_date', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Finish Date</label><input type="text" value={crs.finish_date} onChange={(e) => handleArrayChange('courses', idx, 'finish_date', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div className="col-span-2"><label className="block text-xs font-medium">URL</label><input type="text" value={crs.url} onChange={(e) => handleArrayChange('courses', idx, 'url', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                     </div>
                     <div className="flex items-center gap-2 mb-2">
                         <input type="checkbox" checked={crs.has_certification} onChange={(e) => handleArrayChange('courses', idx, 'has_certification', e.target.checked)} className="h-4 w-4 text-blue-600" />
                         <label className="text-xs font-medium">Has Certification</label>
                     </div>
                     <div><label className="block text-xs font-medium">Description</label><textarea value={crs.description} onChange={(e) => handleArrayChange('courses', idx, 'description', e.target.value)} rows={2} className="w-full p-2 text-sm border rounded" /></div>
                   </div>
                 ))}
                 <button onClick={() => addRow('courses', { title: '', description: '', url: '', start_date: '', finish_date: '', organized_by: '', has_certification: false })} className="mt-2 text-sm text-blue-600 font-medium">+ Add Course</button>
               </div>

               {/* Patents */}
               <div className="p-4 bg-gray-50 border rounded-md">
                 <h3 className="font-semibold mb-3 border-b pb-2">Patents</h3>
                 {profileData.patents.map((pat, idx) => (
                   <div key={idx} className="mb-6 p-4 bg-white border rounded relative">
                     <button onClick={() => removeRow('patents', idx)} className="absolute top-1 right-1 px-2 py-1 bg-red-100 text-red-600 rounded text-xs hover:bg-red-200">Remove</button>
                     <div className="grid grid-cols-2 gap-4 mb-2">
                       <div><label className="block text-xs font-medium">Title</label><input type="text" value={pat.title} onChange={(e) => handleArrayChange('patents', idx, 'title', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Inventor</label><input type="text" value={pat.inventor} onChange={(e) => handleArrayChange('patents', idx, 'inventor', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Office</label><input type="text" value={pat.office} onChange={(e) => handleArrayChange('patents', idx, 'office', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Number</label><input type="text" value={pat.number} onChange={(e) => handleArrayChange('patents', idx, 'number', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Issued Date</label><input type="text" value={pat.issued_date} onChange={(e) => handleArrayChange('patents', idx, 'issued_date', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Status</label><input type="text" value={pat.status} onChange={(e) => handleArrayChange('patents', idx, 'status', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div className="col-span-2"><label className="block text-xs font-medium">URL</label><input type="text" value={pat.url} onChange={(e) => handleArrayChange('patents', idx, 'url', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                     </div>
                     <div><label className="block text-xs font-medium">Description</label><textarea value={pat.description} onChange={(e) => handleArrayChange('patents', idx, 'description', e.target.value)} rows={2} className="w-full p-2 text-sm border rounded" /></div>
                   </div>
                 ))}
                 <button onClick={() => addRow('patents', { title: '', office: '', number: '', inventor: '', url: '', description: '', issued_date: '', status: '' })} className="mt-2 text-sm text-blue-600 font-medium">+ Add Patent</button>
               </div>

               {/* Publications */}
               <div className="p-4 bg-gray-50 border rounded-md">
                 <h3 className="font-semibold mb-3 border-b pb-2">Publications</h3>
                 {profileData.publications.map((pub, idx) => (
                   <div key={idx} className="mb-6 p-4 bg-white border rounded relative">
                     <button onClick={() => removeRow('publications', idx)} className="absolute top-1 right-1 px-2 py-1 bg-red-100 text-red-600 rounded text-xs hover:bg-red-200">Remove</button>
                     <div className="grid grid-cols-2 gap-4 mb-2">
                       <div><label className="block text-xs font-medium">Title</label><input type="text" value={pub.title} onChange={(e) => handleArrayChange('publications', idx, 'title', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Date</label><input type="text" value={pub.date} onChange={(e) => handleArrayChange('publications', idx, 'date', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div className="col-span-2"><label className="block text-xs font-medium">Publisher</label><input type="text" value={pub.publisher} onChange={(e) => handleArrayChange('publications', idx, 'publisher', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                     </div>
                     <div><label className="block text-xs font-medium">Description</label><textarea value={pub.description} onChange={(e) => handleArrayChange('publications', idx, 'description', e.target.value)} rows={2} className="w-full p-2 text-sm border rounded" /></div>
                   </div>
                 ))}
                 <button onClick={() => addRow('publications', { title: '', publisher: '', date: '', description: '' })} className="mt-2 text-sm text-blue-600 font-medium">+ Add Publication</button>
               </div>

               {/* Honors */}
               <div className="p-4 bg-gray-50 border rounded-md">
                 <h3 className="font-semibold mb-3 border-b pb-2">Honors & Awards</h3>
                 {profileData.honors.map((honor, idx) => (
                   <div key={idx} className="mb-6 p-4 bg-white border rounded relative">
                     <button onClick={() => removeRow('honors', idx)} className="absolute top-1 right-1 px-2 py-1 bg-red-100 text-red-600 rounded text-xs hover:bg-red-200">Remove</button>
                     <div className="grid grid-cols-3 gap-4 mb-2">
                       <div><label className="block text-xs font-medium">Title</label><input type="text" value={honor.title} onChange={(e) => handleArrayChange('honors', idx, 'title', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Issuer</label><input type="text" value={honor.issuer} onChange={(e) => handleArrayChange('honors', idx, 'issuer', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                       <div><label className="block text-xs font-medium">Date</label><input type="text" value={honor.date} onChange={(e) => handleArrayChange('honors', idx, 'date', e.target.value)} className="w-full p-2 text-sm border rounded" /></div>
                     </div>
                   </div>
                 ))}
                 <button onClick={() => addRow('honors', { title: '', issuer: '', date: '' })} className="mt-2 text-sm text-blue-600 font-medium">+ Add Honor</button>
               </div>

               {/* Websites & IM */}
               <div className="p-4 bg-gray-50 border rounded-md grid grid-cols-2 gap-4">
                 <div>
                   <h3 className="font-semibold mb-3 border-b pb-2">Websites</h3>
                   {profileData.websites.map((site, idx) => (
                     <div key={idx} className="mb-2 flex gap-2 relative pr-8">
                       <input type="text" placeholder="URL" value={site.url} onChange={(e) => handleArrayChange('websites', idx, 'url', e.target.value)} className="flex-1 p-2 text-sm border rounded" />
                       <input type="text" placeholder="Type" value={site.website_type} onChange={(e) => handleArrayChange('websites', idx, 'website_type', e.target.value)} className="w-1/3 p-2 text-sm border rounded" />
                       <button onClick={() => removeRow('websites', idx)} className="absolute right-0 top-1 text-red-500 font-bold">✕</button>
                     </div>
                   ))}
                   <button onClick={() => addRow('websites', { url: '', website_type: '' })} className="mt-2 text-sm text-blue-600 font-medium">+ Add Website</button>
                 </div>
                 <div>
                   <h3 className="font-semibold mb-3 border-b pb-2">Instant Messaging</h3>
                   {profileData.instant_messaging.map((im, idx) => (
                     <div key={idx} className="mb-2 flex gap-2 relative pr-8">
                       <input type="text" placeholder="App (e.g. Skype)" value={im.name} onChange={(e) => handleArrayChange('instant_messaging', idx, 'name', e.target.value)} className="w-1/3 p-2 text-sm border rounded" />
                       <input type="text" placeholder="Username" value={im.username} onChange={(e) => handleArrayChange('instant_messaging', idx, 'username', e.target.value)} className="flex-1 p-2 text-sm border rounded" />
                       <button onClick={() => removeRow('instant_messaging', idx)} className="absolute right-0 top-1 text-red-500 font-bold">✕</button>
                     </div>
                   ))}
                   <button onClick={() => addRow('instant_messaging', { name: '', username: '' })} className="mt-2 text-sm text-blue-600 font-medium">+ Add IM</button>
                 </div>
               </div>

               {/* Skills & Languages */}
               <div className="p-4 bg-gray-50 border rounded-md grid grid-cols-2 gap-4">
                 <div>
                   <h3 className="font-semibold mb-3 border-b pb-2">Technical Skills</h3>
                   {profileData.technical_skills.map((skill, idx) => (
                     <div key={idx} className="mb-2 flex gap-2 relative pr-8">
                       <input type="text" placeholder="Skill" value={skill.name} onChange={(e) => handleArrayChange('technical_skills', idx, 'name', e.target.value)} className="flex-1 p-2 text-sm border rounded" />
                       <button onClick={() => removeRow('technical_skills', idx)} className="absolute right-0 top-1 text-red-500 font-bold">✕</button>
                     </div>
                   ))}
                   <button onClick={() => addRow('technical_skills', { name: '' })} className="mt-2 text-sm text-blue-600 font-medium">+ Add Skill</button>
                 </div>
                 <div>
                   <h3 className="font-semibold mb-3 border-b pb-2">Languages</h3>
                   {profileData.languages.map((lang, idx) => (
                     <div key={idx} className="mb-2 flex gap-2 relative pr-8">
                       <input type="text" placeholder="Language" value={lang.name} onChange={(e) => handleArrayChange('languages', idx, 'name', e.target.value)} className="flex-1 p-2 text-sm border rounded" />
                       <input type="text" placeholder="Level" value={lang.proficiency} onChange={(e) => handleArrayChange('languages', idx, 'proficiency', e.target.value)} className="w-1/3 p-2 text-sm border rounded" />
                       <button onClick={() => removeRow('languages', idx)} className="absolute right-0 top-1 text-red-500 font-bold">✕</button>
                     </div>
                   ))}
                   <button onClick={() => addRow('languages', { name: '', proficiency: '' })} className="mt-2 text-sm text-blue-600 font-medium">+ Add Language</button>
                 </div>
               </div>

               {/* Other Info */}
               <div className="p-4 bg-gray-50 border rounded-md">
                 <h3 className="font-semibold mb-3 border-b pb-2">Other Info (Hobbies, Interests)</h3>
                 {profileData.other_info.map((info, idx) => (
                   <div key={idx} className="mb-2 flex gap-2 relative pr-8">
                     <input type="text" placeholder="Type (e.g. Hobby)" value={info.type} onChange={(e) => handleArrayChange('other_info', idx, 'type', e.target.value)} className="w-1/3 p-2 text-sm border rounded" />
                     <input type="text" placeholder="Description" value={info.description} onChange={(e) => handleArrayChange('other_info', idx, 'description', e.target.value)} className="flex-1 p-2 text-sm border rounded" />
                     <button onClick={() => removeRow('other_info', idx)} className="absolute right-0 top-1 text-red-500 font-bold">✕</button>
                   </div>
                 ))}
                 <button onClick={() => addRow('other_info', { type: '', description: '' })} className="mt-2 text-sm text-blue-600 font-medium">+ Add Info</button>
               </div>

             </div>
           )}

           <button onClick={handleProfileSubmit} disabled={isLoading} className="mt-6 w-full bg-gray-900 text-white font-medium py-3 rounded-md hover:bg-gray-800 transition-colors disabled:opacity-50">
             {isLoading ? 'Saving...' : 'Save Profile to Database'}
           </button>
           {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
         </div>
        )}

        {activeTab === 'generate' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white p-6 border border-gray-200 rounded-md shadow-sm space-y-4">
              <h2 className="text-xl font-semibold mb-4">CV Strategy & Generation</h2>
              
              <div className="p-4 bg-blue-50 border border-blue-100 rounded-md">
                <label className="block text-sm font-medium text-blue-900 mb-1">Target Candidate</label>
                <select className="w-full p-2 border border-blue-200 rounded-md bg-white mb-2" onChange={(e) => loadCandidateProfile(e.target.value)} value={candidateName}>
                  <option value="">-- Select a saved candidate --</option>
                  {candidates.map(name => <option key={name} value={name}>{name}</option>)}
                </select>
                <p className="text-xs text-blue-700">The generator will align this candidate's history to the job description.</p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Target Job Description</label>
                <textarea value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} rows={10} placeholder="Paste the job requirements here..." className="w-full p-2 border border-gray-300 rounded-md shadow-sm" />
              </div>

              <div className="flex gap-4">
                <button onClick={handleGenerateHybrid} disabled={isLoading || !jobDescription || !candidateName} className="flex-1 bg-gray-800 text-white font-medium py-3 rounded-md hover:bg-gray-900 disabled:opacity-50 transition-colors">
                  Run Hybrid RAG
                </button>
              </div>

              {error && <div className="p-3 bg-red-100 text-red-700 border border-red-200 rounded-md text-sm">{error}</div>}
              
              <div className="border-t pt-4 mt-6">
                <h3 className="font-semibold text-gray-700 mb-4">Export to PDF</h3>
                <div className="grid grid-cols-3 gap-2">
                  <button onClick={() => loadEditor(1)} disabled={isLoading || !candidateName} className="border border-blue-200 bg-blue-50 hover:bg-blue-100 text-blue-700 py-3 rounded-md text-sm font-medium transition-colors disabled:opacity-50">Design 1</button>
                  <button onClick={() => loadEditor(2)} disabled={isLoading || !candidateName} className="border border-blue-200 bg-blue-50 hover:bg-blue-100 text-blue-700 py-3 rounded-md text-sm font-medium transition-colors disabled:opacity-50">Design 2</button>
                  <button onClick={() => loadEditor(3)} disabled={isLoading || !candidateName} className="border border-blue-200 bg-blue-50 hover:bg-blue-100 text-blue-700 py-3 rounded-md text-sm font-medium transition-colors disabled:opacity-50">Design 3</button>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 border border-gray-200 rounded-md shadow-sm h-full min-h-[500px] overflow-y-auto">
              <h3 className="text-sm font-semibold text-gray-500 mb-2 uppercase tracking-wide">LLM Strategy Output</h3>
              {generatedCv ? <pre className="whitespace-pre-wrap font-sans text-sm bg-gray-50 p-4 rounded border">{generatedCv}</pre> : <div className="flex items-center justify-center h-full text-gray-400 italic">Hybrid search results will appear here...</div>}
            </div>
          </div>
        )}

        {activeTab === 'editor' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4">
          <div className="space-y-2">
            <h3 className="font-bold text-lg">Edit LaTeX Source</h3>
            <textarea
              value={latexCode}
              onChange={(e) => setLatexCode(e.target.value)}
              className="w-full h-[600px] p-4 font-mono text-sm border rounded bg-gray-900 text-green-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="space-y-4">
            <h3 className="font-bold text-lg">Actions</h3>
            <div className="flex flex-col gap-4 bg-white p-6 border rounded shadow-sm">
              <p className="text-sm text-gray-600">
                Make any final manual adjustments. Compile the code to download your final CV.
              </p>
              
              <button
                onClick={async () => {
                  setIsLoading(true);
                  setError('');
                  try {
                    const response = await fetch('http://127.0.0.1:8000/compile-latex', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ latex: latexCode }), 
                    });
                    
                    if (!response.ok) throw new Error("Compilation failed on backend");

                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = "cv.pdf";
                    a.click();
                  } catch (err: any) {
                    setError(err.message);
                  } finally {
                    setIsLoading(false);
                  }
                }}
                disabled={isLoading || !latexCode}
                className="bg-blue-600 text-white font-medium py-3 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {isLoading ? 'Compiling PDF...' : 'Compile & Download PDF'}
              </button>
              
              {error && <p className="text-red-500 text-sm font-medium">{error}</p>}
            </div>
          </div>
        </div>
      )}
      </div>
    </main>
  );
}