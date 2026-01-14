import { User } from 'lucide-svelte';

// --- Type Definitions ---
export interface ApiMovie {
    movie_id: number;
    title: string;
    overview: string;
    release_date?: string;
    score?: number;
    runtime?: string;
    posterUrl?: string;
    vibe_pacing?: number;
    vibe_complexity?: number;
    vibe_atmosphere?: number;
    genres?: string[];
    certData?: { code: string; reason: string };
    cast?: string[];
    director?: string;
    original_language?: string;
    trailerUrl?: string;
    popularity?: number;
}

export interface EnrichedMovie extends ApiMovie {
    year: string;
    score: number;
    runtime: string;
    posterUrl: string | null;
    vibeDynamics: {
        [key: string]: { label: string; val: number; low: string; high: string; }
    };
    momentSentence: string;
    palette: { name: string; colors: string[] };
    socialBadges: { text: string; icon: any }[];
    initialTags: { name: string; score: number; userVoted: boolean; isCustom: boolean }[];
    recommendations: any[];
}

// --- Logic ---

export function pseudoRandom(str: string | null): number {
    let hash = 0;
    if (!str) return 0.5;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = (hash << 5) - hash + char;
        hash = hash & hash; 
    }
    return Math.abs(hash) / 2147483647;
}

export function getGradient(title: string): string {
    const colors = [
        'from-rose-500 to-orange-600', 'from-violet-600 to-indigo-900',
        'from-emerald-500 to-teal-900', 'from-blue-600 to-cyan-800', 
        'from-amber-700 to-yellow-600',
    ];
    return colors[Math.floor(pseudoRandom(title) * colors.length)];
}

export const enrichMovieData = (apiMovie: ApiMovie): EnrichedMovie => {
    const seed = apiMovie.title + apiMovie.movie_id;
    const r = (offset = 0) => pseudoRandom(seed + offset);

    const vibeDynamics = {
        pacing: { label: "Pacing", val: apiMovie.vibe_pacing || 50, low: "Slow", high: "Fast" },
        complexity: { label: "Cognitive Load", val: apiMovie.vibe_complexity || 50, low: "Light", high: "Heavy" },
        atmosphere: { label: "Mood", val: apiMovie.vibe_atmosphere || 50, low: "Dark", high: "Bright" }
    };

    const contextPitches = [
        "Perfect for when you want to feel smart but don't want to work for it.",
        "The visual equivalent of a double espresso.",
        "Slow, methodical, and deeply rewarding.",
        "Zero cognitive load. Just vibes.",
        "A cinematic warm hug."
    ];
    
    const palettes = [
        { name: "Neon Noir", colors: ["#f43f5e", "#8b5cf6", "#1e293b"] },
        { name: "Industrial", colors: ["#94a3b8", "#475569", "#0f172a"] },
        { name: "Warm Retro", colors: ["#f59e0b", "#78350f", "#fffbeb"] },
        { name: "Miami Sunset", colors: ["#f97316", "#db2777", "#8b5cf6"] },
    ];

    const socialBadges = [{ text: "Immersive", icon: User }]; 

    const initialTags = (apiMovie.genres || []).map(name => ({
        name, 
        score: Math.floor(r(name) * 50) + 1, 
        userVoted: false, 
        isCustom: false 
    }));

    return {
        ...apiMovie,
        year: apiMovie.release_date || 'N/A',
        score: apiMovie.score || 0,
        runtime: apiMovie.runtime || "Unknown",
        posterUrl: apiMovie.posterUrl || null,
        vibeDynamics,
        momentSentence: contextPitches[Math.floor(r(1) * contextPitches.length)],
        palette: palettes[Math.floor(r(5) * palettes.length)],
        socialBadges,
        initialTags,
        certData: apiMovie.certData || { code: "NR", reason: "Not Rated" },
        director: apiMovie.director || "Unknown", 
        cast: apiMovie.cast || [],
        recommendations: [] 
    };
};