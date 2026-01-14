import { writable, get } from 'svelte/store';
import { API_URL } from './constants';
import { enrichMovieData, type EnrichedMovie } from '$lib/logic'; // Ensure this points to $lib/logic or ./logic

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
        activeContext: { social: null, mood: null }
    });

    return {
        subscribe,
        reset: () => update(s => ({ 
            ...s, 
            query: '', 
            movies: [], 
            hasSearched: false, 
            activeContext: { social: null, mood: null } 
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
            update(s => ({ ...s, isLoading: true, hasSearched: true }));
            
            const state = get(searchStore);
            const query = queryOverride || state.query.trim();
            if(queryOverride) update(s => ({ ...s, query: queryOverride }));

            if (!query) {
                update(s => ({ ...s, isLoading: false }));
                return;
            }

            const contextString = Object.values(state.activeContext).filter(Boolean).join(' ');
            const finalQuery = `${query} ${contextString}`.trim();

            try {
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: finalQuery, top_k: 9 })
                });

                if (!response.ok) throw new Error("Search failed");
                const result = await response.json();
                const enriched = result.map(enrichMovieData);
                
                update(s => ({ ...s, movies: enriched, isLoading: false }));
            } catch (e) {
                console.error(e);
                toast.show("Failed to connect to Motif Core.", "error");
                update(s => ({ ...s, isLoading: false }));
            }
        }
    };
}
 
export const searchStore = createSearchStore();