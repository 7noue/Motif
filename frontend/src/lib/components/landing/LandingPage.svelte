<script lang="ts">
    import { Film, Search, Sparkles, TrendingUp } from 'lucide-svelte';
    import { searchStore } from '../../stores';
    import { LANDING_STATS, LANDING_FEATURES, VIBES } from '../../constants';

    // Local state for the input
    let queryLocal = '';

    function handleSearch() {
        if (!queryLocal.trim()) return;
        searchStore.performSearch(queryLocal);
    }
</script>

<div class="relative z-10 w-full max-w-7xl mx-auto px-6 flex flex-col items-center justify-center min-h-screen py-12">
    
    <div class="flex items-center gap-5 mb-6">
        <div class="flex items-center justify-center w-14 h-14 bg-[#0A0A0A] border border-white/10 rounded-2xl shadow-2xl shadow-black/50">
            <Film class="w-7 h-7 text-white" />
        </div>
        <h1 class="text-5xl font-semibold tracking-tighter text-white">
            Motif
        </h1>
    </div>
    
    <p class="text-neutral-400 text-lg font-light tracking-wide text-center mb-16">
        Films for the moment. Not just the plot.
    </p>

    <div class="w-full max-w-2xl relative mb-24 group">
        
        <div class="absolute -inset-1 bg-linear-to-r from-indigo-500/20 via-purple-500/10 to-rose-500/20 rounded-[28px] blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>

        <div class="relative flex flex-col p-2 bg-[#0A0A0A] border border-white/10 rounded-[24px] shadow-2xl shadow-black/80 transition-all duration-300 group-focus-within:border-white/20 group-focus-within:shadow-indigo-500/10">
            
            <div class="flex items-center w-full pr-2">
                <div class="pl-4 pr-3 text-neutral-500 group-focus-within:text-indigo-400 transition-colors">
                    <Search class="w-6 h-6" />
                </div>
                
                <input 
                    type="text" 
                    bind:value={queryLocal} 
                    placeholder="Describe the occasion..." 
                    class="w-full h-14 bg-transparent text-white text-lg outline-none placeholder-neutral-600 font-light" 
                    on:keydown={(e) => e.key === 'Enter' && handleSearch()} 
                />
                
                <button 
                    on:click={handleSearch} 
                    disabled={!queryLocal} 
                    class="relative flex items-center justify-center w-12 h-12 rounded-xl bg-white/5 border border-white/10 text-neutral-400 hover:text-white hover:bg-white/10 hover:border-white/20 transition-all cursor-pointer disabled:opacity-30 disabled:hover:bg-white/5 disabled:hover:border-white/10 disabled:cursor-not-allowed group/btn"
                >
                    <div class="absolute inset-0 bg-indigo-500/20 rounded-xl blur-md opacity-0 group-hover/btn:opacity-100 transition-opacity duration-300 {queryLocal ? 'animate-pulse' : ''}"></div>
                    
                    <Sparkles class="w-5 h-5 relative z-10 transition-transform duration-300 group-hover/btn:scale-110 {queryLocal ? 'text-indigo-300' : ''}" />
                </button>
            </div>

            <div class="h-px w-full bg-white/5 my-2"></div>

            <div class="flex flex-wrap gap-1.5 px-2 pb-1">
                <span class="text-[10px] uppercase font-bold text-neutral-600 tracking-widest mr-2 self-center">Try:</span>
                {#each VIBES as vibe}
                    <button 
                        on:click={() => searchStore.performSearch(vibe.label)} 
                        class="px-3 py-1.5 rounded-lg text-xs font-medium text-neutral-400 hover:text-white hover:bg-white/5 transition-all cursor-pointer flex items-center gap-1.5"
                    >
                        <svelte:component this={vibe.icon} class="w-3 h-3 opacity-50" />
                        {vibe.label}
                    </button>
                {/each}
            </div>
        </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 w-full max-w-6xl mb-24">
        {#each LANDING_FEATURES as feature}
            <div class="group relative p-6 bg-[#0A0A0A] border border-white/5 rounded-2xl overflow-hidden transition-all duration-300 hover:border-white/15 hover:bg-[#0f0f0f] shadow-xl">
                <div class="absolute inset-x-0 top-0 h-px bg-linear-to-r from-transparent via-white/10 to-transparent opacity-50"></div>
                <div class="absolute -top-10 -right-10 w-24 h-24 bg-indigo-500/10 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <div class="relative w-12 h-12 rounded-xl bg-white/5 border border-white/5 flex items-center justify-center mb-5 group-hover:scale-105 group-hover:bg-white/10 group-hover:border-white/10 transition-all duration-300">
                    <svelte:component this={feature.icon} class="w-5 h-5 text-indigo-400 group-hover:text-white transition-colors" />
                </div>
                <h3 class="relative text-base font-semibold text-slate-200 mb-2 group-hover:text-white transition-colors">{feature.title}</h3>
                <p class="relative text-sm text-neutral-500 font-normal leading-relaxed group-hover:text-neutral-400 transition-colors">{feature.desc}</p>
            </div>
        {/each}
    </div>

    <div class="flex items-center justify-center gap-12 pt-12 border-t border-white/5 w-full max-w-3xl opacity-50 hover:opacity-100 transition-opacity duration-300">
        {#each LANDING_STATS as stat}
            <div class="text-center px-4">
                <div class="text-2xl font-bold text-white mb-1">{stat.value}</div>
                <div class="text-[10px] text-neutral-500 font-medium tracking-widest uppercase mb-1">{stat.label}</div>
                <div class="flex items-center justify-center gap-1 text-[10px] text-emerald-400">
                    <TrendingUp class="w-3 h-3" /> {stat.trend}
                </div>
            </div>
        {/each}
    </div>
</div>