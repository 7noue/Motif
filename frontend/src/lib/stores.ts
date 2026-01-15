import { writable, get } from 'svelte/store';
import { auth, googleProvider, db } from './firebase'; 
import { signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth';
import { doc, getDoc, setDoc } from 'firebase/firestore'; 
import { API_URL } from './constants';
import { enrichMovieData, type EnrichedMovie } from '$lib/logic';

// --- Types ---
export interface User {
    uid: string;
    name: string;
    email: string | null;
    avatar: string | null;
    watchlist: string[]; 
    hearts: string[];    
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
    error: string | null;
    selectedMovie: EnrichedMovie | null;
}

export type ToastType = 'error' | 'success';

// --- STORES ---
export const isLoginModalOpen = writable(false);

function createToastStore() {
    const { subscribe, set } = writable<{ message: string; type: ToastType } | null>(null);
    let timeout: ReturnType<typeof setTimeout>;

    return {
        subscribe,
        show: (message: string, type: ToastType = 'error') => {
            console.log(`[Toast] ${type}: ${message}`);
            clearTimeout(timeout);
            set({ message, type });
            timeout = setTimeout(() => set(null), 3000);
        }
    };
}
export const toast = createToastStore();

// --- AUTH STORE ---
function createAuthStore() {
    const { subscribe, set, update } = writable<User | null>(null);

    return {
        subscribe,
        init: () => {
            if (typeof window === 'undefined') return;
            
            onAuthStateChanged(auth, async (firebaseUser) => {
                if (firebaseUser) {
                    // 1. FAST UPDATE: Set UI immediately (Optimistic)
                    // The user sees they are logged in instantly.
                    const userData: User = {
                        uid: firebaseUser.uid,
                        name: firebaseUser.displayName || 'Curator',
                        email: firebaseUser.email,
                        avatar: firebaseUser.photoURL,
                        watchlist: [], // Empty for now
                        hearts: []     // Empty for now
                    };
                    set(userData); 

                    // 2. BACKGROUND UPDATE: Fetch Database Data
                    try {
                        const userRef = doc(db, 'users', firebaseUser.uid);
                        const userSnap = await getDoc(userRef);

                        if (userSnap.exists()) {
                            const data = userSnap.data();
                            // Update the existing store with the data when it arrives
                            update(u => {
                                if (!u) return null;
                                return {
                                    ...u,
                                    watchlist: data.watchlist?.map((m: any) => String(m.id)) || [],
                                    hearts: data.hearts?.map((m: any) => String(m.id)) || []
                                };
                            });
                        } else {
                            // Create profile silently
                            await setDoc(userRef, {
                                name: userData.name,
                                email: userData.email,
                                watchlist: [],
                                hearts: [],
                                tags_contributed: 0
                            });
                        }
                    } catch (e) {
                        console.error("Background sync error:", e);
                    }
                } else {
                    set(null);
                }
            });
        },
        login: async () => {
            try {
                await signInWithPopup(auth, googleProvider);
                // Success toast handled by listener or UI
            } catch (err: any) {
                console.error("Login failed", err);
                toast.show(err.message, "error");
                throw err; // Re-throw so the modal knows to stop loading
            }
        },
        logout: async () => {
            await signOut(auth);
            set(null);
            toast.show("Logged out.", "success");
        },
        updateLocalLists: (type: 'hearts' | 'watchlist', movieId: string, isAdding: boolean) => {
            update(u => {
                if (!u) return null;
                const list = u[type];
                const newList = isAdding ? [...list, movieId] : list.filter(id => id !== movieId);
                return { ...u, [type]: newList };
            });
        }
    };
}
export const currentUser = createAuthStore();

function createSearchStore() {
    const { subscribe, set, update } = writable<SearchState>({
        query: '',
        movies: [],
        isLoading: false,
        hasSearched: false,
        activeContext: { social: null, mood: null },
        error: null,
        selectedMovie: null
    });

    return {
        subscribe,
        reset: () => update(s => ({ 
            ...s, query: '', movies: [], hasSearched: false, 
            activeContext: { social: null, mood: null }, error: null, selectedMovie: null 
        })),
        setQuery: (q: string) => update(s => ({ ...s, query: q })),
        selectMovie: (movie: EnrichedMovie) => update(s => ({ ...s, selectedMovie: movie })),
        closeModal: () => update(s => ({ ...s, selectedMovie: null })),
        
        toggleContext: (type: keyof SearchState['activeContext'], value: string) => update(s => {
            const current = s.activeContext[type];
            return { ...s, activeContext: { ...s.activeContext, [type]: current === value ? null : value } };
        }),

        performSearch: async (queryOverride: string | null = null) => {
            const currentState = get(searchStore);
            const queryToUse = queryOverride || currentState.query.trim();
            if (!queryToUse) return;

            update(s => ({ ...s, query: queryToUse, isLoading: true, hasSearched: true, error: null }));
            const contextString = Object.values(currentState.activeContext).filter(Boolean).join(' ');
            const finalQuery = `${queryToUse} ${contextString}`.trim();

            try {
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: finalQuery, top_k: 9 })
                });
                if (!response.ok) throw new Error(`API Error: ${response.status}`);
                
                const rawData = await response.json();
                const enriched = rawData.map((movie: any) => {
                    try { return enrichMovieData(movie); } catch (err) { return null; }
                }).filter(Boolean);
                
                update(s => ({ ...s, movies: enriched, isLoading: false }));
            } catch (e: any) {
                toast.show("Failed to connect to Motif Core.", "error");
                update(s => ({ ...s, isLoading: false, error: e.message || "Unknown error" }));
            }
        }
    };
}
export const searchStore = createSearchStore();