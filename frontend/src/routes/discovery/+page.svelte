<script lang="ts">
    import { Flame, Activity, Hash, Eye, Trophy, ArrowUpRight, Crown, TrendingUp } from 'lucide-svelte';
    import { searchStore } from '$lib/stores';
    import { getGradient } from '$lib/logic';

    // --- 1. HERO DATA (The Zeitgeist) ---
    const HERO_FILM = {
        title: "Mid90s",
        director: "Jonah Hill",
        year: 2018,
        tag: "Nostalgic & Gritty",
        votes: 1420,
        gradient: "from-yellow-900 to-orange-900"
    };

    // --- 2. TRENDING SCROLL DATA ---
    const TRENDING_VIBES = [
        { label: "Liminal Spaces", count: "2.4k", trend: "+12%" },
        { label: "Neon Noir", count: "1.8k", trend: "+8%" },
        { label: "Female Rage", count: "1.5k", trend: "+5%" },
        { label: "Slow Cinema", count: "1.2k", trend: "+2%" },
        { label: "Gothic Horror", count: "0.8k", trend: "+1%" },
        { label: "Whodunnit", count: "0.7k", trend: "+4%" },
    ];

    // --- 3. LIVE FEED DATA ---
    const LIVE_ACTIVITY = [
        { user: "mark_aaron", action: "tagged", movie: "Inception", tag: "Mind-Melting", time: "2m" },
        { user: "cinephile_99", action: "voted", movie: "Heat", tag: "Sigma Grindset", time: "5m" },
        { user: "sarah_j", action: "tagged", movie: "Her", tag: "Lonely", time: "12m" },
        { user: "guest_user", action: "voted", movie: "Aftersun", tag: "Emotional Damage", time: "15m" },
    ];

    // --- 4. TOP RATED BY TAG (Your Request) ---
    const TOP_RATED = [
        { title: "Blade Runner 2049", score: 98, tag: "Neon Noir" },
        { title: "The Truman Show", score: 96, tag: "Liminal" },
        { title: "Lady Bird", score: 94, tag: "Coming of Age" },
        { title: "Hereditary", score: 92, tag: "Gothic Horror" }
    ];

    function handleTagClick(tag: string) {
        searchStore.performSearch(tag);
    }
</script>

