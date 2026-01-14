<script lang="ts">
    import { Film, TrendingUp, Search, ArrowRight } from 'lucide-svelte';
    import { searchStore } from '../../stores';
    import { LANDING_STATS, LANDING_FEATURES, VIBES } from '../../constants';

    let queryLocal = '';

    function handleSearch() {
        searchStore.performSearch(queryLocal);
    }
</script>

<div class="relative z-10 w-full max-w-7xl mx-auto px-6 flex flex-col items-center justify-center min-h-screen py-12">
    
    <div class="flex items-center gap-5 mb-6">
        <div class="flex items-center justify-center w-14 h-14 bg-black border border-white/10 rounded-2xl shadow-2xl backdrop-blur-sm">
            <Film class="w-7 h-7 text-white" />
        </div>
        <h1 class="text-5xl font-semibold tracking-tighter text-transparent bg-clip-text bg-linear-to-b from-white to-white/50">
            Motif
        </h1>
    </div>
    
    <p class="text-neutral-400 text-lg font-light tracking-wide text-center mb-12">
        Films for the moment. Not just the plot.
    </p>

    <div class="w-full max-w-2xl relative mb-20">
        <div class="relative flex items-center p-2 bg-white/3 hover:bg-white/5 focus-within:bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl transition-all duration-200 shadow-lg">
            <Search class="w-6 h-6 text-neutral-500 group-focus-within:text-indigo-400 ml-4 transition-colors duration-200" />
            <input 
                type="text" 
                bind:value={queryLocal} 
                placeholder="Describe the occasion..." 
                class="w-full h-12 bg-transparent text-white outline-none px-4 placeholder-neutral-600 font-light" 
                on:keydown={(e) => e.key === 'Enter' && handleSearch()} 
            />
            <button 
                on:click={handleSearch} 
                disabled={!queryLocal} 
                class="flex items-center justify-center w-10 h-10 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white transition-all cursor-pointer"
            >
                <ArrowRight class="w-5 h-5" />
            </button>
        </div>
        
        <div class="mt-6 flex flex-wrap justify-center gap-2">
            {#each VIBES as vibe}
                <button on:click={() => searchStore.performSearch(vibe.label)} class="flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium border border-white/5 bg-white/2 hover:bg-white/10 hover:border-white/20 hover:text-indigo-300 text-neutral-400 transition-all duration-200 active:scale-95 cursor-pointer">
                    <svelte:component this={vibe.icon} class="w-3 h-3" /> {vibe.label}
                </button>
            {/each}
        </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full max-w-5xl mb-24">
        {#each LANDING_FEATURES as feature}
            <div class="group p-6 bg-white/2 border border-white/5 rounded-2xl hover:border-white/10 hover:bg-white/4 transition-all">
                <div class="w-10 h-10 rounded-xl bg-white/5 border border-white/5 flex items-center justify-center mb-4 group-hover:bg-white/10 transition-colors">
                    <svelte:component this={feature.icon} class="w-5 h-5 text-indigo-400" />
                </div>
                <h3 class="text-base font-semibold text-white mb-2">{feature.title}</h3>
                <p class="text-xs text-neutral-400 font-light leading-relaxed">{feature.desc}</p>
            </div>
        {/each}
    </div>

    <div class="flex items-center justify-center gap-12 pt-12 border-t border-white/5 w-full max-w-3xl opacity-60 hover:opacity-100 transition-opacity">
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