document.addEventListener('DOMContentLoaded', function() {
    // Formattazione automatica delle celle della tabella
    const table = document.querySelector('table');
    if (!table) return;

    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        
        cells.forEach((cell, index) => {
            const text = cell.textContent.trim();
            
            // Formatta celle vuote o NULL/None
            if (!text || text === 'NULL' || text === 'None' || text === 'null' || text === 'none') {
                cell.innerHTML = '<span style="color: #666; font-style: italic;">—</span>';
                cell.style.textAlign = 'center';
            }
            
            // Formatta date e orari (colonne TIME)
            if (cell.textContent.match(/\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}/)) {
                const dateTime = cell.textContent.trim();
                const [date, time] = dateTime.split(' ');
                cell.innerHTML = `
                    <div style="display: flex; flex-direction: column; gap: 2px;">
                        <span style="color: #aaddff; font-weight: 500;">${date}</span>
                        <span style="color: #888; font-size: 0.85rem;">${time}</span>
                    </div>
                `;
            }
            
            // Formatta ID lunghi (colonne ID)
            if (text.length > 15 && /^\d+$/.test(text)) {
                cell.style.fontFamily = 'Courier New, monospace';
                cell.style.fontSize = '0.85rem';
                cell.style.letterSpacing = '0.5px';
            }
            
            // Aggiungi tooltip per celle con testo lungo (esclusi XML)
            if (text.length > 50 && !cell.classList.contains('campo-xml')) {
                cell.title = text;
                cell.style.cursor = 'help';
            }
        });
    });

    // Aggiungi numerazione righe (opzionale)
    addRowNumbers();
    
    // Aggiungi filtri di ricerca rapida
    addQuickSearch();
});

// Funzione per aggiungere numerazione righe
function addRowNumbers() {
    const table = document.querySelector('table');
    if (!table) return;
    
    const thead = table.querySelector('thead tr');
    const tbody = table.querySelector('tbody');
    
    // Aggiungi header per numero riga
    const numberHeader = document.createElement('th');
    numberHeader.textContent = '#';
    numberHeader.style.width = '50px';
    numberHeader.style.textAlign = 'center';
    thead.insertBefore(numberHeader, thead.firstChild);
    
    // Aggiungi numero a ogni riga
    const rows = tbody.querySelectorAll('tr');
    rows.forEach((row, index) => {
        const numberCell = document.createElement('td');
        numberCell.textContent = index + 1;
        numberCell.style.textAlign = 'center';
        numberCell.style.color = '#00aaff';
        numberCell.style.fontWeight = '600';
        numberCell.style.fontSize = '0.85rem';
        row.insertBefore(numberCell, row.firstChild);
    });
}

// Funzione per aggiungere ricerca rapida
function addQuickSearch() {
    const container = document.querySelector('.table-container');
    if (!container) return;
    
    // Crea barra di ricerca
    const searchBar = document.createElement('div');
    searchBar.style.cssText = `
        padding: 1rem;
        background: linear-gradient(135deg, #1a1a1a, #2a2a2a);
        border-bottom: 2px solid #004466;
        position: sticky;
        top: 0;
        z-index: 100;
        display: flex;
        gap: 1rem;
        align-items: center;
    `;
    
    searchBar.innerHTML = `
        <input 
            type="text" 
            id="tableSearch" 
            placeholder="🔍 Cerca nella tabella..." 
            style="
                flex: 1;
                padding: 0.8rem 1rem;
                background-color: #0d0d0d;
                border: 2px solid #004466;
                border-radius: 8px;
                color: #eee;
                font-size: 0.95rem;
                transition: all 0.3s ease;
            "
        />
        <button 
            id="clearSearch"
            style="
                padding: 0.8rem 1.5rem;
                background: linear-gradient(135deg, #006699, #00ccff);
                border: none;
                border-radius: 8px;
                color: white;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.2s ease;
            "
        >
            Cancella
        </button>
    `;
    
    container.insertBefore(searchBar, container.firstChild);
    
    const searchInput = document.getElementById('tableSearch');
    const clearBtn = document.getElementById('clearSearch');
    const table = container.querySelector('table');
    const rows = table.querySelectorAll('tbody tr');
    
    // Focus styling
    searchInput.addEventListener('focus', function() {
        this.style.borderColor = '#00aaff';
        this.style.boxShadow = '0 0 15px rgba(0, 170, 255, 0.5)';
    });
    
    searchInput.addEventListener('blur', function() {
        this.style.borderColor = '#004466';
        this.style.boxShadow = 'none';
    });
    
    // Ricerca in tempo reale
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        let visibleCount = 0;
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });
        
        // Mostra conteggio risultati
        updateResultCount(visibleCount, rows.length);
    });
    
    // Pulsante cancella
    clearBtn.addEventListener('click', function() {
        searchInput.value = '';
        rows.forEach(row => row.style.display = '');
        searchInput.focus();
        updateResultCount(rows.length, rows.length);
    });
    
    // Hover del pulsante
    clearBtn.addEventListener('mouseenter', function() {
        this.style.transform = 'scale(1.05)';
        this.style.boxShadow = '0 4px 15px rgba(0, 170, 255, 0.6)';
    });
    
    clearBtn.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
        this.style.boxShadow = 'none';
    });
}

// Mostra conteggio risultati
function updateResultCount(visible, total) {
    let countDisplay = document.getElementById('resultCount');
    
    if (!countDisplay) {
        countDisplay = document.createElement('div');
        countDisplay.id = 'resultCount';
        countDisplay.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(135deg, #006699, #00ccff);
            color: white;
            padding: 0.8rem 1.2rem;
            border-radius: 25px;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(0, 170, 255, 0.6);
            z-index: 1000;
            font-size: 0.9rem;
        `;
        document.body.appendChild(countDisplay);
    }
    
    countDisplay.textContent = `${visible} / ${total} righe`;
    
    if (visible === total) {
        countDisplay.style.display = 'none';
    } else {
        countDisplay.style.display = 'block';
    }
}