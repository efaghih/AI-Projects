from gmail_client import DEFAULT_QUERY, fetch_primary_emails

def main():
    print(f"Query: {DEFAULT_QUERY}\n")
    emails = fetch_primary_emails(max_results=10)

    print(f"Found {len(emails)} email(s).\n")
    for i, em in enumerate(emails, start=1):
        print(f"--- {i} ---")
        print(f"From:    {em.from_addr}")
        print(f"To:      {em.to_addr}")
        print(f"Date:    {em.date}")
        print(f"Subject: {em.subject}")
        print(f"Snippet: {em.snippet[:200]}...")
        print()

if __name__ == "__main__":
    main()