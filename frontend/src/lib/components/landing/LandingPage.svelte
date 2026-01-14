<script>
    import { Film, TrendingUp, Search, ArrowRight } from 'lucide-svelte';
    import { searchStore } from '@/stores';
    import { LANDING_STATS, LANDING_FEATURES, VIBES } from '$lib/constants';

    let queryLocal = '';

    function handleSearch() {
        searchStore.performSearch(queryLocal);
    }
</script>

<div class="relative z-10 w-full max-w-7xl mx-auto px-6 flex flex-col items-center justify-center h-screen">
    <div class="flex flex-col items-center mb-16">
        <div class="relative flex items-center justify-center w-24 h-24 bg-black border border-white/10 rounded-2xl shadow-2xl backdrop-blur-sm mb-8">
            <Film class="w-12 h-12 text-white" />
        </div>
        <h1 class="text-6xl font-semibold tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white to-white/50 mb-6">Motif</h1>
        <p class="text-neutral-400 text-lg font-light tracking-wide text-center">Films for the moment. Not just the plot.</p>
    </div>

    <div class="flex items-center justify-center gap-8 mb-16">
        {#each LANDING_STATS as stat}
            <div class="text-center">
                <div class="text-4xl font-bold text-white mb-2">{stat.value}</div>
                <div class="text-xs text-neutral-500 font-medium tracking-widest uppercase">{stat.label}</div>
                <div class="flex items-center justify-center gap-1 mt-1 text-[10px] text-emerald-400">
                    <TrendingUp class="w-3 h-3" /> {stat.trend}
                </div>
            </div>
        {/each}
    </div>

    <div class="w-full max-w-2xl relative">
        <div class="relative flex items-center p-2 bg-white/[0.03] hover:bg-white/[0.05] focus-within:bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl transition-all duration-200 shadow-lg">
            <Search class="w-6 h-6 text-neutral-500 ml-4" />
            <input type="text" bind:value={queryLocal} placeholder="Describe the occasion..." class="w-full h-12 bg-transparent text-white outline-none px-4 placeholder-neutral-600 font-light" on:keydown={(e) => e.key === 'Enter' && handleSearch()} />
            <button on:click={handleSearch} disabled={!queryLocal} class="flex items-center justify-center w-10 h-10 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white transition-all">
                <ArrowRight class="w-5 h-5" />
            </button>
        </div>
        
        <div class="mt-6 flex flex-wrap justify-center gap-2 w-full max-w-3xl">
            {#each VIBES as vibe}
                <button on:click={() => searchStore.performSearch(vibe.label)} class="flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium border border-white/5 bg-white/[0.02] hover:bg-white/10 text-neutral-400 transition-all">
                    <svelte:component this={vibe.icon} class="w-3 h-3" /> {vibe.label}
                </button>
            {/each}
        </div>
    </div>

    <div class="mt-24 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full max-w-5xl">
        {#each LANDING_FEATURES as feature}
            <div class="group p-6 bg-white/[0.02] border border-white/5 rounded-2xl hover:border-white/10 transition-all">
                <div class="w-10 h-10 rounded-xl bg-white/[0.05] border border-white/5 flex items-center justify-center mb-4">
                    <svelte:component this={feature.icon} class="w-5 h-5 text-indigo-400" />
                </div>
                <h3 class="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                <p class="text-sm text-neutral-400 font-light">{feature.desc}</p>
            </div>
        {/each}
    </div>
</div>