<script lang="ts">
    import { Flame, Trophy, Activity, Hash, ArrowUpRight, Crown } from 'lucide-svelte';
    import { searchStore } from '$lib/stores';
    import { getGradient } from '$lib/logic';

    // --- MOCK DATA: HALL OF FAME ---
    // In production, this comes from: SELECT movie_id, COUNT(tag) as count FROM tags GROUP BY movie_id
    const HALL_OF_FAME = [
        { label: "Most '90s' Film", title: "Mid90s", count: 1420, icon: Crown, color: "text-yellow-400", border: "border-yellow-500/50" },
        { label: "Ultimate 'Neon Noir'", title: "Blade Runner 2049", count: 980, icon: Trophy, color: "text-fuchsia-400", border: "border-fuchsia-500/50" },
        { label: "King of 'Liminal'", title: "The Truman Show", count: 850, icon: Hash, color: "text-emerald-400", border: "border-emerald-500/50" }
    ];

    // --- MOCK DATA: LIVE FEED ---
    // Simulates users tagging things in real-time
    const LIVE_ACTIVITY = [
        { user: "mark_aaron", action: "tagged", movie: "Inception", tag: "Mind-Melting", time: "2m ago" },
        { user: "cinephile_99", action: "voted", movie: "Heat", tag: "Sigma Grindset", time: "5m ago" },
        { user: "sarah_j", action: "tagged", movie: "Her", tag: "Lonely", time: "12m ago" },
        { user: "guest_user", action: "voted", movie: "Aftersun", tag: "Emotional Damage", time: "15m ago" },
    ];

    const TRENDING_VIBES = [
        { label: "Dad Approved", count: "3.2k", trend: "+12%" },
        { label: "Female Rage", count: "2.1k", trend: "+8%" },
        { label: "Gothic Horror", count: "1.5k", trend: "+5%" },
        { label: "Sunday Scaries", count: "900", trend: "+2%" },
    ];

    function handleTagClick(tag: string) {
        searchStore.performSearch(tag);
    }
</script>

<div class="w-full min-h-screen pb-32 px-6 pt-8 max-w-7xl mx-auto">
    
    <div class="flex items-center gap-3 mb-10">
        <div class="p-2 bg-[#111] border border-white/10 rounded-xl">
            <Activity class="w-5 h-5 text-indigo-500" />
        </div>
        <div>
            <h1 class="text-3xl font-bold text-white tracking-tight">Community Pulse</h1>
            <p class="text-xs text-neutral-500">Live data from the Motif ecosystem</p>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
        
        <div class="lg:col-span-2 space-y-6">
            <h3 class="text-sm font-bold text-neutral-400 uppercase tracking-widest flex items-center gap-2">
                <Trophy class="w-4 h-4 text-yellow-500" /> Hall of Fame
            </h3>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                {#each HALL_OF_FAME as item}
                    <button 
                        on:click={() => searchStore.performSearch(item.title)}
                        class="relative p-5 rounded-2xl bg-[#0e0e0e] border {item.border} hover:bg-[#141414] transition-colors text-left group overflow-hidden"
                    >
                        <div class="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                        <div class="flex items-start justify-between mb-4 relative z-10">
                            <svelte:component this={item.icon} class="w-5 h-5 {item.color}" />
                            <span class="text-[10px] font-mono text-neutral-500">{item.count} votes</span>
                        </div>
                        <div class="relative z-10">
                            <p class="text-[10px] text-neutral-400 uppercase tracking-widest mb-1">{item.label}</p>
                            <h4 class="text-lg font-bold text-white leading-tight">{item.title}</h4>
                        </div>
                    </button>
                {/each}
            </div>

            <div class="pt-8">
                <h3 class="text-sm font-bold text-neutral-400 uppercase tracking-widest flex items-center gap-2 mb-4">
                    <Flame class="w-4 h-4 text-orange-500" /> Trending Vibes
                </h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {#each TRENDING_VIBES as vibe}
                        <button 
                            on:click={() => handleTagClick(vibe.label)}
                            class="p-3 rounded-xl bg-[#111] border border-white/10 hover:border-white/30 text-left transition-colors"
                        >
                            <div class="text-sm font-bold text-white mb-1">{vibe.label}</div>
                            <div class="flex items-center gap-2 text-[10px] text-neutral-500">
                                <span>{vibe.count}</span>
                                <span class="text-emerald-500">{vibe.trend}</span>
                            </div>
                        </button>
                    {/each}
                </div>
            </div>
        </div>

        <div class="lg:col-span-1">
            <div class="bg-[#0e0e0e] border border-white/5 rounded-3xl p-6 h-full min-h-[400px]">
                <h3 class="text-sm font-bold text-neutral-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Live Activity
                </h3>
                
                <div class="space-y-6 relative">
                    <div class="absolute left-1.5 top-2 bottom-2 w-px bg-white/5"></div>

                    {#each LIVE_ACTIVITY as log}
                        <div class="relative pl-6">
                            <div class="absolute left-0 top-1.5 w-3 h-3 rounded-full bg-[#111] border border-white/10 z-10"></div>
                            <p class="text-xs text-neutral-300 leading-relaxed">
                                <span class="text-indigo-400 font-bold">{log.user}</span> 
                                <span class="text-neutral-500">{log.action}</span> 
                                <span class="text-white font-medium">"{log.tag}"</span> 
                                <span class="text-neutral-500">on</span> 
                                <span class="text-white font-medium">{log.movie}</span>
                            </p>
                            <span class="text-[10px] text-neutral-600 font-mono mt-1 block">{log.time}</span>
                        </div>
                    {/each}
                    
                    <div class="pt-4 text-center">
                        <span class="text-[10px] text-neutral-700 uppercase tracking-widest">End of recent stream</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>