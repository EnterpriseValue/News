import os
from bs4 import BeautifulSoup
import json
import time
import decorators
import webbrowser
import random


def startup():
    parse_news()
    summarize_folder()

# def timing_decorator(func):
#     def wrapper(*args, **kwargs):
#         start_time = time.time()
#         print('-----------------------------------------------------------------------------')
#         print(f"{func.__name__}")
#         print(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
#         result = func(*args, **kwargs)

#         print('\n')
#         end_time = time.time()
#         print(f"End Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")

#         runtime = end_time - start_time
#         print(f"Runtime: {runtime: .2f} seconds")
#         print('-----------------------------------------------------------------------------')
#         return result
#     return wrapper


def folder_locations():
    """
    This function reads the folder_location.ini file and returns the master and output directories
    """
    import configparser

    # Create a dictionary to store the folder locations
    FOLDER_LOCATIONS = {}

    # Get the directory of the source file
    SOURCEFILE_DIRECTORY = os.path.dirname(f"{__file__}")
    # print(f"Source file directory: {SOURCEFILE_DIRECTORY}")

    # Get the directory of the folder_location.ini file
    SOURCEFILE_DIRECTORY = os.path.dirname(SOURCEFILE_DIRECTORY)

    # Get the directory of the folder_location.ini file
    FOLDER_LOCATION_INI_FILE = os.path.join(SOURCEFILE_DIRECTORY, "docs/config.ini")

    # Read the folder_location.ini file
    config = configparser.ConfigParser()
    config.read(FOLDER_LOCATION_INI_FILE, encoding='UTF-8')

    # Check if the project_directory is set to None because it is the default value
    # If it is set to None, then set the project_directory to the source file directory
    if config.get('folder_location', 'project_directory') == 'None':
        FOLDER_LOCATIONS['PROJECT_DIRECTORY'] = os.path.join(SOURCEFILE_DIRECTORY)
    else:
        FOLDER_LOCATIONS['PROJECT_DIRECTORY'] = config.get('folder_location', 'project_directory')

    # Create the master and output directories - based on the user's home directory
    FOLDER_LOCATIONS['OUTPUT_DIRECTORY'] = f"{FOLDER_LOCATIONS['PROJECT_DIRECTORY']}/data/output"
    FOLDER_LOCATIONS['ARTICLE_DIRECTORY'] = f"{FOLDER_LOCATIONS['PROJECT_DIRECTORY']}/data/input/articles"
    FOLDER_LOCATIONS['OPENAI_KEY'] = config.get('passwords', 'openai_apikey')
    FOLDER_LOCATIONS['OUTPUT_SUMMARISED'] = f"{FOLDER_LOCATIONS['OUTPUT_DIRECTORY']}/summarised"

    return FOLDER_LOCATIONS


def parse_html(file_path):
    """
    Parse through an html file and extract the article text from it and save to a txt file.
    The txt file will than be put through ChatGPT.

    Return the text and the soup.

    Parameters
    ----------
    file_path : TYPE
        DESCRIPTION.

    Returns
    -------
    list
        DESCRIPTION.

    """
    with open(file_path, "r", encoding='utf-8') as file:
        # Read the contents of the file
        file_contents = file.read()

        # Parse the HTML content of the file using BeautifulSoup
        soup = BeautifulSoup(file_contents, 'html.parser')

        # Find all the <p> tags
        p_tags = soup.find_all(['p', 'title'])
        tag_list = [p.name for p in p_tags]

        # Extract the text from each <p> tag
        text_list = [p.get_text() for p in p_tags]

        paragraphs = ''
        for i in range(0, len(text_list)):
            if tag_list[i] == 'title':
                # paragraphs = f"{paragraphs}Title: {p_tags[i]}{text_list[i]}\n\n"

                paragraphs = f"{paragraphs}Title: {text_list[i]}\n\n"
                print(text_list[i])

            elif p_tags[i].attrs:  # only use if there are attributes, otherwise it's junk
                # print(f"{text}\n")

                # paragraphs = ''.join([f'{text}\n\n' for text in text_list])

                if 'id' in p_tags[i].attrs:
                    if p_tags[i].attrs['id'] == 'article-summary':
                        pass

                else:
                    paragraphs = f"{paragraphs}{text_list[i]}\n\n"

        # Add URL to the bottom of the extracted file
        url = soup.find('meta', property='og:url')['content']
        paragraphs = f"{paragraphs}URL: {url}"
        # return text_list
        return [paragraphs, soup]


