// ==========================================
// THEME SWITCHER - SAVE PREFERENCE & TOGGLE
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    initThemeSwitcher();
});

function initThemeSwitcher() {
    // Check if theme toggle already exists (prevent duplicates)
    if (document.getElementById('themeToggle')) {
        return;
    }

    // Get saved theme from localStorage or default to dark
    const savedTheme = localStorage.getItem('theme') || 'dark';
    
    // Apply saved theme immediately
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
    }

    // Find header controls container (preferito) o fallback su header-content
    let targetContainer = document.querySelector('.header-controls');
    
    if (!targetContainer) {
        // Fallback: se non esiste header-controls, usa header-content
        targetContainer = document.querySelector('.header-content');
        
        if (!targetContainer) return; // Nessun container trovato, esci
        
        // Crea header-controls se non esiste
        const controlsContainer = document.createElement('div');
        controlsContainer.className = 'header-controls';
        targetContainer.appendChild(controlsContainer);
        targetContainer = controlsContainer;
    }

    // Create theme toggle button
    const themeToggleContainer = document.createElement('div');
    themeToggleContainer.className = 'theme-toggle-container';
    themeToggleContainer.innerHTML = `
        <button id="themeToggle" class="theme-toggle-btn ${savedTheme === 'light' ? 'light' : ''}" 
                title="Toggle theme" aria-label="Toggle light/dark theme">
            <div class="theme-toggle-slider">
                <span class="theme-icon">${savedTheme === 'light' ? '☀️' : '🌙'}</span>
            </div>
        </button>
    `;

    // Append al container (sarà dopo il language selector)
    targetContainer.appendChild(themeToggleContainer);

    // Add click event listener
    const toggleBtn = document.getElementById('themeToggle');
    const slider = toggleBtn.querySelector('.theme-toggle-slider');
    const icon = toggleBtn.querySelector('.theme-icon');

    toggleBtn.addEventListener('click', function() {
        // Toggle theme class on body
        document.body.classList.toggle('light-theme');
        
        // Update button state
        const isLight = document.body.classList.contains('light-theme');
        this.classList.toggle('light', isLight);
        
        // Update icon
        icon.textContent = isLight ? '☀️' : '🌙';
        
        // Save preference to localStorage
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
        
        // Add a little animation feedback
        slider.style.transform = 'scale(1.2)';
        setTimeout(() => {
            slider.style.transform = 'scale(1)';
        }, 200);
        
        // Log for debugging (remove in production)
        console.log(`Theme switched to: ${isLight ? 'light' : 'dark'} mode 🎨`);
    });

    // Add keyboard support (Space or Enter)
    toggleBtn.addEventListener('keypress', function(e) {
        if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            this.click();
        }
    });
}

// Export for use in other scripts if needed
window.themeSwitcher = {
    getCurrentTheme: function() {
        return document.body.classList.contains('light-theme') ? 'light' : 'dark';
    },
    setTheme: function(theme) {
        if (theme === 'light') {
            document.body.classList.add('light-theme');
            localStorage.setItem('theme', 'light');
        } else {
            document.body.classList.remove('light-theme');
            localStorage.setItem('theme', 'dark');
        }
    }
};