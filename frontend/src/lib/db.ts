import { db } from './firebase';
import { doc, updateDoc, arrayUnion, arrayRemove, increment } from 'firebase/firestore';
import type { EnrichedMovie } from '$lib/logic';

const USERS_COLLECTION = 'users';

export type InteractionType = 'hearts' | 'watchlist';

/**
 * Helper: Firestore crashes if you save 'undefined'.
 * This converts 'undefined' to 'null' for every field.
 */
function sanitize(obj: any) {
    const clean: any = {};
    Object.keys(obj).forEach(key => {
        clean[key] = obj[key] === undefined ? null : obj[key];
    });
    return clean;
}

export async function toggleInteraction(uid: string, movie: EnrichedMovie, type: InteractionType, isAdding: boolean) {
    if (!uid) {
        console.error("[DB] No UID provided to toggleInteraction");
        return;
    }

    const userRef = doc(db, USERS_COLLECTION, uid);
    
    // 1. Construct the minimal object safely
    // REMOVED: posterUrl (to save space and avoid undefined errors)
    const rawData = {
        id: movie.movie_id || (movie as any).id || (movie as any)._id || "unknown_id", 
        title: movie.title || "Unknown Title",
        year: movie.year || "N/A"
    };

    // 2. Sanitize it just in case 'year' or 'title' are missing
    const movieMin = sanitize(rawData);

    console.log(`[DB] Attempting to ${isAdding ? 'add' : 'remove'} ${type}:`, movieMin);

    try {
        if (isAdding) {
            await updateDoc(userRef, {
                [type]: arrayUnion(movieMin)
            });
        } else {
            // Note: arrayRemove requires the EXACT object to work.
            // If the stored object has different fields than this one, remove might fail silently.
            // But since we standardized movieMin above, it should match future removals.
            await updateDoc(userRef, {
                [type]: arrayRemove(movieMin)
            });
        }
        console.log(`[DB] Success: Updated ${type}`);
    } catch (error) {
        console.error(`[DB] CRITICAL ERROR updating ${type}:`, error);
        throw error;
    }
}

export async function submitTag(uid: string, movieId: number, tag: string) {
    if (!uid) return;
    const userRef = doc(db, USERS_COLLECTION, uid);
    
    try {
        const tagData = sanitize({
            movieId: movieId || null,
            tag: tag || "unknown",
            timestamp: new Date().toISOString()
        });

        await updateDoc(userRef, {
            tags_contributed_count: increment(1),
            tags_history: arrayUnion(tagData)
        });
        console.log(`[DB] Tag submitted: ${tag}`);
    } catch (error) {
        console.error("[DB] Error submitting tag:", error);
        throw error;
    }
}