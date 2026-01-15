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
        <h3 class="text-xs font-bold text-neutral-400 uppercase tracking-widest">Taste Topology</h3>
    </div>

    <div class="relative mt-4">
        <svg width={size} height={size} viewBox="0 0 {size} {size}" class="overflow-visible">
            
            {#each levels as level}
                <polygon 
                    points={keys.map((_, i) => getPoint(i, level)).join(' ')} 
                    fill="none" 
                    stroke="#333" 
                    stroke-width="1" 
                    class="opacity-20"
                />
            {/each}

            {#each keys as key, i}
                {@const point = getPoint(i, 100)}
                <line 
                    x1={center} y1={center} 
                    x2={point.split(',')[0]} y2={point.split(',')[1]} 
                    stroke="#333" 
                    stroke-width="1" 
                    class="opacity-20" 
                />
                
                {@const labelPoint = getPoint(i, 125)} <text 
                    x={labelPoint.split(',')[0]} 
                    y={labelPoint.split(',')[1]} 
                    text-anchor="middle" 
                    dominant-baseline="middle" 
                    class="text-[10px] fill-neutral-500 font-bold uppercase tracking-wider"
                >
                    {key}
                </text>
            {/each}

            <polygon 
                points={pathData} 
                fill="url(#gradient)" 
                fill-opacity="0.5" 
                stroke="#818cf8" 
                stroke-width="2"
                style="filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.5));"
                class="transition-all duration-1000 ease-out"
            />
            
            <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#4f46e5;stop-opacity:1" /> <stop offset="100%" style="stop-color:#ec4899;stop-opacity:1" /> </linearGradient>
            </defs>
            
            {#each keys as key, i}
                {@const point = getPoint(i, (stats as any)[key])}
                <circle cx={point.split(',')[0]} cy={point.split(',')[1]} r="3" fill="#fff" class="shadow-lg" />
            {/each}
        </svg>
    </div>

    <div class="mt-2 text-center z-10">
        <p class="text-[10px] text-neutral-600">
            Based on your last <span class="text-neutral-400">24 rated films</span>.
        </p>
    </div>
    
    <div class="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-indigo-900/10 pointer-events-none"></div>
</div>