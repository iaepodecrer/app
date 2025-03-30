// ...existing code...

// Using custom event system instead of direct DOM event listeners
// This decouples visualization updates from UI components

// Listen for theme changes through the custom event system
document.addEventListener('themeChanged', function(e) {
    // Update visualizations when theme changes
    updateVisualizationColors();
    
    // If there are active visualizations, redraw them with the new theme
    if (currentVisualization) {
        drawVisualization(currentVisualization.type, currentVisualization.data);
    }
});

function updateVisualizationColors() {
    // Get current theme colors
    const isDarkMode = document.body.classList.contains('dark-theme');
    chartColors = isDarkMode ? darkThemeColors : lightThemeColors;
    
    // Update any active chart configurations with new colors
    // ...existing code...
}

// ...existing code...
