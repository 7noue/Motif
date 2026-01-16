import { writable, get } from 'svelte/store';
import { auth, googleProvider, db } from './firebase'; 
import { signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth';
import { doc, getDoc, setDoc } from 'firebase/firestore'; 
import { API_URL } from './constants';
import { enrichMovieData, type EnrichedMovie } from '$lib/logic';

// --- TYPES ---
export interface SavedMovie {
    id: string;
    title: string;
    year: string | number;
    posterUrl?: string | null; 
}

export interface User {
    uid: string;
    name: string;
    email: string | null;
    avatar: string | null;
    watchlist: SavedMovie[]; 
    hearts: SavedMovie[];    
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
                    const userData: User = {
                        uid: firebaseUser.uid,
                        name: firebaseUser.displayName || 'Curator',
                        email: firebaseUser.email,
                        avatar: firebaseUser.photoURL,
                        watchlist: [],
                        hearts: []
                    };
                    set(userData); 

                    try {
                        const userRef = doc(db, 'users', firebaseUser.uid);
                        const userSnap = await getDoc(userRef);

                        if (userSnap.exists()) {
                            const data = userSnap.data();
                            update(u => {
                                if (!u) return null;
                                return {
                                    ...u,
                                    watchlist: data.watchlist || [],
                                    hearts: data.hearts || []
                                };
                            });
                        } else {
                            await setDoc(userRef, {
                                name: userData.name,
                                email: userData.email,
                                watchlist: [],
                                hearts: [],
                                tags_contributed: 0
                            });
                        }
                    } catch (e) {
                        console.error("Sync error:", e);
                    }
                } else {
                    set(null);
                }
            });
        },
        login: async () => {
            try {
                await signInWithPopup(auth, googleProvider);
            } catch (err: any) {
                console.error("Login failed", err);
                toast.show(err.message, "error");
                throw err;
            }
        },
        logout: async () => {
            await signOut(auth);
            set(null);
            toast.show("Logged out.", "success");
        },
        updateLocalLists: (type: 'hearts' | 'watchlist', movie: SavedMovie, isAdding: boolean) => {
            update(u => {
                if (!u) return null;
                const list = u[type];
                const exists = list.some(m => String(m.id) === String(movie.id));
                
                let newList;
                if (isAdding) {
                    newList = exists ? list : [...list, movie];
                } else {
                    newList = list.filter(m => String(m.id) !== String(movie.id));
                }
                return { ...u, [type]: newList };
            });
        }
    };
}
export const currentUser = createAuthStore();

// --- SEARCH STORE ---
function createSearchStore() {
    const { subscribe, set, update } = writable<SearchState>({
        query: '', movies: [], isLoading: false, hasSearched: false,
        activeContext: { social: null, mood: null }, error: null, selectedMovie: null
    });

    return {
        subscribe,
        reset: () => update(s => ({ ...s, query: '', movies: [], hasSearched: false, activeContext: { social: null, mood: null }, error: null, selectedMovie: null })),
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
            console.log(`[Search] Sending query to ${API_URL}:`, queryToUse);

            try {
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: queryToUse, top_k: 9 })
                });
                
                if (!response.ok) throw new Error(`API Error: ${response.status}`);
                
                const rawData = await response.json();
                console.log("[Search] Raw Data received:", rawData);

                // FIX: Look into rawData.results, not just rawData
                if (rawData.results) {
                    const enriched = rawData.results.map((movie: any) => {
                        try { return enrichMovieData(movie); } catch (err) { return null; }
                    }).filter(Boolean);
                    update(s => ({ ...s, movies: enriched, isLoading: false }));
                }
                
                const enriched = rawData.results.map((movie: any) => {
                    try { return enrichMovieData(movie); } catch (err) { return null; }
                }).filter(Boolean);
                
                update(s => ({ ...s, movies: enriched, isLoading: false }));
            } catch (e: any) {
                console.error("[Search] Failed:", e);
                toast.show("Failed to connect to Motif Core.", "error");
                update(s => ({ ...s, isLoading: false, error: e.message || "Unknown error" }));
            }
        }
    };
}
export const searchStore = createSearchStore();