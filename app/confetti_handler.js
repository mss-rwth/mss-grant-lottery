if ('serviceWorker' in navigator && !navigator.serviceWorker.controller) {
    navigator.serviceWorker.addEventListener('controllerchange', function() {
        window.location.reload();
    });
}

$(document).on('shiny:connected', function() {
    Shiny.addCustomMessageHandler('fire_confetti', function(_) {
        const colors = [...Array(20).keys()].map(i => getComputedStyle(document.documentElement).getPropertyValue(`--mss-${i+1}`).trim()).filter(Boolean);
        [
            { origin: { x: 0.1, y: 0.3 }, angle: 60  },
            { origin: { x: 0.9, y: 0.3 }, angle: 120 },
            { origin: { x: 0.5, y: 0.5 }, angle: 90  },
            { origin: { x: 0.2, y: 0.8 }, angle: 75  },
            { origin: { x: 0.8, y: 0.8 }, angle: 105 },
        ].forEach(({ origin, angle }) => confetti({
            particleCount: 120,
            spread: 80,
            origin,
            angle,
            scalar: 2,
            colors,
        }));
    });
});
