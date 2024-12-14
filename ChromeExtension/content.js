
function captureSearchOnButtonClick() {
    const searchButton = document.querySelector('button[aria-label="Search"]');
    const searchInput = document.querySelector('input'); 

    if (searchButton && searchInput) {
        searchButton.addEventListener('click', () => {
            const query = searchInput.value.trim();
            console.log('Search query detected:', query);

            chrome.storage.local.clear(() => {
                console.log('Chrome local storage cleared.');
            });

            if (query && chrome.runtime && chrome.runtime.sendMessage) {
                try {
                    chrome.runtime.sendMessage({ 
                        type: 'OUTLOOK_SEARCH_QUERY', 
                        query: query 
                    }, (response) => {
                        if (chrome.runtime.lastError) {
                            console.error('Error in runtime message:', chrome.runtime.lastError.message);
                        } else if (response) {
                            console.log('Server response in content.js:', response.serverResponse);
                        } else {
                            console.warn('No response received from the background script.');
                        }
                    });
                } catch (error) {
                    console.error('Error sending message:', error);
                }
            } else {
                console.error('Chrome runtime messaging is not available');
            }
        });
    } else {
        setTimeout(captureSearchOnButtonClick, 1000); // Retry after 1 second if not found
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', captureSearchOnButtonClick);
} else {
    captureSearchOnButtonClick();
}
