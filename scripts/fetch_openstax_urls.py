"""Fetch correct OpenStax PDF URLs from their API."""
import requests
import json

r = requests.get('https://openstax.org/apps/cms/api/books/?format=json', timeout=30)
data = r.json()
books = data.get('books', [])

targets = ['algebra', 'calculus', 'statistic', 'psychology', 'physics', 'anatomy', 
           'computer', 'precalculus', 'speech', 'public speaking']

print("=== OpenStax PDF URLs ===\n")
for b in books:
    title = b.get('title', '')
    title_lower = title.lower()
    if any(t in title_lower for t in targets):
        pdf = b.get('high_resolution_pdf_url', 'NONE')
        pdf_low = b.get('low_resolution_pdf_url', '')
        print(f"Title: {title}")
        print(f"  HiRes: {pdf}")
        if pdf_low:
            print(f"  LoRes: {pdf_low}")
        print()
