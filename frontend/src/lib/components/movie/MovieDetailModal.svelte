<script lang="ts">
    import { X, Play, Heart, Bookmark, Brain, Gauge } from 'lucide-svelte';
    import { fade, fly } from 'svelte/transition';
    import { createEventDispatcher } from 'svelte';
    import { currentUser, toast } from '$lib/stores';
    import type { EnrichedMovie } from '$lib/logic';

    export let movie: EnrichedMovie;
    
    const dispatch = createEventDispatcher();
    const MAX_VOTES = 3; 
    const MAX_CUSTOM_TAGS = 3; 

    // --- Local Interaction State ---
    interface Tag {
        name: string;
        score: number;
        userVoted: boolean;
        isCustom: boolean;
    }

    let interactionState = { 
        isHearted: false, 
        isBookmarked: false, 
        tags: JSON.parse(JSON.stringify(movie.initialTags || [])) as Tag[], 
        customTagsAdded: 0,
        userTagVotes: 0 
    };
    
    let showAddTagInput = false;
    let newTagValue = '';

    // Action to handle focus cleanly without A11y warnings
    function focusOnMount(node: HTMLInputElement) {
        node.focus();
    }

    function close() { dispatch('close'); }

    function requireAuth(): boolean {
        if (!$currentUser) {
            toast.show("Sign in to curate vibes.", 'error');
            return false;
        }
        return true;
    }

    const toggleInteraction = (type: 'heart' | 'bookmark') => {
        if (!requireAuth()) return;
        if (type === 'heart') interactionState.isHearted = !interactionState.isHearted;
        if (type === 'bookmark') interactionState.isBookmarked = !interactionState.isBookmarked;
    };

    const voteTag = (index: number) => {
        if (!requireAuth()) return;
        const newTags = [...interactionState.tags];
        const tag = { ...newTags[index] }; 
        
        if (tag.userVoted) {
            tag.userVoted = false; 
            tag.score -= 1;
            interactionState.userTagVotes -= 1; 
            if (tag.isCustom && tag.score <= 0) {
                newTags.splice(index, 1); 
                interactionState.customTagsAdded -= 1;
            } else { 
                newTags[index] = tag; 
            }
        } else {
            if (interactionState.userTagVotes >= MAX_VOTES) {
                toast.show("Limit 3 votes per movie.", "error"); 
                return;
            }
            tag.userVoted = true; 
            tag.score += 1; 
            interactionState.userTagVotes += 1; 
            newTags[index] = tag;
        }
        interactionState.tags = newTags;
    };

    const addNewTag = () => {
        if (!requireAuth()) return;
        const cleanTag = newTagValue.trim();
        if (!cleanTag) return;
        if (interactionState.userTagVotes >= MAX_VOTES) { 
            toast.show("Limit 3 votes per movie.", "error"); return; 
        }
        
        const existingIndex = interactionState.tags.findIndex(t => t.name.toLowerCase() === cleanTag.toLowerCase());
        if (existingIndex !== -1) {
            if (!interactionState.tags[existingIndex].userVoted) {
                voteTag(existingIndex); 
                toast.show('Upvoted existing tag!', 'success');
            }
            newTagValue = ''; showAddTagInput = false; return;
        }

        if (interactionState.customTagsAdded >= MAX_CUSTOM_TAGS) {
            toast.show('Custom tag limit reached.', 'error'); return;
        }
        
        const newTag: Tag = { name: cleanTag, score: 1, userVoted: true, isCustom: true };
        interactionState.tags = [newTag, ...interactionState.tags];
        interactionState.customTagsAdded++;
        interactionState.userTagVotes++;
        newTagValue = ''; showAddTagInput = false;
    };

    // Keyboard handler for backdrop
    const handleBackdropKeydown = (e: KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') close();
    };
</script>

<div 
    role="button"
    tabindex="0"
    on:click={close}
    on:keydown={handleBackdropKeydown}
    transition:fade={{ duration: 150 }} 
    class="fixed inset-0 z-[100] bg-black/80 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 cursor-default select-none outline-none"
