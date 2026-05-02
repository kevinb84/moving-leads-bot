import { useEffect, useState } from 'react';
import { insforge } from './lib/insforge';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { 
  Briefcase, 
  MapPin, 
  Clock, 
  Search,
  Filter,
  CheckCircle,
  XCircle,
  AlertCircle,
  Truck,
  MessageSquare,
  Calendar,
  ExternalLink,
  ChevronDown,
  Archive,
  Phone
} from 'lucide-react';

import { MarketingHub } from './components/MarketingHub';

interface Lead {
  id: string;
  customer_name: string | null;
  phone_number: string | null;
  move_date: string | null;
  origin_neighborhood: string | null;
  destination_city: string | null;
  inventory_summary: string | null;
  packing_service: boolean | null;
  call_summary: string | null;
  raw_text: string | null;
  source_url: string;
  is_moving_lead: boolean | null;
  estimated_quote: string | null;
  whatsapp_draft: string | null;
  created_at: string;
  is_client: boolean | null;
  lead_intent_score?: number;
  pain_points?: string;
}

function App() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Navigation State
  const [activeTab, setActiveTab] = useState<'leads' | 'marketing'>('leads');
  
  // Marketing State
  const [marketingContent, setMarketingContent] = useState('');
  const [isBroadcasting, setIsBroadcasting] = useState(false);
  
  // filtering
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [isLocalData, setIsLocalData] = useState(false);

  const fetchLeads = async () => {
    try {
      setLoading(true);
      setError(null);
      setIsLocalData(false);

      // 1. Try fetching from InsForge
      try {
        let query = insforge.database
          .from('moving_leads')
          .select('*');
          
        if (statusFilter !== 'all') {
          const isClient = statusFilter === 'client';
          if (isClient) {
            query = query.eq('is_client', true);
          } else if (statusFilter === 'qualified') {
            query = query.eq('is_moving_lead', true);
          } else if (statusFilter === 'unqualified') {
            query = query.eq('is_moving_lead', false);
          }
        }

        const { data, error: fetchError } = await query;

        if (fetchError) throw fetchError;
        
        let filteredData = (data as Lead[]) || [];
        // Filter out our internal marketing queues so they don't render on the dashboard
        filteredData = filteredData.filter(lead => !lead.customer_name?.includes('MARKETING_BROADCAST'));
        
        processAndSetLeads(filteredData);
      } catch (insforgeErr) {
        console.warn('InsForge connection failed, trying local fallback...', insforgeErr);
        // 2. Fallback to local leads.json
        const response = await fetch('/leads.json');
        if (response.ok) {
          const localData = await response.json();
          setIsLocalData(true);
          processAndSetLeads(localData);
        } else {
          throw insforgeErr; // Re-throw original error if local fallback also fails
        }
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to fetch leads');
    } finally {
      setLoading(false);
    }
  };

  const processAndSetLeads = (data: Lead[]) => {
    let filteredData = [...data];
    if (searchQuery) {
      filteredData = filteredData.filter(lead => 
        (lead.raw_text && lead.raw_text.toLowerCase().includes(searchQuery.toLowerCase())) || 
        (lead.destination_city && lead.destination_city.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (lead.customer_name && lead.customer_name.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }
    
    // Sort by created_at descending
    filteredData.sort((a, b) => {
        const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
        const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
        return dateB - dateA;
    });

    setLeads(filteredData);
  };

  useEffect(() => {
    fetchLeads();
  }, [statusFilter, searchQuery]);

  const updateLeadStatus = async (id: string, updates: Partial<Lead>) => {
    try {
      const { error } = await insforge.database
        .from('moving_leads')
        .update(updates)
        .eq('id', id);
        
      if (error) throw error;
      
      setLeads(leads.map(lead => lead.id === id ? { ...lead, ...updates } : lead));
    } catch (err) {
      console.error('Failed to update lead', err);
      alert('Failed to update status. Check console.');
    }
  };

  const handleBroadcast = async (platform: string) => {
    if (!marketingContent.trim()) return alert('Enter ad content first!');
    setIsBroadcasting(true);
    try {
      const { error } = await insforge.database.from('moving_leads').insert([{
        customer_name: 'MARKETING_BROADCAST_PENDING',
        source_url: `queue_marketing_${platform}_${Date.now()}`,
        raw_text: marketingContent,
        is_moving_lead: false,
        text_hash: `hash_${Date.now()}` // Bypass unique constraint
      }]);
      if (error) throw error;
      alert(`Successfully queued ad for ${platform.toUpperCase()}! The worker will post it shortly.`);
      setMarketingContent('');
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsBroadcasting(false);
    }
  };

  const handleSmartComment = async (lead: Lead) => {
    if (!confirm('Deploy Smart Commenter to officially reply to this lead on Facebook?')) return;
    try {
      const { error } = await insforge.database.from('moving_leads').insert([{
        customer_name: 'MARKETING_BROADCAST_PENDING',
        source_url: `queue_marketing_facebook_comment_${Date.now()}`,
        raw_text: lead.whatsapp_draft || "Hey! We are local movers and would love to help. Let us know if you still need a hand!",
        whatsapp_draft: lead.source_url, // Store the TARGET URL inside the whatsapp draft field
        is_moving_lead: false,
        text_hash: `hash_comment_${Date.now()}`
      }]);
      if (error) throw error;
      alert(`Smart Comment queued! The worker will reply in the thread momentarily.`);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const getStatusBadge = (isMovingLead: boolean | null) => {
    if (isMovingLead === true) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
          <CheckCircle className="w-3.5 h-3.5" />
          Qualified
        </span>
      );
    }
    if (isMovingLead === false) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-500 border border-rose-500/20">
          <XCircle className="w-3.5 h-3.5" />
          Unqualified
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-500 border border-amber-500/20">
        <AlertCircle className="w-3.5 h-3.5" />
        Needs Review
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-black font-sans text-neutral-200 selection:bg-indigo-500/30">
      
      {/* Decorative Background Gradients */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-600/20 blur-[120px] animate-float"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-emerald-600/10 blur-[120px] animate-float" style={{ animationDelay: '3s' }}></div>
      </div>

      {/* Header Area */}
      <header className="sticky top-0 z-50 bg-black/60 backdrop-blur-xl border-b border-white/10 shadow-2xl">
        <div className="max-w-7xl mx-auto px-6 py-4 relative">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 flex items-center justify-center rounded-2xl bg-white/5 border border-white/10 shadow-[0_0_30px_-5px_rgba(99,102,241,0.3)] backdrop-blur-md relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/50 to-purple-600/50"></div>
                <Truck className="h-6 w-6 text-white relative z-10" />
              </div>
              <div>
                <h1 className="text-2xl font-display font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-neutral-400 tracking-tight">Moving Leads Hub</h1>
                <div className="flex items-center gap-2 mt-0.5">
                  <p className="text-xs text-indigo-300/80 font-medium tracking-wide uppercase">AI-Qualified Opportunities</p>
                  {isLocalData && (
                    <span className="px-1.5 py-0.5 rounded-md bg-amber-500/10 text-amber-500 border border-amber-500/20 text-[10px] font-bold uppercase tracking-wider">
                      Local Offline Mode
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex bg-white/5 p-1 rounded-2xl border border-white/10 shadow-inner backdrop-blur-md">
              <button 
                onClick={() => setActiveTab('leads')}
                className={`px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${activeTab === 'leads' ? 'bg-indigo-500 text-white shadow-[0_0_20px_-5px_rgba(99,102,241,0.5)]' : 'text-neutral-400 hover:text-white hover:bg-white/5'}`}
              >
                Lead Gen Pipeline
              </button>
              <button 
                onClick={() => setActiveTab('marketing')}
                className={`px-6 py-2.5 rounded-xl text-sm font-bold transition-all flex items-center gap-2 ${activeTab === 'marketing' ? 'bg-white text-black shadow-[0_0_20px_-5px_rgba(255,255,255,0.5)]' : 'text-neutral-400 hover:text-white hover:bg-white/5'}`}
              >
                Marketing Assets
              </button>
            </div>

            <div className="flex items-center gap-3 flex-1 md:max-w-md">
              <div className="relative flex-1 group">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-500 group-focus-within:text-indigo-400 transition-colors" />
                <input
                  type="text"
                  disabled={activeTab !== 'leads'}
                  placeholder={activeTab === 'leads' ? "Search text, name, or city..." : ""}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-neutral-800/50 border border-neutral-700/50 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all placeholder:text-neutral-500"
                />
              </div>

              <div className="relative">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="appearance-none pl-10 pr-10 py-2.5 bg-neutral-800/50 border border-neutral-700/50 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all cursor-pointer"
                >
                  <option value="all">All Leads</option>
                  <option value="qualified">Qualified</option>
                  <option value="unqualified">Unqualified</option>
                  <option value="client">Secured Clients</option>
                </select>
                <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-500" />
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-500 pointer-events-none" />
              </div>
            </div>
          </div>

          {/* Analytics Stats Bar */}
          {activeTab === 'leads' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-6 border-t border-white/5 animate-in fade-in slide-in-from-top-4 duration-500">
            <div className="bg-white/5 backdrop-blur-xl rounded-2xl p-5 border border-white/10 flex items-center justify-between group hover:border-indigo-500/50 transition-colors">
              <div>
                <p className="text-[10px] text-neutral-400 font-bold uppercase tracking-widest mb-1">Total Valid Leads</p>
                <p className="text-3xl font-display font-bold text-white group-hover:text-indigo-400 transition-colors">{leads.filter(l => l.is_moving_lead).length}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
                <Briefcase className="w-5 h-5" />
              </div>
            </div>
            <div className="bg-white/5 backdrop-blur-xl rounded-2xl p-5 border border-white/10 flex items-center justify-between group hover:border-emerald-500/50 transition-colors">
              <div>
                <p className="text-[10px] text-neutral-400 font-bold uppercase tracking-widest mb-1">Conversion Win Rate</p>
                <p className="text-3xl font-display font-bold text-emerald-400">
                  {leads.filter(l => l.is_moving_lead !== false).length > 0 
                    ? ((leads.filter(l => l.is_client).length / leads.filter(l => l.is_moving_lead !== false).length) * 100).toFixed(1) 
                    : '0.0'}%
                </p>
              </div>
              <div className="h-12 w-12 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20">
                <CheckCircle className="w-5 h-5" />
              </div>
            </div>
            <div className="bg-white/5 backdrop-blur-xl rounded-2xl p-5 border border-white/10 flex items-center justify-between group hover:border-rose-500/50 transition-colors">
              <div>
                <p className="text-[10px] text-neutral-400 font-bold uppercase tracking-widest mb-1">Total Unqualified</p>
                <p className="text-3xl font-display font-bold text-rose-400">{leads.filter(l => l.is_moving_lead === false).length}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-rose-500/10 flex items-center justify-center text-rose-400 border border-rose-500/20">
                <XCircle className="w-5 h-5" />
              </div>
            </div>
          </div>
          )}

        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        
        {activeTab === 'marketing' ? (
          <MarketingHub 
            marketingContent={marketingContent}
            setMarketingContent={setMarketingContent}
            handleBroadcast={handleBroadcast}
            isBroadcasting={isBroadcasting}
          />
        ) : loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="w-8 h-8 rounded-full border-2 border-indigo-500/20 border-t-indigo-500 animate-spin" />
            <p className="text-neutral-400 text-sm animate-pulse">Scanning the database...</p>
          </div>
        ) : error ? (
          <div className="bg-rose-500/10 border border-rose-500/20 p-6 rounded-2xl flex items-center gap-4 text-rose-400">
            <AlertCircle className="h-6 w-6" />
            <div>
              <h3 className="font-semibold text-rose-300">Connection Error</h3>
              <p className="text-sm mt-1">{error}</p>
            </div>
            <button 
              onClick={fetchLeads}
              className="ml-auto px-4 py-2 bg-rose-500/20 hover:bg-rose-500/30 rounded-lg text-sm font-medium transition-colors"
            >
              Try Again
            </button>
          </div>
        ) : leads.length === 0 ? (
          <div className="bg-neutral-900 border border-neutral-800 p-12 rounded-3xl flex flex-col items-center text-center">
            <div className="w-16 h-16 bg-neutral-800 rounded-2xl flex items-center justify-center mb-4">
              <Archive className="h-8 w-8 text-neutral-500" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">No leads found</h3>
            <p className="text-neutral-400 max-w-sm">
              We couldn't find any leads matching your current filters. Adjust your search or wait for the scraper to pick up new posts.
            </p>
            <button 
              onClick={() => { setStatusFilter('all'); setSearchQuery(''); }}
              className="mt-6 px-6 py-2.5 bg-white text-black font-semibold rounded-xl hover:bg-neutral-200 transition-colors"
            >
              Clear Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {leads.map(lead => (
              <div 
                key={lead.id} 
                className={`group relative flex flex-col bg-white/5 backdrop-blur-md border ${lead.is_client ? 'border-emerald-500/50 shadow-[0_0_30px_-5px_rgba(16,185,129,0.2)]' : 'border-white/10'} rounded-3xl overflow-hidden hover:border-white/20 transition-all duration-500 hover:-translate-y-1 hover:shadow-2xl z-10`}
              >
                
                {/* Card Header */}
                <div className="p-6 border-b border-white/5 bg-gradient-to-b from-white/5 to-transparent relative overflow-hidden">
                  <div className="flex justify-between items-start mb-5">
                    {getStatusBadge(lead.is_moving_lead)}
                    <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1.5 bg-black/40 px-2 py-1 rounded-md">
                      <Clock className="w-3 h-3" />
                      {lead.created_at ? formatDistanceToNow(parseISO(lead.created_at), { addSuffix: true }) : 'Unknown'}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-4 relative z-10">
                    <div className="h-12 w-12 flex items-center justify-center rounded-2xl bg-white/10 border border-white/10 shadow-inner shrink-0">
                      <span className="font-display font-bold text-white text-lg">{(lead.customer_name || 'U')[0].toUpperCase()}</span>
                    </div>
                    <div className="overflow-hidden">
                      <h3 className="font-display font-bold text-white text-xl leading-tight w-full truncate tracking-tight" title={lead.customer_name || 'Unknown Potential Client'}>
                        {lead.customer_name || 'Unknown Potential Client'}
                      </h3>
                      <div className="text-xs text-neutral-400 font-medium flex items-center gap-1.5 mt-1.5 truncate">
                        <MapPin className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                        <span className="truncate">{lead.origin_neighborhood ? `${lead.origin_neighborhood} → ` : ''}{lead.destination_city || 'Unknown Location'}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Card Body */}
                <div className="p-5 flex-1 flex flex-col">
                  {/* Notes / Reasonings */}
                  {lead.lead_intent_score && (
                    <div className="mb-4 flex items-center justify-between">
                      <div className="flex items-center gap-1.5 overflow-hidden">
                        <span className="text-xs font-bold text-neutral-500 uppercase tracking-widest shrink-0">Priority Score:</span>
                        <div className="flex gap-0.5">
                          {[...Array(10)].map((_, i) => (
                            <div 
                              key={i} 
                              className={`h-1.5 w-3 rounded-full ${i < (lead.lead_intent_score || 0) ? (lead.lead_intent_score || 0) > 7 ? 'bg-indigo-500' : 'bg-emerald-500' : 'bg-neutral-800'}`} 
                            />
                          ))}
                        </div>
                      </div>
                      <span className={`text-[10px] font-black italic ${ (lead.lead_intent_score || 0) > 7 ? 'text-indigo-400' : 'text-emerald-400'}`}>
                        {lead.lead_intent_score}/10
                      </span>
                    </div>
                  )}

                  {lead.pain_points && (
                     <div className="mb-4 bg-rose-500/5 border border-rose-500/10 rounded-xl p-3 text-xs font-medium text-rose-200">
                        <p className="line-clamp-2 leading-relaxed">
                          <strong className="text-rose-400 uppercase text-[10px] tracking-tighter">🚨 PAIN POINT:</strong> {lead.pain_points}
                        </p>
                    </div>
                  )}

                  {lead.call_summary && (
                    <div className="mb-4 bg-indigo-500/5 border border-indigo-500/10 rounded-xl p-3 text-xs font-medium text-indigo-200">
                      <p className="line-clamp-2 leading-relaxed">
                        <strong className="text-indigo-400">AI Note:</strong> {lead.call_summary}
                      </p>
                    </div>
                  )}

                  <div className="relative mb-5 flex-1">
                    <MessageSquare className="absolute top-0.5 left-0 w-3.5 h-3.5 text-neutral-500" />
                    <p className="text-sm text-neutral-300 pl-6 leading-relaxed italic opacity-80 line-clamp-4">
                      "{lead.raw_text}"
                    </p>
                  </div>

                  {/* Attributes */}
                  <div className="flex flex-wrap gap-2 mt-auto pt-4 border-t border-neutral-800">
                    {lead.estimated_quote && (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-sm font-bold text-emerald-400 w-full mb-1">
                        💰 Estimated Quote: {lead.estimated_quote}
                      </span>
                    )}
                    {lead.move_date && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-neutral-800 text-xs text-neutral-300">
                        <Calendar className="w-3 h-3 text-neutral-500" />
                        {lead.move_date}
                      </span>
                    )}
                    {lead.inventory_summary && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-neutral-800 text-xs text-neutral-300">
                        <Briefcase className="w-3 h-3 text-neutral-500" />
                        {lead.inventory_summary}
                      </span>
                    )}

                  </div>
                  
                  {/* 1-Click Communication Shortcuts */}
                  <div className="flex flex-col gap-2 mt-4 pt-4 border-t border-neutral-800/50">
                    {lead.source_url.includes('facebook.com') && (
                      <button onClick={() => handleSmartComment(lead)} className="w-full flex items-center justify-center gap-1.5 px-3 py-2.5 bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 border border-purple-500/20 rounded-xl text-sm font-bold transition-all shadow-[0_0_15px_-5px_rgba(168,85,247,0.3)]">
                        <MessageSquare className="w-4 h-4" /> Smart Auto-Comment Reply
                      </button>
                    )}
                    {lead.phone_number && (
                      <div className="flex w-full items-center gap-2">
                        <a href={`https://wa.me/${lead.phone_number.replace(/\D/g, '')}${lead.whatsapp_draft ? `?text=${encodeURIComponent(lead.whatsapp_draft)}` : ''}`} target="_blank" rel="noopener noreferrer" className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2.5 bg-[#25D366]/10 hover:bg-[#25D366]/20 text-[#25D366] rounded-xl text-sm font-bold transition-all">
                          <MessageSquare className="w-4 h-4" /> WhatsApp Draft
                        </a>
                        <a href={`tel:${lead.phone_number.replace(/\D/g, '')}`} className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2.5 bg-sky-500/10 hover:bg-sky-500/20 text-sky-500 rounded-xl text-sm font-bold transition-all">
                          <Phone className="w-4 h-4 text-sky-400" /> Call Now
                        </a>
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Footer */}
                <div className="p-4 bg-neutral-900 border-t border-neutral-800 flex items-center justify-between gap-3">
                  <a 
                    href={lead.source_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-1.5 px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-white text-sm font-medium rounded-xl transition-colors w-full group-hover:bg-neutral-700"
                  >
                    View Post
                    <ExternalLink className="w-3.5 h-3.5 text-neutral-400 group-hover:text-white transition-colors" />
                  </a>
                  
                  <button
                    onClick={() => updateLeadStatus(lead.id, { is_client: !lead.is_client })}
                    className={`flex items-center justify-center px-4 py-2 text-sm font-medium rounded-xl transition-colors w-full ${
                      lead.is_client 
                        ? 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 border border-emerald-500/20' 
                        : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20'
                    }`}
                  >
                    {lead.is_client ? '✓ Client Won' : 'Mark as Client'}
                  </button>
                </div>

              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
