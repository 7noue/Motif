import { writable, get } from 'svelte/store';
import { API_URL } from './constants';
import { enrichMovieData, type EnrichedMovie } from '$lib/logic';

// --- Types ---
export interface User {
    name: string;
    avatar: string | null;
}

export interface SearchState {
    query: string;
    movies: EnrichedMovie[];
    isLoading: boolean;
    hasSearched: boolean;
    activeContext: {
        social: string | null;
        mood: string | null;
    };
    error: string | null; // Added error state
}

export type ToastType = 'error' | 'success';

// --- AUTH STORE ---
export const currentUser = writable<User | null>(null);

// --- TOAST STORE ---
function createToastStore() {
    const { subscribe, set } = writable<{ message: string; type: ToastType } | null>(null);
    let timeout: ReturnType<typeof setTimeout>;

    return {
        subscribe,
        show: (message: string, type: ToastType = 'error') => {
            console.log(`[Toast] ${type}: ${message}`); // Debug log
            clearTimeout(timeout);
            set({ message, type });
            timeout = setTimeout(() => set(null), 3000);
        }
    };
}
export const toast = createToastStore();

// --- SEARCH STORE ---
function createSearchStore() {
    const { subscribe, set, update } = writable<SearchState>({
        query: '',
        movies: [],
        isLoading: false,
        hasSearched: false,
        activeContext: { social: null, mood: null },
        error: null
    });

    return {
        subscribe,
        
        reset: () => update(s => ({ 
            ...s, 
            query: '', 
            movies: [], 
            hasSearched: false, 
            activeContext: { social: null, mood: null },
            error: null
        })),
        
        setQuery: (q: string) => update(s => ({ ...s, query: q })),
        
        toggleContext: (type: keyof SearchState['activeContext'], value: string) => update(s => {
            const current = s.activeContext[type];
            return { 
                ...s, 
                activeContext: { 
                    ...s.activeContext, 
                    [type]: current === value ? null : value 
                } 
            };
        }),

        performSearch: async (queryOverride: string | null = null) => {
            // Get current state to construct the query
            const currentState = get(searchStore);
            const queryToUse = queryOverride || currentState.query.trim();

            if (!queryToUse) return;

            // Update state: Loading starts
            update(s => ({ 
                ...s, 
                query: queryToUse,
                isLoading: true, 
                hasSearched: true, 
                error: null 
            }));

            const contextString = Object.values(currentState.activeContext).filter(Boolean).join(' ');
            const finalQuery = `${queryToUse} ${contextString}`.trim();

            console.log(`[Search] Sending query to ${API_URL}:`, finalQuery);

            try {
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        query: finalQuery, 
                        top_k: 9 
                    })
                });

                if (!response.ok) {
                    throw new Error(`API Error: ${response.status} ${response.statusText}`);
                }

                const rawData = await response.json();
                console.log('[Search] Raw Data received:', rawData);

                // Transform data safely
                const enriched = rawData.map((movie: any) => {
                    try {
                        return enrichMovieData(movie);
                    } catch (err) {
                        console.error('[Search] Failed to enrich movie:', movie, err);
                        return null;
                    }
                }).filter(Boolean); // Remove any failed items
                
                update(s => ({ ...s, movies: enriched, isLoading: false }));

            } catch (e: any) {
                console.error('[Search] Failed:', e);
                toast.show("Failed to connect to Motif Core.", "error");
                update(s => ({ 
                    ...s, 
                    isLoading: false, 
                    error: e.message || "Unknown error" 
                }));
            }
        }
    };
}
 
export const searchStore = createSearchStore();