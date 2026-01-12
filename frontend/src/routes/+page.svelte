<script lang="ts">
  import axios from 'axios';
  import { fly, fade } from 'svelte/transition';
  
  // UI Components
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import * as Card from "$lib/components/ui/card";
  import * as Dialog from "$lib/components/ui/dialog";
  
  // State
  let query = "";
  let movies: any[] = [];
  let loading = false;
  let explanation = "";
  let selectedMovie: any = null;
  let explainLoading = false;
  let dialogOpen = false;

  // 🔭 Zoom State
  // false = Detail (3-col, wide), true = Overview (6-col, vertical posters)
  let isZoomedOut = false; 

  // 1. SEARCH
  async function searchMovies() {
    if (!query) return;
    loading = true;
    try {
      // We fetch 50 items so the dense "Overview" grid feels populated
      const res = await axios.get(`http://127.0.0.1:8000/search?q=${query}&limit=50`);
      movies = res.data;
    } catch (e) {
      console.error(e);
    } finally {
      loading = false;
    }
  }

  // 2. EXPLAIN
  async function askWhy(movie: any) {
    selectedMovie = movie;
    dialogOpen = true;
    explainLoading = true;
    explanation = "";

    try {
      const res = await axios.post('http://127.0.0.1:8000/explain', {
        movie: movie.title,
        query: query,
        vibe: movie.vibe,
        director: movie.director,
        cast: movie.cast
      });
      explanation = res.data.reason;
    } catch (e) {
      explanation = "Honestly, the vibes were so strong the server blinked. It's a match.";
    } finally {
      explainLoading = false;
    }
  }
</script>

