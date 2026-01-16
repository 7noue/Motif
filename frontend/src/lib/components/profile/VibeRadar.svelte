<script lang="ts">
    /**
     * VibeRadar.svelte
     * A zero-dependency, high-performance SVG radar chart for user taste profiles.
     */
    
    // Default stats if none provided
    let { stats = {
        Melancholy: 50,
        Adrenaline: 50,
        Intellectual: 50,
        Wholesome: 50,
        Surreal: 50,
        Romantic: 50
    }} = $props();

    // Configuration
    const size = 300;
    const center = size / 2;
    const radius = 100; // How big the spiderweb is
    const keys = Object.keys(stats);
    const totalpoints = keys.length;

    // Helper: Calculate X/Y coordinates for the polygon
    // Math: x = center + radius * cos(angle)
    function getPoint(index: number, value: number) {
        const angle = (Math.PI * 2 * index) / totalpoints - Math.PI / 2;
        // Normalize value (0-100) to pixel radius
        const r = (value / 100) * radius;
        const x = center + r * Math.cos(angle);
        const y = center + r * Math.sin(angle);
        return `${x},${y}`;
    }

    // Reactive: Generate the path string for the user's stats
    const pathData = $derived(keys.map((key, i) => getPoint(i, (stats as any)[key])).join(' '));
    
    // Generate the background web levels (100%, 75%, 50%, 25%)
    const levels = [100, 75, 50, 25];
</script>

<div class="flex flex-col items-center justify-center p-6 bg-[#0e0e0e] border border-white/5 rounded-3xl relative overflow-hidden group h-full min-h-[350px]">
    
    <div class="absolute top-6 left-6 flex items-center gap-2 z-10">
        <div class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></div>
        <h3 class="text-xs font-bold text-neutral-400 uppercase tracking-widest">Vibe Topology</h3>
    </div>

    <div class="mt-2 text-center z-10">
        <p class="text-[10px] text-neutral-600">
            Derived from your <span class="text-neutral-400">tagging patterns</span>.
        </p>
    </div>
    
    </div>