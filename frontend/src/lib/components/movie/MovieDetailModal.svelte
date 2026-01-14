<script lang="ts">
    import { X, Play, Heart, Bookmark, Brain, Gauge, Star, Users, Zap } from 'lucide-svelte';
    import { createEventDispatcher } from 'svelte';
    import { currentUser, toast } from '$lib/stores';
    import type { EnrichedMovie } from '$lib/logic';

    let { movie } = $props<{ movie: EnrichedMovie }>();
    
    const dispatch = createEventDispatcher();
    const MAX_VOTES = 3; 
    const MAX_CUSTOM_TAGS = 3; 

    interface Tag {
        name: string;
        score: number;
        userVoted: boolean;
        isCustom: boolean;
    }

    let isHearted = $state(false);
    let isBookmarked = $state(false);
    
    let tags = $state<Tag[]>([]);
    let customTagsAdded = $state(0);
    let userTagVotes = $state(0);
    let showAddTagInput = $state(false);
    let newTagValue = $state('');

    const humanContext = {
        perfectFor: [
            "Late Night Contemplation",
            "Cinephile Deep Dive", 
            "Atmospheric Mood Setting",
            "Philosophical Discussion"
        ],
        subculture: "Sigma Male Grindset / Neo-Noir Enthusiasts"
    };

    const mockRecommendations = [
        { title: "Blade Runner", year: 1982, match: 92, gradient: "from-cyan-500 to-blue-900" },
        { title: "Drive", year: 2011, match: 88, gradient: "from-pink-500 to-rose-900" },
        { title: "Taxi Driver", year: 1976, match: 85, gradient: "from-amber-500 to-orange-900" },
        { title: "Nightcrawler", year: 2014, match: 83, gradient: "from-green-500 to-emerald-900" },
        { title: "Collateral", year: 2004, match: 79, gradient: "from-purple-500 to-violet-900" }
    ];

    $effect(() => {
        tags = [...(movie.initialTags || [])];
        isHearted = false;
        isBookmarked = false;
        customTagsAdded = 0;
        userTagVotes = 0;
    });

    function focusOnMount(node: HTMLInputElement) {
        node.focus();
    }

    function close() { 
        dispatch('close'); 
    }

    function requireAuth(): boolean {
        if (!$currentUser) {
            toast.show("Sign in to curate vibes.", 'error');
            return false;
        }
        return true;
    }

    const toggleInteraction = (type: 'heart' | 'bookmark') => {
        if (!requireAuth()) return;
        if (type === 'heart') isHearted = !isHearted;
        if (type === 'bookmark') isBookmarked = !isBookmarked;
    };

    const voteTag = (index: number) => {
        if (!requireAuth()) return;
        const tag = tags[index];
        if (tag.userVoted) {
            tag.userVoted = false; 
            tag.score -= 1;
            userTagVotes -= 1; 
            if (tag.isCustom && tag.score <= 0) {
                tags.splice(index, 1); 
                customTagsAdded -= 1;
            }
        } else {
            if (userTagVotes >= MAX_VOTES) {
                toast.show("Limit 3 votes per movie.", "error"); 
                return;
            }
            tag.userVoted = true; 
            tag.score += 1; 
            userTagVotes += 1; 
        }
    };

    const addNewTag = () => {
        if (!requireAuth()) return;
        const cleanTag = newTagValue.trim();
        if (!cleanTag) return;
        if (userTagVotes >= MAX_VOTES) { 
            toast.show("Limit 3 votes per movie.", "error"); 
            return; 
        }
        
        const existingIndex = tags.findIndex(t => t.name.toLowerCase() === cleanTag.toLowerCase());
        if (existingIndex !== -1) {
            if (!tags[existingIndex].userVoted) {
                voteTag(existingIndex); 
                toast.show('Upvoted existing tag!', 'success');
            }
            newTagValue = ''; 
            showAddTagInput = false; 
            return;
        }

        if (customTagsAdded >= MAX_CUSTOM_TAGS) {
            toast.show('Custom tag limit reached.', 'error'); 
            return;
        }
        
        const newTag: Tag = { name: cleanTag, score: 1, userVoted: true, isCustom: true };
        tags.push(newTag);
        customTagsAdded++;
        userTagVotes++;
        newTagValue = ''; 
        showAddTagInput = false;
    };

    const handleBackdropKeydown = (e: KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') close();
    };
