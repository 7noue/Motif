// motifApp.ts
// Pure TypeScript logic extracted from Svelte component
// No UI, no framework bindings, no logic changes

// ---------------- ICON TYPES (placeholders) ----------------
export type Icon = unknown;

// ---------------- CONFIG ----------------
export const API_URL = 'http://localhost:8000/api/search';

// ---------------- AUTH STATE ----------------
export interface User {
  name: string;
  avatar: string | null;
}

export let currentUser: User | null = null;
export let showProfileMenu = false;

export interface Toast {
  message: string;
  type: 'error' | 'success';
}

export let toast: Toast | null = null;
let toastTimeout: number | undefined;

// ---------------- APP STATE ----------------
export let searchQuery = '';
export let movies: Movie[] = [];
export let isLoading = false;
export let hasSearched = false;
export let selectedMovie: EnrichedMovie | null = null;

export let activeContext = {
  social: null as string | null,
  mood: null as string | null
};

// ---------------- INTERACTION STATE ----------------
export interface Tag {
  name: string;
  score: number;
  userVoted: boolean;
  isCustom: boolean;
}

export interface MovieInteractionState {
  isHearted: boolean;
  isBookmarked: boolean;
  tags: Tag[];
  customTagsAdded: number;
  userTagVotes: number;
}

export let movieInteractionState: MovieInteractionState = {
  isHearted: false,
  isBookmarked: false,
  tags: [],
  customTagsAdded: 0,
  userTagVotes: 0
};

export let showAddTagInput = false;
export let newTagValue = '';

export const MAX_VOTES = 3;
export const MAX_CUSTOM_TAGS = 3;

// ---------------- CONTEXT OPTIONS ----------------
export const CONTEXT_OPTIONS = {
  social: [
    { id: 'parents', label: 'With Parents', icon: null },
    { id: 'date', label: 'Date Night', icon: null },
    { id: 'group', label: 'Drinking/Party', icon: null },
    { id: 'solo', label: 'Solo Watch', icon: null }
  ],
  mood: [
    { id: 'hype', label: 'High Energy', icon: null },
    { id: 'chill', label: 'Chill', icon: null },
    { id: 'deep', label: 'Deep', icon: null }
  ]
};

// ---------------- VIBES ----------------
export const VIBES = [
  { label: 'Cyberpunk', icon: null },
  { label: 'Cozy', icon: null },
  { label: 'Rainy', icon: null },
  { label: 'Melancholic', icon: null },
  { label: 'Dreamy', icon: null }
];

// ---------------- HELPERS ----------------
export function showToast(message: string, type: Toast['type'] = 'error') {
  if (toastTimeout) clearTimeout(toastTimeout);
  toast = { message, type };
  toastTimeout = window.setTimeout(() => {
    toast = null;
  }, 3000);
}

export function handleLogin() {
  setTimeout(() => {
    currentUser = { name: 'Mark', avatar: null };
    showToast('Welcome back, Mark.', 'success');
  }, 500);
}

export function handleLogout() {
  currentUser = null;
  showProfileMenu = false;
  showToast('Logged out.', 'success');
}

export function requireAuth(): boolean {
  if (!currentUser) {
    showToast('Sign in to curate vibes.', 'error');
    return false;
  }
  return true;
}

// ---------------- DETERMINISTIC RANDOM ----------------
export function pseudoRandom(str: string): number {
  let hash = 0;
  if (!str) return 0.5;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash) / 2147483647;
}

export function getGradient(title: string): string {
  const colors = [
    'from-rose-500 to-orange-600',
    'from-violet-600 to-indigo-900',
    'from-emerald-500 to-teal-900',
    'from-blue-600 to-cyan-800',
    'from-amber-700 to-yellow-600'
  ];
  return colors[Math.floor(pseudoRandom(title) * colors.length)];
}