<main class="min-h-screen bg-black text-foreground p-8 font-sans selection:bg-purple-500">
  
  <div class="max-w-4xl mx-auto mb-12 text-center space-y-4">
    <h1 class="text-7xl font-extrabold tracking-tighter bg-gradient-to-b from-white to-zinc-500 bg-clip-text text-transparent">
      MOTIF.
    </h1>
    <p class="text-zinc-500 uppercase tracking-[0.2em] text-xs font-bold">
      Context-Aware Discovery Engine
    </p>
  </div>

  <div class="max-w-2xl mx-auto mb-12 flex gap-2 relative z-10">
    <Input 
      bind:value={query} 
      onkeydown={(e) => e.key === 'Enter' && searchMovies()} 
      placeholder="Identify a mood..." 
      class="text-lg p-7 bg-zinc-900/50 border-zinc-800 focus-visible:ring-purple-500 text-white"
    />
    <Button 
      onclick={searchMovies} 
      size="lg" 
      class="h-auto px-8 bg-white hover:bg-zinc-200 text-black font-bold transition-all"
    >
      {loading ? '...' : 'SEARCH'}
    </Button>
  </div>

  {#if movies.length > 0}
    <div class="max-w-[1600px] mx-auto mb-8 flex justify-end items-center gap-1" in:fade>
       <span class="text-[10px] text-zinc-600 uppercase tracking-widest mr-3">View Density</span>
       <div class="bg-zinc-900 p-1 rounded-lg flex gap-1 border border-zinc-800">
         <Button 
           variant={!isZoomedOut ? "secondary" : "ghost"} 
           size="sm" 
           onclick={() => isZoomedOut = false}
           class="text-[10px] h-7 px-3 uppercase tracking-tighter"
         >
           Detail
         </Button>
         <Button 
           variant={isZoomedOut ? "secondary" : "ghost"} 
           size="sm" 
           onclick={() => isZoomedOut = true}
           class="text-[10px] h-7 px-3 uppercase tracking-tighter"
         >
           Overview
         </Button>
       </div>
    </div>
  {/if}

  <div class={`mx-auto grid gap-6 transition-all duration-700 ease-in-out
      ${isZoomedOut 
          ? 'grid-cols-2 md:grid-cols-4 lg:grid-cols-6 max-w-[1600px]' 
          : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 max-w-7xl'
      }`}>
      
    {#each movies as movie, i}
      <div in:fly={{ y: 20, duration: 400, delay: i * 30 }}>
        <Card.Root 
            class={`bg-zinc-900/30 border-zinc-800/50 hover:border-purple-500/50 transition-all cursor-pointer group h-full flex flex-col overflow-hidden
              ${isZoomedOut ? 'hover:scale-105 active:scale-95' : ''} 
            `}
            onclick={() => askWhy(movie)}
        >
          
          <div class={`relative overflow-hidden bg-zinc-800
              ${isZoomedOut ? 'aspect-[2/3]' : 'aspect-video'} 
          `}>
            {#if movie.poster_url}
              <img 
                src={movie.poster_url} 
                alt={movie.title} 
                class="object-cover w-full h-full grayscale group-hover:grayscale-0 opacity-60 group-hover:opacity-100 transition duration-700" 
              />
            {/if}
            <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-80"></div>
            
            <div class={`absolute bottom-3 left-3 right-3 ${isZoomedOut ? 'text-center' : ''}`}>
              <h3 class={`font-bold text-white tracking-tight leading-tight ${isZoomedOut ? 'text-xs uppercase' : 'text-xl'}`}>
                  {movie.title}
              </h3>
              {#if !isZoomedOut}
                <p class="text-[10px] text-zinc-400 uppercase tracking-widest mt-1">{movie.director || 'Unknown Director'}</p>
              {/if}
            </div>
          </div>

          {#if !isZoomedOut}
            <Card.Content class="p-6 flex-grow flex flex-col justify-between space-y-4">
                <p class="text-sm text-zinc-400 line-clamp-3 leading-relaxed font-light">
                {movie.vibe || movie.overview}
                </p>
                <div class="flex items-center justify-between pt-2">
                <Badge variant="outline" class="border-zinc-800 text-zinc-500 text-[10px] font-mono">
                    {movie.match_score} MATCH
                </Badge>
                <span class="text-[10px] font-bold text-purple-400 group-hover:translate-x-1 transition-transform uppercase tracking-widest">
                    ASK WHY →
                </span>
                </div>
            </Card.Content>
          {:else}
             <div class="absolute top-2 right-2 px-1.5 py-0.5 bg-black/80 rounded border border-white/10 backdrop-blur-md">
                <span class="text-[9px] font-mono font-bold text-purple-400">
                    {movie.match_score}
                </span>
             </div>
          {/if}

        </Card.Root>
      </div>
    {/each}
  </div>

  <Dialog.Root bind:open={dialogOpen}>
    <Dialog.Content class="sm:max-w-[450px] bg-zinc-950 border-zinc-800 text-white shadow-2xl">
      <Dialog.Header>
        <div class="flex items-center justify-between mb-2">
            <Dialog.Title class="text-3xl font-black tracking-tighter uppercase italic">
            {selectedMovie?.title}
            </Dialog.Title>
            <div class="text-right">
                <p class="text-[10px] text-zinc-500 uppercase font-bold tracking-widest">Confidence</p>
                <p class="text-xl font-mono text-purple-500">{selectedMovie?.match_score}</p>
            </div>
        </div>
      </Dialog.Header>
      
      <div class="py-8">
        {#if explainLoading}
          <div class="flex flex-col items-center gap-4 text-purple-500">
            <div class="h-1 w-full bg-zinc-900 rounded-full overflow-hidden">
                <div class="h-full bg-purple-500 animate-[loading_1.5s_infinite]"></div>
            </div>
            <span class="text-[10px] font-bold uppercase tracking-[0.3em]">Mapping Latent Space</span>
          </div>
        {:else}
          <div class="text-lg leading-relaxed border-l-4 border-purple-500 pl-6 text-zinc-200 font-medium italic">
            "{explanation}"
          </div>
        {/if}
      </div>

      <Dialog.Footer>
        <Button variant="outline" class="border-zinc-800 hover:bg-zinc-900 text-xs uppercase font-bold tracking-widest" onclick={() => dialogOpen = false}>Close</Button>
      </Dialog.Footer>
    </Dialog.Content>
  </Dialog.Root>

</main>

<style>
  @keyframes loading {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
</style>