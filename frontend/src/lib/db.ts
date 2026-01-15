import { db } from './firebase';
import { doc, updateDoc, arrayUnion, arrayRemove, increment } from 'firebase/firestore';
import type { EnrichedMovie } from './logic';

const USERS_COLLECTION = 'users';

/**
 * Type definition for the interaction
 */
export type InteractionType = 'hearts' | 'watchlist';

/**
 * Toggles a movie in the user's list (Heart or Watchlist)
 * @param uid The user's ID
 * @param movie The full movie object
 * @param type 'hearts' or 'watchlist'
 * @param isAdding true to add, false to remove
 */
export async function toggleInteraction(uid: string, movie: EnrichedMovie, type: InteractionType, isAdding: boolean) {
    const userRef = doc(db, USERS_COLLECTION, uid);
    
    // We store a minimal version to save database costs.
    // We don't need the full palette/cast list in the user's profile.
    const movieMin = {
        id: movie.movie_id, // Ensure this matches your API ID
        title: movie.title,
        year: movie.year,
        posterUrl: movie.posterUrl // Keep poster for the Profile Grid
    };

    try {
        if (isAdding) {
            await updateDoc(userRef, {
                [type]: arrayUnion(movieMin)
            });
        } else {
            // NOTE: Firestore arrayRemove requires an EXACT match of the object.
            // In a real production app, you might just store IDs and fetch details later,
            // but for this prototype, storing the object is faster for the UI.
            await updateDoc(userRef, {
                [type]: arrayRemove(movieMin)
            });
        }
    } catch (error) {
        console.error(`Error updating ${type}:`, error);
        throw error;
    }
}

/**
 * Submits a tag for a movie.
 * 1. Adds to User's "contributions" stats.
 * 2. In a real backend, this would also add to the Movie's global tag cloud.
 */
export async function submitTag(uid: string, movieId: number, tag: string) {
    const userRef = doc(db, USERS_COLLECTION, uid);
    
    try {
        await updateDoc(userRef, {
            // 1. Increment the user's "Level" score
            tags_contributed_count: increment(1),
            
            // 2. Keep a log of their specific tags (Optional, good for "My Tags" tab)
            tags_history: arrayUnion({
                movieId,
                tag,
                timestamp: new Date().toISOString()
            })
        });
        
        console.log(`Tag "${tag}" submitted for movie ${movieId}`);
        
    } catch (error) {
        console.error("Error submitting tag:", error);
        throw error;
    }
}