// ---------------- DATA TYPES ----------------
export interface Movie {
  movie_id?: number;
  title: string;
  overview?: string;
  posterUrl?: string | null;
  release_date?: string;
  score?: number;
  runtime?: string;
  popularity?: number;
  genres?: string[];
  cast?: string[];
  original_language?: string;
  trailerUrl?: string;
  certData?: {
    code: string;
    reason: string;
  };
  vibe_pacing?: number;
  vibe_complexity?: number;
  vibe_atmosphere?: number;
}

export interface EnrichedMovie extends Movie {
  year: string;
  score: number;
  runtime: string;
  posterUrl: string | null;
  vibeDynamics: Record<string, any>;
  momentSentence: string;
  palette: { name: string; colors: string[] };
  socialBadges: { text: string; icon: Icon }[];
  initialTags: Tag[];
  director: string;
  recommendations: any[];
}

// ---------------- ENRICH MOVIE ----------------
export function enrichMovieData(apiMovie: Movie): EnrichedMovie {
  const seed = `${apiMovie.title}${apiMovie.movie_id ?? ''}`;
  const r = (offset = 0) => pseudoRandom(seed + offset);

  const year = apiMovie.release_date ?? 'N/A';
  const score = apiMovie.score ?? 0;
  const runtime = apiMovie.runtime ?? 'Unknown';

  const vibeDynamics = {
    pacing: { label: 'Pacing', val: apiMovie.vibe_pacing ?? 50, low: 'Slow', high: 'Fast' },
    complexity: { label: 'Cognitive Load', val: apiMovie.vibe_complexity ?? 50, low: 'Light', high: 'Heavy' },
    atmosphere: { label: 'Mood', val: apiMovie.vibe_atmosphere ?? 50, low: 'Dark', high: 'Bright' }
  };

  const pitches = [
    "Perfect for when you want to feel smart but don't want to work for it.",
    'The visual equivalent of a double espresso.',
    'Slow, methodical, and deeply rewarding.',
    'Zero cognitive load. Just vibes.',
    'A cinematic warm hug.'
  ];

  const palettes = [
    { name: 'Neon Noir', colors: ['#f43f5e', '#8b5cf6', '#1e293b'] },
    { name: 'Industrial', colors: ['#94a3b8', '#475569', '#0f172a'] },
    { name: 'Warm Retro', colors: ['#f59e0b', '#78350f', '#fffbeb'] },
    { name: 'Miami Sunset', colors: ['#f97316', '#db2777', '#8b5cf6'] }
  ];

  const initialTags: Tag[] = (apiMovie.genres ?? []).map(g => ({
    name: g,
    score: Math.floor(r(g) * 50) + 1,
    userVoted: false,
    isCustom: false
  }));

  return {
    ...apiMovie,
    year,
    score,
    runtime,
    posterUrl: apiMovie.posterUrl ?? null,
    vibeDynamics,
    momentSentence: pitches[Math.floor(r(1) * pitches.length)],
    palette: palettes[Math.floor(r(5) * palettes.length)],
    socialBadges: [],
    initialTags,
    certData: apiMovie.certData ?? { code: 'NR', reason: 'Not Rated' },
    director: 'Unknown',
    cast: apiMovie.cast ?? [],
    recommendations: []
  };
}

// ---------------- SEARCH ----------------
export async function semanticSearch(queryOverride?: string) {
  const query = (queryOverride ?? searchQuery).trim();
  if (!query) return;

  searchQuery = query;
  hasSearched = true;
  isLoading = true;
  movies = [];
  selectedMovie = null;

  const contextString = Object.values(activeContext).filter(Boolean).join(' ');
  const finalQuery = `${query} ${contextString}`.trim();

  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: finalQuery, top_k: 9 })
    });

    if (!res.ok) throw new Error('Search failed');

    const data: Movie[] = await res.json();
    movies = data.map(enrichMovieData);
  } catch {
    showToast('Failed to connect to Motif Core.', 'error');
  } finally {
    isLoading = false;
  }
}
