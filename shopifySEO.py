from openai import OpenAI
import json, time, csv

# The file with your API credentials
creds = "creds.json"

with open(creds) as f:
    creds = json.load(f)

seo_assisant_id = creds['seo_assistant_id']
open_ai_key = creds['secret']
open_ai_org = creds['org']

# Create the Assistant Client
client = OpenAI(api_key=open_ai_key,organization=open_ai_org)


# Handles calls to assistant
def submit_message(assistant_id, thread, user_message):
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_message
    )
    return client.beta.threads.runs.create(
        thread_id = thread.id,
        assistant_id = assistant_id
    )

# Gets response
def get_response(thread):
    return client.beta.threads.messages.list(thread_id=thread.id, order="asc")

# Runs the calls to assistant
def create_thread_and_run(user_input):
    thread = client.beta.threads.create()
    run = submit_message(seo_assisant_id,thread,user_input)
    return thread, run

# Returns the response once its completed.
def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

# Opens a csv file and returns it as a python dictionary
def open_csv(path):
    with open(path, 'r', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = [row for row in reader if reader.fieldnames[0] != None]
        data = json.loads(json.dumps(data))
        return data

# Saves csv file to specified path
def save_csv(path,products,field_names):
    with open(path,'a',newline="") as f:
        writer = csv.DictWriter(f,fieldnames=field_names)
        writer.writeheader()
        writer.writerows(products)

# Path to Shopify Products Export
path = "products_export_example.csv"

# Path to save the SEO ChatGPT Results
save_path = "products_descriptions.csv"

# Field names from products export that will be used to reupload into Shopify
field_names = ['Handle','Title','Body (HTML)','SEO Title','SEO Description']

products = open_csv(path)
product_results = []

for product in products:
    thread1, run1 = create_thread_and_run(product['Title'])
    run1 = wait_on_run(run1, thread1)
    seo = get_response(thread1)

    for row in seo:
        if row.role == 'assistant':
            seo_response = row.content[0].text.value
            seo_response = json.loads(seo_response)

    # Update the CSV export with ChatGPT results
    product['Body (HTML)'] = seo_response['product_description']
    product['SEO Title'] = seo_response['meta_title']
    product['SEO Description'] = seo_response['meta_description']

    product_results.append(product)

# Save results
save_csv('seo_results.csv',product_results,field_names=field_names)
