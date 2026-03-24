import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import { createClient } from '@insforge/sdk';
import OpenAI from 'openai';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load the dashboard .env for InsForge keys
dotenv.config({ path: path.resolve(__dirname, './.env') });
// Load the root .env for OpenAI keys
dotenv.config({ 
    path: path.resolve(__dirname, '../.env'),
    override: true 
});

// Initialize InsForge client
const insforge = createClient({
  baseUrl: process.env.VITE_INSFORGE_BASE_URL || 'https://58izx8nr.us-east.insforge.app',
  anonKey: process.env.VITE_INSFORGE_ANON_KEY
});

import cron from 'node-cron';

// Initialize OpenAI client
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});

import fs from 'fs';

// Brand Identity Configuration
const BRAND = {
    name: "QuickMove Solutions",
    locations: "Calgary, Edmonton, Strathmore",
    website: "https://quickmovesolution.com", 
    colors: ["Vibrant Orange", "Black", "White"],
};

async function generateAIAd() {
    console.log(`\n--- [BRAIN] Generating AI Image and Copy for ${BRAND.name} ---`);
    try {
        // Load the external Business Knowledge document
        const knowledgePath = path.resolve(__dirname, 'brand_knowledge.txt');
        let brandKnowledge = "";
        try {
            brandKnowledge = fs.readFileSync(knowledgePath, 'utf-8');
            console.log("[BRAIN] Successfully read the brand_knowledge.txt file!");
        } catch(e) {
            console.warn("[BRAIN] Missing brand_knowledge.txt file, running on generic internal defaults...");
        }

        // 1. Roll a dice to decide the marketing angle
        const angles = [
            `Highlight our expertise in moving delicate items like Pianos and Artwork.`,
            `Focus on our stress-free residential moving services.`,
            `Emphasize our corporate office relocation efficiency.`,
            `Promote our fast packing and wrapping services.`
        ];
        const angle = angles[Math.floor(Math.random() * angles.length)];
        
        // 2. Draft the Post Copy using GPT-4o-mini
        console.log("[BRAIN] Drafting post copy...");
        const chatReq = await openai.chat.completions.create({
            model: 'gpt-4o-mini',
            temperature: 0.9,
            messages: [
            {
                role: 'system',
                content: `You are QuickMove Solutions' elite Social Media Director. You are writing engaging, extremely persuasive marketing copy for Facebook.\n\nREAD THIS COMPREHENSIVE BRAND KNOWLEDGE BASE DO NOT HALLUCINATE OUTSIDE OF THIS:\n${brandKnowledge}\n\nCRITICAL RULE: DO NOT EVER start the post by saying "Hello Edmonton" or "Hello Calgary" or "Hello [City]". Make the first sentence a strong hook instead. Keep the post under 3 to 4 sentences, use 2-4 emojis appropriately.`
            },
            {
                role: 'user', 
                content: `Write a highly engaging, unique, non-repetitive Facebook post for ${BRAND.name}. The company operates in ${BRAND.locations}. Our core angle for today's advertising campaign is: ${angle}. Make sure it includes a CTA referencing our website or phone number.`
            }]
        });
        const postCopy = chatReq.choices[0].message.content;
        console.log("[BRAIN] Drafted Copy:", postCopy);

        // 3. Roll a dice: 50% chance to use a real "Memory Asset", 50% chance to AI Generate a graphic
        const useRealPhoto = Math.random() > 0.5;
        let finalImageUrl = null;
        
        if (useRealPhoto) {
            console.log("[BRAIN] Attempting to pick a real photo from Marketing Assets Vault...");
            const { data: assets } = await insforge.database.from('moving_leads').select('whatsapp_draft').eq('customer_name', 'ASSET_UPLOAD');
            if (assets && assets.length > 0) {
                const randomAsset = assets[Math.floor(Math.random() * assets.length)];
                finalImageUrl = randomAsset.whatsapp_draft;
                console.log("[BRAIN] Selected Vault Photo:", finalImageUrl);
            } else {
                console.log("[BRAIN] Vault empty! Falling back to AI Generation...");
            }
        }
        
        if (!finalImageUrl) {
            console.log("[BRAIN] Generating synthetic 3D Brand Image with DALL-E 3...");
            // Generate Image using Brand Colors
            const imgPrompt = `A premium, modern 3D render representing a moving and storage company. The central theme is a moving box or a delivery truck. The color palette must absolutely strictly use only ${BRAND.colors.join(", ")}. Highly detailed, cinematic lighting, corporate marketing style, clean background, 4k. No text.`;
            
            const imgReq = await openai.images.generate({
                model: 'dall-e-3',
                prompt: imgPrompt,
                size: '1024x1024'
            });
            
            const originalUrl = imgReq.data[0].url;
            console.log("[BRAIN] AI Image Generated via OpenAI! Bypassing local vault mapping...");
            
            finalImageUrl = originalUrl;
            console.log("[BRAIN] Temporary Synthetic Image URL prepared for Python Worker:", finalImageUrl);
        }
        
        // 4. Push the Job to the Python Worker Queue!
        console.log("[BRAIN] Pushing Broadcast Job to Queue...");
        const { error: dbError } = await insforge.database.from('moving_leads').insert([{
            customer_name: 'MARKETING_BROADCAST_PENDING',
            source_url: `cron_generated_${Date.now()}`,
            raw_text: postCopy,
            is_moving_lead: false,
            whatsapp_draft: finalImageUrl, // Hack: Storing the image URL in whatsapp_draft so python can read it!
            text_hash: `hash_${Date.now()}`
        }]);
        
        if (dbError) throw dbError;
        console.log("[BRAIN] Job queued successfully! The Python worker will handle it.");
        console.log("--- [BRAIN] Cycle complete. Going back to sleep. ---");
    } catch (err) {
        console.error("[BRAIN] Fatal Error during generation:", err.message);
    }
}

// Start the daily Cron scheduler based on environment
if (process.env.GITHUB_ACTIONS) {
    console.log("🤖 [BRAIN] Detected GitHub Actions Environment. Generating 1 marketing broadcast and exiting.");
    generateAIAd();
} else {
    console.log("🤖 [BRAIN] Core initialized and running securely in local loop.");
    console.log("⏰ [BRAIN] Scheduled to generate and push exactly 1 marketing broadcast every day at 9:00 AM.");

    cron.schedule('0 9 * * *', () => {
        generateAIAd();
    });
}
