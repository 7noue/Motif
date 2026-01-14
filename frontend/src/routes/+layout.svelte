<script>
    import favicon from '$lib/assets/favicon.svg';
    import { Home, Compass, User, Layers } from 'lucide-svelte';
    import { page } from '$app/stores';
        
    let { children } = $props();
</script>

<svelte:head>
    <link rel="icon" href={favicon} />
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</svelte:head>

<!-- Background with visible gradients and subtle noise -->
<div class="fixed inset-0 z-[-1] bg-[#09090b] pointer-events-none">
    <!-- Base dark color -->
    <div class="absolute inset-0 bg-[#09090b]"></div>
    
    <!-- Subtle gradient overlay - VISIBLE -->
    <div class="absolute inset-0 bg-gradient-to-br from-[#0f0f15] via-[#09090b] to-[#101016] opacity-90"></div>
    
    <!-- Visible gradient orbs -->
    <div class="absolute top-[-10%] left-[20%] w-[500px] h-[500px] bg-gradient-to-br from-yellow-500/15 via-transparent to-transparent rounded-full blur-[120px] opacity-40"></div>
    <div class="absolute bottom-[-10%] right-[10%] w-[600px] h-[600px] bg-gradient-to-bl from-blue-600/20 via-transparent to-transparent rounded-full blur-[120px] opacity-40"></div>
    
    <!-- Center subtle gradient -->
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-br from-purple-500/5 via-transparent to-blue-500/5 rounded-full blur-[150px] opacity-30"></div>
    
    <!-- SUBTLE NOISE TEXTURE - Very subtle so it doesn't hide gradients -->
    <div class="absolute inset-0 opacity-[0.015] mix-blend-overlay grain-texture"></div>
</div>

<main class="w-full min-h-screen text-slate-200 pb-32 relative font-sans antialiased selection:bg-yellow-400/30 selection:text-yellow-200">
    {@render children()}
</main>

<nav class="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50">
    <div class="flex items-center gap-1 bg-[#18181b]/80 backdrop-blur-xl border border-white/10 p-1.5 rounded-2xl shadow-2xl shadow-black/80 ring-1 ring-white/5">
        
        <a href="/" class="group relative px-4 py-3 rounded-xl transition-all duration-300 ease-out flex flex-col items-center gap-1 {$page.url.pathname === '/' ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}">
            <Home class="w-5 h-5" />
            {#if $page.url.pathname === '/'} <span class="absolute -bottom-1 w-1 h-1 rounded-full bg-yellow-400"></span> {/if}
        </a>

        <a href="/explore" class="group relative px-4 py-3 rounded-xl transition-all duration-300 ease-out flex flex-col items-center gap-1 {$page.url.pathname === '/explore' ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}">
            <Compass class="w-5 h-5" />
        </a>

        <div class="w-px h-6 bg-white/10 mx-1"></div>

        <a href="/profile" class="group relative px-4 py-3 rounded-xl transition-all duration-300 ease-out flex flex-col items-center gap-1 {$page.url.pathname === '/profile' ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}">
            <User class="w-5 h-5" />
        </a>
    </div>
</nav>

<style global>
    @import "tailwindcss"; 
    
    :root {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    .font-mono {
        font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
    }
    
    /* PERFORMANT GRAIN TEXTURE - Very subtle */
    .grain-texture {
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
        background-size: 256px 256px;
        filter: contrast(140%) brightness(100%);
    }
    
    /* Alternative: Even more subtle CSS grain */
    .subtle-grain {
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(255,255,255,0.03) 0.5px, transparent 0.5px),
            radial-gradient(circle at 90% 80%, rgba(255,255,255,0.02) 0.5px, transparent 0.5px);
        background-size: 80px 80px, 60px 60px;
        opacity: 0.02;
    }
    
    /* Ensure gradients are visible */
    .opacity-40 {
        opacity: 0.4 !important;
    }
    
    /* Smooth scrolling */
    html {
        scroll-behavior: smooth;
    }
    
    /* Selection styling */
    ::selection {
        background: rgba(250, 204, 21, 0.3);
        color: rgb(254, 240, 138);
    }
    
    /* Better contrast for text */
    .text-slate-200 {
        color: rgb(226 232 240);
    }
    
    /* Performance optimizations */
    * {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
</style>