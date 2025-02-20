from bs4 import BeautifulSoup
import re
import json
from lxml import html
import random
import asyncio
from tqdm.asyncio import trange as atrange, tqdm as atqdm
from tqdm import tqdm, trange
import aiohttp
##Brightdata Proxies
host = "brd.superproxy.io"
port = 33335
username ="brd-customer-hl_5abbed84-zone-datacenter_proxy1"
password = "k54fqfrc20li"
session_id = random.random()
proxy_url=('http://{}-session-{}:{}@{}:{}'.format(username, session_id ,password,host, port))
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html",
}
def parse_definitions(html_content):
    """
    Parse dictionary definitions from HTML content, handling multiple word forms and their definitions
    
    Args:
        html_content (str): The HTML content to parse
        
    Returns:
        list: List of dictionaries containing words and their definitions
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the main definition container
    definition_div = soup.select_one('div#definition')
    if not definition_div:
        return []
    
    results = []
    
    # Find all articles
    articles = definition_div.select('article.BlocDefinition')
    
    for article in articles:
        entries = []
        
        # Find all header sections (both Zone-Entree1 and Zone-Entree)
        headers = article.select('.Zone-Entree1.header-article, .Zone-Entree.header-article')
        
        for i, header in enumerate(headers):
            # Extract all words in this header section
            word_elems = header.select('h2.AdresseDefinition')
            words = [clean_text(' '.join(elem.stripped_strings)) for elem in word_elems]
            # Join words with "ou" if there are multiple
            word = ",".join(words)
            
            # Get grammatical category
            catgram = header.select_one('p.CatgramDefinition')
            catgram_text = clean_text(' '.join(catgram.stripped_strings)) if catgram else ""
            
            # Get etymology if present
            origine = header.select_one('p.OrigineDefinition')
            origine_text = clean_text(origine.get_text(strip=True)) if origine else ""
            
            # Find the next definitions list
            definitions_section = header.find_next('ul', class_='Definitions')
            if not definitions_section or (i < len(headers) - 1 and definitions_section.find_previous('div', class_=['Zone-Entree1 header-article', 'Zone-Entree header-article']) != header):
                definitions_text = []
            else:
                divisions = definitions_section.select('li.DivisionDefinition')
                definitions_text = []
                
                for div in divisions:
                    # Get special domain indicator if present
                    rubrique = div.select_one('p.RubriqueDefinition')
                    rubrique_text = clean_text(rubrique.get_text(strip=True)) if rubrique else ""
                    
                    # Get usage indicator if present
                    indicateur = div.select_one('.indicateurDefinition')
                    indicateur_text = clean_text(indicateur.get_text(strip=True)) if indicateur else ""
                    
                    # Get definition number
                    num = div.select_one('.numDef')
                    num_text = clean_text(num.get_text(strip=True)) if num else ""
                    
                    # Get main definition text by removing unwanted elements first
                    for unwanted in div.select('.LibelleSynonyme, .Synonymes, .numDef, .RubriqueDefinition, .indicateurDefinition'):
                        unwanted.decompose()
                    def_text = clean_text(div.get_text(strip=True))
                    
                    # Get examples
                    examples = div.select('.ExempleDefinition')
                    example_texts = [clean_text(ex.get_text(strip=True)) for ex in examples]
                    
                    # Get synonyms
                    synonymes_label = div.find(class_='LibelleSynonyme')
                    synonymes = div.find('p', class_='Synonymes') if synonymes_label else None
                    synonym_text = clean_text(synonymes.get_text(strip=True)) if synonymes else ""
                    
                    # Get antonyms (contraires)
                    contraires_label = div.find(string='Contraires :')
                    contraires = contraires_label.find_next('p', class_='Synonymes') if contraires_label else None
                    contraires_text = clean_text(contraires.get_text(strip=True)) if contraires else ""
                    
                    definitions_text.append({
                        'number': num_text,
                        'domain': rubrique_text,
                        'usage': indicateur_text,
                        'text': def_text,
                        'examples': example_texts,
                        'synonyms': synonym_text if synonym_text else "",
                        'antonyms': contraires_text if contraires_text else ""
                    })
            
            entries.append({
                'word': word,
                'category': catgram_text,
                'etymology': origine_text,
                'definitions': definitions_text
            })
        
        results.extend(entries)
    
    return results


def clean_text(text):
    """
    Clean text by removing unwanted unicode characters and normalizing spaces
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove private use unicode characters (e.g., \ue82c)
    text = re.sub(r'[\ue000-\uf8ff]', '', text)
    
    # Replace non-breaking spaces (\xa0) with regular spaces
    text = text.replace('\xa0', ' ')
    
    # Normalize multiple spaces to single space
    text = ' '.join(text.split())
    
    return text.strip()



# Save to JSON file in one line
def format_and_save_json(formatted_entries, file_path):
    # Create a pretty-printed JSON string with newlines between entries
    json_str = "[\n"
    for i, entry in enumerate(formatted_entries):
        entry_str = json.dumps(entry, ensure_ascii=False)
        json_str += entry_str
        if i < len(formatted_entries) - 1:
            json_str += ","
        json_str += "\n"
    json_str += "]"
    
    # Save to file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(json_str)


def read_words_from_file(file_path, start, end):
    with open(file_path, 'r', encoding='utf-8') as file:
        pbar = end
        for _ in range(start - 1):
            file.read(1)  # Skip characters until reaching the start index
            pbar.update(1)
        content = file.read()
    words_list = content.split(',')

    return [word.strip() for word in words_list[:end - start + 1]]


def find_best_category_match(category, category_map):
    # Clean the input category
    category = clean_text(category)
    
    # First try exact match
    if category in category_map:
        return category_map[category]
    
    # If no exact match, look for partial matches
    for map_key in category_map:
        if category.startswith(map_key) or map_key in category:
            return category_map[map_key]
    
    # If no match found, return original
    return category


async def fetch_html(url: str) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, timeout=7200) as response:
                response.raise_for_status()
                html = await response.text()
                    
                return html
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""

def check_link_xpath(html_content):
    if not html_content.strip():
        return False 
    good = False
    tree = html.fromstring(html_content)
    links = tree.xpath("/html/head/link[position() = 7]")  # Directly fetch the 7th link
    
    if links:
        href = links[0].get("href", "")
        if href and href[-1].isdigit():  # Check if last character is a digit
            good = True
            return good 
        else:
            good = True
    else:
        good = False
    return good