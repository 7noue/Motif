import { User, Zap, Feather, AlertTriangle } from 'lucide-svelte';

export interface ApiMovie {
    tmdb_id?: number | null; // Allow null
    title: string;
    year: number;     
    confidence_score: number;
    overview?: string;
    runtime?: number;
    director?: string;
    cast?: string; 
    poster_url?: string;
    trailer_url?: string;
    certification?: string;
    primary_aesthetic?: string;
    fit_quote?: string;
    tone_label?: string;
    vibe_signature_label?: string;
    vibe_signature_val?: number;
    palette?: { name: string; colors: string[] };
    is_unverified?: boolean; // New flag from backend
}

export interface EnrichedMovie extends ApiMovie {
    movie_id: number; 
    score: number;    
    runtimeStr: string;
    posterUrl: string | null;
    trailerUrl: string | null;
    vibeDynamics: { [key: string]: any };
    momentSentence: string;
    socialBadges: { text: string; icon: any }[];
    initialTags: any[];
    recommendations: any[];
    certData: { code: string; reason: string };
    isUnverified: boolean; // Clean flag for UI
}

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
        'from-rose-900 to-orange-900', 'from-violet-900 to-indigo-950',
        'from-emerald-900 to-teal-950', 'from-blue-900 to-cyan-950', 
        'from-amber-900 to-yellow-950',
    ];
    return colors[Math.floor(pseudoRandom(title) * colors.length)];
}

export const enrichMovieData = (apiMovie: ApiMovie): EnrichedMovie => {
    const seed = (apiMovie.title || 'Unknown');
    const r = (offset = 0) => pseudoRandom(seed + offset);

    // Vibe Dynamics
    const baseVal = apiMovie.vibe_signature_val || Math.floor(r() * 100);
    const vibeDynamics = {
        pacing: { label: "Pacing", val: baseVal, low: "Slow", high: "Fast" },
        complexity: { label: "Cognitive Load", val: Math.floor(r(1) * 100), low: "Light", high: "Heavy" },
        atmosphere: { label: "Mood", val: Math.floor(r(2) * 100), low: "Dark", high: "Bright" }
    };

    // Social Badges
    const socialBadges = [];
    if (apiMovie.is_unverified) {
        socialBadges.push({ text: "Unverified", icon: AlertTriangle });
    } else {
        if (apiMovie.certification) socialBadges.push({ text: apiMovie.certification, icon: User });
        if (apiMovie.tone_label) socialBadges.push({ text: apiMovie.tone_label, icon: Zap });
    }
    if (socialBadges.length === 0) socialBadges.push({ text: "Immersive", icon: Feather });

    const castArray = typeof apiMovie.cast === 'string' ? apiMovie.cast.split(',').slice(0, 3) : [];

    return {
        ...apiMovie,
        
        // --- ID HANDLING ---
        // If unverified, we use a negative hash just for React keys, 
        // but we FLAG it so we never save it to DB.
        movie_id: apiMovie.tmdb_id 
            ? apiMovie.tmdb_id 
            : Math.floor(Math.random() * 1000000) * -1,
        isUnverified: !!apiMovie.is_unverified,
        score: (apiMovie.confidence_score || 0) / 100,
        year: apiMovie.year,
        runtimeStr: apiMovie.runtime ? `${apiMovie.runtime} min` : "Unknown",
        posterUrl: apiMovie.poster_url || null,
        trailerUrl: apiMovie.trailer_url || null,
        
        vibeDynamics,
        momentSentence: apiMovie.fit_quote || "Suggested by the neural engine.",
        palette: apiMovie.palette || { name: "Mystery", colors: ["#171717", "#262626", "#404040"] },
        socialBadges,
        initialTags: [
            ...(apiMovie.primary_aesthetic ? [{ name: apiMovie.primary_aesthetic, score: 90, userVoted: false, isCustom: false }] : []),
            ...(castArray.map(actor => ({ name: actor.trim(), score: 60, userVoted: false, isCustom: false })))
        ],
        recommendations: [],
        certData: { code: apiMovie.certification || "NR", reason: "" }
    };
};