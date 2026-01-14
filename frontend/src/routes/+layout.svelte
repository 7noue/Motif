<script lang="ts">
    import favicon from '$lib/assets/favicon.svg';
    import { Home, Compass, User as UserIcon, LogIn, LogOut, Loader2 } from 'lucide-svelte';
    import { page } from '$app/stores';
    import { currentUser, toast } from '$lib/stores';
    import { fly, fade } from 'svelte/transition';
        
    let { children } = $props();
    
    let showProfileMenu = false;
    let isLoggingIn = false;

    function handleLogin() {
        isLoggingIn = true;
        setTimeout(() => {
            $currentUser = { name: 'Mark', avatar: null };
            toast.show('Welcome back, Mark.', 'success');
            isLoggingIn = false;
        }, 800);
    }

    function handleLogout() {
        $currentUser = null;
        showProfileMenu = false;
        toast.show('Logged out.', 'success');
    }
</script>

<svelte:head>
    <link rel="icon" href={favicon} />
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
</svelte:head>

<!-- Main background -->
<div class="fixed inset-0 z-[-2] bg-[#050505] pointer-events-none overflow-hidden">
    <div class="absolute inset-0 opacity-[0.03] mix-blend-overlay grain-texture"></div>
    <div class="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vh] bg-linear-to-br from-indigo-900/20 via-purple-900/10 to-transparent rounded-full blur-[120px] opacity-40 animate-pulse-slow"></div>
    <div class="absolute bottom-[-20%] right-[-10%] w-[80vw] h-[80vh] bg-linear-to-tl from-rose-900/10 via-blue-900/10 to-transparent rounded-full blur-[120px] opacity-30"></div>
    <div class="absolute inset-0 bg-radial-at-c from-transparent via-[#050505]/50 to-[#050505]/90"></div>
</div>

<!-- Fallback background -->
<div class="fixed inset-0 z-[-3] bg-[#050505]"></div>

<div class="fixed top-6 right-6 z-50">
    {#if $currentUser}
        <div class="relative">
            <button 
                on:click={() => showProfileMenu = !showProfileMenu} 
                class="flex items-center gap-3 pl-4 pr-1.5 py-1.5 bg-[#0e0e0e]/80 backdrop-blur-xl border border-white/10 rounded-full hover:bg-white/5 hover:border-white/20 transition-all shadow-lg group cursor-pointer"
            >
                <span class="text-xs font-medium text-neutral-400 group-hover:text-white transition-colors">{$currentUser.name}</span>
                <div class="w-8 h-8 rounded-full bg-linear-to-tr from-indigo-500 to-purple-500 border border-white/10 shadow-inner"></div>
            </button>

            {#if showProfileMenu}
                <div 
                    transition:fly={{ y: 10, duration: 200 }} 
                    class="absolute right-0 mt-2 w-48 bg-[#0e0e0e] border border-white/10 rounded-2xl shadow-2xl overflow-hidden backdrop-blur-xl p-1"
                >
                    <button 
                        on:click={handleLogout} 
                        class="w-full text-left px-3 py-2.5 text-xs font-medium text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 rounded-xl flex items-center gap-2 transition-colors cursor-pointer"
                    >
                        <LogOut class="w-3.5 h-3.5" /> Sign Out
                    </button>
                </div>
            {/if}
        </div>
    {:else}
        <button 
            on:click={handleLogin} 
            disabled={isLoggingIn}
            class="flex items-center gap-2 px-4 py-2 bg-[#0e0e0e]/50 backdrop-blur-md border border-white/10 text-neutral-400 text-xs font-medium rounded-full hover:bg-white/10 hover:text-white hover:border-white/20 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-wait"
        >
            {#if isLoggingIn}
                <Loader2 class="w-3.5 h-3.5 animate-spin" />
            {:else}
                <LogIn class="w-3.5 h-3.5" /> 
            {/if}
            <span>Sign In</span>
        </button>
    {/if}
</div>

<main class="w-full min-h-screen text-slate-200 pb-32 relative font-sans antialiased selection:bg-indigo-500/30 selection:text-white bg-transparent">
    {@render children()}
</main>

<nav class="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50">
    <div class="flex items-center gap-2 bg-black/60 backdrop-blur-2xl border border-white/10 p-2 rounded-2xl shadow-2xl shadow-black/50 ring-1 ring-white/5 transition-all hover:bg-black/70 hover:scale-[1.02] hover:border-white/15">
        
        <a href="/" class="relative px-5 py-3 rounded-xl transition-all duration-300 group flex flex-col items-center gap-1 {$page.url.pathname === '/' ? 'bg-white/10 text-white shadow-inner' : 'text-neutral-500 hover:text-white hover:bg-white/5'}">
            <Home class="w-5 h-5 transition-transform group-hover:scale-110" />
            {#if $page.url.pathname === '/'}
                <span class="absolute bottom-1.5 w-1 h-1 bg-white rounded-full"></span>
            {/if}
        </a>

        <a href="/explore" class="relative px-5 py-3 rounded-xl transition-all duration-300 group flex flex-col items-center gap-1 {$page.url.pathname === '/explore' ? 'bg-white/10 text-white shadow-inner' : 'text-neutral-500 hover:text-white hover:bg-white/5'}">
            <Compass class="w-5 h-5 transition-transform group-hover:scale-110" />
            {#if $page.url.pathname === '/explore'}
                <span class="absolute bottom-1.5 w-1 h-1 bg-white rounded-full"></span>
            {/if}
        </a>

        <div class="w-px h-8 bg-white/5 mx-1"></div>

        <a href="/profile" class="relative px-5 py-3 rounded-xl transition-all duration-300 group flex flex-col items-center gap-1 {$page.url.pathname === '/profile' ? 'bg-white/10 text-white shadow-inner' : 'text-neutral-500 hover:text-white hover:bg-white/5'}">
            <UserIcon class="w-5 h-5 transition-transform group-hover:scale-110" />
            {#if $page.url.pathname === '/profile'}
                <span class="absolute bottom-1.5 w-1 h-1 bg-white rounded-full"></span>
            {/if}
        </a>
    </div>
</nav>

<style>
    .grain-texture {
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
        background-size: 200px 200px;
        filter: contrast(120%) brightness(90%);
    }

    .bg-radial-at-c {
        background-image: radial-gradient(circle at center, var(--tw-gradient-stops));
    }

    @keyframes pulse-slow {
        0%, 100% { opacity: 0.4; transform: scale(1); }
        50% { opacity: 0.3; transform: scale(1.05); }
    }
    
    .animate-pulse-slow {
        animation: pulse-slow 8s ease-in-out infinite;
    }
</style>