# Outlook Enhanced Email Search Engine

## Project Overview

This project focuses on enhancing the search capability of Microsoft Outlook using an advanced search engine built with Python, Flask, Whoosh, and spacy for lexical and semantic understanding of the queries. The solution allows users to query their email inboxes with natural language queries like:

- "Show me emails from anc527 received last month"
- "Are there any emails from panera"
- "List emails sent to azz8"
- "Find all emails regarding project deadline"

The system also supports advanced analytics, such as identifying the top emailed recipients and most active senders.

---

## Project Structure

The project is organized into the following key folders and files:

```
.
├── GraphAPI
│   ├── graph.py       # Handles interaction with Microsoft Graph API to retrieve emails
│   └── main.py        # Handles cleaning and preprocessing of email data
│
├── TextModel
│   └── main.py        # Handles email indexing and search using Whoosh
│   └── server.py      # Runs the search engine server
│
├── API
│   └── server.py      # Runs the Flask API server to receive search queries from Chrome extension
│
├── Chrome Extension
│   ├── manifest.json  # Chrome extension configuration
│   └── background.js  # Handles query forwarding to the local Flask API server
│
└── README.md          # Documentation for the project
```

---

## Key Features

1. **Natural Language Query Support**

   - Query examples: "Find emails from John received in the last week", "Show emails sent to Alice", "Emails about the project deadline."

2. **Advanced Query Expansion**

   - Uses NLP to detect sender/recipient intent.
   - Expands search terms with synonyms using WordNet and SpaCy.

3. **Email Indexing**

   - Emails are indexed using Whoosh to enable fast, full-text search.

4. **Analytics and Insights**

   - Identify the most frequently emailed recipients and most active senders.

5. **Seamless Integration with Chrome**

   - A Chrome extension captures search queries from Outlook and sends them to the local server.

6. **Flask API for Search Requests**

   - A lightweight Flask server processes incoming search queries and returns the results.

7. **Usage of SpaCy**

    - Named Entity Recognition (NER): Identifies names of people, organizations, and dates in email subjects and bodies.

    - Lemmatization: Processes words to their base forms to improve search relevance.

    - POS Tagging: Assists in intent detection for sender/recipient-based queries.

---

## Setup Instructions

### Prerequisites

1. **Python 3.8+**
2. **Pipenv or Virtualenv** (Optional but recommended)
3. **Google Chrome** (For Chrome extension usage)
4. **Flask** for API and server management
5. **Whoosh** for indexing and searching email content
6. **Microsoft Graph API** credentials

### Installation Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-repo-name.git
   cd your-repo-name
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Microsoft Graph API**

   - Create an Azure app registration and obtain `clientId`, `tenantId`, and `graphUserScopes`.
   - Add these details to `config.cfg` inside the `GraphAPI` folder.

4. **Run the servers**

   - **Start GraphAPI server**:
     ```bash
     python GraphAPI/main.py
     ```
   - **Start TextModel search engine server**:
     ```bash
     python TextModel/server.py
     ```
   - **Start API server**:
     ```bash
     python API/server.py
     ```

5. **Load Chrome extension**

   - Open Chrome and navigate to `chrome://extensions/`.
   - Enable **Developer Mode**.
   - Click **Load unpacked** and select the `Chrome Extension` folder.

---

## Usage

1. Open **Outlook Web** and navigate to the search bar.
2. Type a search query like **"List emails sent to John in the last week"**.
3. The query is captured by the Chrome extension and forwarded to the local Flask API.
4. The API forwards the query to the Whoosh-based search engine.
5. Results are displayed directly in the extension's popup.

---

## Detailed Component Overview

### 1. **GraphAPI**

This module connects to the Microsoft Graph API to pull email data and store it as JSON lines for further processing.

- **File**: `GraphAPI/graph.py`
- **Key Functions**:
  - `get_inbox()` - Retrieves email messages from the inbox.
  - `get_deleted_items()` - Retrieves deleted items from the mailbox.

---

### 2. **TextModel**

This module handles **email indexing** and **query processing** using Whoosh.

- **File**: `TextModel/main.py`
- **Key Functions**:
  - `build_index()` - Builds the Whoosh index from email JSON data.
  - `query_emails()` - Handles natural language query interpretation and builds Whoosh-compatible queries.

---

### 3. **API**

This is the Flask server responsible for processing search queries from the Chrome extension and forwarding them to the TextModel search server.

- **File**: `API/server.py`
- **Key Endpoint**: `/outlook-query` - Receives search queries and returns search results.

---

### 4. **Chrome Extension**

This extension enables capturing search queries directly from Outlook's search bar and sends them to the API server.

- **File**: `Chrome Extension/background.js`
- **Key Event**: Listens for incoming search queries and forwards them to the API server.

---

## Example Queries

Here are some queries that can be used with this search engine:

- **Simple Queries**:
  - "Show me emails from anc527 received last month"
  - "Are there any emails from Panera?"
- **Date-Specific Queries**:
  - "List all emails sent last week"
  - "Find emails from December 2023"
- **Intent-Based Queries**:
  - "List emails sent to azz8"
  - "Find all emails about project deadlines"

---

## Troubleshooting

| Issue                        | Cause                | Solution                                                     |
| ---------------------------- | -------------------- | ------------------------------------------------------------ |
| No search results            | Index not built      | Run `build_index()` in `TextModel/main.py`                   |
| Chrome extension not working | Extension not loaded | Reload the Chrome extension from the **Extensions** page     |
| API server errors            | Port conflict        | Check if port 5002 is in use or change it in `API/server.py` |

---

## Contributing

1. **Fork** the repository.
2. **Create a feature branch**.
3. **Make your changes**.
4. **Submit a pull request**.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

## Contact

For any inquiries or issues, please open a GitHub issue or reach out to the project maintainers.
