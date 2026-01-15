<script lang="ts">
    import { Play, Settings, Heart, Bookmark, Tag, User } from 'lucide-svelte';
    import { currentUser } from '$lib/stores';
    import VibeRadar from '$lib/components/profile/VibeRadar.svelte'; // Ensure you created this file!
    import { getGradient } from '$lib/logic';

    // --- MOCK USER DATA ---
    const USER_STATS = {
        Melancholy: 85,
        Adrenaline: 40,
        Intellectual: 90,
        Wholesome: 30,
        Surreal: 75,
        Romantic: 20
    };

    const WATCHLIST = [
        { title: "Solaris", year: 1972 },
        { title: "Perfect Blue", year: 1997 },
        { title: "Burning", year: 2018 },
        { title: "The Lighthouse", year: 2019 }
    ];

    let activeTab = 'hearts'; // 'hearts' | 'watchlist' | 'tags'
</script>

<div class="w-full min-h-screen pb-32 px-6 pt-12 max-w-5xl mx-auto">

    <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-12">
        <div class="flex items-center gap-6">
            <div class="w-20 h-20 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 border-2 border-white/10 shadow-2xl"></div>
            <div>
                <h1 class="text-3xl font-bold text-white tracking-tight">{$currentUser?.name || 'Mark Aaron'}</h1>
                <p class="text-sm text-neutral-400">"Films for 3AM existential crises."</p>
                <div class="flex gap-3 mt-3">
                    <span class="px-2 py-1 rounded bg-white/5 border border-white/5 text-[10px] uppercase text-neutral-400">Level 4 Curator</span>
                    <span class="px-2 py-1 rounded bg-white/5 border border-white/5 text-[10px] uppercase text-neutral-400">CS Student</span>
                </div>
            </div>
        </div>
        <button class="p-2 rounded-full bg-[#111] border border-white/10 hover:bg-[#222] transition-colors">
            <Settings class="w-5 h-5 text-neutral-400" />
        </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
        
        <div class="md:col-span-1">
            <VibeRadar stats={USER_STATS} />
        </div>

        <div class="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="p-6 rounded-3xl bg-[#0e0e0e] border border-white/5 flex flex-col justify-center">
                <h3 class="text-xs font-bold text-neutral-500 uppercase tracking-widest mb-1">Top Vibe</h3>
                <p class="text-2xl font-bold text-white mb-2">Melancholic & Surreal</p>
                <p class="text-xs text-neutral-400 leading-relaxed">
                    You gravitate towards films that question reality. Your watching peaks on 
                    <span class="text-indigo-400">Friday nights</span>.
                </p>
            </div>
            
            <div class="p-6 rounded-3xl bg-[#0e0e0e] border border-white/5 flex flex-col justify-center">
                <h3 class="text-xs font-bold text-neutral-500 uppercase tracking-widest mb-1">Contribution</h3>
                <div class="flex items-baseline gap-1 mb-2">
                    <span class="text-3xl font-bold text-white">42</span>
                    <span class="text-sm text-neutral-500">tags added</span>
                </div>
                <div class="w-full bg-[#1a1a1a] h-1.5 rounded-full overflow-hidden">
                    <div class="bg-emerald-500 h-full w-[70%]"></div>
                </div>
                <p class="text-[10px] text-neutral-500 mt-2">Top 15% of contributors</p>
            </div>
        </div>
    </div>

    <div>
        <div class="flex items-center gap-6 border-b border-white/5 mb-8">
            <button 
                on:click={() => activeTab = 'hearts'}
                class="pb-4 text-sm font-medium transition-colors border-b-2 {activeTab === 'hearts' ? 'text-white border-indigo-500' : 'text-neutral-500 border-transparent hover:text-neutral-300'}"
            >
                <Heart class="w-4 h-4 inline mr-2" /> Hearts
            </button>
            <button 
                on:click={() => activeTab = 'watchlist'}
                class="pb-4 text-sm font-medium transition-colors border-b-2 {activeTab === 'watchlist' ? 'text-white border-indigo-500' : 'text-neutral-500 border-transparent hover:text-neutral-300'}"
            >
                <Bookmark class="w-4 h-4 inline mr-2" /> Watchlist
            </button>
            <button 
                on:click={() => activeTab = 'tags'}
                class="pb-4 text-sm font-medium transition-colors border-b-2 {activeTab === 'tags' ? 'text-white border-indigo-500' : 'text-neutral-500 border-transparent hover:text-neutral-300'}"
            >
                <Tag class="w-4 h-4 inline mr-2" /> My Tags
            </button>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4" style="content-visibility: auto;">
            {#if activeTab === 'hearts' || activeTab === 'watchlist'}
                {#each WATCHLIST as movie}
                    <div class="group relative aspect-[2/3] rounded-xl overflow-hidden bg-[#111] border border-white/5 cursor-pointer">
                        <div class="absolute inset-0 bg-gradient-to-br {getGradient(movie.title)} opacity-40 group-hover:opacity-60 transition-opacity"></div>
                        <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                             <Play class="w-8 h-8 text-white fill-white" />
                        </div>
                        <div class="absolute bottom-0 left-0 w-full p-3 bg-gradient-to-t from-black/90 to-transparent">
                            <p class="text-sm font-bold text-white truncate">{movie.title}</p>
                            <p class="text-[10px] text-neutral-400">{movie.year}</p>
                        </div>
                    </div>
                {/each}
                {#each Array(4) as _}
                    <div class="aspect-[2/3] rounded-xl border border-dashed border-white/5 flex items-center justify-center">
                        <span class="text-xs text-neutral-700">Add more</span>
                    </div>
                {/each}
            {:else}
                <div class="col-span-full py-12 text-center text-neutral-500">
                    <p>Your contribution history will appear here.</p>
                </div>
            {/if}
        </div>
    </div>
</div>