</script>

<div
  class="fixed inset-0 z-[100] bg-black/95 flex items-center justify-center p-4 sm:p-6 cursor-default select-none"
  onclick={close}
  onkeydown={handleBackdropKeydown}
  tabindex="0"
  role="button"
  aria-label="Close modal"
>
    
    <div 
        onclick={(e) => e.stopPropagation()} 
        onkeydown={(e) => e.stopPropagation()}
        class="relative w-full max-w-4xl h-[90vh] bg-[#0e0e0e] border border-white/10 rounded-[24px] shadow-2xl overflow-hidden flex flex-col md:flex-row will-change-transform"
    >
        
        <button 
            onclick={close}
            class="absolute top-4 right-4 z-50 p-2 bg-black/60 rounded-full text-white/70 hover:text-white border border-white/10 hover:bg-white/10 transition-colors cursor-pointer"
        >
            <X class="w-4 h-4"/>
        </button>

        <div class="w-full md:w-5/12 bg-[#0e0e0e] border-r border-white/5 flex flex-col group shrink-0 relative overflow-hidden">
             
            <div class="flex-1 relative overflow-hidden min-h-0">
                {#if movie.posterUrl}
                    <img 
                        src={movie.posterUrl} 
                        alt={movie.title} 
                        class="w-full h-full object-cover" 
                        loading="eager"
                        fetchpriority="high"
                        decoding="async"
                    />
                {:else}
                     <div class="w-full h-full bg-neutral-900 flex items-center justify-center text-neutral-700">No Image</div>
                {/if}
                
                <div class="absolute inset-0 bg-linear-to-t from-[#0e0e0e] via-[#0e0e0e]/40 to-transparent opacity-90"></div>
                <div class="absolute inset-0 bg-linear-to-r from-black/50 to-transparent"></div>
                
                <div class="absolute bottom-0 left-0 w-full p-5 z-20">
                    <h2 class="text-3xl font-bold text-white tracking-tighter leading-none mb-2">
                        {movie.title}
                    </h2>
                    
                    <div class="flex flex-wrap items-center gap-2 text-xs font-medium text-white/80">
                        <span class="text-white">{movie.year}</span>
                        <span class="w-0.5 h-0.5 rounded-full bg-white/40"></span>
                        <span>{movie.runtime}</span>
                    </div>
                </div>
            </div>

            <div class="p-5 flex flex-col gap-5 bg-[#0e0e0e] flex-shrink-0">
                
                <div class="flex items-center gap-3 border-b border-white/5 pb-3">
                    <div class="flex -space-x-1.5">
                        {#each movie.palette.colors as color}
                            <div class="w-2.5 h-2.5 rounded-full border border-white/10" style="background-color: {color};"></div>
                        {/each}
                    </div>
                    <span class="text-[9px] font-bold uppercase tracking-widest text-white/50">{movie.palette.name}</span>
                </div>

                <div class="grid grid-cols-3  py-2 border-b border-white/5">
                    <div class="flex flex-col items-center">
                        <span class="text-[9px] font-bold text-neutral-500 uppercase tracking-widest mb-0.5">Match</span>
                        <span class="text-emerald-400 font-bold text-lg">{Math.round(movie.score * 100)}%</span>
                    </div>
                    <div class="flex flex-col items-center border-l border-white/5">
                        <span class="text-[9px] font-bold text-neutral-500 uppercase tracking-widest mb-0.5">Pop</span>
                        <span class="text-yellow-500 font-bold text-lg flex items-center gap-1">
                            <Star class="w-3 h-3 fill-current" /> 
                            {Math.round(movie.popularity || 0)/10}
                        </span>
                    </div>
                    <div class="flex flex-col items-center border-l border-white/5 text-center px-1">
                        <span class="text-[9px] font-bold text-neutral-500 uppercase tracking-widest mb-0.5">Rating</span>
                        <div class="flex flex-col items-center leading-none">
                            <span class="text-white font-bold text-lg">{movie.certData?.code || 'NR'}</span>
                            <span class="text-[7px] text-neutral-500 uppercase tracking-tight mt-0.5 w-full truncate px-1">
                                {movie.certData?.reason || 'Not Rated'}
                            </span>
                        </div>
                    </div>
                </div>

                <div class="space-y-3">
                    <h3 class="text-[9px] font-bold text-neutral-500 uppercase tracking-widest flex items-center gap-2">
                        <Gauge class="w-3 h-3" /> Vibe Signature
                    </h3>
                    {#each Object.values(movie.vibeDynamics) as metric}
                        <div>
                            <div class="flex justify-between items-end text-[8px] mb-1 uppercase font-medium tracking-wider">
                                <span class="text-neutral-500">{(metric as any).low}</span>
                                <span class="text-white font-bold">{(metric as any).label}</span>
                                <span class="text-neutral-500">{(metric as any).high}</span>
                            </div>
                            <div class="h-0.5 w-full bg-white/10 rounded-full overflow-hidden">
                                <div class="h-full bg-indigo-500/80 rounded-full" style="width: {(metric as any).val}%"></div>
                            </div>
                        </div>
                    {/each}
                </div>

                <div class="space-y-3 pt-4 border-t border-white/5">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <Zap class="w-3 h-3 text-neutral-500" />
                            <span class="text-[9px] font-bold text-neutral-500 uppercase tracking-widest">Subculture</span>
                        </div>
                        <span class="text-xs font-medium text-indigo-300 text-right">{humanContext.subculture}</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="w-full md:w-7/12 flex flex-col bg-[#0e0e0e] md:overflow-y-auto custom-scrollbar">
            <div class="p-6 md:p-8 flex flex-col gap-6">
                
                <div class="border-l-2 border-indigo-500 pl-4 py-1 mt-2">
                     <p class="text-lg text-white/90 font-light italic leading-snug">
                         "{movie.momentSentence}"
                     </p>
                </div>

                <div>
                     <h3 class="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-2">Story</h3>
                     <p class="text-sm text-neutral-400 font-light leading-relaxed">
                         {movie.overview}
                     </p>
                     
                     <div class="mt-4 pt-3 border-t border-white/5 flex flex-col gap-1.5 text-xs text-neutral-400">
                         <p><span class="text-white font-bold uppercase text-[10px] tracking-wider mr-2">Director</span> {movie.director || 'Unknown'}</p>
                         <p><span class="text-white font-bold uppercase text-[10px] tracking-wider mr-2">Cast</span> 
                             {movie.cast ? movie.cast.slice(0, 4).join(", ") : 'N/A'}
                         </p>
                          <p><span class="text-white font-bold uppercase text-[10px] tracking-wider mr-2">Genre</span> {movie.original_language ? movie.original_language.toUpperCase() : 'N/A'}</p>
                         <p><span class="text-white font-bold uppercase text-[10px] tracking-wider mr-2">Language</span> {movie.original_language ? movie.original_language.toUpperCase() : 'N/A'}</p>
                     </div>
                </div>

                <div class="pt-2">
                    <h3 class="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                        <Users class="w-3 h-3" /> Perfect For
                    </h3>
                    <div class="grid grid-cols-2 gap-2">
                        {#each humanContext.perfectFor as occasion}
                            <div class="flex items-center gap-2 p-2.5 rounded-lg bg-white/5 border border-white/10">
                                <div class="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0"></div>
                                <span class="text-xs font-medium text-white/90 flex-1 leading-tight">
                                    {occasion}
                                </span>
                            </div>
                        {/each}
                    </div>
                </div>

                <div class="pt-2">
                    <h3 class="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-3 flex items-center justify-between">
                        <span class="flex items-center gap-2">
                            <Brain class="w-3 h-3" /> Content Descriptors
                        </span>
                        <span class="text-[9px] text-neutral-600 font-normal">Rank top {MAX_VOTES}</span>
                    </h3>
                    <div class="flex flex-wrap gap-2">
                        {#each tags as tag, i}
                            <button 
                                onclick={() => voteTag(i)} 
                                class="flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs font-medium cursor-pointer transition-colors {tag.userVoted ? 'bg-indigo-500/10 border-indigo-500/40 text-indigo-300' : 'bg-[#141414] border-white/5 text-neutral-400 hover:bg-white/5'}"
                            >
                                <span>{tag.name}</span>
                                <span class="text-[10px] {tag.userVoted ? 'text-indigo-400' : 'opacity-40'}">{tag.score}</span>
                            </button>
                        {/each}
                        {#if customTagsAdded < MAX_CUSTOM_TAGS}
                            {#if !showAddTagInput}
                                <button 
                                    onclick={() => showAddTagInput = true} 
                                    class="px-2.5 py-1.5 rounded-md border border-dashed border-white/10 text-neutral-600 text-xs cursor-pointer hover:border-white/30 hover:text-neutral-400 transition-colors"
                                >+</button>
                            {:else}
                                <form onsubmit={(e) => { e.preventDefault(); addNewTag(); }} class="flex items-center">
                                    <input 
                                        use:focusOnMount 
                                        bind:value={newTagValue} 
                                        class="bg-transparent border-b border-indigo-500 text-white text-xs w-20 outline-none px-1 py-1" 
                                        placeholder="Add..." 
                                        onblur={() => {if(!newTagValue) showAddTagInput=false}} 
                                    />
                                </form>
                            {/if}
                        {/if}
                    </div>
                </div>

                <div class="pt-4 border-t border-white/5">
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="text-[10px] font-bold text-neutral-500 uppercase tracking-widest">Similarity Graph</h3>
                        <span class="text-[9px] text-neutral-600 font-normal">Vibe matches</span>
                    </div>
                    <div class="grid grid-cols-5 gap-2">
                        {#each mockRecommendations as rec}
                            <div class="cursor-pointer flex flex-col items-center group">
                                <div class="relative w-full aspect-[3/4] rounded-lg overflow-hidden mb-1.5 bg-neutral-900 border border-white/5">
                                    <div class="absolute inset-0 bg-linear-to-br {rec.gradient} opacity-60 group-hover:opacity-80 transition-opacity"></div>
                                    <div class="absolute bottom-1 left-1 right-1">
                                        <span class="text-[8px] font-bold text-white/90 bg-black/60 px-1.5 py-0.5 rounded truncate block text-center">
                                            {rec.title}
                                        </span>
                                    </div>
                                    <div class="absolute top-1 right-1 px-1 py-0.5 bg-black/80 rounded text-[7px] font-bold text-emerald-400 border border-white/5">
                                        {rec.match}%
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            </div>

            <div class="p-6 border-t border-white/5 bg-[#0e0e0e] flex items-center gap-3 z-10 mt-auto sticky bottom-0 md:static">
                <a 
                    href={movie.trailerUrl || `https://www.youtube.com/results?search_query=${movie.title} trailer`} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    class="flex-1 h-12 rounded-xl bg-white text-black flex items-center justify-center gap-2 text-sm font-bold hover:bg-neutral-200 cursor-pointer transition-colors"
                >
                    <Play class="w-4 h-4 fill-current" /> 
                    {movie.trailerUrl ? 'Watch Trailer' : 'Search Trailer'}
                </a>
                
                <button 
                    onclick={() => toggleInteraction('heart')} 
                    class="w-12 h-12 rounded-xl border border-white/10 bg-white/5 text-neutral-300 flex items-center justify-center cursor-pointer transition-all {isHearted ? 'text-rose-400 border-rose-500/30 bg-rose-500/10' : 'hover:bg-white/10'}"
                >
                    <Heart class="w-5 h-5 {isHearted ? 'fill-current' : ''}" />
                </button>

                <button 
                    onclick={() => toggleInteraction('bookmark')} 
                    class="w-12 h-12 rounded-xl border border-white/10 bg-white/5 text-neutral-300 flex items-center justify-center cursor-pointer transition-all {isBookmarked ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' : 'hover:bg-white/10'}"
                >
                    <Bookmark class="w-5 h-5 {isBookmarked ? 'fill-current' : ''}" />
                </button>
            </div>
        </div>
    </div>
</div>

<style>
    .custom-scrollbar::-webkit-scrollbar { 
        height: 4px; 
        width: 4px; 
    }
    .custom-scrollbar::-webkit-scrollbar-track { 
        background: transparent; 
    }
    .custom-scrollbar::-webkit-scrollbar-thumb { 
        background: #262626; 
        border-radius: 9999px; 
    }
</style>