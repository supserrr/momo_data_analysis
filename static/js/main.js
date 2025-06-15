document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('file-info');
    const previewContainer = document.getElementById('preview-container');
    const filenamePreview = document.getElementById('filename-preview');
    const filesizePreview = document.getElementById('filesize-preview');
    const changeFileBtn = document.getElementById('change-file-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const loadingContainer = document.getElementById('loading-container');
    const loadingStatus = document.getElementById('loading-status');
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    
    // Detection elements
    const detectBtn = document.getElementById('detect-btn');
    const detectedFiles = document.getElementById('detected-files');
    const filesList = document.getElementById('files-list');
    
    let selectedFile = null;
    
    // File detection functionality
    if (detectBtn) {
        detectBtn.addEventListener('click', async () => {
            try {
                detectBtn.disabled = true;
                detectBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
                
                const response = await fetch('/api/detect-files');
                const data = await response.json();
                
                if (data.files && data.files.length > 0) {
                    displayDetectedFiles(data.files);
                    detectedFiles.classList.remove('hidden');
                } else {
                    showError('No XML files found in the data directory');
                    detectedFiles.classList.add('hidden');
                }
            } catch (error) {
                showError('Error scanning for files: ' + error.message);
            } finally {
                detectBtn.disabled = false;
                detectBtn.innerHTML = '<i class="fas fa-search"></i> Scan for Files';
            }
        });
    }
    
    function displayDetectedFiles(files) {
        if (!filesList) return;
        
        filesList.innerHTML = '';
        
        files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.style.cssText = `
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem;
                margin-bottom: 0.5rem;
                background-color: var(--card-bg);
                border: 1px solid var(--border);
                border-radius: 8px;
                transition: all 0.3s ease;
            `;
            
            fileItem.innerHTML = `
                <div class="file-details-mini">
                    <div style="font-weight: 600; color: var(--text-primary);">${file.name}</div>
                    <div style="font-size: 0.9rem; color: var(--text-secondary);">
                        Size: ${file.size} | Modified: ${new Date(file.modified).toLocaleDateString()}
                    </div>
                </div>
                <button class="process-file-btn primary-btn" data-file-path="${file.path}" style="margin-left: 1rem;">
                    <i class="fas fa-cogs"></i> Process
                </button>
            `;
            
            // Hover effect
            fileItem.addEventListener('mouseenter', () => {
                fileItem.style.transform = 'translateY(-2px)';
                fileItem.style.boxShadow = '0 4px 12px var(--shadow)';
            });
            
            fileItem.addEventListener('mouseleave', () => {
                fileItem.style.transform = 'translateY(0)';
                fileItem.style.boxShadow = 'none';
            });
            
            filesList.appendChild(fileItem);
        });
        
        // Add event listeners to process buttons
        document.querySelectorAll('.process-file-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filePath = e.target.closest('.process-file-btn').dataset.filePath;
                processDetectedFile(filePath);
            });
        });
    }
    
    async function processDetectedFile(filePath) {
        try {
            showLoading('Processing detected file...');
            
            const response = await fetch('/api/process-detected-file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ file_path: filePath })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                hideLoading();
                showSuccess(`Successfully processed ${data.processed} transactions!`);
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 2000);
            } else {
                hideLoading();
                showError(data.error || 'Error processing file');
            }
        } catch (error) {
            hideLoading();
            showError('Error processing file: ' + error.message);
        }
    }
    
    // File input and drag & drop functionality
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    if (dropArea) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight, false);
        });
        
        // Handle dropped files
        dropArea.addEventListener('drop', handleDrop, false);
        
        // Handle click
        dropArea.addEventListener('click', () => {
            if (fileInput) fileInput.click();
        });
    }
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        if (dropArea) dropArea.classList.add('active');
    }
    
    function unhighlight() {
        if (dropArea) dropArea.classList.remove('active');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            handleFiles(files);
        }
    }
    
    function handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            handleFiles(files);
        }
    }
    
    function handleFiles(files) {
        const file = files[0];
        
        // Validate file type
        if (!file.name.toLowerCase().endsWith('.xml')) {
            showError('Please select an XML file');
            return;
        }
        
        // Validate file size (16MB limit)
        if (file.size > 16 * 1024 * 1024) {
            showError('File size must be less than 16MB');
            return;
        }
        
        selectedFile = file;
        showFilePreview(file);
    }
    
    function showFilePreview(file) {
        if (filenamePreview) filenamePreview.textContent = file.name;
        if (filesizePreview) filesizePreview.textContent = formatFileSize(file.size);
        if (fileInfo) fileInfo.textContent = `Selected: ${file.name}`;
        if (previewContainer) previewContainer.classList.remove('hidden');
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Change file button
    if (changeFileBtn) {
        changeFileBtn.addEventListener('click', () => {
            selectedFile = null;
            if (fileInput) fileInput.value = '';
            if (fileInfo) fileInfo.textContent = 'No file selected';
            if (previewContainer) previewContainer.classList.add('hidden');
            hideError();
        });
    }
    
    // Upload button
    if (uploadBtn) {
        uploadBtn.addEventListener('click', async () => {
            if (!selectedFile) {
                showError('Please select a file first');
                return;
            }
            
            await uploadFile(selectedFile);
        });
    }
    
    async function uploadFile(file) {
        try {
            showLoading('Uploading and processing file...');
            
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                hideLoading();
                showSuccess(`Successfully processed ${data.processed} transactions!`);
                
                // Reset form
                selectedFile = null;
                if (fileInput) fileInput.value = '';
                if (fileInfo) fileInfo.textContent = 'No file selected';
                if (previewContainer) previewContainer.classList.add('hidden');
                
                // Redirect to dashboard after a delay
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 2000);
            } else {
                hideLoading();
                showError(data.error || 'Error uploading file');
            }
        } catch (error) {
            hideLoading();
            showError('Error uploading file: ' + error.message);
        }
    }
    
    function showLoading(message = 'Processing...') {
        if (loadingStatus) loadingStatus.textContent = message;
        if (loadingContainer) loadingContainer.classList.remove('hidden');
        if (previewContainer) previewContainer.classList.add('hidden');
        hideError();
    }
    
    function hideLoading() {
        if (loadingContainer) loadingContainer.classList.add('hidden');
    }
    
    function showError(message) {
        if (errorText) errorText.textContent = message;
        if (errorMessage) errorMessage.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            hideError();
        }, 5000);
    }
    
    function hideError() {
        if (errorMessage) errorMessage.classList.add('hidden');
    }
    
    function showSuccess(message) {
        // Create success message element if it doesn't exist
        let successEl = document.getElementById('success-message');
        if (!successEl) {
            successEl = document.createElement('div');
            successEl.id = 'success-message';
            successEl.style.cssText = `
                background-color: var(--success);
                color: white;
                padding: 0.75rem;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 1.5rem;
                font-size: 0.9rem;
                box-shadow: 0 4px 12px var(--shadow);
            `;
            
            // Insert at the top of the container
            const container = document.querySelector('.container main') || document.querySelector('.container');
            if (container) {
                container.insertBefore(successEl, container.firstChild);
            }
        }
        
        successEl.textContent = message;
        successEl.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            successEl.style.display = 'none';
        }, 5000);
    }
});