>
    <div 
        role="document"
        on:click|stopPropagation 
        on:keydown|stopPropagation
        transition:fly={{ y: 40, duration: 300 }} 
        class="relative w-full max-w-4xl h-[90vh] bg-[#0e0e0e] border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col md:flex-row"
    >
        
        <button on:click={close} class="absolute top-4 right-4 z-50 p-2 bg-black/40 backdrop-blur-md rounded-full text-white/70 hover:text-white border border-white/10 hover:bg-white/10 transition-colors cursor-pointer"><X class="w-4 h-4" /></button>

        <div class="w-full md:w-5/12 bg-black/50 border-r border-white/5 flex flex-col group shrink-0 relative overflow-hidden">
            <div class="flex-1 relative overflow-hidden min-h-0">
                {#if movie.posterUrl}
                    <img src={movie.posterUrl} alt={movie.title} class="w-full h-full object-cover" />
                {:else}
                    <div class="w-full h-full bg-neutral-900 flex items-center justify-center text-neutral-700">No Image</div>
                {/if}
                <div class="absolute inset-0 bg-gradient-to-t from-[#0e0e0e] via-[#0e0e0e]/40 to-transparent opacity-90"></div>
                <div class="absolute bottom-0 left-0 w-full p-5 z-20">
                    <h2 class="text-3xl font-bold text-white tracking-tighter leading-none mb-2 drop-shadow-xl">{movie.title}</h2>
                    <div class="flex flex-wrap items-center gap-2 text-xs font-medium text-white/80">
                        <span>{movie.year}</span><span class="w-0.5 h-0.5 rounded-full bg-white/40"></span><span>{movie.runtime}</span>
                    </div>
                </div>
            </div>

            <div class="p-5 flex flex-col gap-5 bg-[#0e0e0e] shrink-0">
                <div class="flex items-center gap-3 border-b border-white/5 pb-3">
                    <div class="flex -space-x-1.5">
                        {#each movie.palette.colors as color}
                            <div class="w-2.5 h-2.5 rounded-full border border-white/10 shadow-sm" style="background-color: {color};"></div>
                        {/each}
                    </div>
                    <span class="text-[9px] font-bold uppercase tracking-widest text-white/50">{movie.palette.name}</span>
                </div>

                <div class="grid grid-cols-3 gap-2 py-2 border-b border-white/5">
                    <div class="flex flex-col items-center">
                        <span class="text-[9px] font-bold text-neutral-500 uppercase tracking-widest mb-0.5">Match</span>
                        <span class="text-emerald-400 font-bold text-lg">{Math.round(movie.score * 100)}%</span>
                    </div>
                    <div class="col-span-2"></div>
                </div>

                <div class="space-y-3">
                    <h3 class="text-[9px] font-bold text-neutral-500 uppercase tracking-widest flex items-center gap-2"><Gauge class="w-3 h-3" /> Vibe Signature</h3>
                    {#each Object.values(movie.vibeDynamics) as metric}
                        <div>
                            <div class="flex justify-between items-end text-[8px] mb-1 uppercase font-medium tracking-wider">
                                <span class="text-neutral-500">{metric.low}</span><span class="text-white font-bold">{metric.label}</span><span class="text-neutral-500">{metric.high}</span>
                            </div>
                            <div class="h-0.5 w-full bg-white/10 rounded-full overflow-hidden">
                                <div class="h-full bg-indigo-500/80 rounded-full" style="width: {metric.val}%"></div>
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        </div>

        <div class="w-full md:w-7/12 flex flex-col bg-[#0e0e0e]">
            <div class="flex-1 overflow-y-auto custom-scrollbar p-6 md:p-8 flex flex-col gap-6">
                <div class="flex flex-wrap gap-2 pt-2">
                     {#each movie.socialBadges as badge}
                        <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] uppercase font-bold text-neutral-300">
                            <svelte:component this={badge.icon} class="w-3 h-3" /> {badge.text}
                        </div>
                    {/each}
                </div>

                <div class="pt-2">
                    <h3 class="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-3 flex items-center justify-between">
                        <span class="flex items-center gap-2"><Brain class="w-3 h-3" /> Content Descriptors</span>
                    </h3>
                    <div class="flex flex-wrap gap-2">
                        {#each interactionState.tags as tag, i}
                            <button on:click={() => voteTag(i)} class="group relative flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs font-medium transition-all active:scale-95 select-none cursor-pointer {tag.userVoted ? 'bg-indigo-500/10 border-indigo-500/40 text-indigo-300' : 'bg-[#141414] border-white/5 text-neutral-400'}">
                                <span>{tag.name}</span>
                                <span class="text-[10px] opacity-40 group-hover:opacity-100 transition-opacity">{tag.score}</span>
                            </button>
                        {/each}
                        {#if interactionState.customTagsAdded < MAX_CUSTOM_TAGS}
                            {#if !showAddTagInput}
                                <button on:click={() => showAddTagInput = true} class="px-2.5 py-1.5 rounded-md border border-dashed border-white/10 text-neutral-600 text-xs hover:border-white/20 hover:text-neutral-400 transition-all cursor-pointer">+</button>
                            {:else}
                                <form on:submit|preventDefault={addNewTag} class="flex items-center">
                                    <input use:focusOnMount bind:value={newTagValue} class="bg-transparent border-b border-indigo-500 text-white text-xs w-20 outline-none px-1 py-1" placeholder="Add..." on:blur={() => {if(!newTagValue) showAddTagInput=false}} />
                                </form>
                            {/if}
                        {/if}
                    </div>
                </div>

                <div class="p-6 border-t border-white/5 bg-[#0e0e0e] flex items-center gap-3 z-10 mt-auto">
                    <a href={movie.trailerUrl || `https://www.youtube.com/results?search_query=${movie.title} trailer`} target="_blank" rel="noopener noreferrer" class="flex-1 h-12 rounded-xl bg-white text-black flex items-center justify-center gap-2 text-sm font-bold tracking-wide hover:bg-neutral-200 transition-all cursor-pointer">
                        <Play class="w-4 h-4 fill-current" /> {movie.trailerUrl ? 'Watch Trailer' : 'Search Trailer'}
                    </a>
                    <button on:click={() => toggleInteraction('heart')} class="w-12 h-12 rounded-xl border border-white/10 bg-white/5 text-neutral-300 flex items-center justify-center cursor-pointer {interactionState.isHearted ? 'text-rose-400 border-rose-500/30' : ''}">
                        <Heart class="w-5 h-5 {interactionState.isHearted ? 'fill-current' : ''}" />
                    </button>
                    <button on:click={() => toggleInteraction('bookmark')} class="w-12 h-12 rounded-xl border border-white/10 bg-white/5 text-neutral-300 flex items-center justify-center cursor-pointer {interactionState.isBookmarked ? 'text-emerald-400 border-emerald-500/30' : ''}">
                        <Bookmark class="w-5 h-5 {interactionState.isBookmarked ? 'fill-current' : ''}" />
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>