<div class="w-full min-h-screen pb-32 px-6 pt-10 max-w-7xl mx-auto">
    
    <div class="flex items-center justify-between mb-8">
        <div class="flex items-center gap-3">
            <div class="p-2.5 bg-[#111] border border-white/10 rounded-xl">
                <Flame class="w-5 h-5 text-orange-500" />
            </div>
            <div>
                <h1 class="text-2xl font-bold text-white tracking-tight">Discovery</h1>
                <p class="text-xs text-neutral-500">The pulse of the ecosystem.</p>
            </div>
        </div>
    </div>

    <div class="relative w-full aspect-2/1 md:aspect-3/1 rounded-3xl overflow-hidden border border-white/10 group cursor-pointer mb-12">
        <div class="absolute inset-0 bg-neutral-900">
             <div class="w-full h-full bg-linear-to-br {HERO_FILM.gradient} opacity-60"></div>
        </div>
        <div class="absolute inset-0 bg-linear-to-t from-black via-black/40 to-transparent"></div>

        <div class="absolute bottom-0 left-0 p-6 md:p-10 w-full flex items-end justify-between">
            <div>
                <div class="flex items-center gap-2 mb-3">
                    <span class="flex items-center gap-1.5 px-2 py-1 rounded bg-yellow-500/20 border border-yellow-500/20 text-[10px] font-bold text-yellow-400 uppercase tracking-widest">
                        <Crown class="w-3 h-3" /> Most Voted '90s'
                    </span>
                </div>
                <h2 class="text-4xl md:text-5xl font-bold text-white mb-2 tracking-tighter">{HERO_FILM.title}</h2>
                <p class="text-neutral-300 text-sm font-light">Director: {HERO_FILM.director} • {HERO_FILM.year}</p>
            </div>
            
            <div class="hidden md:block text-right">
                <div class="text-3xl font-mono font-bold text-white">{HERO_FILM.votes}</div>
                <div class="text-[10px] text-neutral-500 uppercase tracking-widest">Community Votes</div>
            </div>
        </div>
    </div>

    <div class="mb-12">
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-xs font-bold text-neutral-400 uppercase tracking-widest flex items-center gap-2">
                <TrendingUp class="w-4 h-4" /> Trending Vibes
            </h3>
            <span class="text-[10px] text-neutral-600 hidden md:inline">Scroll -></span>
        </div>

        <div class="flex gap-3 overflow-x-auto pb-4 snap-x snap-mandatory scrollbar-hide" style="scrollbar-width: none;">
            {#each TRENDING_VIBES as item}
                <button 
                    on:click={() => handleTagClick(item.label)}
                    class="snap-start shrink-0 px-4 py-3 rounded-xl bg-[#0e0e0e] border border-white/10 hover:border-white/30 hover:bg-[#141414] transition-colors flex flex-col min-w-[140px] group cursor-pointer text-left"
                >
                    <span class="text-sm font-bold text-white mb-1">{item.label}</span>
                    <div class="flex items-center gap-2 text-[10px]">
                        <span class="text-neutral-500">{item.count}</span>
                        <span class="text-emerald-500 flex items-center gap-0.5">
                            <ArrowUpRight class="w-2.5 h-2.5" /> {item.trend}
                        </span>
                    </div>
                </button>
            {/each}
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-16">
        
        <div class="lg:col-span-2 p-6 rounded-3xl bg-[#0e0e0e] border border-white/5 relative overflow-hidden">
            <div class="flex items-center justify-between mb-6 relative z-10">
                <h3 class="text-xs font-bold text-neutral-400 uppercase tracking-widest flex items-center gap-2">
                    <Hash class="w-4 h-4" /> Community Signals
                </h3>
            </div>
            
            <div class="flex flex-wrap gap-x-5 gap-y-3 relative z-10">
                {#each ['Existential', 'Neon', 'Lonely', 'Dreamy', 'Brutalism', 'Love', '80s', 'Synth', 'Quiet', 'Rain', 'Subway'] as word, i}
                    <button 
                         on:click={() => handleTagClick(word)}
                         class="text-neutral-500 hover:text-white transition-colors cursor-pointer font-light"
                         style="font-size: {Math.max(0.8, 1.8 - i * 0.12)}rem; opacity: {Math.max(0.4, 1 - i * 0.05)}"
                    >
                        #{word}
                    </button>
                {/each}
            </div>
            
            <div class="absolute -right-10 -bottom-10 w-40 h-40 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
        </div>
        
        <div class="lg:col-span-1 p-6 rounded-3xl bg-[#0e0e0e] border border-white/5 h-full min-h-[300px]">
            <h3 class="text-xs font-bold text-neutral-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> Live Feed
            </h3>
            
            <div class="space-y-6 relative">
                <div class="absolute left-1.5 top-2 bottom-2 w-px bg-white/5"></div>

                {#each LIVE_ACTIVITY as log}
                    <div class="relative pl-6 group">
                        <div class="absolute left-0 top-1.5 w-3 h-3 rounded-full bg-[#0e0e0e] border border-white/10 z-10 group-hover:border-emerald-500/50 transition-colors">
                            <div class="absolute inset-0.5 bg-white/20 rounded-full"></div>
                        </div>
                        
                        <p class="text-xs text-neutral-400 leading-relaxed font-mono">
                            <span class="text-indigo-400">{log.user}</span> 
                            <span class="text-neutral-600">{log.action}</span> 
                            <span class="text-white">"{log.tag}"</span>
                        </p>
                        <div class="flex items-center gap-2 mt-1">
                            <span class="text-[9px] text-neutral-600">{log.time} ago</span>
                            <span class="text-[9px] text-neutral-700">•</span>
                            <span class="text-[9px] text-neutral-500">{log.movie}</span>
                        </div>
                    </div>
                {/each}
            </div>
        </div>
    </div>

    <div class="mb-8">
        <div class="flex items-center justify-between mb-6">
            <h3 class="text-xs font-bold text-neutral-400 uppercase tracking-widest flex items-center gap-2">
                <Trophy class="w-4 h-4" /> Top Rated in Tags
            </h3>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {#each TOP_RATED as film, i}
                <div class="p-4 rounded-2xl bg-[#0e0e0e] border border-white/5 flex items-center gap-4 hover:border-white/10 transition-colors group cursor-pointer">
                    <div class="text-xl font-bold text-white/10 font-mono group-hover:text-white/30 transition-colors">0{i+1}</div>
                    <div>
                        <h4 class="text-sm font-bold text-white leading-tight">{film.title}</h4>
                        <div class="flex items-center gap-2 mt-1">
                            <span class="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-neutral-400 border border-white/5">{film.tag}</span>
                            <span class="text-[10px] text-emerald-400 font-bold">{film.score}%</span>
                        </div>
                    </div>
                </div>
            {/each}
        </div>
    </div>
</div>

<style>
    .scrollbar-hide::-webkit-scrollbar {
        display: none;
    }
</style>