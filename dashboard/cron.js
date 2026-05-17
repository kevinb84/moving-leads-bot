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

async function getBrandKnowledge() {
    try {
        const { data, error } = await insforge.database
            .from('moving_leads')
            .select('raw_text')
            .eq('customer_name', 'BRAND_KNOWLEDGE')
            .single();
        
        if (error) throw error;
        return data.raw_text;
    } catch (e) {
        console.warn("[BRAIN] Could not fetch cloud brand knowledge, falling back to local/generic...");
        return "";
    }
}

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
        let brandKnowledge = await getBrandKnowledge();
        if (!brandKnowledge) {
            // Fallback to local
            const knowledgePath = path.resolve(__dirname, 'brand_knowledge.txt');
            try {
                brandKnowledge = fs.readFileSync(knowledgePath, 'utf-8');
                console.log("[BRAIN] Successfully read the brand_knowledge.txt file!");
            } catch(e) {
                console.warn("[BRAIN] Missing brand_knowledge.txt file, running on generic internal defaults...");
            }
        } else {
            console.log("[BRAIN] Successfully fetched brand knowledge from cloud database!");
        }

        // 1. Roll a dice to decide the marketing angle
        const angles = [
            `Stress-Free Moving: Focus on handling relocation from start to finish so customers can relax.`,
            `Residential Move: Helping families relocate smoothly with care and efficiency.`,
            `Business Relocation: Minimizing downtime for office moves with organized equipment handling.`,
            `Quick & Reliable Service: Fast relocation without compromising safety.`,
            `Heavy Lifting Done Right: Safely moving everything from furniture to equipment.`,
            `Trust & Care: Treating belongings like our own with professionalism.`,
            `Packing Services: Full packing/unpacking services for an effortless move.`,
            `Local Moves: Specializing in fast and affordable local relocations.`,
            `Customer Experience: Celebrating happy customer success stories.`,
            `Strong Call-To-Action: Professional movers, affordable rates, reliable service.`
        ];
        const angle = angles[Math.floor(Math.random() * angles.length)];
        
        // 2. Draft the Post Copy using GPT-4o-mini
        console.log("[BRAIN] Drafting post copy...");
        const chatReq = await openai.chat.completions.create({
            model: 'gpt-4o-mini',
            temperature: 0.8,
            messages: [
            {
                role: 'system',
                content: `You are QuickMove Solutions' elite Social Media Director. \n\nREAD THE APPROVED TEMPLATES IN THE BRAND KNOWLEDGE BASE:\n${brandKnowledge}\n\nSTRICT RULES:\n1. Your task is to write a unique post starting from one of the 10 APPROVED TEMPLATES.\n2. Do NOT use corporate jargon like "elevate your business".\n3. Maintain the Friendly, Professional tone of the templates.\n4. Keep it under 3 to 4 sentences, use 2-4 emojis.\n5. Always include the CTA with website and phone number.`
            },
            {
                role: 'user', 
                content: `Write a unique advertising post for ${BRAND.name} based on the angle: ${angle}. Follow the structure of the corresponding template in the Brand Knowledge but make it feel fresh.`
            }]
        });
        const postCopy = chatReq.choices[0].message.content;
        console.log("[BRAIN] Drafted Copy:", postCopy);

        // 3. ZERO-WASTE PROTECTION: We no longer generate images in the cron.
        // We set the image to "AUTO" so the live worker only spends tokens
        // if the Facebook post box is successfully opened!
        const finalImageUrl = "AUTO";
        console.log("[BRAIN] Strategy: Zero-Waste 'AUTO' image requested for the Python Worker.");
        
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
    console.log("🤖 [BRAIN] Detected GitHub Actions Environment. Marketing is currently DISABLED.");
    // generateAIAd(); // DISABLED PER USER REQUEST
} else {
    console.log("🤖 [BRAIN] Core initialized and running securely in local loop.");
    console.log("⏰ [BRAIN] Marketing Broadcasts are currently DISABLED PER USER REQUEST.");

    // Run at 9:00 AM and 3:00 PM
    /*
    cron.schedule('0 9,15 * * *', () => {
        generateAIAd();
    });
    */
}
