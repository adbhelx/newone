// Global state
let allSections = [];
let currentFilter = 'all';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadSections();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentFilter = e.target.dataset.category;
            filterSections();
        });
    });

    // Search on Enter key
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    // Close modals on background click
    document.getElementById('sectionModal').addEventListener('click', (e) => {
        if (e.target.id === 'sectionModal') {
            closeModal();
        }
    });

    document.getElementById('itemModal').addEventListener('click', (e) => {
        if (e.target.id === 'itemModal') {
            closeItemModal();
        }
    });
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        animateCounter('totalSections', stats.total_sections);
        animateCounter('totalItems', stats.total_items);
        animateCounter('sectionsWithContent', stats.sections_with_content);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Animate counter
function animateCounter(elementId, target) {
    const element = document.getElementById(elementId);
    const duration = 2000;
    const steps = 60;
    const increment = target / steps;
    let current = 0;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, duration / steps);
}

// Load sections
async function loadSections() {
    try {
        const response = await fetch('/api/sections');
        allSections = await response.json();
        displaySections(allSections);
    } catch (error) {
        console.error('Error loading sections:', error);
        document.getElementById('sectionsGrid').innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <p>حدث خطأ في تحميل الأقسام</p>
            </div>
        `;
    }
}

// Display sections
function displaySections(sections) {
    const grid = document.getElementById('sectionsGrid');
    
    if (sections.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <p>لا توجد أقسام متاحة</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = sections.map(section => `
        <div class="section-card" onclick="openSection('${section.id}', '${section.name}', '${section.icon}')" data-category="${section.category}">
            <span class="section-icon">${section.icon}</span>
            <div class="section-name">${section.name}</div>
            <div class="section-count">${section.count} عنصر</div>
            <span class="section-category">${section.category}</span>
        </div>
    `).join('');
}

// Filter sections
function filterSections() {
    const filtered = currentFilter === 'all' 
        ? allSections 
        : allSections.filter(s => s.category === currentFilter);
    
    displaySections(filtered);
}

// Open section modal
async function openSection(sectionId, sectionName, sectionIcon) {
    const modal = document.getElementById('sectionModal');
    const title = document.getElementById('modalTitle');
    const body = document.getElementById('modalBody');
    
    title.innerHTML = `${sectionIcon} ${sectionName}`;
    body.innerHTML = '<div class="loading">جاري التحميل...</div>';
    modal.classList.add('active');
    
    try {
        const response = await fetch(`/api/section/${sectionId}`);
        const data = await response.json();
        
        if (data.items.length === 0) {
            body.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <p>لا يوجد محتوى في هذا القسم</p>
                </div>
            `;
            return;
        }
        
        body.innerHTML = `
            <div class="items-grid">
                ${data.items.map(item => {
                    const isFile = item.content.startsWith('BQA') || 
                                   item.content.startsWith('AgA') || 
                                   item.content.startsWith('CQA');
                    return `
                        <div class="item-card" onclick="openItem('${sectionId}', ${item.id})">
                            <div class="item-title">${escapeHtml(item.title)}</div>
                            <span class="item-type">${isFile ? 'ملف' : 'نص'}</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Error loading section:', error);
        body.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <p>حدث خطأ في تحميل المحتوى</p>
            </div>
        `;
    }
}

// Close section modal
function closeModal() {
    document.getElementById('sectionModal').classList.remove('active');
}

// Open item modal
async function openItem(sectionId, itemId) {
    const modal = document.getElementById('itemModal');
    const title = document.getElementById('itemModalTitle');
    const body = document.getElementById('itemModalBody');
    
    title.textContent = 'جاري التحميل...';
    body.innerHTML = '<div class="loading">جاري التحميل...</div>';
    modal.classList.add('active');
    
    try {
        const response = await fetch(`/api/item/${sectionId}/${itemId}`);
        const item = await response.json();
        
        title.textContent = item.title;
        
        const isFile = item.content.startsWith('BQA') || 
                       item.content.startsWith('AgA') || 
                       item.content.startsWith('CQA');
        
        if (isFile) {
            body.innerHTML = `
                <div class="item-content">
                    <p style="text-align: center; color: var(--text-secondary);">
                        📄 هذا المحتوى عبارة عن ملف<br><br>
                        للوصول إلى الملف، يرجى استخدام البوت على تليجرام
                    </p>
                    <div style="text-align: center; margin-top: 2rem;">
                        <a href="https://t.me/YOUR_BOT_USERNAME" target="_blank" class="telegram-btn">
                            <span>فتح في تليجرام</span>
                            <span>✈️</span>
                        </a>
                    </div>
                </div>
            `;
        } else {
            body.innerHTML = `
                <div class="item-content">
                    ${escapeHtml(item.content)}
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading item:', error);
        body.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <p>حدث خطأ في تحميل المحتوى</p>
            </div>
        `;
    }
}

// Close item modal
function closeItemModal() {
    document.getElementById('itemModal').classList.remove('active');
}

// Perform search
async function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    
    if (!query) {
        closeSearch();
        return;
    }
    
    const resultsSection = document.getElementById('searchResults');
    const resultsContent = document.getElementById('searchResultsContent');
    
    resultsContent.innerHTML = '<div class="loading">جاري البحث...</div>';
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const results = await response.json();
        
        if (results.length === 0) {
            resultsContent.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🔍</div>
                    <p>لم يتم العثور على نتائج لـ "${escapeHtml(query)}"</p>
                </div>
            `;
            return;
        }
        
        resultsContent.innerHTML = `
            <div class="items-grid">
                ${results.map(result => {
                    const isFile = result.item.content.startsWith('BQA') || 
                                   result.item.content.startsWith('AgA') || 
                                   result.item.content.startsWith('CQA');
                    return `
                        <div class="item-card" onclick="openItem('${result.section}', ${result.item.id})">
                            <div>
                                <div class="item-title">${escapeHtml(result.item.title)}</div>
                                <div style="color: var(--text-secondary); font-size: 0.9rem; margin-top: 0.5rem;">
                                    القسم: ${result.section}
                                </div>
                            </div>
                            <span class="item-type">${isFile ? 'ملف' : 'نص'}</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Error searching:', error);
        resultsContent.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <p>حدث خطأ في البحث</p>
            </div>
        `;
    }
}

// Close search
function closeSearch() {
    document.getElementById('searchResults').style.display = 'none';
    document.getElementById('searchInput').value = '';
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});
