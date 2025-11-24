document.addEventListener('DOMContentLoaded', function() {
    // Crea il popup per l'XML
    const popup = document.createElement('div');
    popup.id = 'xml-popup';
    popup.className = 'xml-popup';
    popup.innerHTML = `
        <div class="xml-popup-header">
            <span class="xml-popup-title">XML Content</span>
            <div class="header-actions">
                <button type="button" class="copy-btn" title="Copia XML">
                    <i class="fa-regular fa-copy"></i>
                    <span class="copy-label">Copia</span>
                </button>
                <button class="xml-popup-close" title="Chiudi">&times;</button>
            </div>
        </div>
        <div class="xml-popup-content">
            <pre class="xml-popup-code"></pre>
        </div>
    `;
    document.body.appendChild(popup);

    const popupContent = popup.querySelector('.xml-popup-code');
    const closeBtn = popup.querySelector('.xml-popup-close');
    const copyBtn = popup.querySelector('.copy-btn');
    const copyLabel = copyBtn.querySelector('.copy-label');

    // Funzione per chiudere il popup
    function closePopup() {
        popup.classList.remove('show');
        popup.style.display = "none";
        // Ripristina lo scroll della pagina
        document.body.style.overflow = "";
    }

    // Event listener per il pulsante di chiusura
    closeBtn.addEventListener('click', closePopup);

    // Event listener per il pulsante copia
    copyBtn.addEventListener('click', function() {
        const xmlText = popupContent.textContent;
        
        // Copia negli appunti
        navigator.clipboard.writeText(xmlText).then(function() {
            // Feedback visivo: cambia il testo del pulsante
            const originalHTML = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fa-solid fa-check"></i><span class="copy-label">Copiato!</span>';
            copyBtn.style.backgroundColor = '#00aa00';
            
            // Ripristina dopo 2 secondi
            setTimeout(function() {
                copyBtn.innerHTML = originalHTML;
                copyBtn.style.backgroundColor = '';
            }, 2000);
        }).catch(function(err) {
            console.error('Errore nella copia: ', err);
            // Feedback di errore
            copyLabel.textContent = 'Errore!';
            setTimeout(function() {
                copyLabel.textContent = 'Copia';
            }, 2000);
        });
    });

    // Chiudi con ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && popup.classList.contains('show')) {
            closePopup();
        }
    });

    // Trova tutte le celle XML e aggiungi gli event listener
    const xmlCells = document.querySelectorAll('.campo-xml');
    
    xmlCells.forEach(cell => {
        // Limita il testo a 2 righe inizialmente
        const pre = cell.querySelector('pre');
        if (pre) {
            const fullText = pre.textContent;
            cell.dataset.fullXml = fullText;
            
            // Mostra solo le prime 2 righe
            const lines = fullText.split('\n');
            const preview = lines.slice(0, 2).join('\n');
            pre.textContent = preview + (lines.length > 2 ? '...' : '');
        }

        // Event listener per mostrare il popup
        cell.addEventListener('click', function(e) {
            e.stopPropagation();
            const fullXml = this.dataset.fullXml;
            
            if (fullXml) {
                popupContent.textContent = fullXml;
                popup.classList.add('show');
                popup.style.display = 'flex';
                // Blocca lo scroll della pagina mentre il popup è aperto
                document.body.style.overflow = "hidden";
            }
        });

        // Aggiungi indicatore visivo al hover
        cell.style.cursor = 'pointer';
        cell.title = 'Click per visualizzare XML completo';
    });
});