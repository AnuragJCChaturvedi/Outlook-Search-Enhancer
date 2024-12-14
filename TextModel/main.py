import os
import json
import datetime
import re
from collections import Counter

from whoosh import index
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC, DATETIME
from whoosh.analysis import RegexTokenizer
from whoosh.index import create_in, open_dir
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.query import Term, Or, And, DateRange, Prefix
from whoosh.query import Wildcard
from whoosh import scoring

import spacy
from nltk.corpus import wordnet
from dateutil.parser import parse as dateutil_parse

# Constants
INDEX_DIR = "../WhooshEmailIndex"
MAIN_DATA_FILE = "cleaned_data.jsonl"

nlp = spacy.load("en_core_web_trf")

def create_schema():
    return Schema(
        docNo=NUMERIC(stored=True, unique=True),
        docID=ID(stored=True),
        sender=KEYWORD(stored=True, lowercase=True, commas=True),
        recipient=KEYWORD(stored=True, lowercase=True, commas=True),
        cc=KEYWORD(stored=True, lowercase=True, commas=True),
        date=DATETIME(stored=True),
        subject=TEXT(stored=True, analyzer=RegexTokenizer()),
        body=TEXT(stored=True, analyzer=RegexTokenizer()),
        thread_count=NUMERIC(stored=True),
        people=KEYWORD(stored=True, lowercase=True, commas=True),
        isRead=NUMERIC(stored=True),
        receivedDateTime=DATETIME(stored=True)
    )

def preprocess_text(text):
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc if not token.is_stop])

def parse_date(date_str):
    return datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S%z')

def extract_entities(subject, body):
    doc = nlp(subject + " " + body)
    return [ent.text for ent in doc.ents if ent.label_ in ["PERSON", "ORG"]]

def build_index():
    count = 0
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
    idx = create_in(INDEX_DIR, create_schema()) if not index.exists_in(INDEX_DIR) else open_dir(INDEX_DIR)
    writer = idx.writer()
    with open(MAIN_DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            count += 1
            data = json.loads(line)
            people = extract_entities(data.get('subject', ''), data.get('body', ''))
            writer.add_document(
                docNo=data['docNo'],
                docID=data['id'],
                sender=data.get('from', ''),
                recipient=",".join(data.get('to', [])),
                cc=",".join(data.get('cc', [])),
                date=parse_date(data.get('date', "2023-01-01 00:00:00+00:00")),
                subject=preprocess_text(data.get('subject', '')),
                body=preprocess_text(data.get('body', '')),
                thread_count=data.get('thread_count', 1),
                people=",".join(people),
                isRead=int(data.get('isRead', False)),
                receivedDateTime=parse_date(data.get('receivedDateTime', '2023-01-01 00:00:00+00:00'))
            )
            if count % 100 == 0:
                print("finished docs:", count, datetime.datetime.now())
    writer.commit()

def filtered_synonyms(token_text, token_pos):
    synsets = wordnet.synsets(token_text)
    synonyms = set()
    original_token = nlp(token_text)[0]
    for s in synsets:
        for lemma in s.lemmas():
            candidate = lemma.name().replace('_', ' ')
            candidate_token = nlp(candidate)
            if candidate_token and candidate_token[0].pos_ == original_token.pos_:
                if original_token.has_vector and candidate_token[0].has_vector:
                    sim = original_token.similarity(candidate_token[0])
                    if sim > 0.6:
                        synonyms.add(candidate)
    return synonyms

def expand_query_with_synonyms(keywords):
    # Expand the original keywords with relevant synonyms
    expanded_keywords = []
    for kw in keywords:
        doc = nlp(kw)
        if doc and doc[0].has_vector:
            syns = filtered_synonyms(kw, doc[0].pos_)
            expanded_terms = [kw] + list(syns)
            expanded_keywords.append("(" + " OR ".join(expanded_terms) + ")")
        else:
            # If no vector or no synonyms, just add original kw
            expanded_keywords.append(kw)
    return " OR ".join(expanded_keywords)

def detect_sender_recipient_intent(query_str, doc):
    # We rely on words like "from", "to", etc. to detect intent,
    # so we shouldn't remove them before this step.
    search_sender = any(
        phrase in query_str.lower()
        for phrase in ["received from", "sent by", "from", "authored by", "emailed by", "written by"]
    ) or any(
        token.lemma_ in ["send", "author", "email", "write"] and token.head.text.lower() in ["from", "by"]
        for token in doc
    )

    search_recipients = any(
        phrase in query_str.lower()
        for phrase in ["sent to", "to", "delivered to", "addressed to", "copied to", "sent toward"]
    ) or any(
        token.lemma_ in ["receive", "send", "address", "deliver", "copy"] and token.head.text.lower() in ["to", "toward"]
        for token in doc
    )

    return search_sender, search_recipients

def interpret_query(query_str):
    doc = nlp(query_str.lower())
    person_entities = [ent.text for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "GPE"]]

    keywords = []
    for token in doc:
        if not token.is_stop and not token.is_punct:
            keywords.append(token.lemma_)

    search_sender, search_recipients = detect_sender_recipient_intent(query_str, doc)

    date_entities = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
    start_date, end_date = None, None
    for d in date_entities:
        try:
            now=datetime.datetime.now()
            # if "today" in d:
            #     start_date = datetime.datetime(now.year, now.month, now.day)
            #     end_date = start_date + datetime.timedelta(days=1)
            # elif "yesterday" in d:
            #     end_date = datetime.datetime(now.year, now.month, now.day)
            #     start_date = end_date - datetime.timedelta(days=1)
            # elif "week" in d:
            #     end_date = now
            #     start_date = now - datetime.timedelta(days=7)
            # else:
            parsed_date = dateutil_parse(d, fuzzy=True)
            start_date = parsed_date
            end_date = parsed_date + datetime.timedelta(days=1)
        except ValueError:
            continue

    return person_entities, keywords, search_sender, search_recipients, (start_date, end_date)

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

