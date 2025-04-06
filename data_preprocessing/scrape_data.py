import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time

def get_assessment_urls(base_url):
    """
    Fetch all assessment URLs from the first page of the catalog and check for Adaptive/IRT support from all tables.
    """
    assessment_urls = []
    page = 1
    
    url = f"{base_url}"
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")  # Debug: Check if request was successful
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all tables on the page
    tables = soup.find_all('table')
    if not tables:
        print("No tables found on the page!")
        return assessment_urls
    
    print(f"Found {len(tables)} tables on the page")
    
    url_to_adaptive = {}  # Map URLs to adaptive support
    
    # Process each table
    for table_index, table in enumerate(tables, start=1):
        print(f"Processing table {table_index}...")
        rows = table.find_all('tr')
        for i, row in enumerate(rows[1:], start=1):  # Skip header row
            cells = row.find_all('td')
            if len(cells) >= 3:  # Ensure there are enough columns
                print(f"Row {i} in table {table_index} has {len(cells)} cells: {[cell.text.strip() for cell in cells]}")  # Debug
                # First cell contains the assessment name/link
                name_cell = cells[0]
                link = name_cell.find('a', href=lambda x: x and 'product-catalog/view/' in x)
                if link:
                    full_url = 'https://www.shl.com' + link['href']
                    print(f"Found URL in row {i} of table {table_index}: {full_url}")  # Debug
                    # Check Adaptive/IRT column (third cell, index 2)
                    adaptive_cell = cells[2]
                    adaptive_support = 'Yes' if adaptive_cell.find(class_='catalogue__circle -yes') else 'No'
                    print(f"Adaptive Support for {full_url}: {adaptive_support}")  # Debug
                    url_to_adaptive[full_url] = adaptive_support
                else:
                    print(f"No valid link found in row {i} of table {table_index}")
            else:
                print(f"Row {i} in table {table_index} has insufficient cells: {len(cells)}")
    
    # Step 3: Associate all extracted links with adaptive support
    links = soup.find_all('a', href=lambda x: x and 'product-catalog/view/' in x)
    if not links:
        print("No links found with 'product-catalog/view/' in href")
        return assessment_urls
    
    print(f"Found {len(links)} potential links: {[link.get('href') for link in links]}")  # Debug
    for link in links:
        full_url = 'https://www.shl.com' + link['href']
        assessment_urls.append({'url': full_url, 'adaptive_support': url_to_adaptive.get(full_url, 'N/A')})
    
    print(f"Total URLs found: {len(assessment_urls)}")
    return assessment_urls

def extract_details(url, initial_adaptive_support):
    """
    Extract assessment details from an individual page.
    Uses HTML parsing and regex for specific fields.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    # Extract name from <h1>
    name_tag = soup.find('h1')
    name = name_tag.text.strip() if name_tag else 'N/A'
    # Extract duration using regex
    duration_pattern = r'Approximate Completion Time in minutes =\s*(\d+)'
    match = re.search(duration_pattern, soup.get_text())
    duration = match.group(1) if match else 'N/A'
    # Extract test_type using regex, capturing all types (space or comma separated)
    test_type_pattern = r'Test Type:\s*([\w\s,]+)'
    match = re.search(test_type_pattern, soup.get_text())
    if match:
        raw_test_types = match.group(1).strip()
        # Split by whitespace or comma, filter out empty strings, and join with commas
        test_types = ','.join(filter(None, re.split(r'[\s,]+', raw_test_types)))
        test_type = test_types if test_types else 'N/A'
    else:
        test_type = 'N/A'
    # Determine remote_support by checking for 'remote testing'
    remote_support = 'Yes' if 'remote testing' in soup.get_text().lower() else 'No'
    
    return {
        'name': name,
        'url': url,
        'remote_support': remote_support,
        'adaptive_support': initial_adaptive_support,
        'duration': duration,
        'test_type': test_type
    }

if __name__ == "__main__":

    urls = [
        "https://www.shl.com/solutions/products/product-catalog/?start=12&type=2",
        "https://www.shl.com/solutions/products/product-catalog/?start=24&type=2&type=2",
        "https://www.shl.com/solutions/products/product-catalog/?page=24&start=36&type=2&type=2",
        "https://www.shl.com/solutions/products/product-catalog/?page=24&start=48&type=2&type=2",
        "https://www.shl.com/solutions/products/product-catalog/?page=24&start=60&type=2&type=2",
        "https://www.shl.com/solutions/products/product-catalog/?page=24&start=72&type=2&type=2",
        "https://www.shl.com/solutions/products/product-catalog/?page=24&start=84&type=2&type=2",
        "https://www.shl.com/solutions/products/product-catalog/?page=24&start=96&type=2&type=2",
        "https://www.shl.com/solutions/products/product-catalog/?page=24&start=108&type=2&type=2",
        "https://www.shl.com/solutions/products/product-catalog/?page=24&start=120&type=2&type=2",
        "https://www.shl.com/solutions/products/product-catalog/?page=24&start=132&type=2&type=2",
        "https://www.shl.com/solutions/products/product-catalog/?start=12&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=24&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=36&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=48&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=60&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=72&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=84&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=96&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=108&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=120&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=132&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=146&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=158&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=170&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=182&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=194&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=204&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=216&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=228&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=240&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=252&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=264&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=276&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=288&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=300&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=312&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=324&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=336&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=348&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=360&type=1&type=1",
        "https://www.shl.com/solutions/products/product-catalog/?start=372&type=1&type=1",
    ]

    for idx, url in enumerate(urls):
        assessment_urls = get_assessment_urls(base_url=url)

        print(f"{idx} Assessment URLs with Adaptive Support:", assessment_urls)

        data = []
        for item in assessment_urls:
            url = item['url']
            initial_adaptive_support = item['adaptive_support']
            details = extract_details(url, initial_adaptive_support)
            data.append(details)

        # Convert to DataFrame and save to CSV
        df = pd.DataFrame(data)
        df.to_csv(f'assessments{idx}.csv', index=False)
        print("Data saved to assessments.csv")
        time.sleep(5)
    
    

