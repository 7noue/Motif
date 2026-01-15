<script lang="ts">
    import { Film, Search, ArrowRight, Star } from 'lucide-svelte';
    import { createEventDispatcher } from 'svelte';
    import { searchStore } from '$lib/stores';
    import { CONTEXT_OPTIONS, VIBES } from '$lib/constants';
    import { getGradient, type EnrichedMovie } from '$lib/logic';

    const dispatch = createEventDispatcher<{ select: EnrichedMovie }>();

    $: ({ query, movies, isLoading, activeContext } = $searchStore);

    function onSelect(movie: EnrichedMovie) { 
        dispatch('select', movie); 
    }

    let localQuery = '';
    $: localQuery = query;

    function handleInput(e: Event) {
        const target = e.currentTarget as HTMLInputElement;
        localQuery = target.value;
        searchStore.setQuery(target.value);
    }
</script>

<div class="relative z-10 w-full max-w-7xl mx-auto px-6 flex flex-col items-center pt-10 justify-start">
    
    <div class="w-full flex flex-col md:flex-row items-center justify-between gap-6 mb-8">
        <button on:click={searchStore.reset} class="flex items-center gap-3 group transition-opacity duration-300 cursor-pointer outline-none hover:opacity-80">
            <div class="flex items-center justify-center w-10 h-10 bg-[#0e0e0e] border border-white/10 rounded-xl shadow-lg">
                <Film class="text-white w-5 h-5" />
            </div>
            <h1 class="font-semibold tracking-tighter text-white text-2xl">Motif</h1>
        </button>

        <div class="flex flex-wrap justify-center md:justify-end gap-2 {isLoading ? 'opacity-50' : 'opacity-100'}">
            <div class="flex bg-[#0e0e0e] p-1 rounded-full border border-white/10">
                {#each CONTEXT_OPTIONS.social as opt}
                    <button on:click={() => searchStore.toggleContext('social', opt.id)} class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer {activeContext.social === opt.id ? 'bg-indigo-500 text-white' : 'text-neutral-500 hover:text-white hover:bg-white/5'}">
                        <svelte:component this={opt.icon} class="w-3 h-3" /> {opt.label}
                    </button>
                {/each}
            </div>
        </div>
    </div>

    <div class="w-full max-w-3xl relative z-20 flex flex-col gap-6 mb-12">
        <form on:submit|preventDefault={() => searchStore.performSearch()} class="w-full relative group z-20">
            <div class="relative flex items-center p-2 bg-[#0e0e0e] border border-white/10 hover:border-white/20 focus-within:border-white/30 rounded-2xl transition-colors duration-200">
                <Search class="w-5 h-5 text-neutral-500 group-focus-within:text-indigo-400 ml-4 transition-colors duration-200" />
                <input 
                    type="text" 
                    value={localQuery} 
                    on:input={handleInput} 
                    class="w-full h-12 bg-transparent text-white outline-none px-4 placeholder-neutral-600 font-light text-base" 
                    placeholder="Search for a vibe..."
                    disabled={isLoading} 
                />
                <button type="submit" disabled={isLoading} class="flex items-center justify-center w-10 h-10 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white transition-colors cursor-pointer">
                    <ArrowRight class="w-5 h-5" />
                </button>
            </div>
        </form>

        <div class="flex flex-wrap justify-center gap-2 {isLoading ? 'opacity-50 pointer-events-none' : 'opacity-100'}">
            {#each VIBES as vibe}
                <button on:click={() => searchStore.performSearch(vibe.label)} class="flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs font-medium transition-transform active:scale-95 select-none cursor-pointer bg-[#141414] border-white/5 text-neutral-400 hover:border-neutral-700 hover:text-neutral-300">
                    <svelte:component this={vibe.icon} class="w-3 h-3" /> {vibe.label}
                </button>
            {/each}
        </div>
    </div>

    <div class="w-full pb-32">
        <section class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3" style="content-visibility: auto; contain-intrinsic-size: 1px 350px;">
            {#if isLoading}
                {#each Array(8) as _} 
                    <div class="aspect-square rounded-2xl bg-[#0e0e0e] border border-white/5 animate-pulse"></div> 
                {/each}
            {:else}
                {#each movies as movie, i (movie.movie_id || i)}
                    <button 
                        on:click={() => onSelect(movie)} 
                        class="group flex flex-col bg-[#0e0e0e] border border-white/10 rounded-2xl overflow-hidden hover:border-white/30 text-left transition-colors duration-200 cursor-pointer animate-enter transform-gpu shadow-lg shadow-black/20"
                        style="animation-delay: {i < 10 ? i * 50 : 0}ms"
                    >
                        <div class="relative w-full aspect-square overflow-hidden bg-[#111] border-b border-white/5">
                            {#if movie.posterUrl}
                                <img 
                                    src={movie.posterUrl} 
                                    alt={movie.title} 
                                    loading="lazy"
                                    decoding="async"
                                    class="w-full h-full object-cover object-top opacity-90 group-hover:opacity-100 group-hover:scale-105 transition-all duration-500 ease-out"
                                />
                            {:else}
                                <div class="w-full h-full bg-linear-to-br {getGradient(movie.title)} opacity-60"></div>
                            {/if}
                            
                            <div class="absolute top-2 right-2 flex items-center gap-1 bg-black/80 backdrop-blur-sm px-2 py-1 rounded-md border border-white/10">
                                <Star class="w-3 h-3 text-indigo-400 fill-indigo-400" />
                                <span class="text-[10px] font-bold text-white">{Math.round(movie.score * 100)}%</span>
                            </div>
                        </div>

                        <div class="p-4 bg-[#0e0e0e]">
                            <h2 class="text-sm font-bold text-white leading-tight line-clamp-1 group-hover:text-indigo-300 transition-colors mb-1">
                                {movie.title}
                            </h2>
                            <div class="flex items-center justify-between mt-2">
                                <p class="text-[10px] text-neutral-500 line-clamp-1">{movie.director || 'Unknown'}</p>
                                <span class="text-[10px] font-mono text-neutral-400">{movie.year}</span>
                            </div>
                            
                            {#if movie.socialBadges && movie.socialBadges[0]}
                                <div class="mt-3 pt-3 border-t border-white/5 flex items-center gap-1.5 text-[9px] text-neutral-400 uppercase tracking-wider font-medium">
                                    <svelte:component this={movie.socialBadges[0].icon} class="w-2.5 h-2.5 opacity-70" /> 
                                    {movie.socialBadges[0].text}
                                </div>
                            {/if}
                        </div>
                    </button>
                {/each}
            {/if}
        </section>
    </div>
</div>

<style>
    @keyframes enter {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-enter {
        animation: enter 0.4s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
        opacity: 0; 
    }
</style>