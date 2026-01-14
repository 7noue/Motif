<script>
    import { 
        Search, Film, Star, ArrowRight, Sparkles, X, 
        Zap, Heart, Coffee, Moon, Bookmark,
        Users, User, Check, Plus, LogIn, LogOut, AlertCircle,
        ShieldCheck, Flame, Sofa, Beer,
        Cloud, Play, Brain, Gauge, TrendingUp, BarChart3, Grid3X3
    } from 'lucide-svelte';
    import { fade, fly } from 'svelte/transition';

    // --- CONFIGURATION ---
    const API_URL = 'http://localhost:8000/api/search';
    
    // --- AUTH STATE ---
    let currentUser = null;
    let showProfileMenu = false;
    let toast = null; 
    let toastTimeout;

    // --- APP STATE ---
    let searchQuery = '';
    let movies = []; 
    let isLoading = false;
    let hasSearched = false;
    let selectedMovie = null; 
    let activeContext = { social: null, mood: null };

    // --- INTERACTIVE STATE ---
    let movieInteractionState = { 
        isHearted: false, 
        isBookmarked: false, 
        tags: [], 
        customTagsAdded: 0,
        userTagVotes: 0    
    };
    let showAddTagInput = false;
    let newTagValue = '';

    const MAX_VOTES = 3; 
    const MAX_CUSTOM_TAGS = 3; 

    // --- UI CONSTANTS ---
    const CONTEXT_OPTIONS = {
        social: [
            { id: 'parents', label: 'With Parents', icon: ShieldCheck }, 
            { id: 'date', label: 'Date Night', icon: Heart },
            { id: 'group', label: 'Drinking/Party', icon: Beer }, 
            { id: 'solo', label: 'Solo Watch', icon: User }
        ],
        mood: [
            { id: 'hype', label: 'High Energy', icon: Zap },
            { id: 'chill', label: 'Chill', icon: Sofa }, 
            { id: 'deep', label: 'Deep', icon: Moon }
        ]
    };

    const VIBES = [
        { label: "Cyberpunk", icon: Zap },
        { label: "Cozy", icon: Coffee },
        { label: "Rainy", icon: Cloud },
        { label: "Melancholic", icon: Moon },
        { label: "Dreamy", icon: Sparkles },
    ];

    // --- LANDING PAGE DATA ---
    let landingStats = [
        { label: "Films Indexed", value: "42.8K", trend: "+12%" },
        { label: "Vibe Accuracy", value: "94%", trend: "Match Rate" },
        { label: "Active Users", value: "18.2K", trend: "+24%" }
    ];
    
    let landingFeatures = [
        { icon: Brain, title: "Semantic Search", desc: "Find films by mood, not just keywords" },
        { icon: Zap, title: "Context-Aware", desc: "Recommendations adapt to your situation" },
        { icon: Gauge, title: "Vibe Analysis", desc: "Understand a film's energy before watching" },
        { icon: Users, title: "Social Curation", desc: "Collective tagging builds better suggestions" }
    ];

    // --- HELPERS ---
    function showToast(message, type = 'error') {
        clearTimeout(toastTimeout);
        toast = { message, type };
        toastTimeout = setTimeout(() => { toast = null; }, 3000);
    }

    const handleLogin = () => {
        setTimeout(() => {
            currentUser = { name: 'Mark', avatar: null };
            showToast('Welcome back, Mark.', 'success');
        }, 500);
    };

    const handleLogout = () => {
        currentUser = null;
        showProfileMenu = false;
        showToast('Logged out.', 'success');
    };

    const requireAuth = () => {
        if (!currentUser) {
            showToast("Sign in to curate vibes.", 'error');
            return false;
        }
        return true;
    };

    // Deterministic random for UI Consistency (Gradients only)
    function pseudoRandom(str) {
        let hash = 0;
        if (!str) return 0.5;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = (hash << 5) - hash + char;
            hash = hash & hash; 
        }
        return Math.abs(hash) / 2147483647;
    }

    function getGradient(title) {
        const colors = [
            'from-rose-500 to-orange-600', 'from-violet-600 to-indigo-900',
            'from-emerald-500 to-teal-900', 'from-blue-600 to-cyan-800', 'from-amber-700 to-yellow-600',
        ];
        return colors[Math.floor(pseudoRandom(title) * colors.length)];
    }

    // --- CORE LOGIC: DATA TRANSFORMATION ---
    const enrichMovieData = (apiMovie) => {
        const seed = apiMovie.title + apiMovie.movie_id;
        const r = (offset = 0) => pseudoRandom(seed + offset);

        const posterUrl = apiMovie.posterUrl || null; 
        const year = apiMovie.release_date || 'N/A';
        const score = apiMovie.score || 0;
        const runtime = apiMovie.runtime || "Unknown";
        
        const vibeDynamics = {
            pacing: { 
                label: "Pacing", 
                val: apiMovie.vibe_pacing || 50, 
                low: "Slow", high: "Fast" 
            },
            complexity: { 
                label: "Cognitive Load", 
                val: apiMovie.vibe_complexity || 50, 
                low: "Light", high: "Heavy" 
            },
            atmosphere: { 
                label: "Mood", 
                val: apiMovie.vibe_atmosphere || 50, 
                low: "Dark", high: "Bright" 
            }
        };

        const contextPitches = [
            "Perfect for when you want to feel smart but don't want to work for it.",
            "The visual equivalent of a double espresso.",
            "Slow, methodical, and deeply rewarding.",
            "Zero cognitive load. Just vibes.",
            "A cinematic warm hug."
        ];
        const momentSentence = contextPitches[Math.floor(r(1) * contextPitches.length)];

        const palettes = [
            { name: "Neon Noir", colors: ["#f43f5e", "#8b5cf6", "#1e293b"] },
            { name: "Industrial", colors: ["#94a3b8", "#475569", "#0f172a"] },
            { name: "Warm Retro", colors: ["#f59e0b", "#78350f", "#fffbeb"] },
            { name: "Miami Sunset", colors: ["#f97316", "#db2777", "#8b5cf6"] },
        ];
        const palette = palettes[Math.floor(r(5) * palettes.length)];

        const socialBadges = [];
        if (activeContext.social === 'parents') socialBadges.push({ text: "Safe Choice", icon: ShieldCheck });
        else if (activeContext.social === 'group') socialBadges.push({ text: "Crowd Pleaser", icon: Flame });
        else if (activeContext.social === 'date') socialBadges.push({ text: "Romantic", icon: Heart });
        else socialBadges.push({ text: "Immersive", icon: User });

        const initialTags = (apiMovie.genres || []).map(name => ({
            name, 
            score: Math.floor(r(name) * 50) + 1, 
            userVoted: false, 
            isCustom: false 
        }));

        return {
            ...apiMovie,
            year,
            score,
            runtime,
            posterUrl,
            vibeDynamics,
            momentSentence,
            palette,
            socialBadges,
            initialTags,
            certData: apiMovie.certData || { code: "NR", reason: "Not Rated" },
            director: "Unknown", 
            cast: apiMovie.cast || [],
            recommendations: [] 
        };
    };

    function toggleContext(type, value) {
        activeContext[type] = activeContext[type] === value ? null : value;
    }

    // --- SEARCH FUNCTION ---
    async function semanticSearch(queryOverride = null) {
        const query = queryOverride || searchQuery.trim();
        if (!query) return;
        
        searchQuery = query;
        hasSearched = true;
        isLoading = true;
        movies = [];
        selectedMovie = null;

        const contextString = Object.values(activeContext).filter(Boolean).join(' ');
        const finalQuery = `${query} ${contextString}`.trim();

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    query: finalQuery,
                    top_k: 9 
                })
            });

            if (!response.ok) throw new Error("Search failed");
            
            const result = await response.json();
            movies = result.map(enrichMovieData);

        } catch (e) { 
            console.error(e);
            showToast("Failed to connect to Motif Core.", "error");
        } finally { 
            isLoading = false; 
        }
    }

    const resetView = () => {
        searchQuery = ''; movies = []; hasSearched = false; selectedMovie = null;
        activeContext = { social: null, mood: null };
        document.body.style.overflow = 'auto';
    };

    // --- MODAL & INTERACTION LOGIC ---
    const openDetail = movie => {
        selectedMovie = movie;
        movieInteractionState = {
            isHearted: false, 
            isBookmarked: false, 
            tags: JSON.parse(JSON.stringify(movie.initialTags)), 
            customTagsAdded: 0,
            userTagVotes: 0 
        };
        showAddTagInput = false;
        newTagValue = '';
        document.body.style.overflow = 'hidden';
    };

    const closeDetail = () => {
        selectedMovie = null;
        document.body.style.overflow = 'auto';
    };

    const toggleInteraction = (type) => {
        if (!requireAuth()) return;
        const newState = { ...movieInteractionState };
        if (type === 'heart') newState.isHearted = !newState.isHearted;
        if (type === 'bookmark') newState.isBookmarked = !newState.isBookmarked;
        movieInteractionState = newState;
    };

    const voteTag = (index) => {
        if (!requireAuth()) return;
        const newTags = [...movieInteractionState.tags];
        const tag = { ...newTags[index] }; 
        
        if (tag.userVoted) {
            tag.userVoted = false; 
            tag.score -= 1;
            movieInteractionState.userTagVotes -= 1; 
            if (tag.isCustom && tag.score <= 0) {
                newTags.splice(index, 1); 
                movieInteractionState.customTagsAdded -= 1;
            } else { 
                newTags[index] = tag; 
            }
        } else {
            if (movieInteractionState.userTagVotes >= MAX_VOTES) {
                showToast("Limit 3 votes per movie.", "error"); 
                return;
            }
            tag.userVoted = true; 
            tag.score += 1; 
            movieInteractionState.userTagVotes += 1; 
            newTags[index] = tag;
        }
        movieInteractionState = { ...movieInteractionState, tags: newTags };
    };

    const addNewTag = () => {
        if (!requireAuth()) return;
        const cleanTag = newTagValue.trim();
        if (!cleanTag) return;
        if (movieInteractionState.userTagVotes >= MAX_VOTES) { 
            showToast("Limit 3 votes per movie.", "error"); 
            return; 
        }
        const existingIndex = movieInteractionState.tags.findIndex(t => t.name.toLowerCase() === cleanTag.toLowerCase());
        if (existingIndex !== -1) {
            if (!movieInteractionState.tags[existingIndex].userVoted) {
                voteTag(existingIndex); 
                showToast('Upvoted existing tag!', 'success');
            }
            newTagValue = ''; showAddTagInput = false; return;
        }
        if (movieInteractionState.customTagsAdded >= MAX_CUSTOM_TAGS) {
            showToast('Custom tag limit reached.', 'error'); return;
        }
        const newTag = { name: cleanTag, score: 1, userVoted: true, isCustom: true };
        movieInteractionState = { 
            ...movieInteractionState, 
            tags: [newTag, ...movieInteractionState.tags], 
            customTagsAdded: movieInteractionState.customTagsAdded + 1,
            userTagVotes: movieInteractionState.userTagVotes + 1
        };
        newTagValue = ''; showAddTagInput = false;
    };

    function handleKeydown(e) { if (e.key === 'Escape') closeDetail(); }
