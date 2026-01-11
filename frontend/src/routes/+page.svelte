<script lang="ts">
  import axios from 'axios';
  import { fly } from 'svelte/transition';
  
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

  // 1. SEARCH
  async function searchMovies() {
    if (!query) return;
    loading = true;
    try {
      const res = await axios.get(`http://127.0.0.1:8000/search?q=${query}`);
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
        vibe: movie.vibe
      });
      explanation = res.data.reason;
    } catch (e) {
      explanation = "The system is calculating. Try again.";
    } finally {
      explainLoading = false;
    }
  }
</script>

<main class="min-h-screen bg-black text-foreground p-8 font-sans selection:bg-purple-500 selection:text-white">
  
  <div class="max-w-4xl mx-auto mb-12 text-center space-y-4">
    <h1 class="text-6xl font-extrabold tracking-tighter bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent">
      MOTIF.
    </h1>
    <p class="text-muted-foreground text-lg">
      Context-aware cinema search. Engineered by <span class="text-white font-bold">zxnyk</span>.
    </p>
  </div>

  <div class="max-w-2xl mx-auto mb-16 flex gap-2">
    <Input 
      bind:value={query} 
      onkeydown={(e) => e.key === 'Enter' && searchMovies()} 
      placeholder="Type a feeling (e.g. '3 AM existential dread')..." 
      class="text-lg p-6 bg-secondary/50 border-secondary-foreground/20 focus-visible:ring-purple-500"
    />
    <Button 
      onclick={searchMovies} 
      size="lg" 
      class="h-auto px-8 bg-purple-600 hover:bg-purple-700 text-white font-bold"
    >
      {loading ? '...' : 'Search'}
    </Button>
  </div>

  <div class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {#each movies as movie, i}
      <div in:fly={{ y: 20, duration: 400, delay: i * 50 }}>
        <Card.Root 
            class="bg-card/50 border-white/10 hover:border-purple-500/50 transition-all cursor-pointer group h-full flex flex-col" 
            onclick={() => askWhy(movie)}
        >
          
          <div class="aspect-video relative overflow-hidden rounded-t-lg bg-muted">
            {#if movie.poster_url}
              <img src={movie.poster_url} alt={movie.title} class="object-cover w-full h-full opacity-80 group-hover:scale-105 transition duration-500" />
            {/if}
            <div class="absolute inset-0 bg-gradient-to-t from-black/90 to-transparent"></div>
            <div class="absolute bottom-4 left-4 right-4">
              <h3 class="text-xl font-bold text-white leading-tight">{movie.title}</h3>
            </div>
          </div>

          <Card.Content class="p-6 flex-grow flex flex-col justify-between space-y-4">
            <p class="text-sm text-muted-foreground line-clamp-3">
              {movie.vibe || movie.overview}
            </p>
            <div class="flex items-center justify-between pt-2">
              <Badge variant="outline" class="border-white/20 text-xs font-mono">
                {movie.match_score} Match
              </Badge>
              <span class="text-xs font-bold text-purple-400 group-hover:translate-x-1 transition">
                ASK WHY &rarr;
              </span>
            </div>
          </Card.Content>

        </Card.Root>
      </div>
    {/each}
  </div>

  <Dialog.Root bind:open={dialogOpen}>
    <Dialog.Content class="sm:max-w-[425px] bg-zinc-950 border-purple-500/30 text-white">
      <Dialog.Header>
        <Dialog.Title class="text-2xl font-bold tracking-tight">
          {selectedMovie?.title}
        </Dialog.Title>
        <Dialog.Description class="text-zinc-400">
          Why the system chose this.
        </Dialog.Description>
      </Dialog.Header>
      
      <div class="py-6">
        {#if explainLoading}
          <div class="flex items-center gap-2 text-purple-400 animate-pulse">
            <div class="h-2 w-2 bg-current rounded-full animate-bounce"></div>
            <span class="text-sm font-medium">Analyzing context...</span>
          </div>
        {:else}
          <div class="text-lg leading-relaxed border-l-2 border-purple-500 pl-4 italic text-zinc-300">
            "{explanation}"
          </div>
        {/if}
      </div>

      <Dialog.Footer>
        <Button variant="secondary" onclick={() => dialogOpen = false}>Close</Button>
      </Dialog.Footer>
    </Dialog.Content>
  </Dialog.Root>

</main>