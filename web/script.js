// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        tab.classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
    });
});

// Drag and drop
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleLogFile(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleLogFile(e.target.files[0]);
    }
});

// Handle log file
function handleLogFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('log-paste').value = e.target.result;
        analyzeLog(e.target.result);
    };
    reader.readAsText(file);
}

// Analyze button
document.getElementById('analyze-btn').addEventListener('click', () => {
    const logContent = document.getElementById('log-paste').value;
    if (logContent.trim()) {
        analyzeLog(logContent);
    } else {
        alert('Please paste a crash log or upload a file');
    }
});

// Scan button
document.getElementById('scan-btn').addEventListener('click', () => {
    const files = document.getElementById('folder-input').files;
    if (files.length > 0) {
        scanModsFolder(files);
    } else {
        alert('Please select your mods folder');
    }
});

// Analysis function
function analyzeLog(logContent) {
    showLoading(true);
    
    // Simulate API call - in production, this would call your Python backend
    setTimeout(() => {
        const results = parseLogContent(logContent);
        displayResults(results);
        showLoading(false);
    }, 1500);
}

// Parse log content (simplified - in production use Python backend)
function parseLogContent(content) {
    const results = {
        errors: [],
        missingDeps: [],
        mcVersion: extractMCVersion(content),
        loader: extractLoader(content)
    };
    
    // Detect missing dependencies
    const depRegex = /(?:Mod|mod) (\S+) requires (\S+)/gi;
    let match;
    while ((match = depRegex.exec(content)) !== null) {
        results.missingDeps.push({
            mod: match[1],
            required: match[2],
            // Mock data - real implementation would fetch from API
            downloadInfo: {
                name: match[2],
                pageUrl: `https://modrinth.com/mod/${match[2]}`,
                versionUrl: `https://modrinth.com/mod/${match[2]}/version/latest`,
                downloadUrl: `https://cdn.modrinth.com/data/${match[2]}/versions/latest.jar`
            }
        });
    }
    
    // Detect other errors
    if (content.includes('ClassNotFoundException')) {
        results.errors.push({
            type: 'Missing Class',
            reason: 'Missing dependency or corrupted mod',
            solution: 'Reinstall the mod or check for missing dependencies'
        });
    }
    
    if (content.includes('Mixin')) {
        results.errors.push({
            type: 'Mixin Conflict',
            reason: 'Incompatible mods modifying the same code',
            solution: 'Remove conflicting mods one by one to identify the issue'
        });
    }
    
    return results;
}

function extractMCVersion(content) {
    const match = content.match(/Minecraft\s+(\d+\.\d+(?:\.\d+)?)/i);
    return match ? match[1] : 'Unknown';
}

function extractLoader(content) {
    if (content.toLowerCase().includes('fabric')) return 'Fabric';
    if (content.toLowerCase().includes('forge')) return 'Forge';
    return 'Unknown';
}

// Display results
function displayResults(results) {
    const resultsDiv = document.getElementById('results');
    const contentDiv = document.getElementById('results-content');
    
    let html = '';
    
    // Header info
    html += `
        <div class="success-card">
            <h3>🎮 Detected Configuration</h3>
            <p><strong>Minecraft Version:</strong> ${results.mcVersion}</p>
            <p><strong>Mod Loader:</strong> ${results.loader}</p>
        </div>
    `;
    
    // Missing dependencies
    if (results.missingDeps.length > 0) {
        html += '<h3 style="margin-top: 30px;">📦 Missing Dependencies</h3>';
        results.missingDeps.forEach(dep => {
            html += `
                <div class="dependency-card">
                    <div class="mod-name">❌ ${dep.required}</div>
                    <p>Required by: <strong>${dep.mod}</strong></p>
                    ${dep.downloadInfo ? `
                        <div style="margin-top: 15px;">
                            <a href="${dep.downloadInfo.pageUrl}" target="_blank" class="download-link">
                                🔗 Mod Page
                            </a>
                            <a href="${dep.downloadInfo.versionUrl}" target="_blank" class="download-link">
                                📦 Version for ${results.mcVersion}
                            </a>
                            <a href="${dep.downloadInfo.downloadUrl}" target="_blank" class="download-link">
                                📥 Direct Download
                            </a>
                        </div>
                    ` : ''}
                </div>
            `;
        });
    }
    
    // Other errors
    if (results.errors.length > 0) {
        html += '<h3 style="margin-top: 30px;">🔍 Detected Errors</h3>';
        results.errors.forEach(error => {
            html += `
                <div class="error-card">
                    <div class="mod-name">❌ ${error.type}</div>
                    <p><strong>Reason:</strong> ${error.reason}</p>
                    <p><strong>Solution:</strong> ${error.solution}</p>
                </div>
            `;
        });
    }
    
    if (results.errors.length === 0 && results.missingDeps.length === 0) {
        html += `
            <div class="success-card">
                <h3>✅ No Issues Detected</h3>
                <p>Your mod configuration appears to be correct!</p>
            </div>
        `;
    }
    
    contentDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
}

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
    document.getElementById('results').style.display = show ? 'none' : 'block';
}

// Scan mods folder
function scanModsFolder(files) {
    showLoading(true);
    
    // In production, send files to Python backend for processing
    setTimeout(() => {
        alert('Mods folder scanning would be implemented with backend API');
        showLoading(false);
    }, 1000);
}