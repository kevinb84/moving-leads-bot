import { useState, useEffect } from 'react';
import { insforge } from '../lib/insforge';
import { ExternalLink, Image as ImageIcon, Upload, Loader2, Trash2 } from 'lucide-react';

interface MediaAsset {
  name: string;
  url: string;
  size: number;
}

export function MarketingHub({ 
  marketingContent, 
  setMarketingContent, 
  handleBroadcast, 
  isBroadcasting 
}: any) {
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Load existing assets from the Storage Bucket
  const fetchAssets = async () => {
    try {
      setIsLoading(true);
      const { data, error } = await insforge.database
        .from('moving_leads')
        .select('*')
        .eq('customer_name', 'ASSET_UPLOAD');
      
      if (error) throw error;
      
      // Re-map the database structure back into the Asset gallery UI logically
      const mappedAssets = (data || []).map(item => ({
          name: item.raw_text || item.id,
          key: item.id,
          url: item.whatsapp_draft,
          size: 0
      }));
      setAssets(mappedAssets as MediaAsset[]);
    } catch (err: any) {
      console.error("Error fetching assets:", err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, []);

  // Upload new assets
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    setIsUploading(true);

    try {
      const files = Array.from(e.target.files);
      for (const file of files) {
        // Upload to bucket
        const { data: uploadData, error: uploadError } = await insforge.storage.from('marketing_assets').uploadAuto(file);
        if (uploadError) throw uploadError;
        
        // Save the key and URL securely inside the primary database instead
        const { error: dbError } = await insforge.database.from('moving_leads').insert([{
            customer_name: 'ASSET_UPLOAD',
            source_url: uploadData?.key || "",
            whatsapp_draft: uploadData?.url || "",
            is_moving_lead: false,
            raw_text: "vault_asset_" + Date.now() + "_" + Math.random()
        }]);
        if (dbError) throw dbError;
      }
      
      // Refresh the gallery
      await fetchAssets();
      alert(`Successfully uploaded ${files.length} memory asset(s)!`);
      
    } catch (err: any) {
      alert(`Failed to upload: ${err.message}`);
    } finally {
      setIsUploading(false);
      // clear the input
      e.target.value = '';
    }
  };

  const deleteAsset = async (asset: any) => {
    if (!confirm("Delete this memory? It won't be used for marketing posts anymore.")) return;
    try {
      // Find the original key that we packed inside source_url
      const { data } = await insforge.database.from('moving_leads').select('source_url').eq('id', asset.key || asset.id).limit(1);
      const originalKey = data?.[0]?.source_url;
      
      if (originalKey) {
          await insforge.storage.from('marketing_assets').remove(originalKey);
      }
      await insforge.database.from('moving_leads').delete().eq('id', asset.key || asset.id);
      await fetchAssets();
    } catch (err: any) {
      alert("Failed to delete asset: " + err.message);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* Auto Broadcast Box */}
      <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-8 border border-white/10 shadow-[0_0_40px_-10px_rgba(99,102,241,0.15)]">
        <div className="flex items-center gap-4 mb-6">
          <div className="h-12 w-12 rounded-2xl bg-indigo-500/20 flex flex-col items-center justify-center text-indigo-400 border border-indigo-500/30">
            <ExternalLink className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-display font-bold text-white tracking-tight">AI Broadcast Hub</h2>
            <p className="text-sm text-neutral-400 mt-1">Write your official localized promo below, and instantly push it to your connected platforms.</p>
          </div>
        </div>
        
        <textarea 
          value={marketingContent}
          onChange={(e) => setMarketingContent(e.target.value)}
          placeholder="Example: Need Calgary movers this weekend? We have a truck available! 🚚 Call us today for 10% off local moves! #yyc #calgarymovers"
          className="w-full h-32 bg-black/40 border border-white/10 rounded-2xl p-5 text-sm text-neutral-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-none mb-6 placeholder:text-neutral-600 shadow-inner backdrop-blur-md transition-all"
        />
        
        <div className="flex flex-wrap gap-4">
          <button 
            onClick={() => handleBroadcast('facebook_page')}
            disabled={isBroadcasting}
            className="px-6 py-3 bg-[#1877F2]/10 hover:bg-[#1877F2]/20 border border-[#1877F2]/30 text-[#1877F2] text-sm font-bold rounded-xl transition-all disabled:opacity-50 flex items-center gap-2"
          >
            {isBroadcasting ? <Loader2 className="w-4 h-4 animate-spin" /> : null} Broadcast to FB Page
          </button>
          <button 
            onClick={() => handleBroadcast('instagram')}
            disabled={isBroadcasting}
            className="px-6 py-3 bg-gradient-to-r from-[#833AB4]/20 via-[#FD1D1D]/20 to-[#F56040]/20 border border-[#E1306C]/40 text-[#E1306C] text-sm font-bold rounded-xl hover:opacity-80 transition-all disabled:opacity-50 shadow-lg flex items-center gap-2"
          >
            {isBroadcasting ? <Loader2 className="w-4 h-4 animate-spin" /> : null} Broadcast to Instagram
          </button>
        </div>
      </div>

      {/* Corporate Memories / Media Library */}
      <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-white/5 bg-black/40">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 flex items-center justify-center rounded-2xl bg-orange-500/20 border border-orange-500/30 shadow-[0_0_30px_-5px_rgba(249,115,22,0.3)]">
                <ImageIcon className="h-6 w-6 text-orange-400" />
              </div>
              <div>
                <h2 className="text-2xl font-display font-bold text-white tracking-tight">Marketing Assets & Memories</h2>
                <p className="text-sm text-neutral-400 mt-1">Upload raw photos & videos. The AI will curate these alongside generated brand art.</p>
              </div>
            </div>

            <div className="relative overflow-hidden group">
              <input 
                type="file" 
                multiple 
                accept="image/*,video/*"
                onChange={handleUpload}
                disabled={isUploading}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed z-20" 
              />
              <button disabled={isUploading} className="pointer-events-none px-6 py-3 bg-white hover:bg-neutral-200 text-black font-bold rounded-xl text-sm transition-all flex items-center gap-2 group-disabled:opacity-50 relative z-10">
                {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />} 
                {isUploading ? "Uploading..." : "Upload New Memory"}
              </button>
            </div>
          </div>
        </div>

        {/* Gallery */}
        <div className="p-8 bg-black/20 min-h-[300px]">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <Loader2 className="w-8 h-8 text-neutral-500 animate-spin" />
              <p className="text-neutral-500 text-sm animate-pulse font-medium">Scanning the Vault...</p>
            </div>
          ) : assets.length === 0 ? (
            <div className="flex flex-col flex-1 h-full items-center justify-center py-20 text-center border-2 border-dashed border-white/10 rounded-2xl bg-white/5 backdrop-blur-sm">
              <div className="h-16 w-16 bg-black/40 rounded-2xl flex items-center justify-center mb-4 border border-white/10">
                <ImageIcon className="h-8 w-8 text-neutral-500" />
              </div>
              <h3 className="text-xl font-display font-bold text-neutral-300">Your Vault is Empty</h3>
              <p className="text-sm text-neutral-500 mt-2 max-w-sm">Drag and drop photos or videos of your moving trucks here to let the AI feature them in future marketing broadcasts.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
              {assets.map((asset: any) => (
                <div key={asset.key} className="group relative aspect-square bg-black/40 border border-white/10 rounded-2xl overflow-hidden hover:border-white/30 transition-all duration-300 shadow-xl hover:-translate-y-1">
                  <img 
                    src={asset.url} 
                    alt={asset.key}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                  
                  {/* Overlay shadow for text legibility */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/20 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-between p-3">
                    <div className="flex justify-end">
                      <button 
                        onClick={() => deleteAsset(asset)}
                        className="bg-black/50 hover:bg-rose-500 backdrop-blur text-white p-2 rounded-lg transition-colors shadow-xl"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
