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

    // ============================================
    // FUNZIONE PER FORMATTARE XML CORRETTAMENTE
    // ============================================
    function formatXml(xml) {
        try {
            // Rimuove spazi bianchi extra e newline
            xml = xml.trim().replace(/>\s+</g, '><');
            
            // Parse XML
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(xml, 'text/xml');
            
            // Controlla errori di parsing
            const parserError = xmlDoc.getElementsByTagName('parsererror');
            if (parserError.length > 0) {
                console.warn('XML parsing error, returning original');
                return xml;
            }
            
            // Serializza con formattazione
            const serializer = new XMLSerializer();
            let formatted = serializer.serializeToString(xmlDoc);
            
            // Indentazione manuale per maggiore controllo
            let indentLevel = 0;
            const indent = '  '; // 2 spazi per livello
            
            formatted = formatted
                .replace(/></g, '>\n<') // Nuova riga tra tag
                .split('\n')
                .map(line => {
                    line = line.trim();
                    
                    // Tag di chiusura: riduci indentazione prima
                    if (line.match(/^<\/\w/)) {
                        indentLevel = Math.max(0, indentLevel - 1);
                    }
                    
                    const indentedLine = indent.repeat(indentLevel) + line;
                    
                    // Tag di apertura senza chiusura immediata: aumenta indentazione
                    if (line.match(/^<\w[^>]*[^\/]>$/)) {
                        indentLevel++;
                    }
                    
                    return indentedLine;
                })
                .join('\n');
            
            return formatted;
            
        } catch (error) {
            console.error('Error formatting XML:', error);
            return xml; // Ritorna XML originale in caso di errore
        }
    }

    // Funzione per chiudere il popup
    function closePopup() {
        popup.classList.remove('show');
        popup.style.display = "none";
        document.body.style.overflow = "";
    }

    // Event listener per il pulsante di chiusura
    closeBtn.addEventListener('click', closePopup);

    // Event listener per il pulsante copia
    copyBtn.addEventListener('click', function() {
        const xmlText = popupContent.textContent;
        
        navigator.clipboard.writeText(xmlText).then(function() {
            const originalHTML = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fa-solid fa-check"></i><span class="copy-label">Copiato!</span>';
            copyBtn.style.backgroundColor = '#00aa00';
            
            setTimeout(function() {
                copyBtn.innerHTML = originalHTML;
                copyBtn.style.backgroundColor = '';
            }, 2000);
        }).catch(function(err) {
            console.error('Errore nella copia: ', err);
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
        const pre = cell.querySelector('pre');
        if (pre) {
            const fullText = pre.textContent;
            
            // *** FORMATTA L'XML CORRETTAMENTE ***
            const formattedXml = formatXml(fullText);
            cell.dataset.fullXml = formattedXml;
            
            // Mostra solo le prime 2 righe nel preview
            const lines = formattedXml.split('\n');
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
                document.body.style.overflow = "hidden";
            }
        });

        // Aggiungi indicatore visivo al hover
        cell.style.cursor = 'pointer';
        cell.title = 'Click per visualizzare XML completo';
    });
});