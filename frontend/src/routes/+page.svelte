<script lang="ts">
    import { AlertCircle, Check } from 'lucide-svelte';
    import { fly } from 'svelte/transition';
    
    // Components
    import LandingPage from '$lib/components/landing/LandingPage.svelte';
    import ResultsView from '$lib/components/search/ResultsView.svelte';
    import MovieDetailModal from '$lib/components/movie/MovieDetailModal.svelte';
    import './layout.css'
    // Stores & Types
    import { toast, searchStore } from '$lib/stores';
    import type { EnrichedMovie } from '$lib/logic';

    // App Local State
    let selectedMovie: EnrichedMovie | null = null;

    // Derived from search store
    $: hasSearched = $searchStore.hasSearched;
</script>

<svelte:window on:keydown={(e) => { if (e.key === 'Escape') selectedMovie = null; }} />

{#if $toast}
    <div transition:fly={{ y: -20, duration: 300 }} class="fixed top-6 left-1/2 transform -translate-x-1/2 z-200">
        <div class="px-6 py-3 rounded-full shadow-2xl border backdrop-blur-md flex items-center gap-3 bg-neutral-900/90 border-neutral-700 text-neutral-200">
            {#if $toast.type === 'error'} <AlertCircle class="w-4 h-4" /> {:else} <Check class="w-4 h-4 text-emerald-400" /> {/if}
            <span class="text-sm font-medium">{$toast.message}</span>
        </div>
    </div>
{/if}

{#if !hasSearched}
    <LandingPage />
{:else}
    <ResultsView on:select={(e) => selectedMovie = e.detail} />
{/if}

{#if selectedMovie}
    <MovieDetailModal movie={selectedMovie} on:close={() => selectedMovie = null} />
{/if}