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
  created_at: string;
  is_client: boolean | null;
}

function App() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // filtering
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchLeads = async () => {
    try {
      setLoading(true);
      setError(null);
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
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to fetch leads');
    } finally {
      setLoading(false);
    }
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
    <div className="min-h-screen bg-neutral-950 font-sans text-neutral-200 selection:bg-indigo-500/30">
      
      {/* Header Area */}
      <header className="sticky top-0 z-50 bg-neutral-900/80 backdrop-blur-xl border-b border-white/10 shadow-2xl">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 flex items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/20">
                <Truck className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white tracking-tight">Moving Leads Hub</h1>
                <p className="text-xs text-neutral-400 font-medium">AI-Qualified Opportunities</p>
              </div>
            </div>

            <div className="flex items-center gap-3 flex-1 md:max-w-md">
              <div className="relative flex-1 group">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-500 group-focus-within:text-indigo-400 transition-colors" />
                <input
                  type="text"
                  placeholder="Search text, name, or city..."
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
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        
        {loading ? (
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
                className={`group relative flex flex-col bg-neutral-900 border ${lead.is_client ? 'border-emerald-500/30 shadow-[0_0_20px_-5px_rgba(16,185,129,0.15)]' : 'border-neutral-800'} rounded-3xl overflow-hidden hover:border-neutral-700 transition-all duration-300`}
              >
                
                {/* Card Header */}
                <div className="p-5 border-b border-neutral-800/80 bg-neutral-800/20">
                  <div className="flex justify-between items-start mb-4">
                    {getStatusBadge(lead.is_moving_lead)}
                    <span className="text-xs font-medium text-neutral-500 flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      {lead.created_at ? formatDistanceToNow(parseISO(lead.created_at), { addSuffix: true }) : 'Unknown'}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 flex items-center justify-center rounded-full bg-neutral-800 overflow-hidden shrink-0">
                      <span className="font-bold text-neutral-400 text-sm">FB</span>
                    </div>
                    <div className="overflow-hidden">
                      <h3 className="font-bold text-white text-base leading-tight w-full truncate" title={lead.customer_name || 'Unknown Potential Client'}>
                        {lead.customer_name || 'Unknown Potential Client'}
                      </h3>
                      <div className="text-xs text-neutral-400 flex items-center gap-1.5 mt-1 truncate">
                        <MapPin className="w-3 h-3 shrink-0" />
                        <span className="truncate">{lead.origin_neighborhood ? `${lead.origin_neighborhood} → ` : ''}{lead.destination_city || 'Unknown Location'}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Card Body */}
                <div className="p-5 flex-1 flex flex-col">
                  {/* Notes / Reasonings */}
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
                    {lead.phone_number && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-emerald-500/10 text-xs text-emerald-400">
                        <Phone className="w-3 h-3" />
                        {lead.phone_number}
                      </span>
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
