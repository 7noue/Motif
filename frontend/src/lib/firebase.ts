import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getAnalytics, isSupported } from 'firebase/analytics';

// Replace with your actual keys
const firebaseConfig = {
  apiKey: "AIzaSyAUz_e9x6VMEL0x7xfafe3EEwWnKKuCejU",
  authDomain: "motif-914e4.firebaseapp.com",
  projectId: "motif-914e4",
  storageBucket: "motif-914e4.firebasestorage.app",
  messagingSenderId: "676694689205",
  appId: "1:676694689205:web:6dedbf9c7d1cbba9dd85fc",
  measurementId: "G-LZ62F7HDHQ"
}

// 1. Initialize Firebase (Singleton Pattern)
// This prevents "Firebase App already exists" errors during hot reload
const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();

// 2. Export Services
export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();

// 3. FIX: Initialize Analytics ONLY in the browser
// We export 'analytics' as a promise or undefined to be safe
export let analytics: any;

if (typeof window !== 'undefined') {
    // Only run this code on the client-side (browser)
    isSupported().then((supported) => {
        if (supported) {
            analytics = getAnalytics(app);
        }
    });
}



