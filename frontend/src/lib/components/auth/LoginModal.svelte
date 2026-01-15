<script lang="ts">
    import { X } from 'lucide-svelte';
    import { currentUser, isLoginModalOpen } from '$lib/stores';
    import { fade, scale } from 'svelte/transition';

    function close() {
        $isLoginModalOpen = false;
    }

    async function handleGoogleLogin() {
        try {
            await currentUser.login();
            // If login succeeds, the store updates and we close the modal
            close(); 
        } catch (error) {
            console.error("Login Error:", error);
            // Toast is handled in stores.ts, so we just log here
        }
    }
</script>

<div 
    class="fixed inset-0 z-[200] flex items-center justify-center p-4 sm:p-6"
    role="dialog"
    aria-modal="true"
>
    <div 
        transition:fade={{ duration: 200 }}
        class="absolute inset-0 bg-black/80 backdrop-blur-sm cursor-pointer"
        onclick={close}
    ></div>

    <div 
        transition:scale={{ start: 0.95, duration: 200, opacity: 0 }}
        class="relative w-full max-w-sm bg-[#0e0e0e] border border-white/10 rounded-3xl overflow-hidden shadow-2xl shadow-indigo-500/10 flex flex-col items-center text-center p-8"
    >
        <button 
            onclick={close}
            class="absolute top-4 right-4 p-2 text-neutral-500 hover:text-white transition-colors rounded-full hover:bg-white/5 cursor-pointer"
        >
            <X class="w-4 h-4" />
        </button>

        <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-white/5 flex items-center justify-center mb-6">
            <div class="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
                <div class="w-3 h-3 rounded-full bg-white shadow-[0_0_10px_white]"></div>
            </div>
        </div>

        <h2 class="text-xl font-bold text-white tracking-tight mb-2">Unlock the Archive</h2>
        <p class="text-sm text-neutral-400 mb-8 leading-relaxed">
            Sign in to curate your vibe map, save hidden gems, and contribute to the ecosystem.
        </p>

        <button 
            onclick={handleGoogleLogin}
            class="w-full h-12 rounded-xl bg-white text-black font-bold text-sm flex items-center justify-center gap-3 hover:bg-neutral-200 transition-colors group cursor-pointer"
        >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Continue with Gmail
        </button>

        <p class="mt-6 text-[10px] text-neutral-600">
            By continuing, you agree to our <span class="text-neutral-400">Manifesto</span>.
        </p>
    </div>
</div>