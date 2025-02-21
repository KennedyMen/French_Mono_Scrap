import argparse 
import random
import asyncio
import time
from tqdm.asyncio import trange as atrange, tqdm as atqdm
from tqdm.contrib.concurrent import process_map
from tqdm import tqdm 
from Functions.Roussesearch import parse_definitions ,clean_text,format_and_save_json,read_words_from_file,find_best_category_match, fetch_html, check_link_xpath
import logging
import os 
from dotenv import load_dotenv
logging.getLogger("asyncio").setLevel(logging.ERROR)
def configure():
    load_dotenv()
configure()
# Define proxies to use.
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html",
}
##Brightdata Proxies
host = os.getenv('host')
port = os.getenv('port')
username =os.getenv('username')
password = os.getenv('password')
session_id = random.random()
proxy_url=('http://{}-session-{}:{}@{}:{}'.format(username, session_id ,password,host, port))
category_map = {
    "adjectif": "adj",
    "adverbe": "adv",
    "article défini": "art def",
    "adjectif numéral cardinal": "adj num card",
    "nom masculin invariable": "n masc invar",
    "nom masculin": "n masc invar",
    "nom féminin": "n fém",
    "pronom personnel": "pn pers",
    "adverbe exclamatif": "adv excl",
    "conjonction de coordination": "conj",
    "préposition": "prép",
    "interjection": "interj",
    "nom": "n",
    "pronom": "pn",
    "verbe": "v"
}
# Argument parser
parser = argparse.ArgumentParser(description="Fetch and format dictionary definitions.")
parser.add_argument("textfilepath", type=str, help="Path to the words file")
parser.add_argument("start", type=int, help="Starting index for words")
parser.add_argument("end", type=int, help="Ending index for words")
parser.add_argument("out_file_path", type=str, help="Path to save the dictionary JSON")
args = parser.parse_args()
####VARIABLES
words = read_words_from_file(args.textfilepath, args.start, args.end)
valid_html=[]
formatted_entries = []
out_file_path = args.out_file_path
start = time.time()
async def check_words():
    limiter=0
    tasks = []
    async with asyncio.TaskGroup() as tg:
        # Create and STORE the tasks
        Semaphore = asyncio.Semaphore(100)
        for word in words:
            url = "https://www.larousse.fr/dictionnaires/francais/" + word.lower()
            tasks.append(tg.create_task(fetch_html(url,Semaphore,word)))
        for done in atqdm.as_completed(tasks,desc="downloading HTML"):
                limiter += 1
                await done
                if limiter == 900:
                     time.sleep(75)
                     limiter =0


    # After TaskGroup cpletes, get results
    html_content = [task.result() for task in tasks]
    
    for data in tqdm(html_content,desc="checking"):
        good = check_link_xpath(data)
        if good:
            valid_html.append(data)
def request_definitions(valid_data):
        definitions = parse_definitions(valid_data)
        return definitions
    
    # Get results after all tasks complete
def final_output(entry):
    word = entry["word"]

    # Skip if word already exists (to avoid duplicates)

    category = entry["category"]
    category_short = find_best_category_match(category, category_map)
    definitions = []

    for definition in entry["definitions"]:
        def_text = definition["text"]
        if def_text:
            definitions.append(f"{category_short}, {def_text}")

    formatted_entry = [word, "", "", "", 0, definitions, 0, ""]
    return formatted_entry

if __name__ == "__main__":
    asyncio.run(check_words(),debug=True)
    parsed_data = process_map(request_definitions,valid_html , max_workers=10, desc="parsing data")
    # Flatten the nested lists of dictionaries
    new_entries = [item for sublist in parsed_data for item in sublist]  # Flatten list of lists
    formatted_entries = process_map(final_output, new_entries, max_workers=10, desc="appending JSON")
    end = time.time()    
    total_time = end - start
    print (total_time)
    format_and_save_json(formatted_entries, out_file_path)
    print(f"JSON file saved as {out_file_path} with newlines between entries.")
    print("JSON file saved as dictionary.json in one line.")