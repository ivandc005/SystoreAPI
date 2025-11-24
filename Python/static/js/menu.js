document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const cards = document.querySelectorAll('.card');
    const categories = document.querySelectorAll('.category');
    const noResults = document.getElementById('noResults');

    if (!searchInput) return;

    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase().trim();
        let visibleCount = 0;

        if (searchTerm === '') {
            cards.forEach(card => card.style.display = 'block');
            categories.forEach(cat => cat.style.display = 'block');
            noResults.style.display = 'none';
            return;
        }

        cards.forEach(card => {
            const keywords = card.getAttribute('data-keywords') || '';
            const title = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
            const description = card.querySelector('.card-description')?.textContent.toLowerCase() || '';
            const matchFound =
                keywords.toLowerCase().includes(searchTerm) ||
                title.includes(searchTerm) ||
                description.includes(searchTerm);

            if (matchFound) {
                card.style.display = 'block';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        categories.forEach(category => {
            const visibleCards = Array.from(category.querySelectorAll('.card')).filter(card =>
                card.style.display !== 'none'
            );
            category.style.display = visibleCards.length > 0 ? 'block' : 'none';
        });

        noResults.style.display = visibleCount === 0 ? 'block' : 'none';
    });

    // Animazione al caricamento
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.4s ease';

            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 50);
        }, index * 50);
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const logo = document.getElementById('logo');
    if (!logo) return;

    const originalSrc = logo.src;
    const hoverSrc = logo.getAttribute('data-hover');

    logo.addEventListener('mouseenter', () => {
        if (hoverSrc) logo.src = hoverSrc;
    });

    logo.addEventListener('mouseleave', () => {
        logo.src = originalSrc;
    });
});

