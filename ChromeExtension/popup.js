

document.addEventListener('DOMContentLoaded', () => {
    const queryList = document.getElementById('queryList');
    const clearButton = document.getElementById('clearButton');

    function loadQueries() {
        chrome.storage.local.get(['serverResponse'], (result) => {
            console.log('Loading responses in popup.js:', result);
            const serverResponse = result.serverResponse || [];
            
            queryList.innerHTML = ''; // Clear existing list

            if (!serverResponse || !serverResponse.external_response || serverResponse.external_response.result.length === 0) {
                queryList.innerHTML = '<p>No search results found</p>';
            } else {
                serverResponse.external_response.result.forEach((email) => {
                    const queryItem = document.createElement('div');
                    queryItem.classList.add('query-item');

                    queryItem.innerHTML = `
                    <div class="email-container">
                        <div class="email-header">
                            <div class="email-from">From: ${email.from}</div>
                            <div class="email-to">To: ${email.to.join(', ')}</div>
                            <span class="email-date">${new Date(email.receivedDateTime).toLocaleString()}</span>
                        </div>
                        <div class="email-subject">${email.subject}</div>
                        <div class="email-preview">${email.body.replace(/<[^>]*>?/gm, '').substring(0, 100)}...</div>
                    </div>
                `;
                

                    // Open a new tab and render the email body when the email is clicked
                    queryItem.addEventListener('click', () => {
                        openEmailBodyInNewTab(email.body);
                    });

                    queryList.appendChild(queryItem);
                });
            }
        });
    }

    function openEmailBodyInNewTab(emailBodyHTML) {
        const htmlContent = `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Email</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        padding: 20px;
                        background-color: #f9f9f9;
                    }
                    .email-body {
                        background-color: #fff;
                        padding: 20px;
                        border-radius: 5px;
                        box-shadow: 0 0 5px rgba(0,0,0,0.1);
                    }
                </style>
            </head>
            <body>
                <div class="email-body">
                    ${emailBodyHTML}
                </div>
            </body>
            </html>
        `;

        const blob = new Blob([htmlContent], { type: 'text/html' });
        const url = URL.createObjectURL(blob);

        chrome.tabs.create({ url });
    }




    // Clear all queries when the button is clicked
    clearButton.addEventListener('click', () => {
        chrome.storage.local.remove('serverResponse', () => {
            loadQueries(); // Refresh the list
        });
    });

    // Initial load of queries
    loadQueries();
});

