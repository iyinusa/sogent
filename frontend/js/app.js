// Animation and chat functionality for support.html
window.addEventListener('DOMContentLoaded', () => {
    const btn = document.querySelector('.open-agent-btn');
    if (btn) {
        btn.addEventListener('click', (e) => {
            btn.classList.add('clicked');
            setTimeout(() => btn.classList.remove('clicked'), 400);
        });
    }

    const chatForm = document.querySelector('.chat-input-area');
    const chatInput = document.querySelector('.chat-input');
    const chatWindow = document.getElementById('chat-window');

    let selectedWebsiteId = null;

    // Helper to add a chat bubble
    function addChatBubble(message, sender = 'user') {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${sender}`;
        const msgSpan = document.createElement('span');
        msgSpan.innerHTML = sender === 'agent' ? `<i class="fa-solid fa-robot"></i> ${message}` : message;
        bubble.appendChild(msgSpan);
        const timeSpan = document.createElement('span');
        timeSpan.className = 'chat-time';
        const now = new Date();
        timeSpan.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        bubble.appendChild(timeSpan);
        chatWindow.appendChild(bubble);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Helper to add a product card bubble
    function addProductCard(product) {
        const card = document.createElement('div');
        card.className = 'chat-bubble agent product-card';
        card.innerHTML = `
            <div class="product-card-content">
                <div class="product-image-wrap">
                    <img src="${product.image || '/images/logo.png'}" alt="${product.name || 'Product'}" class="product-image">
                </div>
                <div class="product-details">
                    <div class="product-title">${product.name || ''}</div>
                    <div class="product-desc">${product.content || ''}</div>
                    <div class="product-meta">
                        ${product.price ? `<span class="product-price">${product.price}</span>` : ''}
                        ${product.link ? `<a href="${product.link}" class="product-link" target="_blank"><i class="fa-solid fa-arrow-up-right-from-square"></i> View</a>` : ''}
                    </div>
                </div>
            </div>
            <span class="chat-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        `;
        chatWindow.appendChild(card);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Helper to add a product comparison table
    function addProductComparisonTable(products) {
        if (!Array.isArray(products) || products.length < 2) return;
        // Collect all unique keys for table columns
        const allKeys = Array.from(new Set(products.flatMap(p => Object.keys(p)))).filter(k => k !== 'role');
        // Table header
        let table = `<div class="chat-bubble agent product-compare-table"><table><thead><tr><th>Feature</th>`;
        products.forEach((p, i) => {
            table += `<th>Product ${i + 1}</th>`;
        });
        table += `</tr></thead><tbody>`;
        allKeys.forEach(key => {
            table += `<tr><td>${key.charAt(0).toUpperCase() + key.slice(1)}</td>`;
            products.forEach(p => {
                let val = p[key] || '';
                if (key === 'image' && val) {
                    val = `<img src="${val}" alt="Product Image" style="max-width:60px;max-height:60px;border-radius:8px;">`;
                } else if (key === 'link' && val) {
                    val = `<a href="${val}" target="_blank"><i class="fa-solid fa-arrow-up-right-from-square"></i> View</a>`;
                }
                table += `<td>${val}</td>`;
            });
            table += `</tr>`;
        });
        table += `</tbody></table></div>`;
        chatWindow.insertAdjacentHTML('beforeend', table);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    if (chatForm && chatInput && chatWindow) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (!message) return;
            addChatBubble(message, 'user');
            chatInput.value = '';
            chatInput.disabled = true;
            // Send to backend
            try {
                const body = { message };
                if (selectedWebsiteId) body.website_id = selectedWebsiteId;
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                const data = await res.json();
                // If product info is present, render as product card
                if (data && data.product && (data.product.name || data.product.content)) {
                    addProductCard(data.product);
                } else if (data && data.response) {
                    // Try to parse as JSON for product info or comparison
                    let parsed = null;
                    try {
                        parsed = JSON.parse(data.response);
                    } catch {}
                    if (Array.isArray(parsed) && parsed.length > 1 && parsed.every(p => typeof p === 'object')) {
                        addProductComparisonTable(parsed);
                    } else if (parsed && typeof parsed === 'object' && (parsed.name || parsed.content)) {
                        if (parsed.name || parsed.image || parsed.price || parsed.link) {
                            addProductCard(parsed);
                        } else if (parsed.content) {
                            addChatBubble(parsed.content, 'agent');
                        } else {
                            addChatBubble(data.response, 'agent');
                        }
                    } else {
                        addChatBubble(data.response, 'agent');
                    }
                } else {
                    addChatBubble('Sorry, no response from agent.', 'agent');
                }
            } catch (err) {
                addChatBubble('Error connecting to agent.', 'agent');
            }
            chatInput.disabled = false;
            chatInput.focus();
        });
    }

    // Website URL form logic
    const websiteForm = document.querySelector('.website-url-form');
    const websiteInput = document.querySelector('.website-url-input');
    const websiteName = document.querySelector('.website-name');
    const websiteDesc = document.querySelector('.website-desc');
    const websiteLogo = document.querySelector('.website-logo img');
    const websiteDropdown = document.querySelector('.website-url-dropdown');

    // Helper to populate website info
    function populateWebsiteInfo(data) {
        websiteName.textContent = data.name || data.url || '';
        websiteDesc.textContent = data.description || '';
        websiteLogo.src = data.icon || '/images/logo.png';
    }

    // Fetch and populate dropdown
    async function loadWebsitesDropdown() {
        if (!websiteDropdown) return;
        websiteDropdown.innerHTML = '<option value="">🌐 Select Website</option>';
        try {
            const res = await fetch('/api/websites/');
            if (!res.ok) throw new Error('Failed to fetch websites');
            const websites = await res.json();
            websites.forEach(site => {
                const opt = document.createElement('option');
                opt.value = site.url;
                opt.textContent = site.name;
                opt.dataset.icon = site.icon;
                opt.dataset.description = site.description;
                opt.dataset.site = JSON.stringify(site);
                websiteDropdown.appendChild(opt);
            });
        } catch (err) {
            // Optionally handle error
        }
    }

    if (websiteDropdown && websiteInput && websiteName && websiteDesc && websiteLogo) {
        websiteDropdown.addEventListener('change', (e) => {
            const selected = websiteDropdown.options[websiteDropdown.selectedIndex];
            if (selected && selected.value) {
                websiteInput.value = selected.value;
                try {
                    const site = JSON.parse(selected.dataset.site);
                    populateWebsiteInfo(site);
                    selectedWebsiteId = site.id;
                } catch {
                    selectedWebsiteId = null;
                }
            } else {
                selectedWebsiteId = null;
            }
        });
        loadWebsitesDropdown();
    }

    if (websiteForm && websiteInput && websiteName && websiteDesc && websiteLogo) {
        websiteForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = websiteInput.value.trim();
            if (!url) return;
            websiteInput.disabled = true;
            try {
                const res = await fetch('/api/websites/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                if (!res.ok) throw new Error('Failed to fetch website details');
                const data = await res.json();
                populateWebsiteInfo(data);
                websiteInput.value = '';
                // Reload dropdown to include new website
                await loadWebsitesDropdown();
            } catch (err) {
                websiteName.textContent = 'Could not fetch website';
                websiteDesc.textContent = '';
                websiteLogo.src = '/images/logo.png';
            }
            websiteInput.disabled = false;
            websiteInput.focus();
        });
    }
});