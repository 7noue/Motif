<script lang="ts">
    import { Settings, Heart, Bookmark, Tag, Trophy, Activity, Clock, Play, Award, Zap } from 'lucide-svelte';
    import { currentUser } from '$lib/stores';
    import VibeRadar from '$lib/components/profile/VibeRadar.svelte'; 
    import { getGradient } from '$lib/logic';

    // Mock Data
    const USER_STATS = { Melancholy: 85, Adrenaline: 40, Intellectual: 90, Wholesome: 30, Surreal: 75, Romantic: 20 };
    
    const WATCHLIST = [
        { title: "Solaris", year: 1972 },
        { title: "Perfect Blue", year: 1997 },
        { title: "Burning", year: 2018 },
        { title: "The Lighthouse", year: 2019 }
    ];

    // Mock activity: 0 = 12AM. High activity at night.
    const ACTIVITY_BARS = [10, 5, 2, 0, 0, 0, 5, 15, 30, 40, 50, 60, 40, 30, 20, 60, 80, 90, 100, 80, 60, 40, 30, 20];

    let activeTab = 'hearts'; 
</script>

<div class="w-full min-h-screen pb-32 px-6 pt-12 max-w-6xl mx-auto">

    <div class="flex items-center justify-between mb-8">
        <div class="flex items-center gap-4">
            <div class="w-16 h-16 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 border border-white/20 shadow-xl"></div>
            <div>
                <h1 class="text-2xl font-bold text-white tracking-tight">{$currentUser?.name || 'Mark Aaron'}</h1>
                <div class="flex items-center gap-2 text-xs text-neutral-400 mt-1">
                    <span class="px-1.5 py-0.5 rounded bg-white/5 border border-white/5">Lv. 4 Curator</span>
                    <span>•</span>
                    <span>"Films for 3AM existential crises."</span>
                </div>
            </div>
        </div>
        <button class="p-2 rounded-full bg-[#111] border border-white/10 hover:bg-[#222] transition-colors">
            <Settings class="w-5 h-5 text-neutral-400" />
        </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-12">
        
        <div class="lg:col-span-1 h-full min-h-[320px]">
            <VibeRadar stats={USER_STATS} />
        </div>

        <div class="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4 h-full">
            
            <div class="p-6 rounded-3xl bg-[#0e0e0e] border border-white/5 flex flex-col justify-between group hover:border-white/10 transition-colors">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <div class="flex items-center gap-2 text-[10px] uppercase tracking-widest text-indigo-400 font-bold mb-1">
                            <Clock class="w-3 h-3" /> Tagging Rhythm
                        </div>
                        <h3 class="text-lg font-bold text-white">The Night Owl</h3>
                    </div>
                    <div class="text-[10px] text-neutral-500 text-right">
                        Peak Flow<br><span class="text-white">11:00 PM</span>
                    </div>
                </div>

                <div class="flex items-end justify-between gap-1 h-24 w-full">
                    {#each ACTIVITY_BARS as height, i}
                        <div 
                            class="w-full bg-white/10 rounded-sm hover:bg-indigo-500 transition-colors duration-300"
                            style="height: {height}%; opacity: {0.3 + (height/200)}"
                            title="{height}% activity at {i}:00"
                        ></div>
                    {/each}
                </div>
                
                <p class="text-[10px] text-neutral-500 mt-3 border-t border-white/5 pt-3">
                    You tend to tag <span class="text-white">Psychological Thrillers</span> on Friday nights.
                </p>
            </div>

            <div class="p-6 rounded-3xl bg-[#0e0e0e] border border-white/5 flex flex-col justify-between group hover:border-white/10 transition-colors">
                <div>
                    <div class="flex items-center gap-2 text-[10px] uppercase tracking-widest text-emerald-400 font-bold mb-1">
                        <Trophy class="w-3 h-3" /> Ecosystem Impact
                    </div>
                    <div class="flex items-baseline gap-1.5">
                        <span class="text-3xl font-bold text-white">Top 15%</span>
                        <span class="text-xs text-neutral-500">of taggers</span>
                    </div>
                </div>

                <div class="mt-4">
                    <div class="flex justify-between text-[10px] text-neutral-400 mb-1">
                        <span>Level 4</span>
                        <span>Level 5</span>
                    </div>
                    <div class="w-full bg-[#1a1a1a] h-2 rounded-full overflow-hidden border border-white/5">
                        <div class="bg-gradient-to-r from-emerald-600 to-emerald-400 h-full w-[72%] shadow-[0_0_10px_rgba(16,185,129,0.3)]"></div>
                    </div>
                    <p class="text-[10px] text-neutral-600 mt-1">12 tags until next level</p>
                </div>

                <div class="flex gap-2 mt-4 pt-4 border-t border-white/5">
                    <div class="w-8 h-8 rounded-full bg-[#1a1a1a] border border-white/10 flex items-center justify-center text-yellow-500 hover:bg-white/5 transition-colors" title="Early Adopter">
                        <Award class="w-4 h-4" />
                    </div>
                    <div class="w-8 h-8 rounded-full bg-[#1a1a1a] border border-white/10 flex items-center justify-center text-rose-500 hover:bg-white/5 transition-colors" title="Genre Explorer">
                        <Activity class="w-4 h-4" />
                    </div>
                    <div class="w-8 h-8 rounded-full bg-[#1a1a1a] border border-white/10 flex items-center justify-center text-blue-500 hover:bg-white/5 transition-colors" title="Fast Tagger">
                        <Zap class="w-4 h-4" />
                    </div>
                    <div class="w-8 h-8 rounded-full bg-[#1a1a1a] border border-dashed border-white/10 flex items-center justify-center text-neutral-600">
                        <span class="text-[9px]">+2</span>
                    </div>
                </div>
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
                <Tag class="w-4 h-4 inline mr-2" /> My Contributions
            </button>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4" style="content-visibility: auto;">
            {#if activeTab === 'hearts' || activeTab === 'watchlist'}
                {#each WATCHLIST as movie}
                    <div class="group relative aspect-2/3 rounded-xl overflow-hidden bg-[#111] border border-white/5 cursor-pointer">
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
                    <div class="aspect-2/3 rounded-xl border border-dashed border-white/5 flex items-center justify-center group hover:border-white/10 transition-colors cursor-pointer">
                        <span class="text-xs text-neutral-700 group-hover:text-neutral-500 transition-colors">Add more</span>
                    </div>
                {/each}
            {:else}
                <div class="col-span-full py-12 text-center text-neutral-500 border border-dashed border-white/5 rounded-2xl">
                    <p class="text-sm">You have contributed <span class="text-white font-bold">42 tags</span> to the ecosystem.</p>
                    <p class="text-xs mt-2 text-neutral-600">Keep tagging to unlock the "Genre Explorer" badge.</p>
                </div>
            {/if}
        </div>
    </div>
</div>