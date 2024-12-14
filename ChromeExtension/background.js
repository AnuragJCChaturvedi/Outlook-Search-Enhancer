chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'OUTLOOK_SEARCH_QUERY') {
        const query = message.query;
        console.log('Received query from content.js:', query);

        // Send query to the Flask server
        fetch('http://127.0.0.1:5002/outlook-query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        })
        .then((response) => response.json())
        .then((data) => {
            console.log('Response from local server:', data);

            // Store the server response to display in popup
            chrome.storage.local.set({ serverResponse: data }, () => {
                console.log('Server response saved in storage:', data);
            });

            // Send response back to content.js
            sendResponse({ status: 'success', query, serverResponse: data });
        })
        .catch((error) => {
            console.error('Error communicating with server:', error);
            sendResponse({ status: 'error', error: error.message });
        });

        return true; // Indicate async response
    }
});

