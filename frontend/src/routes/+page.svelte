<script>
    import { LogIn, LogOut, Check, AlertCircle } from 'lucide-svelte';
    import { fly } from 'svelte/transition';
    
    // Components
    import LandingPage from '$lib/components/landing/LandingPage.svelte';
    import ResultsView from '$lib/components/search/ResultsView.svelte';
    import MovieDetailModal from '$lib/components/movie/MovieDetailModal.svelte';
    import './layout.css'
    
    // Stores
    import { currentUser, toast, searchStore } from '@/stores';

    // App Local State
    let showProfileMenu = false;
    let selectedMovie = null;

    // Derived from search store
    $: hasSearched = $searchStore.hasSearched;

    function handleLogin() {
        setTimeout(() => {
            $currentUser = { name: 'Mark', avatar: null };
            toast.show('Welcome back, Mark.', 'success');
        }, 500);
    }

    function handleLogout() {
        $currentUser = null;
        showProfileMenu = false;
        toast.show('Logged out.', 'success');
    }
</script>

<svelte:window on:keydown={(e) => { if (e.key === 'Escape') selectedMovie = null; }} />

<div class="fixed top-6 right-6 z-50 flex items-center gap-4">
    {#if $currentUser}
        <div class="relative">
            <button on:click={() => showProfileMenu = !showProfileMenu} class="flex items-center gap-2 pl-3 pr-1 py-1 bg-white/10 border border-white/10 rounded-full hover:bg-white/15 transition-all backdrop-blur-md">
                <span class="text-xs font-medium text-white/90">{$currentUser.name}</span>
                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 border border-white/20"></div>
            </button>
            {#if showProfileMenu}
                <div transition:fly={{ y: 10, duration: 200 }} class="absolute right-0 mt-2 w-48 bg-[#0a0a0a] border border-white/10 rounded-xl shadow-2xl overflow-hidden backdrop-blur-xl">
                    <button on:click={handleLogout} class="w-full text-left px-4 py-3 text-sm text-red-400 hover:bg-white/5 flex items-center gap-2"><LogOut class="w-4 h-4" /> Sign Out</button>
                </div>
            {/if}
        </div>
    {:else}
        <button on:click={handleLogin} class="flex items-center gap-2 px-5 py-2.5 bg-white text-black font-semibold text-sm rounded-full hover:bg-gray-200 transition-colors shadow-lg shadow-white/5"><LogIn class="w-4 h-4" /> Sign In</button>
    {/if}
</div>

{#if $toast}
    <div transition:fly={{ y: -20, duration: 300 }} class="fixed top-6 left-1/2 transform -translate-x-1/2 z-[200]">
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