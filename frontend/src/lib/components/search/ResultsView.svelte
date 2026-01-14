<script lang="ts">
    import { Film, Search, ArrowRight, Star } from 'lucide-svelte';
    import { fly } from 'svelte/transition';
    import { createEventDispatcher } from 'svelte';
    import { searchStore } from '$lib/stores';
    import { CONTEXT_OPTIONS, VIBES } from '$lib/constants';
    import { getGradient, type EnrichedMovie } from '$lib/logic';

    const dispatch = createEventDispatcher<{ select: EnrichedMovie }>();

    // Subscribe to searchStore
    $: ({ query, movies, isLoading, activeContext } = $searchStore);

    function onSelect(movie: EnrichedMovie) { 
        dispatch('select', movie); 
    }

    function handleInput(e: Event) {
        const target = e.currentTarget as HTMLInputElement;
        searchStore.setQuery(target.value);
    }
</script>

<div class="relative z-10 w-full max-w-7xl mx-auto px-6 flex flex-col items-center pt-8 justify-start">
    
    <button on:click={searchStore.reset} class="flex flex-row items-center group transition-all duration-300 cursor-pointer outline-none mb-6 gap-4">
        <div class="relative flex items-center justify-center bg-black border border-white/10 rounded-xl shadow-2xl backdrop-blur-sm w-10 h-10">
            <Film class="text-white w-5 h-5" />
        </div>
        <h1 class="font-semibold tracking-tighter text-transparent bg-clip-text bg-linear-to-b from-white to-white/50 text-3xl">Motif</h1>
    </button>

    <div class="w-full max-w-2xl relative z-20 flex flex-col gap-4">
        
        <div class="flex flex-wrap justify-center gap-2 {isLoading ? 'opacity-50' : 'opacity-100'}">
            <div class="flex bg-white/3 p-1 rounded-full border border-white/5 backdrop-blur-md">
                {#each CONTEXT_OPTIONS.social as opt}
                    <button on:click={() => searchStore.toggleContext('social', opt.id)} class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all {activeContext.social === opt.id ? 'bg-indigo-500 text-white' : 'text-neutral-500 hover:text-white'}">
                        <svelte:component this={opt.icon} class="w-3 h-3" /> {opt.label}
                    </button>
                {/each}
            </div>
            </div>

        <form on:submit|preventDefault={() => searchStore.performSearch()} class="w-full relative group z-20">
            <div class="relative flex items-center p-2 bg-white/3 border border-white/10 rounded-2xl">
                <Search class="w-6 h-6 text-neutral-500 ml-4" />
                <input 
                    type="text" 
                    value={query} 
                    on:input={handleInput} 
                    class="w-full h-12 bg-transparent text-white outline-none px-4" 
                    disabled={isLoading} 
                />
                <button type="submit" disabled={isLoading} class="w-10 h-10 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-400 flex items-center justify-center"><ArrowRight class="w-5 h-5" /></button>
            </div>
        </form>
    </div>

    <div class="mt-6 flex flex-wrap justify-center gap-2 w-full max-w-3xl {isLoading ? 'opacity-50 pointer-events-none' : 'opacity-100'}">
        {#each VIBES as vibe}
            <button on:click={() => searchStore.performSearch(vibe.label)} class="flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium border border-white/5 bg-white/2 hover:bg-white/10 text-neutral-400">
                <svelte:component this={vibe.icon} class="w-3 h-3" /> {vibe.label}
            </button>
        {/each}
    </div>

    <div class="w-full pb-20 max-w-7xl mt-8">
        <section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#if isLoading}
                {#each Array(6) as _} <div class="h-64 rounded-3xl bg-white/3 border border-white/5 animate-pulse"></div> {/each}
            {:else}
                {#each movies as movie, i (movie.movie_id || i)}
                    <button on:click={() => onSelect(movie)} in:fly={{ y: 20, duration: 300, delay: i * 50 }} class="group relative w-full flex flex-col h-full bg-[#0a0a0a] border border-white/5 rounded-3xl overflow-hidden hover:-translate-y-1 hover:shadow-2xl hover:border-white/10 text-left">
                        <div class="h-40 w-full relative overflow-hidden shrink-0">
                            <div class="absolute inset-0 bg-linear-to-br {getGradient(movie.title)} opacity-40 group-hover:opacity-60 transition-opacity"></div>
                            <div class="absolute top-3 right-3 flex items-center gap-1.5 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-lg border border-white/5">
                                <Star class="w-3 h-3 text-indigo-400 fill-indigo-400" />
                                <span class="text-xs font-bold text-white">{Math.round(movie.score * 100)}%</span>
                            </div>
                        </div>
                        <div class="p-5 flex flex-col h-full relative z-10 -mt-6">
                            <h2 class="text-xl font-bold text-white leading-tight mb-2">{movie.title}</h2>
                            <p class="text-neutral-400 text-sm font-light leading-relaxed line-clamp-3 mb-4">{movie.overview}</p>
                            <div class="mt-auto border-t border-white/5 pt-4 w-full">
                                <div class="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-white/5 border border-white/10 text-[10px] uppercase text-neutral-400 font-medium">
                                    <svelte:component this={movie.socialBadges[0].icon} class="w-3 h-3" /> {movie.socialBadges[0].text}
                                </div>
                            </div>
                        </div>
                    </button>
                {/each}
            {/if}
        </section>
    </div>
</div>