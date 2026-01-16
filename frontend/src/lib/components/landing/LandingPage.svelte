<script lang="ts">
    import { Film, Search, ArrowRight, Star, Calendar, Clock } from 'lucide-svelte';
    import { fly } from 'svelte/transition';
    import { createEventDispatcher } from 'svelte';
    import { searchStore } from '../../stores';
    import { CONTEXT_OPTIONS, VIBES } from '../../constants';
    import { getGradient, type EnrichedMovie } from '../../logic';

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

<div class="relative z-10 w-full max-w-7xl mx-auto px-6 flex flex-col items-center pt-10 justify-start">
    
    <div class="w-full flex flex-col md:flex-row items-center justify-between gap-6 mb-8">
        <button on:click={searchStore.reset} class="flex items-center gap-3 group transition-all duration-300 cursor-pointer outline-none">
            <div class="flex items-center justify-center w-10 h-10 bg-[#0e0e0e] border border-white/10 rounded-xl shadow-lg">
                <Film class="text-white w-5 h-5" />
            </div>
            <h1 class="font-semibold tracking-tighter text-white text-2xl">Motif</h1>
        </button>

        <div class="flex flex-wrap justify-center md:justify-end gap-2 {isLoading ? 'opacity-50' : 'opacity-100'}">
            <div class="flex bg-[#0e0e0e] p-1 rounded-full border border-white/10">
                {#each CONTEXT_OPTIONS.social as opt}
                    <button on:click={() => searchStore.toggleContext('social', opt.id)} class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer {activeContext.social === opt.id ? 'bg-indigo-500 text-white shadow-lg' : 'text-neutral-500 hover:text-white hover:bg-white/5'}">
                        <svelte:component this={opt.icon} class="w-3 h-3" /> {opt.label}
                    </button>
                {/each}
            </div>
        </div>
    </div>

    <div class="w-full max-w-3xl relative z-20 flex flex-col gap-6 mb-12">
        <form on:submit|preventDefault={() => searchStore.performSearch()} class="w-full relative group z-20">
            <div class="relative flex items-center p-2 bg-[#0e0e0e] border border-white/10 hover:border-white/20 focus-within:border-white/30 rounded-2xl transition-all duration-200 shadow-2xl">
                <Search class="w-5 h-5 text-neutral-500 group-focus-within:text-indigo-400 ml-4 transition-colors duration-200" />
                <input 
                    type="text" 
                    value={query} 
                    on:input={handleInput} 
                    class="w-full h-12 bg-transparent text-white outline-none px-4 placeholder-neutral-600 font-light text-base" 
                    placeholder="Search for a vibe..."
                    disabled={isLoading} 
                />
                <button type="submit" disabled={isLoading} class="flex items-center justify-center w-10 h-10 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white transition-all cursor-pointer">
                    <ArrowRight class="w-5 h-5" />
                </button>
            </div>
        </form>

        <div class="flex flex-wrap justify-center gap-2 {isLoading ? 'opacity-50 pointer-events-none' : 'opacity-100'}">
            {#each VIBES as vibe}
                <button on:click={() => searchStore.performSearch(vibe.label)} class="flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs font-medium transition-all active:scale-95 select-none cursor-pointer bg-[#141414] border-white/5 text-neutral-400 hover:border-neutral-700 hover:text-neutral-300">
                    <svelte:component this={vibe.icon} class="w-3 h-3" /> {vibe.label}
                </button>
            {/each}
        </div>
    </div>

    <div class="w-full pb-32">
        <section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#if isLoading}
                {#each Array(6) as _} <div class="h-[420px] rounded-3xl bg-[#0e0e0e] border border-white/5 animate-pulse"></div> {/each}
            {:else}
                {#each movies as movie, i (movie.movie_id || i)}
                    <button 
                        on:click={() => onSelect(movie)} 
                        in:fly={{ y: 20, duration: 300, delay: i * 50 }} 
                        class="group relative w-full flex flex-col h-full bg-[#0e0e0e] border border-white/10 rounded-3xl overflow-hidden hover:-translate-y-1 hover:shadow-2xl hover:border-white/20 text-left transition-all duration-300 cursor-pointer"
                    >
                        <div class="h-56 w-full relative overflow-hidden shrink-0 bg-[#050505]">
                            {#if movie.posterUrl}
                                <img 
                                    src={movie.posterUrl} 
                                    alt={movie.title} 
                                    class="w-full h-full object-cover opacity-90 group-hover:opacity-100 group-hover:scale-105 transition-all duration-500"
                                    loading="lazy"
                                />
                                <div class="absolute inset-0 bg-gradient-to-t from-[#0e0e0e] via-transparent to-transparent opacity-60"></div>
                            {:else}
                                <div class="absolute inset-0 bg-gradient-to-br {getGradient(movie.title)} opacity-40 group-hover:opacity-60 transition-opacity duration-500"></div>
                            {/if}
                            
                            <div class="absolute top-3 right-3 flex items-center gap-1.5 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-lg border border-white/5 shadow-lg z-10">
                                <Star class="w-3 h-3 text-indigo-400 fill-indigo-400" />
                                <span class="text-xs font-bold text-white">{Math.round(movie.score * 100)}%</span>
                            </div>
                        </div>

                        <div class="p-6 flex flex-col h-full relative z-10 -mt-6">
                            <h2 class="text-xl font-bold text-white leading-tight mb-3 group-hover:text-indigo-200 transition-colors drop-shadow-md">
                                {movie.title}
                            </h2>
                            
                            <p class="text-neutral-400 text-sm font-light leading-relaxed line-clamp-3 mb-6">
                                {movie.overview}
                            </p>
                            
                            <div class="mt-auto border-t border-white/5 pt-4 w-full flex items-center justify-between">
                                <div class="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-white/5 border border-white/10 text-[10px] uppercase text-neutral-400 font-medium group-hover:bg-white/10 transition-colors">
                                    <svelte:component this={movie.socialBadges[0].icon} class="w-3 h-3" /> 
                                    {movie.socialBadges[0].text}
                                </div>

                                <div class="flex items-center gap-3 text-[11px] font-medium text-neutral-500">
                                    <div class="flex items-center gap-1">
                                        <Calendar class="w-3 h-3 text-neutral-600" />
                                        <span>{movie.year}</span>
                                    </div>
                                    {#if movie.runtimeStr !== "Unknown"}
                                        <div class="flex items-center gap-1">
                                            <Clock class="w-3 h-3 text-neutral-600" />
                                            <span>{movie.runtimeStr}</span>
                                        </div>
                                    {/if}
                                </div>
                            </div>
                        </div>
                    </button>
                {/each}
            {/if}
        </section>
    </div>
</div>