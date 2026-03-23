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
        .from('marketing_assets')
        .select('*');
      
      if (error) throw error;
      setAssets((data || []) as any[]);
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
        
        // Save the key and URL to the database
        const { error: dbError } = await insforge.database.from('marketing_assets').insert([{
            key: uploadData?.key,
            url: uploadData?.url,
            size: uploadData?.size || 0
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

  const deleteAsset = async (key: string) => {
    if (!confirm("Delete this memory? It won't be used for marketing posts anymore.")) return;
    try {
      await insforge.storage.from('marketing_assets').remove(key);
      await insforge.database.from('marketing_assets').delete().eq('key', key);
      await fetchAssets();
    } catch (err: any) {
      alert("Failed to delete asset: " + err.message);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* Auto Broadcast Box */}
      <div className="bg-gradient-to-r from-indigo-500/10 to-purple-500/10 rounded-2xl p-6 border border-indigo-500/20 shadow-xl shadow-indigo-500/5 backdrop-blur-md">
        <div className="flex items-center gap-3 mb-4">
          <div className="h-10 w-10 rounded-xl bg-indigo-500/20 flex flex-col items-center justify-center text-indigo-400">
            <ExternalLink className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">AI Broadcast Hub</h2>
            <p className="text-sm text-indigo-200/80">Write your official localized promo below, and instantly push it to your connected platforms.</p>
          </div>
        </div>
        
        <textarea 
          value={marketingContent}
          onChange={(e) => setMarketingContent(e.target.value)}
          placeholder="Example: Need Calgary movers this weekend? We have a truck available! 🚚 Call us today for 10% off local moves! #yyc #calgarymovers"
          className="w-full h-28 bg-neutral-900 border border-indigo-500/20 rounded-xl p-4 text-sm text-neutral-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-none mb-4 placeholder:text-neutral-600 shadow-inner"
        />
        
        <div className="flex flex-wrap gap-3">
          <button 
            onClick={() => handleBroadcast('facebook_page')}
            disabled={isBroadcasting}
            className="px-6 py-2.5 bg-[#1877F2]/10 hover:bg-[#1877F2]/20 border border-[#1877F2]/30 text-[#1877F2] text-sm font-bold rounded-xl transition-all disabled:opacity-50"
          >
            {isBroadcasting ? <Loader2 className="w-4 h-4 animate-spin inline mr-2" /> : null} Broadcast to FB Page
          </button>
          <button 
            onClick={() => handleBroadcast('instagram')}
            disabled={isBroadcasting}
            className="px-6 py-2.5 bg-gradient-to-r from-[#833AB4]/10 via-[#FD1D1D]/10 to-[#F56040]/10 border border-[#E1306C]/30 text-[#E1306C] text-sm font-bold rounded-xl hover:opacity-80 transition-all disabled:opacity-50 shadow-lg"
          >
            {isBroadcasting ? <Loader2 className="w-4 h-4 animate-spin inline mr-2" /> : null} Broadcast to Instagram
          </button>
        </div>
      </div>

      {/* Corporate Memories / Media Library */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-2xl overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-neutral-800">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 flex items-center justify-center rounded-xl bg-orange-500/10 shadow-lg shadow-orange-500/10">
                <ImageIcon className="h-5 w-5 text-orange-500" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight">Marketing Assets & Memories</h2>
                <p className="text-sm text-neutral-400">Upload raw photos & videos of your team moving furniture. The AI will curate these alongside generated brand art when forming daily posts.</p>
              </div>
            </div>

            <div className="relative overflow-hidden group">
              <input 
                type="file" 
                multiple 
                accept="image/*,video/*"
                onChange={handleUpload}
                disabled={isUploading}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed" 
              />
              <button disabled={isUploading} className="pointer-events-none px-6 py-2.5 bg-white hover:bg-neutral-200 text-black font-bold rounded-xl text-sm transition-all flex items-center gap-2 group-disabled:opacity-50">
                {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />} 
                {isUploading ? "Uploading..." : "Upload New Memory"}
              </button>
            </div>
          </div>
        </div>

        {/* Gallery */}
        <div className="p-6 bg-neutral-950/50 min-h-[300px]">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <Loader2 className="w-8 h-8 text-neutral-600 animate-spin" />
              <p className="text-neutral-500 text-sm animate-pulse">Scanning the Vault...</p>
            </div>
          ) : assets.length === 0 ? (
            <div className="flex flex-col flex-1 h-full items-center justify-center py-20 text-center border-2 border-dashed border-neutral-800 rounded-2xl">
              <div className="h-16 w-16 bg-neutral-900 rounded-2xl flex items-center justify-center mb-4 border border-neutral-800">
                <ImageIcon className="h-8 w-8 text-neutral-600" />
              </div>
              <h3 className="text-lg font-bold text-neutral-300">Your Vault is Empty</h3>
              <p className="text-sm text-neutral-500 mt-2 max-w-sm">Drag and drop photos or videos of your moving trucks here to let the AI feature them in future marketing broadcasts.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {assets.map((asset: any) => (
                <div key={asset.key} className="group relative aspect-square bg-neutral-900 border border-neutral-800 rounded-2xl overflow-hidden hover:border-neutral-600 transition-colors shadow-lg">
                  <img 
                    src={asset.url} 
                    alt={asset.key}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                  
                  {/* Overlay shadow for text legibility */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/20 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-between p-3">
                    <div className="flex justify-end">
                      <button 
                        onClick={() => deleteAsset(asset.key)}
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
