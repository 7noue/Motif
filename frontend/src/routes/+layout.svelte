<script lang="ts">
    import favicon from '$lib/assets/favicon.svg';
    import { Home, Compass, User as UserIcon, LogIn, LogOut, Loader2 } from 'lucide-svelte';
    import { page } from '$app/stores';
    import { currentUser, toast } from '$lib/stores';
    import { fly } from 'svelte/transition';
    let { children } = $props();
    
    let showProfileMenu = $state(false);
    let isLoggingIn = $state(false);

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

<div class="fixed inset-0 z-[-2] bg-[#050505] pointer-events-none">
    <div class="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vh] bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-indigo-900/20 via-transparent to-transparent"></div>
    <div class="absolute bottom-[-20%] right-[-10%] w-[80vw] h-[80vh] bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-rose-900/10 via-transparent to-transparent"></div>
</div>

<div class="fixed top-6 right-6 z-50">
    {#if $currentUser}
        <div class="relative">
            <button 
                onclick={() => showProfileMenu = !showProfileMenu} 
                class="flex items-center gap-3 pl-4 pr-1.5 py-1.5 bg-[#111] border border-white/10 rounded-full hover:bg-[#222] transition-colors cursor-pointer"
            >
                <span class="text-xs font-medium text-neutral-400 group-hover:text-white transition-colors">{$currentUser.name}</span>
                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 border border-white/10"></div>
            </button>

            {#if showProfileMenu}
                <div 
                    transition:fly={{ y: 10, duration: 200 }} 
                    class="absolute right-0 mt-2 w-48 bg-[#111] border border-white/10 rounded-2xl overflow-hidden p-1 shadow-xl"
                >
                    <button 
                        onclick={handleLogout} 
                        class="w-full text-left px-3 py-2.5 text-xs font-medium text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 rounded-xl flex items-center gap-2 transition-colors cursor-pointer"
                    >
                        <LogOut class="w-3.5 h-3.5" /> Sign Out
                    </button>
                </div>
            {/if}
        </div>
    {:else}
        <button 
            onclick={handleLogin} 
            disabled={isLoggingIn}
            class="flex items-center gap-2 px-4 py-2 bg-[#111] border border-white/10 text-neutral-400 text-xs font-medium rounded-full hover:bg-[#222] hover:text-white transition-colors cursor-pointer disabled:opacity-50"
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

<main class="w-full min-h-screen text-slate-200 pb-32 relative font-sans antialiased bg-transparent">
    {@render children()}
</main>

<nav class="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50">
    <div class="flex items-center gap-2 bg-[#111] border border-white/10 p-2 rounded-2xl ring-1 ring-white/5">
        <a href="/" class="relative px-5 py-3 rounded-xl transition-colors duration-200 group flex flex-col items-center gap-1 {$page.url.pathname === '/' ? 'bg-white/10 text-white' : 'text-neutral-500 hover:text-white hover:bg-white/5'}">
            <Home class="w-5 h-5" />
        </a>

        <a href="/discovery" class="relative px-5 py-3 rounded-xl transition-colors duration-200 group flex flex-col items-center gap-1 {$page.url.pathname === '/discovery' ? 'bg-white/10 text-white' : 'text-neutral-500 hover:text-white hover:bg-white/5'}">
            <Compass class="w-5 h-5" />
        </a>

        <div class="w-px h-8 bg-white/5 mx-1"></div>

        <a href="/profile" class="relative px-5 py-3 rounded-xl transition-colors duration-200 group flex flex-col items-center gap-1 {$page.url.pathname === '/profile' ? 'bg-white/10 text-white' : 'text-neutral-500 hover:text-white hover:bg-white/5'}">
            <UserIcon class="w-5 h-5" />
        </a>
    </div>
</nav>