</script>

<svelte:window on:keydown={handleKeydown} />

<!-- AUTH & TOAST COMPONENTS -->
<div class="fixed top-6 right-6 z-50 flex items-center gap-4">
    {#if currentUser}
        <div class="relative">
            <button on:click={() => showProfileMenu = !showProfileMenu} class="flex items-center gap-2 pl-3 pr-1 py-1 bg-white/10 border border-white/10 rounded-full hover:bg-white/15 transition-all backdrop-blur-md">
                <span class="text-xs font-medium text-white/90">{currentUser.name}</span>
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

{#if toast}
    <div transition:fly={{ y: -20, duration: 300 }} class="fixed top-6 left-1/2 transform -translate-x-1/2 z-[200]">
        <div class="px-6 py-3 rounded-full shadow-2xl border backdrop-blur-md flex items-center gap-3 bg-neutral-900/90 border-neutral-700 text-neutral-200">
            {#if toast.type === 'error'} <AlertCircle class="w-4 h-4" /> {:else} <Check class="w-4 h-4 text-emerald-400" /> {/if}
            <span class="text-sm font-medium">{toast.message}</span>
        </div>
    </div>
{/if}

<!-- LANDING PAGE -->
{#if !hasSearched}
    <div class="relative z-10 w-full max-w-7xl mx-auto px-6 flex flex-col items-center justify-center h-screen">
        <!-- Minimal Header -->
        <div class="flex flex-col items-center mb-16">
            <div class="relative flex items-center justify-center w-24 h-24 bg-black border border-white/10 rounded-2xl shadow-2xl backdrop-blur-sm mb-8">
                <Film class="w-12 h-12 text-white" />
            </div>
            <h1 class="text-6xl font-semibold tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white to-white/50 mb-6">Motif</h1>
            <p class="text-neutral-400 text-lg font-light tracking-wide text-center">Films for the moment. Not just the plot.</p>
        </div>

        <!-- STATS BAR (Apple-style minimalism) -->
        <div class="flex items-center justify-center gap-8 mb-16">
            {#each landingStats as stat}
                <div class="text-center">
                    <div class="text-4xl font-bold text-white mb-2">{stat.value}</div>
                    <div class="text-xs text-neutral-500 font-medium tracking-widest uppercase">{stat.label}</div>
                    <div class="flex items-center justify-center gap-1 mt-1 text-[10px] text-emerald-400">
                        <TrendingUp class="w-3 h-3" />
                        {stat.trend}
                    </div>
                </div>
            {/each}
        </div>

        <!-- SEARCH SECTION (Inspired by modal layout) -->
        <div class="w-full max-w-2xl relative">
            <div class="w-full relative group z-20">
                <div class="relative flex items-center p-2 bg-white/[0.03] hover:bg-white/[0.05] focus-within:bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl transition-all duration-200 shadow-lg">
                    <Search class="w-6 h-6 text-neutral-500 group-focus-within:text-indigo-400 ml-4 transition-colors duration-200" />
                    <input type="text" bind:value={searchQuery} placeholder="Describe the occasion..." class="w-full h-12 bg-transparent text-white outline-none px-4 placeholder-neutral-600 font-light" />
                    <button on:click={() => semanticSearch()} disabled={isLoading || !searchQuery} class="flex items-center justify-center w-10 h-10 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white transition-all">
                        <ArrowRight class="w-5 h-5" />
                    </button>
                </div>
            </div>
            
            <!-- QUICK VIBES -->
            <div class="mt-6 flex flex-wrap justify-center gap-2 w-full max-w-3xl">
                {#each VIBES as vibe}
                    <button on:click={() => semanticSearch(vibe.label)} class="flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium border border-white/5 bg-white/[0.02] hover:bg-white/10 hover:border-white/20 hover:text-indigo-300 text-neutral-400 transition-all duration-200 active:scale-95">
                        <svelte:component this={vibe.icon} class="w-3 h-3" /> {vibe.label}
                    </button>
                {/each}
            </div>
        </div>

        <!-- FEATURES GRID (Minimal dashboard style) -->
        <div class="mt-24 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full max-w-5xl">
            {#each landingFeatures as feature}
                <div class="group p-6 bg-white/[0.02] border border-white/5 rounded-2xl hover:border-white/10 hover:bg-white/[0.04] transition-all duration-300">
                    <div class="w-10 h-10 rounded-xl bg-white/[0.05] border border-white/5 flex items-center justify-center mb-4 group-hover:bg-white/[0.1] transition-colors">
                        <svelte:component this={feature.icon} class="w-5 h-5 text-indigo-400" />
                    </div>
                    <h3 class="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                    <p class="text-sm text-neutral-400 font-light">{feature.desc}</p>
                </div>
            {/each}
        </div>

        <!-- MINIMAL FOOTER -->
        <div class="mt-24 pt-8 border-t border-white/5 text-center">
            <p class="text-xs text-neutral-600">Search across 42,853 films with semantic understanding</p>
        </div>
    </div>

{:else}
<!-- SEARCH RESULTS VIEW -->
<div class="relative z-10 w-full max-w-7xl mx-auto px-6 flex flex-col items-center transition-all duration-500 cubic-out pt-8 justify-start">

    <button on:click={resetView} class="flex flex-row items-center group transition-all duration-300 cursor-pointer outline-none mb-6 gap-4">
        <div class="relative flex items-center justify-center bg-black border border-white/10 rounded-xl shadow-2xl backdrop-blur-sm transition-all duration-300 w-10 h-10">
            <Film class="text-white w-5 h-5" />
        </div>
        <h1 class="font-semibold tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white to-white/50 transition-all duration-300 text-3xl">Motif</h1>
    </button>

    <div class="w-full max-w-2xl relative z-20 flex flex-col gap-4">
        <div class="flex flex-wrap justify-center gap-2 transition-all duration-300 {isLoading ? 'opacity-50' : 'opacity-100'}">
            <div class="flex bg-white/[0.03] p-1 rounded-full border border-white/5 backdrop-blur-md">
                {#each CONTEXT_OPTIONS.social as opt}
                    <button on:click={() => toggleContext('social', opt.id)} class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 active:scale-95 {activeContext.social === opt.id ? 'bg-indigo-500 text-white shadow-lg' : 'text-neutral-500 hover:text-white hover:bg-white/5'}">
                        <svelte:component this={opt.icon} class="w-3 h-3" /> {opt.label}
                    </button>
                {/each}
            </div>
            <div class="flex bg-white/[0.03] p-1 rounded-full border border-white/5 backdrop-blur-md">
                {#each CONTEXT_OPTIONS.mood as opt}
                    <button on:click={() => toggleContext('mood', opt.id)} class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 active:scale-95 {activeContext.mood === opt.id ? 'bg-purple-500 text-white shadow-lg' : 'text-neutral-500 hover:text-white hover:bg-white/5'}">
                        <svelte:component this={opt.icon} class="w-3 h-3" /> {opt.label}
                    </button>
                {/each}
            </div>
        </div>

        <form on:submit|preventDefault={() => semanticSearch()} class="w-full relative group z-20">
            <div class="relative flex items-center p-2 bg-white/[0.03] hover:bg-white/[0.05] focus-within:bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl transition-all duration-200 shadow-lg">
                <Search class="w-6 h-6 text-neutral-500 group-focus-within:text-indigo-400 ml-4 transition-colors duration-200" />
                <input type="text" bind:value={searchQuery} placeholder="Describe the occasion..." class="w-full h-12 bg-transparent text-white outline-none px-4 placeholder-neutral-600 font-light" disabled={isLoading} />
                <button type="submit" disabled={isLoading || !searchQuery} class="flex items-center justify-center w-10 h-10 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white transition-all">
                    <ArrowRight class="w-5 h-5" />
                </button>
            </div>
        </form>
    </div>
    
    <div class="mt-6 flex flex-wrap justify-center gap-2 w-full max-w-3xl transition-opacity duration-200 {isLoading ? 'opacity-50 pointer-events-none' : 'opacity-100'}">
        {#each VIBES as vibe}
            <button on:click={() => semanticSearch(vibe.label)} class="flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium border border-white/5 bg-white/[0.02] hover:bg-white/10 hover:border-white/20 hover:text-indigo-300 text-neutral-400 transition-all duration-200 active:scale-95">
                <svelte:component this={vibe.icon} class="w-3 h-3" /> {vibe.label}
            </button>
        {/each}
    </div>

    {#if hasSearched}
        <div class="w-full pb-20 max-w-7xl mt-8">
            <section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {#if isLoading}
                    {#each Array(6) as _} <div class="h-64 rounded-3xl bg-white/[0.03] border border-white/5 animate-pulse"></div> {/each}
                {:else}
                    {#each movies as movie, i (movie.movie_id || i)}
                        <button on:click={() => openDetail(movie)} in:fly={{ y: 20, duration: 300, delay: i * 50 }} class="group relative w-full flex flex-col h-full bg-[#0a0a0a] border border-white/5 rounded-3xl overflow-hidden hover:-translate-y-1 hover:shadow-2xl hover:border-white/10 text-left">
                            <div class="h-40 w-full relative overflow-hidden shrink-0">
                                <div class="absolute inset-0 bg-gradient-to-br {getGradient(movie.title)} opacity-40 group-hover:opacity-60 transition-opacity"></div>
                                <div class="absolute inset-0 opacity-20 bg-[url('https://grainy-gradients.vercel.app/noise.svg')]"></div>
                                <div class="absolute inset-0 bg-gradient-to-t from-[#0a0a0a] via-transparent to-transparent"></div>
                                
                                {#if movie.posterUrl}
                                    <img src={movie.posterUrl} alt={movie.title} class="absolute inset-0 w-full h-full object-cover opacity-50 mix-blend-overlay group-hover:opacity-70 transition-opacity" />
                                {/if}

                                <div class="absolute top-3 right-3 flex items-center gap-1.5 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-lg border border-white/5">
                                    <Star class="w-3 h-3 text-indigo-400 fill-indigo-400" />
                                    <span class="text-xs font-bold text-white">{Math.round(movie.score * 100)}%</span>
                                </div>
                            </div>
                            <div class="p-5 flex flex-col h-full relative z-10 -mt-6">
                                <h2 class="text-xl font-bold text-white leading-tight mb-2">{movie.title}</h2>
                                <p class="text-neutral-400 text-sm font-light leading-relaxed line-clamp-3 mb-4">{movie.overview}</p>
                                <div class="mt-auto border-t border-white/5 pt-4 w-full">
                                    <div class="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-white/5 border border-white/10 text-[10px] uppercase text-neutral-400 font-medium">
                                        <svelte:component this={movie.socialBadges[0].icon} class="w-3 h-3" />
                                        {movie.socialBadges[0].text}
                                    </div>
                                </div>
                            </div>
                        </button>
                    {/each}
                {/if}
            </section>
        </div>
    {/if}
</div>
{/if}

<!-- MOVIE DETAIL MODAL (KEEP EXACTLY AS IS) -->
{#if selectedMovie}
    <div 
        transition:fade={{ duration: 150 }} 
        class="fixed inset-0 z-[100] bg-black/80 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 cursor-default select-none" 
        on:click={closeDetail}
    >
        
        <div 
            on:click|stopPropagation 
            transition:fly={{ y: 40, duration: 300 }} 
            class="relative w-full max-w-4xl h-[90vh] bg-[#0e0e0e] border border-white/10 rounded-[24px] shadow-2xl overflow-hidden flex flex-col md:flex-row"
        >
            
            <button on:click={closeDetail} class="absolute top-4 right-4 z-50 p-2 bg-black/40 backdrop-blur-md rounded-full text-white/70 hover:text-white border border-white/10 hover:bg-white/10 transition-colors cursor-pointer"><X class="w-4 h-4" /></button>

            <div class="w-full md:w-5/12 bg-black/50 border-r border-white/5 flex flex-col group shrink-0 relative overflow-hidden">
                
                <div class="flex-1 relative overflow-hidden min-h-0">
                    {#if selectedMovie.posterUrl}
                        <img src={selectedMovie.posterUrl} alt={selectedMovie.title} class="w-full h-full object-cover" />
                    {:else}
                         <div class="w-full h-full bg-neutral-900 flex items-center justify-center text-neutral-700">No Image</div>
                    {/if}
                    <div class="absolute inset-0 bg-gradient-to-t from-[#0e0e0e] via-[#0e0e0e]/40 to-transparent opacity-90"></div>
                    <div class="absolute inset-0 bg-gradient-to-r from-black/50 to-transparent"></div>
                    
                    <div class="absolute bottom-0 left-0 w-full p-5 z-20">
                        <h2 class="text-3xl font-bold text-white tracking-tighter leading-none mb-2 drop-shadow-xl">{selectedMovie.title}</h2>
                        
                        <div class="flex flex-wrap items-center gap-2 text-xs font-medium text-white/80">
                            <span class="text-white">{selectedMovie.year}</span>
                            <span class="w-0.5 h-0.5 rounded-full bg-white/40"></span>
                            <span>{selectedMovie.runtime}</span>
                        </div>
                    </div>
                </div>

                <div class="p-5 flex flex-col gap-5 bg-[#0e0e0e] flex-shrink-0">
                    
                    <div class="flex items-center gap-3 border-b border-white/5 pb-3">
                        <div class="flex -space-x-1.5">
                            {#each selectedMovie.palette.colors as color}
                                <div class="w-2.5 h-2.5 rounded-full border border-white/10 shadow-sm" style="background-color: {color};"></div>
                            {/each}
                        </div>
                        <span class="text-[9px] font-bold uppercase tracking-widest text-white/50">{selectedMovie.palette.name}</span>
                    </div>

                    <div class="grid grid-cols-3 gap-2 py-2 border-b border-white/5">
                        <div class="flex flex-col items-center">
                            <span class="text-[9px] font-bold text-neutral-500 uppercase tracking-widest mb-0.5">Match</span>
                            <span class="text-emerald-400 font-bold text-lg">{Math.round(selectedMovie.score * 100)}%</span>
                        </div>
                        <div class="flex flex-col items-center border-l border-white/5">
                            <span class="text-[9px] font-bold text-neutral-500 uppercase tracking-widest mb-0.5">Pop</span>
                            <span class="text-yellow-500 font-bold text-lg flex items-center gap-1"><Star class="w-3 h-3 fill-current" /> {Math.round(selectedMovie.popularity)/10}</span>
                        </div>
                        <div class="flex flex-col items-center border-l border-white/5 text-center px-1">
                            <span class="text-[9px] font-bold text-neutral-500 uppercase tracking-widest mb-0.5">Rating</span>
                            <div class="flex flex-col items-center leading-none">
                                <span class="text-white font-bold text-lg">{selectedMovie.certData.code}</span>
                                <span class="text-[7px] text-neutral-500 uppercase tracking-tight mt-0.5 w-full truncate px-1" title={selectedMovie.certData.reason}>{selectedMovie.certData.reason}</span>
                            </div>
                        </div>
                    </div>

                    <div class="space-y-3">
                        <h3 class="text-[9px] font-bold text-neutral-500 uppercase tracking-widest flex items-center gap-2">
                            <Gauge class="w-3 h-3" /> Vibe Signature
                        </h3>
                        {#each Object.values(selectedMovie.vibeDynamics) as metric}
                            <div>
                                <div class="flex justify-between items-end text-[8px] mb-1 uppercase font-medium tracking-wider">
                                    <span class="text-neutral-500">{metric.low}</span>
                                    <span class="text-white font-bold">{metric.label}</span>
                                    <span class="text-neutral-500">{metric.high}</span>
                                </div>
                                <div class="h-0.5 w-full bg-white/10 rounded-full overflow-hidden">
                                    <div class="h-full bg-indigo-500/80 rounded-full shadow-[0_0_8px_rgba(99,102,241,0.5)]" style="width: {metric.val}%"></div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            </div>

            <div class="w-full md:w-7/12 flex flex-col bg-[#0e0e0e]">
                
                <div class="flex-1 overflow-y-auto custom-scrollbar p-6 md:p-8 flex flex-col gap-6">
                    
                    <div class="flex flex-wrap gap-2 pt-2">
                         {#each selectedMovie.socialBadges as badge}
                            <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] uppercase font-bold text-neutral-300">
                                <svelte:component this={badge.icon} class="w-3 h-3" /> {badge.text}
                            </div>
                        {/each}
                    </div>

                    <div class="border-l-2 border-indigo-500 pl-4 py-1">
                         <p class="text-lg text-white/90 font-light italic leading-snug">"{selectedMovie.momentSentence}"</p>
                    </div>

                    <div>
                         <h3 class="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-2">Story</h3>
                         <p class="text-sm text-neutral-400 font-light leading-relaxed">{selectedMovie.overview}</p>
                         
                         <div class="mt-4 pt-3 border-t border-white/5 flex flex-col gap-1.5 text-xs text-neutral-400">
                             <p><span class="text-white font-bold uppercase text-[10px] tracking-wider mr-2">Director</span> {selectedMovie.director}</p>
                             <p><span class="text-white font-bold uppercase text-[10px] tracking-wider mr-2">Cast</span> {selectedMovie.cast.join(", ")}</p>
                             <p><span class="text-white font-bold uppercase text-[10px] tracking-wider mr-2">Language</span> {selectedMovie.original_language}</p>
                         </div>
                    </div>

                    <div class="pt-2">
                        <h3 class="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-3 flex items-center justify-between">
                            <span class="flex items-center gap-2"><Brain class="w-3 h-3" /> Content Descriptors</span>
                            <span class="text-[9px] text-neutral-600 font-normal">Rank top {MAX_VOTES}</span>
                        </h3>
                        <div class="flex flex-wrap gap-2">
                            {#each movieInteractionState.tags as tag, i}
                                <button on:click={() => voteTag(i)} class="group relative flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs font-medium transition-all active:scale-95 select-none cursor-pointer {tag.userVoted ? 'bg-indigo-500/10 border-indigo-500/40 text-indigo-300 shadow-[0_0_10px_rgba(99,102,241,0.2)]' : 'bg-[#141414] border-white/5 text-neutral-400 hover:border-neutral-700 hover:text-neutral-300'}">
                                    <span>{tag.name}</span>
                                    <span class="text-[10px] opacity-40 group-hover:opacity-100 transition-opacity {tag.userVoted ? 'text-indigo-400' : ''}">{tag.score}</span>
                                </button>
                            {/each}
                            {#if movieInteractionState.customTagsAdded < MAX_CUSTOM_TAGS}
                                {#if !showAddTagInput}
                                    <button on:click={() => showAddTagInput = true} class="px-2.5 py-1.5 rounded-md border border-dashed border-white/10 text-neutral-600 text-xs hover:border-white/20 hover:text-neutral-400 transition-all cursor-pointer">+</button>
                                {:else}
                                    <form on:submit|preventDefault={addNewTag} class="flex items-center">
                                        <input bind:value={newTagValue} class="bg-transparent border-b border-indigo-500 text-white text-xs w-20 outline-none px-1 py-1" placeholder="Add..." autofocus on:blur={() => {if(!newTagValue) showAddTagInput=false}} />
                                    </form>
                                {/if}
                            {/if}
                        </div>
                    </div>

                    <div class="pt-4 border-t border-white/5 mt-auto">
                        <div class="flex items-center justify-between mb-3">
                            <h3 class="text-[10px] font-bold text-neutral-500 uppercase tracking-widest">Similarity Graph</h3>
                        </div>
                        
                        <div class="flex gap-3 overflow-x-auto pb-2 -mx-2 px-2 custom-scrollbar">
                            {#each selectedMovie.recommendations as rec}
                                <div class="min-w-[120px] w-[120px] group cursor-pointer">
                                    <div class="aspect-[2/3] rounded-lg overflow-hidden bg-neutral-900 border border-white/5 relative mb-2">
                                        <div class="absolute inset-0 bg-gradient-to-br {rec.gradient} opacity-40 group-hover:opacity-60 transition-all"></div>
                                        <div class="absolute inset-0 bg-black/20"></div>
                                        <div class="absolute inset-0 flex items-center justify-center p-2 text-center">
                                            <span class="text-[10px] font-bold text-white/50 uppercase tracking-widest">{rec.title}</span>
                                        </div>
                                        <div class="absolute top-1 right-1 px-1.5 py-0.5 bg-black/60 rounded text-[9px] font-bold text-emerald-400 border border-white/5">{rec.match}%</div>
                                    </div>
                                    <h4 class="text-xs font-medium text-neutral-300 truncate group-hover:text-white transition-colors">{rec.title}</h4>
                                    <span class="text-[10px] text-neutral-600">{rec.year}</span>
                                </div>
                            {/each}
                        </div>
                    </div>
                </div>

                <div class="p-6 border-t border-white/5 bg-[#0e0e0e] flex items-center gap-3 z-10">
                    <a 
                        href={selectedMovie.trailerUrl ? selectedMovie.trailerUrl : `https://www.youtube.com/results?search_query=${selectedMovie.title} trailer`} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        class="flex-1 h-12 rounded-xl bg-white text-black flex items-center justify-center gap-2 text-sm font-bold tracking-wide hover:bg-neutral-200 transition-all active:scale-95 shadow-lg shadow-white/10 cursor-pointer"
                    >
                        <Play class="w-4 h-4 fill-current" /> 
                        {selectedMovie.trailerUrl ? 'Watch Trailer' : 'Search Trailer'}
                    </a>
                    
                    <button on:click={() => toggleInteraction('heart')} class="w-12 h-12 rounded-xl border border-white/10 bg-white/5 text-neutral-300 flex items-center justify-center hover:bg-white/10 transition-all active:scale-95 cursor-pointer {movieInteractionState.isHearted ? 'text-rose-400 border-rose-500/30 bg-rose-500/10' : ''}">
                    <Heart class="w-5 h-5 {movieInteractionState.isHearted ? 'fill-current' : ''}" />
                    </button>

                    <button on:click={() => toggleInteraction('bookmark')} class="w-12 h-12 rounded-xl border border-white/10 bg-white/5 text-neutral-300 flex items-center justify-center hover:bg-white/10 transition-all active:scale-95 cursor-pointer {movieInteractionState.isBookmarked ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' : ''}">
                        <Bookmark class="w-5 h-5 {movieInteractionState.isBookmarked ? 'fill-current' : ''}" />
                    </button>
 
                </div>

            </div>
        </div>
    </div>
{/if}

<style>
    .custom-scrollbar::-webkit-scrollbar { height: 4px; width: 4px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: #262626; border-radius: 9999px; }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #404040; }
</style>