@decorators.timing_decorator
def parse_news(folder_source=None):
    """
    Parse news articles in the specified folder and outputs the parsed articles
    into the 'extracted' folder

    Parameters
    ----------
    folder : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """

    import shutil
    import tqdm

    folder = folder_source
    if folder is None:
        folder = FOLDER_LOCATIONS['ARTICLE_DIRECTORY']

    print(f"Parsing news in folder: {folder}")

    if os.path.exists(folder):

        files = os.listdir(folder)
        print()
        for file in tqdm.tqdm(files):
            item_path = os.path.join(folder, file)
            if os.path.isfile(item_path):
                output_text = parse_html(f"{folder}/{file}")[0]
                # soup = parse_html(os.path.join(folder, file))[1]

                output_file_path = f"{folder}/extracted/{file}.txt"
                with open(output_file_path, "w", encoding="utf-8") as output_file:
                    output_file.write(output_text)

                # If this file is already in the deleted folder, remove it from the deleted folder as it
                # is probably an old version of the file
                deleted_folder_filepath = f"{folder}/deleted/{file}"
                print(f"parse_news: {file}")
                if os.path.exists(deleted_folder_filepath):
                    os.remove(deleted_folder_filepath)
                shutil.move(item_path, deleted_folder_filepath)

    else:
        print(f"{folder} does not exist.")


