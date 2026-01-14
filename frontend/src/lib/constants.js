// src/lib/constants.ts
import { Brain, Zap, Gauge, Users, ShieldCheck, Heart, Beer, User, Sofa, Moon, Coffee, Cloud, Sparkles } from 'lucide-svelte';

export const API_URL = 'http://localhost:8000/api/search';

export const CONTEXT_OPTIONS = {
    social: [
        { id: 'parents', label: 'With Parents', icon: ShieldCheck }, 
        { id: 'date', label: 'Date Night', icon: Heart },
        { id: 'group', label: 'Drinking/Party', icon: Beer }, 
        { id: 'solo', label: 'Solo Watch', icon: User }
    ],
    mood: [
        { id: 'hype', label: 'High Energy', icon: Zap },
        { id: 'chill', label: 'Chill', icon: Sofa }, 
        { id: 'deep', label: 'Deep', icon: Moon }
    ]
};

export const VIBES = [
    { label: "Cyberpunk", icon: Zap },
    { label: "Cozy", icon: Coffee },
    { label: "Rainy", icon: Cloud },
    { label: "Melancholic", icon: Moon },
    { label: "Dreamy", icon: Sparkles },
];

export const LANDING_STATS = [
    { label: "Films Indexed", value: "42.8K", trend: "+12%" },
    { label: "Vibe Accuracy", value: "94%", trend: "Match Rate" },
    { label: "Active Users", value: "18.2K", trend: "+24%" }
];

export const LANDING_FEATURES = [
    { icon: Brain, title: "Semantic Search", desc: "Find films by mood, not just keywords" },
    { icon: Zap, title: "Context-Aware", desc: "Recommendations adapt to your situation" },
    { icon: Gauge, title: "Vibe Analysis", desc: "Understand a film's energy before watching" },
    { icon: Users, title: "Social Curation", desc: "Collective tagging builds better suggestions" }
];