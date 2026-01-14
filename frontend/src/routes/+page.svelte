<script>
    import { 
        Search, Film, Star, ArrowRight, Sparkles, X, 
        Zap, Heart, Coffee, Moon, Bookmark,
        Users, User, Check, Plus, LogIn, LogOut, AlertCircle,
        ShieldCheck, Flame, Sofa, Beer,
        Cloud, Play, Brain, Gauge, ChevronDown
    } from 'lucide-svelte';
    import { fade, fly } from 'svelte/transition';

    // --- CONFIGURATION ---
    const API_URL = 'http://localhost:8000/api/search';
    
    import './layout.css';

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
            'from-rose-500/20 via-orange-600/10 to-transparent', 
            'from-violet-500/20 via-indigo-700/10 to-transparent',
            'from-emerald-500/20 via-teal-700/10 to-transparent', 
            'from-blue-500/20 via-cyan-700/10 to-transparent', 
            'from-amber-500/20 via-yellow-600/10 to-transparent',
        ];
        return colors[Math.floor(pseudoRandom(title) * colors.length)];
    }

    // --- CORE LOGIC: DATA TRANSFORMATION ---
    const enrichMovieData = (apiMovie) => {
        const seed = apiMovie.title + apiMovie.movie_id;
        const r = (offset = 0) => pseudoRandom(seed + offset);

        // Process REAL Data from Backend
        const posterUrl = apiMovie.posterUrl || null; 
        const year = apiMovie.release_date || 'N/A';
        const score = apiMovie.score || 0;
        const runtime = apiMovie.runtime || "Unknown";
        
        // Map Vibe Scores
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

        // UI Flair
        const contextPitches = [
            "Perfect for when you want to feel smart but don't want to work for it.",
            "The visual equivalent of a double espresso.",
            "Slow, methodical, and deeply rewarding.",
            "Zero cognitive load. Just vibes.",
            "A cinematic warm hug."
        ];
        const momentSentence = contextPitches[Math.floor(r(1) * contextPitches.length)];

        // Context Badges
        const socialBadges = [];
        if (activeContext.social === 'parents') socialBadges.push({ text: "Safe Choice", icon: ShieldCheck });
        else if (activeContext.social === 'group') socialBadges.push({ text: "Crowd Pleaser", icon: Flame });
        else if (activeContext.social === 'date') socialBadges.push({ text: "Romantic", icon: Heart });
        else socialBadges.push({ text: "Immersive", icon: User });

        // Tags
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

<!-- Toast -->
{#if toast}
    <div transition:fly={{ y: -20, duration: 300 }} class="fixed top-8 left-1/2 transform -translate-x-1/2 z-[200]">
        <div class="px-6 py-3.5 rounded-xl backdrop-blur-md border border-white/10 shadow-lg flex items-center gap-3 bg-black/90 text-slate-200">
            {#if toast.type === 'error'} 
                <AlertCircle class="w-4 h-4 text-red-400" />
            {:else} 
                <Check class="w-4 h-4 text-emerald-400" />
            {/if}
            <span class="text-sm font-medium">{toast.message}</span>
        </div>
    </div>
{/if}

<!-- User Menu -->
<div class="fixed top-6 right-6 z-50 flex items-center gap-4">
    {#if currentUser}
        <div class="relative">
            <button on:click={() => showProfileMenu = !showProfileMenu} class="flex items-center gap-3 pl-4 pr-3 py-2.5 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all backdrop-blur-md">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                    <span class="text-sm font-bold text-white">M</span>
                </div>
                <ChevronDown class="w-4 h-4 text-white/50" />
            </button>
            {#if showProfileMenu}
                <div transition:fly={{ y: 10, duration: 200 }} class="absolute right-0 mt-2 w-48 bg-black/90 backdrop-blur-md border border-white/10 rounded-xl shadow-xl overflow-hidden">
                    <div class="px-4 py-3 border-b border-white/10">
                        <p class="text-sm font-medium text-white">{currentUser.name}</p>
                        <p class="text-xs text-white/50 mt-1">Free Plan</p>
                    </div>
                    <button on:click={handleLogout} class="w-full text-left px-4 py-3 text-sm text-rose-400 hover:bg-white/5 flex items-center gap-2">
                        <LogOut class="w-4 h-4" /> Sign Out
                    </button>
                </div>
            {/if}
        </div>
    {:else}
        <button on:click={handleLogin} class="flex items-center gap-2.5 px-5 py-2.5 bg-white text-black font-semibold text-sm rounded-xl hover:bg-gray-200 transition-colors shadow-lg">
            <LogIn class="w-4 h-4" /> Sign In
        </button>
    {/if}
</div>

<!-- Main Content -->
<div class="relative z-10 w-full max-w-4xl mx-auto px-6 flex flex-col items-center transition-all duration-500 {hasSearched ? 'pt-12 justify-start' : 'min-h-screen justify-center'}">

    <!-- Minimal Logo -->
    <button on:click={resetView} class="flex flex-col items-center transition-all duration-300 cursor-pointer outline-none {hasSearched ? 'mb-8' : 'mb-12'}">
        <div class="relative flex items-center justify-center w-20 h-20 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-white/10 rounded-2xl backdrop-blur-sm hover:border-white/20 transition-colors">
            <Film class="w-10 h-10 text-white" />
        </div>
        <h1 class="font-bold tracking-tighter text-6xl text-white mt-8">Motif</h1>
    </button>

    <!-- Clean Tagline (only on landing) -->
    {#if !hasSearched}
        <p class="text-white/60 text-xl font-light mb-12 text-center">
            Find the perfect film for your mood
        </p>
    {/if}

    <!-- Search Section (Centered and Clean) -->
    <div class="w-full relative z-20 flex flex-col gap-8">
        <!-- Search Bar (Primary Focus) -->
        <form on:submit|preventDefault={() => semanticSearch()} class="w-full relative group">
            <div class="relative flex items-center bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl hover:border-white/20 focus-within:border-indigo-500/50 transition-all duration-300 shadow-2xl">
                <Search class="w-5 h-5 text-white/40 ml-5" />
                <input 
                    type="text" 
                    bind:value={searchQuery} 
                    placeholder="Describe your mood, occasion, or vibe..." 
                    class="w-full h-16 bg-transparent text-white outline-none px-4 placeholder-white/30 font-light text-lg" 
                    disabled={isLoading}
                    autofocus
                />
                <button 
                    type="submit" 
                    disabled={isLoading || !searchQuery} 
                    class="flex items-center justify-center w-14 h-14 rounded-xl bg-white text-black font-semibold mr-2 hover:bg-gray-200 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                >
                    <ArrowRight class="w-5 h-5" />
                </button>
            </div>
        </form>

        <!-- Context Selectors (Collapsible/Subtle) -->
        {#if !hasSearched}
            <div class="w-full flex flex-col items-center">
                <!-- Simple Divider -->
                <div class="w-24 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent mb-6"></div>
                
                <!-- Quick Options -->
                <div class="flex flex-wrap justify-center gap-3 mb-4">
                    {#each CONTEXT_OPTIONS.social as opt}
                        <button 
                            on:click={() => toggleContext('social', opt.id)} 
                            class="px-4 py-2 rounded-lg border transition-all duration-200 {activeContext.social === opt.id ? 'bg-white/10 border-white/20 text-white' : 'bg-white/5 border-white/10 text-white/60 hover:text-white'}"
                        >
                            <span class="text-sm font-medium">{opt.label}</span>
                        </button>
                    {/each}
                </div>
                
                <div class="flex flex-wrap justify-center gap-3">
                    {#each CONTEXT_OPTIONS.mood as opt}
                        <button 
                            on:click={() => toggleContext('mood', opt.id)} 
                            class="px-4 py-2 rounded-lg border transition-all duration-200 {activeContext.mood === opt.id ? 'bg-white/10 border-white/20 text-white' : 'bg-white/5 border-white/10 text-white/60 hover:text-white'}"
                        >
                            <span class="text-sm font-medium">{opt.label}</span>
                        </button>
                    {/each}
                </div>
                
                <!-- Vibe Chips (Subtle) -->
                <div class="mt-8 flex flex-wrap justify-center gap-2">
                    <span class="text-sm text-white/40 font-medium">Try:</span>
                    {#each VIBES as vibe}
                        <button 
                            on:click={() => semanticSearch(vibe.label)} 
                            class="px-3 py-1.5 rounded-lg text-sm font-medium bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/20 text-white/60 hover:text-white transition-all duration-200"
                        >
                            {vibe.label}
                        </button>
                    {/each}
                </div>
            </div>
        {/if}
    </div>

    <!-- Results Grid -->
    {#if hasSearched}
        <div class="w-full pb-24 max-w-7xl mt-12">
            <div class="flex items-center justify-between mb-8">
                <h2 class="text-2xl font-bold text-white">Recommended Films</h2>
                <div class="text-sm text-white/50">{movies.length} results</div>
            </div>
            <section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {#if isLoading}
                    {#each Array(6) as _, i}
                        <div class="h-80 rounded-2xl bg-white/5 border border-white/10 animate-pulse">
                            <div class="h-48 bg-white/10 rounded-t-2xl"></div>
                            <div class="p-5">
                                <div class="h-6 bg-white/10 rounded mb-3 w-3/4"></div>
                                <div class="h-4 bg-white/10 rounded mb-2 w-full"></div>
                                <div class="h-4 bg-white/10 rounded w-2/3"></div>
                            </div>
                        </div>
                    {/each}
                {:else}
                    {#each movies as movie, i (movie.movie_id || i)}
                        <button on:click={() => openDetail(movie)} in:fly={{ y: 20, duration: 300, delay: i * 50 }} class="group relative w-full flex flex-col h-full bg-white/[0.02] border border-white/10 rounded-2xl overflow-hidden hover:-translate-y-1 hover:shadow-xl hover:border-white/20 text-left transition-all duration-300">
                            <div class="h-48 w-full relative overflow-hidden shrink-0">
                                {#if movie.posterUrl}
                                    <img src={movie.posterUrl} alt={movie.title} class="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-70 transition-opacity duration-300" />
                                {:else}
                                    <div class="absolute inset-0 bg-gradient-to-br from-purple-500/20 to-indigo-500/20"></div>
                                {/if}
                                <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div>
                                <div class="absolute top-4 right-4 flex items-center gap-1.5 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10">
                                    <Star class="w-4 h-4 text-indigo-400 fill-indigo-400" />
                                    <span class="text-sm font-bold text-white">{Math.round(movie.score * 100)}%</span>
                                </div>
                            </div>
                            
                            <!-- Content -->
                            <div class="p-5 flex flex-col h-full relative z-10">
                                <div class="flex items-start justify-between mb-3">
                                    <h2 class="text-xl font-bold text-white leading-tight pr-2">{movie.title}</h2>
                                    <div class="text-xs text-white/50 font-medium bg-white/5 px-2 py-1 rounded">{movie.year}</div>
                                </div>
                                
                                <p class="text-white/70 text-sm font-light leading-relaxed line-clamp-3 mb-4 flex-grow">{movie.overview}</p>
                                
                                <div class="mt-auto pt-4 border-t border-white/10">
                                    <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs font-semibold text-white">
                                        <svelte:component this={movie.socialBadges[0].icon} class="w-3.5 h-3.5" />
                                        {movie.socialBadges[0].text}
                                    </div>
                                    <div class="mt-3 text-xs text-white/40 font-medium">{movie.runtime} • {movie.certData.code}</div>
                                </div>
                            </div>
                        </button>
                    {/each}
                {/if}
            </section>
        </div>
    {/if}
</div>

<!-- Movie Detail Modal -->
{#if selectedMovie}
    <div 
        transition:fade={{ duration: 200 }} 
        class="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6 cursor-default select-none" 
        on:click={closeDetail}
    >
        <div 
            on:click|stopPropagation 
            transition:fly={{ y: 40, duration: 300 }} 
            class="relative w-full max-w-5xl h-[90vh] bg-[#0e0e0e] border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col md:flex-row"
        >
            <!-- Close Button -->
            <button on:click={closeDetail} class="absolute top-4 right-4 z-50 p-2 bg-black/60 backdrop-blur-md rounded-full text-white/70 hover:text-white border border-white/10 hover:bg-white/10 transition-colors cursor-pointer">
                <X class="w-4 h-4" />
            </button>

            <!-- Left Panel -->
            <div class="w-full md:w-2/5 flex flex-col shrink-0 relative overflow-hidden border-r border-white/10">
                <!-- Poster Section -->
                <div class="flex-1 relative overflow-hidden min-h-0">
                    {#if selectedMovie.posterUrl}
                        <img src={selectedMovie.posterUrl} alt={selectedMovie.title} class="w-full h-full object-cover" />
                    {:else}
                        <div class="w-full h-full bg-neutral-900 flex items-center justify-center text-neutral-700">
                            <Film class="w-16 h-16" />
                        </div>
                    {/if}
                    <div class="absolute inset-0 bg-gradient-to-t from-[#0e0e0e] via-[#0e0e0e]/60 to-transparent"></div>
                    <div class="absolute inset-0 bg-gradient-to-r from-black/50 to-transparent md:hidden"></div>
                    
                    <!-- Title and Info -->
                    <div class="absolute bottom-0 left-0 w-full p-6 z-20">
                        <h2 class="text-3xl font-bold text-white tracking-tight leading-none mb-3">{selectedMovie.title}</h2>
                        <div class="flex flex-wrap items-center gap-3 text-sm font-medium text-white/80">
                            <div class="flex items-center gap-2">
                                <Star class="w-4 h-4 text-amber-400 fill-amber-400" />
                                <span class="text-white font-bold">{Math.round(selectedMovie.score * 100)}% Match</span>
                            </div>
                            <div class="w-1 h-1 rounded-full bg-white/40"></div>
                            <span>{selectedMovie.year}</span>
                            <div class="w-1 h-1 rounded-full bg-white/40"></div>
                            <span>{selectedMovie.runtime}</span>
                        </div>
                    </div>
                </div>

                <!-- Stats Section -->
                <div class="p-6 flex flex-col gap-6 bg-[#0e0e0e]">
                    <!-- Quick Stats -->
                    <div class="grid grid-cols-3 gap-4 py-2">
                        <div class="flex flex-col items-center p-3 rounded-xl bg-white/5 border border-white/10">
                            <span class="text-xs font-bold text-white/50 uppercase tracking-widest mb-1.5">Match</span>
                            <span class="text-2xl font-bold text-emerald-400">{Math.round(selectedMovie.score * 100)}%</span>
                        </div>
                        <div class="flex flex-col items-center p-3 rounded-xl bg-white/5 border border-white/10">
                            <span class="text-xs font-bold text-white/50 uppercase tracking-widest mb-1.5">Popularity</span>
                            <span class="text-2xl font-bold text-amber-400 flex items-center gap-1">
                                <Star class="w-4 h-4 fill-current" /> 
                                {Math.round(selectedMovie.popularity)/10}
                            </span>
                        </div>
                        <div class="flex flex-col items-center p-3 rounded-xl bg-white/5 border border-white/10">
                            <span class="text-xs font-bold text-white/50 uppercase tracking-widest mb-1.5">Rating</span>
                            <div class="flex flex-col items-center">
                                <span class="text-2xl font-bold text-white">{selectedMovie.certData.code}</span>
                                <span class="text-[10px] text-white/50 mt-1">{selectedMovie.certData.reason}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Vibe Signature -->
                    <div class="space-y-4 pt-2">
                        <div class="flex items-center gap-2">
                            <Gauge class="w-4 h-4 text-indigo-400" />
                            <h3 class="text-xs font-bold text-white/50 uppercase tracking-widest">Vibe Signature</h3>
                        </div>
                        {#each Object.values(selectedMovie.vibeDynamics) as metric}
                            <div class="space-y-1.5">
                                <div class="flex justify-between items-center">
                                    <span class="text-xs text-white/60">{metric.label}</span>
                                    <span class="text-xs font-bold text-white">{metric.val}%</span>
                                </div>
                                <div class="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                                    <div 
                                        class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full" 
                                        style="width: {metric.val}%"
                                    ></div>
                                </div>
                                <div class="flex justify-between text-[10px] text-white/40">
                                    <span>{metric.low}</span>
                                    <span>{metric.high}</span>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            </div>

            <!-- Right Panel -->
            <div class="w-full md:w-3/5 flex flex-col bg-[#0e0e0e]">
                <!-- Scrollable Content -->
                <div class="flex-1 overflow-y-auto custom-scrollbar p-8 flex flex-col gap-8">
                    <!-- Badges -->
                    <div class="flex flex-wrap gap-3">
                        {#each selectedMovie.socialBadges as badge}
                            <div class="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-white/5 border border-white/10 text-sm font-semibold text-white">
                                <svelte:component this={badge.icon} class="w-4 h-4" /> 
                                {badge.text}
                            </div>
                        {/each}
                    </div>

                    <!-- Moment Sentence -->
                    <div class="border-l-4 border-indigo-500 pl-5 py-2 bg-indigo-500/5 rounded-r-xl">
                        <p class="text-lg text-white/90 font-light italic leading-relaxed">"{selectedMovie.momentSentence}"</p>
                    </div>

                    <!-- Synopsis -->
                    <div class="space-y-4">
                        <div class="flex items-center gap-2">
                            <Sparkles class="w-4 h-4 text-white/50" />
                            <h3 class="text-sm font-bold text-white/50 uppercase tracking-widest">Synopsis</h3>
                        </div>
                        <p class="text-white/80 font-light leading-relaxed">{selectedMovie.overview}</p>
                        
                        <!-- Metadata -->
                        <div class="mt-6 pt-6 border-t border-white/10 grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <span class="text-xs font-bold text-white/50 uppercase tracking-widest block mb-1">Director</span>
                                <span class="text-white font-medium">{selectedMovie.director}</span>
                            </div>
                            <div>
                                <span class="text-xs font-bold text-white/50 uppercase tracking-widest block mb-1">Language</span>
                                <span class="text-white font-medium">{selectedMovie.original_language}</span>
                            </div>
                            <div class="col-span-2">
                                <span class="text-xs font-bold text-white/50 uppercase tracking-widest block mb-1">Cast</span>
                                <span class="text-white/80">{selectedMovie.cast.join(", ")}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Content Descriptors -->
                    <div class="space-y-4">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <Brain class="w-4 h-4 text-indigo-400" />
                                <h3 class="text-sm font-bold text-white/50 uppercase tracking-widest">Content Descriptors</h3>
                            </div>
                            <span class="text-xs text-white/30">Rank top {MAX_VOTES}</span>
                        </div>
                        <div class="flex flex-wrap gap-2">
                            {#each movieInteractionState.tags as tag, i}
                                <button 
                                    on:click={() => voteTag(i)} 
                                    class="group relative flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-medium transition-all active:scale-95 select-none cursor-pointer {tag.userVoted ? 'bg-indigo-500/20 border-indigo-500/40 text-indigo-300' : 'bg-white/5 border-white/10 text-white/70 hover:border-white/20 hover:text-white'}"
                                >
                                    <span>{tag.name}</span>
                                    <span class="text-xs opacity-60 group-hover:opacity-100 transition-opacity {tag.userVoted ? 'text-indigo-400' : ''}">
                                        {tag.score}
                                    </span>
                                </button>
                            {/each}
                            {#if movieInteractionState.customTagsAdded < MAX_CUSTOM_TAGS}
                                {#if !showAddTagInput}
                                    <button 
                                        on:click={() => showAddTagInput = true} 
                                        class="px-4 py-2.5 rounded-xl border border-dashed border-white/20 text-white/50 text-sm hover:border-white/40 hover:text-white transition-all cursor-pointer"
                                    >
                                        + Add Tag
                                    </button>
                                {:else}
                                    <form on:submit|preventDefault={addNewTag} class="flex items-center">
                                        <input 
                                            bind:value={newTagValue} 
                                            class="bg-white/5 border-b-2 border-indigo-500 text-white text-sm w-32 outline-none px-3 py-2 rounded-t-xl" 
                                            placeholder="Add tag..." 
                                            autofocus 
                                            on:blur={() => {if(!newTagValue) showAddTagInput=false}}
                                        />
                                    </form>
                                {/if}
                            {/if}
                        </div>
                    </div>

                    <!-- Similar Films -->
                    <div class="pt-6 border-t border-white/10">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-sm font-bold text-white/50 uppercase tracking-widest">Similar Films</h3>
                        </div>
                        
                        <div class="flex gap-4 overflow-x-auto pb-4 -mx-2 px-2 custom-scrollbar">
                            {#each selectedMovie.recommendations as rec}
                                <div class="min-w-[140px] group cursor-pointer">
                                    <div class="aspect-[2/3] rounded-xl overflow-hidden bg-white/5 border border-white/10 relative mb-3 group-hover:border-white/20 transition-all">
                                        <div class="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-indigo-500/10"></div>
                                        <div class="absolute inset-0 flex items-center justify-center p-3 text-center">
                                            <span class="text-xs font-bold text-white/60 uppercase tracking-widest">{rec.title}</span>
                                        </div>
                                        <div class="absolute top-2 right-2 px-2 py-1 bg-black/60 backdrop-blur-sm rounded-lg text-xs font-bold text-emerald-400 border border-white/5">
                                            {rec.match}%
                                        </div>
                                    </div>
                                    <h4 class="text-sm font-medium text-white truncate">{rec.title}</h4>
                                    <span class="text-xs text-white/40">{rec.year}</span>
                                </div>
                            {/each}
                        </div>
                    </div>
                </div>

                <!-- Action Bar -->
                <div class="p-6 border-t border-white/10 flex items-center gap-4">
                    <a 
                        href={selectedMovie.trailerUrl ? selectedMovie.trailerUrl : `https://www.youtube.com/results?search_query=${selectedMovie.title} trailer`} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        class="flex-1 h-14 rounded-xl bg-white text-black flex items-center justify-center gap-3 text-base font-bold hover:bg-gray-200 transition-all active:scale-95"
                    >
                        <Play class="w-5 h-5" /> 
                        {selectedMovie.trailerUrl ? 'Watch Trailer' : 'Search Trailer'}
                    </a>
                    
                    <div class="flex items-center gap-2">
                        <button 
                            on:click={() => toggleInteraction('heart')} 
                            class="w-14 h-14 rounded-xl border border-white/10 bg-white/5 text-white/70 flex items-center justify-center hover:bg-white/10 hover:text-rose-400 transition-all active:scale-95 cursor-pointer {movieInteractionState.isHearted ? 'text-rose-400 border-rose-500/40 bg-rose-500/10' : ''}"
                        >
                            <Heart class="w-6 h-6 {movieInteractionState.isHearted ? 'fill-current' : ''}" />
                        </button>

                        <button 
                            on:click={() => toggleInteraction('bookmark')} 
                            class="w-14 h-14 rounded-xl border border-white/10 bg-white/5 text-white/70 flex items-center justify-center hover:bg-white/10 hover:text-emerald-400 transition-all active:scale-95 cursor-pointer {movieInteractionState.isBookmarked ? 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10' : ''}"
                        >
                            <Bookmark class="w-6 h-6 {movieInteractionState.isBookmarked ? 'fill-current' : ''}" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
{/if}

<style>
    .custom-scrollbar::-webkit-scrollbar { 
        height: 6px; 
        width: 6px; 
    }
    .custom-scrollbar::-webkit-scrollbar-track { 
        background: transparent; 
    }
    .custom-scrollbar::-webkit-scrollbar-thumb { 
        background: rgba(255, 255, 255, 0.1); 
        border-radius: 10px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover { 
        background: rgba(255, 255, 255, 0.2); 
    }
    
    /* Auto-focus glow effect */
    input:focus {
        box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.2);
    }
</style>