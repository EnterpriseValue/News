import requests
import time
import pandas as pd
import os   # for environment variables
import json
import tqdm
import decorators
import webbrowser


def folder_locations():
    folder = dict()
    folder['project_folder'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return folder


def config_file():
    """
    This function reads the folder_location.ini file and returns the master and output directories
    """
    import configparser

    # Create a dictionary to store the folder locations
    CONFIG_FILE = {}

    # Get the directory of the source file
    SOURCEFILE_DIRECTORY = os.path.dirname(f"{__file__}")
    # print(f"Source file directory: {SOURCEFILE_DIRECTORY}")

    # Get the directory of the folder_location.ini file
    SOURCEFILE_DIRECTORY = os.path.dirname(SOURCEFILE_DIRECTORY)

    # Get the directory of the folder_location.ini file
    FOLDER_LOCATION_INI_FILE = os.path.join(SOURCEFILE_DIRECTORY, ".config/config.ini")

    # Read the folder_location.ini file
    config = configparser.ConfigParser()
    config.read(FOLDER_LOCATION_INI_FILE, encoding='UTF-8')

    # Check if the project_directory is set to None because it is the default value
    # If it is set to None, then set the project_directory to the source file directory
    if config.get('folder_location', 'project_directory') == 'None':
        CONFIG_FILE['PROJECT_DIRECTORY'] = os.path.join(SOURCEFILE_DIRECTORY)
    else:
        CONFIG_FILE['PROJECT_DIRECTORY'] = config.get('folder_location', 'project_directory')

    CONFIG_FILE['API_KEY'] = config.get('password', 'api_key')

    # Create the master and output directories - based on the user's home directory
    CONFIG_FILE['OUTPUT_DIRECTORY'] = f"{CONFIG_FILE['PROJECT_DIRECTORY']}/data/output"

    return CONFIG_FILE


@decorators.timing_decorator
def NYTimesArticles():
    """
    Retrieves and processes articles from the New York Times API.

    Returns:
    None
    """
    urls = ['https://api.nytimes.com/svc/topstories/v2/home.json',
            'https://api.nytimes.com/svc/topstories/v2/business.json',
            'https://api.nytimes.com/svc/topstories/v2/politics.json',
            'https://api.nytimes.com/svc/topstories/v2/realestate.json',
            'https://api.nytimes.com/svc/topstories/v2/us.json',
            'https://api.nytimes.com/svc/topstories/v2/world.json',
            'https://api.nytimes.com/svc/topstories/v2/opinion.json',
            ]
    CONFIG_FILE = config_file()
    output_folder = CONFIG_FILE['OUTPUT_DIRECTORY']

    # config_file = json.load(open(f'{output_folder}/config.json'))
    # Set your API key
    api_key = CONFIG_FILE['API_KEY']
    print(api_key)

    # Set the parameters for the request
    params = {
        "api-key": api_key
    }

    master_results = []

    for url in tqdm.tqdm(urls):
        # Send the GET request to the API endpoint
        response = requests.get(url, params=params)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Get the JSON data from the response
            data = response.json()
            master_results.extend(data['results'])
            time.sleep(10)
        else:
            # Print an error message if the request was not successful
            print("Error: Request failed with status code", response.status_code)

    for result in master_results:
        title = result['title']
        abstract = result['abstract']
        section = result['section']
        if result['subsection'] != '':
            section = result['subsection']
        # print(f"{section}: {title} \nAbstract: {abstract}")
        # print(f"{result['url']}\n")
        # print("Abstract:", abstract)
        url = result['url']
        title_with_url = f"<a href='{url}'>{title}</a>"
        result['title'] = title_with_url


    df = pd.DataFrame(master_results).drop_duplicates(subset='url')
    df.sort_values(by='published_date', ascending=False, inplace=True)

    df['url'] = df['url'].apply(format_url)
    df = df[['section', 'subsection', 'title', 'abstract', 'published_date']]
    df = df.reset_index(drop=True)
    df.to_html(f"{output_folder}/NYTimesArticles.html", escape=False)
    # Open the generated HTML file in a web browser

    html_file_path = f"{output_folder}/NYTimesArticles.html"
    webbrowser.open(html_file_path)
    return df


def format_url(url):
    """
    This function takes a URL as an argument and returns a string that represents a clickable HTML link.
    Args:
        url (str): The URL to be formatted.

    Returns:
        str: The formatted HTML anchor tag.

    Example:
        >>> format_url('https://www.example.com')
        '<a href="https://www.example.com">https://www.example.com</a>'
    """
    return f'<a href="{url}">{url}</a>'

# if __name__ == '__main__':
#     NYTimesArticles()


# CONFIG_FILE = config_file()
# print(f"Current folder is {CONFIG_FILE}")