def combine_summary_folder(directory):
    """
    Combine all summaries in the summarised folder into one html webpage.
    Only do this for summaries created in the last day


    Parameters
    ----------
    directory : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    import os
    import glob
    from datetime import datetime, timedelta

    # Get the current datetime
    current_datetime = datetime.now()

    # Calculate the datetime X hours ago
    datetime_X_hours_ago = current_datetime - timedelta(hours=48)

    # Get all HTML files created since start time
    html_files = glob.glob(os.path.join(directory, '*.html'))
    html_files = [file for file in html_files if datetime.fromtimestamp(os.path.getctime(file)).date()
                  >= datetime_X_hours_ago.date()]
    html_files = sorted(html_files, key=lambda x: datetime.fromtimestamp(os.path.getctime(x)), reverse=True)

    # Combine the contents of the HTML files into a single string with separators
    combined_html = ''
    separator = '<hr>'  # Add a separator after each file
    for file in sorted(html_files, key=lambda x: datetime.fromtimestamp(os.path.getctime(x)), reverse=True):
        with open(file, 'r', encoding='utf-8') as f:
            combined_html += f.read() + separator

    # Define the output file path
    output_file = f"{FOLDER_LOCATIONS['OUTPUT_DIRECTORY']}/summary_combined.html"

    # Write the combined HTML to a new file
    with open(output_file, 'w') as f:
        f.write(combined_html)

    # Open the combined HTML file in the default web browser
    webbrowser.open(output_file)


@decorators.timing_decorator
def summarize_folder(folder_source=None):
    """
    Loop through the html files in the articles/extracted folder and run it through
    ChatGPT.

    Move the extracted file to 'done' subfolder

    Parameters
    ----------
    folder_source : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    None.

    """
    import shutil

    if folder_source is None:
        # print(os.getcwd())
        folder_source = f"{FOLDER_LOCATIONS['ARTICLE_DIRECTORY']}/extracted"
        output_folder = f"{FOLDER_LOCATIONS['OUTPUT_DIRECTORY']}/summarised"

    for file_name in os.listdir(folder_source):
        file_path = os.path.join(folder_source, file_name)
        if os.path.isfile(file_path) and file_name.endswith((".txt")):
            with open(file_path, "r", encoding="utf-8") as file:
                x = file.read()

            filename_new = file_name.split('.')[0]

            url = x.split('\n')[-1].split()[-1]
            output_file_path = os.path.join(output_folder, f"{filename_new}-summarized.html")
            summarised_text = summary_chatgpt(x)
            # print(file, x, summarised_text)
            with open(output_file_path, "w", encoding="utf-8") as file:
                file.write(summarised_text)
                file.write(f"\n\nURL: {url}")

            # If this file is already in the deleted folder, remove it from the deleted folder as it
            # is probably an old version of the file
            deleted_folder_filepath = f"{folder_source}/delete/{file_name}"
            if os.path.exists(deleted_folder_filepath):
                os.remove(deleted_folder_filepath)
            # print(file_name)
            shutil.move(file_path, f"{folder_source}/delete/{file_name}")

    combine_summary_folder(output_folder)
    cleanup()


def summary_chatgpt(text_to_summarize):
    """
    Use ChatGPT to summarize a given text

    1. Initializes an OpenAI client with an API key.
    2. Defines a system role and a user role with a prompt to summarize the text.
    3. Sends the prompt to the OpenAI chat completion model and receives a response.
    4. Extracts the summary from the response and appends metadata (word count, seed, model, tokens, and fingerprint).
    5. Returns the summary with metadata.


    Parameters
    ----------
    text_to_summarize : str
        The text to be summarized

    Returns
    -------
    str
        The summarized text in HTML format

    """

    from openai import OpenAI

    openai_apikey = FOLDER_LOCATIONS['OPENAI_KEY']
    model_choice = "gpt-4-1106-preview"
    model_choice = "gpt-4o-mini"

    client = OpenAI(api_key=openai_apikey)
    chat_bot = client.chat.completions
    system_role = {"role": "system",
                   "content": "This is a news article. Your audience is university professor with no background in this topic."}
    user_content = f"Summarize this article in 300 to 500 words using bullet points. Add subheadings for each major topic discussed. Include the article headline at the top. Use ** as a marker for subheadings. \n: {text_to_summarize}"
    user_content = f"Summarize this article in a minimum of 400 words using bullet points. Add subheadings for each major topic discussed. Include the article headline at the top. Format as an HTML page. \n: {text_to_summarize}"
    user_content = f"Summarise this article. Prefer an annotation-style response, with breakdowns of sections, insights and highlights of key points for context and understanding. Additionally, include all relevant names and quotes by key people. Format as an HTML page. \n: {text_to_summarize}"

    user_role = {"role": "user", "content": user_content}
    message_input = [system_role, user_role]
    seed = random.randint(0, 1000)
    chat_completion = chat_bot.create(model=model_choice, messages=message_input, stream=False)

    output_text = chat_completion.choices[0].message.content
    word_count = len(output_text.split())
    output_text = f"{output_text}\n <p>Word count: {word_count}"
    output_text = f"{output_text}\n <p>Seed: {seed}"
    output_text = f"{output_text}\n <p>Model: {chat_completion.model}"
    output_text = f"{output_text}\n <p>Tokens: {chat_completion.usage}"
    output_text = f"{output_text}\n <p>Fingerprint: {chat_completion.system_fingerprint}"

    print(f"Word count: {word_count}")
    return output_text


@decorators.timing_decorator
def cleanup(days_to_cleanup=7):
    """
    Delete all files in the 'deleted' subfolders

    Deletes all files in the 'output/summarised' subfolder older than a specified number of days.

    Returns
    -------
    None.

    """
    # Specify the directory to search in
    directory = FOLDER_LOCATIONS['PROJECT_DIRECTORY']

    # Iterate over all the directories and subdirectories
    for root, dirs, files in os.walk(directory):
        # Check if the current directory name is "delete"
        if os.path.basename(root) == 'delete':
            # Iterate over the files in the subfolder
            for file in files:
                # Get the full path of the file
                file_path = os.path.join(root, file)
                # Get the modification time of the file
                modification_time = os.path.getmtime(file_path)
                # Calculate the age of the file in days
                age_in_days = (time.time() - modification_time) / (24 * 60 * 60)
                # Check if the file is older than one week (7 days)
                if age_in_days > days_to_cleanup:
                    # Delete the file
                    os.remove(file_path)
    
    # This code snippet deletes files in the OUTPUT_SUMMARISED directory that are older 
    # than a specified number of days (days_to_cleanup). It does this by:
    # Walking through the directory tree rooted at OUTPUT_SUMMARISED.
    # For each file, calculating its age in days since last modification.
    # If the file is older than days_to_cleanup, deleting it.
    for root, dirs, files in os.walk(FOLDER_LOCATIONS['OUTPUT_SUMMARISED']):
        for file in files:
                file_path = os.path.join(root, file)
                modification_time = os.path.getmtime(file_path)
                age_in_days = (time.time() - modification_time) / (24 * 60 * 60)
                if age_in_days > days_to_cleanup:
                    os.remove(file_path)


def replace_bold_tags(text):
    # Loop through the text and replace ** with <b> and </b> by alternating between the two
    import re
    count = 0

    def replace(match):
        nonlocal count
        count += 1
        return '<b>' if count % 2 == 1 else '</b>'
    return re.sub(r'\*\*', replace, text)


def convert_txt_to_html(file_path):
    import markdown
    # Read the text file
    with open(file_path, 'r', encoding="utf-8") as file:
        text = file.read()

    # Convert the text to HTML
    html = text.replace('\n', '<br>')
    # Replace * with dash because it causes problems when running it through markdown
    html = html.replace('*', '-')
    html = replace_bold_tags(html)

    html = markdown.markdown(text)

    html = add_link_tags(html)

    # Save the HTML to a file
    output_file_path = file_path.replace('.txt', '.html')
    with open(output_file_path, 'w', encoding="utf-8") as file:
        file.write(html)


def add_link_tags(text):
    import re
    # Regular expression pattern to match URLs
    url_pattern = r'(https?://\S+)'

    # Find all URLs in the text
    urls = re.findall(url_pattern, text)

    # Replace each URL with an HTML anchor tag
    for url in urls:
        link_tag = f'<a href="{url}">{url}</a>'
        text = text.replace(url, link_tag)

    return text


FOLDER_LOCATIONS = folder_locations()
print(f"Current folder is {FOLDER_LOCATIONS}")