def extract_email_addresses(query_str):
    return EMAIL_REGEX.findall(query_str)

def build_generic_query(idx, query_str, expanded=False):
    # Interpret the query first
    person_entities, keywords, search_sender, search_recipients, date_range = interpret_query(query_str)
    emails = extract_email_addresses(query_str)

    # Define filler words to remove from final search keywords
    # We keep words like "from", "to" for intent detection,
    # but now that intent is detected, we can remove them from the keywords.
    filler_words = {"show", "find", "search", "get", "give", "retrieve", "me", "emails", "email"}
    keywords = [k for k in keywords if k not in filler_words]

    subqueries = []

    # If exact emails found, query them directly
    if emails:
        email_subqueries = []
        for email in emails:
            if search_sender and not search_recipients:
                email_subqueries.append(Or([Term("sender", email), Prefix("sender", email)]))
                email_subqueries.append(Or([Term("cc", email), Prefix("cc", email)]))
            elif search_recipients and not search_sender:
                email_subqueries.append(Or([Term("recipient", email), Prefix("recipient", email)]))
                email_subqueries.append(Or([Term("cc", email), Prefix("cc", email)]))
            else:
                email_subqueries.append(Or([
                    Term("sender", email), Prefix("sender", email),
                    Term("recipient", email), Prefix("recipient", email),
                    Term("cc", email), Prefix("cc", email)
                ]))
        if email_subqueries:
            subqueries.append(Or(email_subqueries))

    # If we have person entities
    if person_entities:
        person_subqueries = []
        for p in person_entities:
            if search_sender:
                person_subqueries.append(Or([Term("sender", p), Prefix("sender", p)]))
            if search_recipients:
                person_subqueries.append(Or([Term("recipient", p), Prefix("recipient", p)]))
        if person_subqueries:
            subqueries.append(Or(person_subqueries))

    # Add keyword queries for subject/body
    if keywords:
        qp = MultifieldParser(["subject", "body"], schema=idx.schema, fieldboosts={"subject": 2.0, "body": 1.0}, group=OrGroup)

        if expanded:
            final_keyword_query = expand_query_with_synonyms(keywords)
        else:
            query_str_expanded = []
            for kw in keywords:
                query_str_expanded.append(f"({kw} OR {kw}~2)")
            final_keyword_query = " OR ".join(query_str_expanded)

        keyword_query = qp.parse(final_keyword_query)
        subqueries.append(keyword_query)

    # Date range filter if needed
    if date_range[0] is not None:
        start, end = date_range
        date_query = DateRange("date", start, end)
        subqueries.append(date_query)

    # If no subqueries formed, fallback to a simple full-text search
    if not subqueries:
        qp = MultifieldParser(["subject", "body"], schema=idx.schema, fieldboosts={"subject": 2.0, "body": 1.0}, group=OrGroup)
        fallback_query = qp.parse(query_str)
        return fallback_query

    return And(subqueries)

def query_emails(query_str, limit=20):
    # First attempt
    idx = open_dir(INDEX_DIR)
    q = build_generic_query(idx, query_str, expanded=False)
    print("Initial Query: ", q)
    with idx.searcher(weighting=scoring.BM25F()) as searcher:
        results = searcher.search(q, limit=limit)
        extracted_results = [(r['docNo'], r['sender'], r['recipient'], r['subject']) for r in results]

    # If no results, try query expansion with synonyms
    if not extracted_results:
        print("No results found. Trying query expansion...")
        q = build_generic_query(idx, query_str, expanded=True)
        print("Expanded Query: ", q)
        with idx.searcher(weighting=scoring.BM25F()) as searcher:
            results = searcher.search(q, limit=limit)
            extracted_results = [(r['docNo'], r['sender'], r['recipient'], r['subject']) for r in results]

    # If still no results, return null
    if not extracted_results:
        print("No results found after expansion.")
        return (None, None, [])

    # Reinterpret the query to get intent flags for sender/recipient logic
    # (We could store them before to avoid double call, but this is simpler)
    person_entities, keywords, search_sender, search_recipients, date_range = interpret_query(query_str)

    top_senders, top_recipients = None, None
    if search_sender:
        senders = [res[1] for res in extracted_results if res[1]]
        sender_freq = Counter(senders)
        top_senders = sender_freq.most_common(1)

    if search_recipients:
        recipients = []
        for r in extracted_results:
            if r[2]:
                recips = [rec.strip() for rec in r[2].split(',') if rec.strip()]
                recipients.extend(recips)
        recipient_freq = Counter(recipients)
        top_recipients = recipient_freq.most_common(1)

    return (top_senders[0] if top_senders else None, top_recipients[0] if top_recipients else None, [i[0] for i in extracted_results])

def main():
    # build_index()  # Uncomment if you need to build the index
    # Example Queries:
    # "Show me emails from John Doe"
    # "Find emails sent by alice.smith@example.com"
    # "Search emails to bob.jones@example.com"
    # "Get me the emails from yesterday"
    # "Show emails received last week"
    # "Find all emails regarding the project deadline"
    # "Give me the emails about the budget from last month"
    # "Retrieve emails mentioning the meeting on Friday"
    sends, recieve, results = query_emails("Show me emails from prime last week")
    
    # print("Results:", results)
    # print("Top sender:", sends)
    # print("Top recipient:", recieve)

if __name__ == "__main__":
    main()