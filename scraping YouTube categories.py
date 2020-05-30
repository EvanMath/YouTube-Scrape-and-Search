import requests
from collections import OrderedDict
import csv

videoCategories_url = 'https://www.googleapis.com/youtube/v3/videoCategories?'
appLanguages_url = 'https://www.googleapis.com/youtube/v3/i18nLanguages?'
search_url = 'https://www.googleapis.com/youtube/v3/search?'
video_url = 'https://www.googleapis.com/youtube/v3/videos?'
channel_url = 'https://www.googleapis.com/youtube/v3/channels?'
headers = ['video_id', 'channel_Id', 'title', 'channel_title', 'tags', 'duration', 'views',
           'likes', 'dislikes', 'comments', 'subscribers']
quotas = 0


def setup(api_path):
    """
    Setting up the API key is important cause we are going to use services of the YouTube.
    Create a YouTube Data API v3 key and write it in the file api_key.txt.

    api_path: In case the file api_key.txt is in another folder
    return: a string
    """
    with open(api_path, 'r') as hfile:
        apikey = hfile.readline().strip()
    # with open(ccode_path, 'r') as hfile:
    #     country_codes = [code.strip() for code in hfile]
    return apikey


def video_categories_req(apikey, country_code="GR", language='el'):
    """
    This function requests all the possible categories for videos for specific region and language.
    Change the parameters "country_code" and "language" with them yours desired.

    apikey: User's YouTube Data API v3 key
    country_code: User's preferred country code (ISO 3166-1 alpha-2 country code)
    language: Users preferred language
    return: a dictionary of categories
    """
    url = videoCategories_url + f'part=snippet&hl={language}&regionCode={country_code}&key={apikey}'
    r = requests.get(url)
    c_data = r.json()
    return c_data


def application_language_request(apikey):
    """
    Here we get all languages and their abbreviations that are applicable with the services we use.

    apikey: User's YouTube Data API v3 key
    return: a dictionary of languages
    """
    url = appLanguages_url + f'part=snippet&key={apikey}'
    r = requests.get(url)
    l_data = r.json()
    return l_data


def get_categories(apikey, code='GR'):
    """
    Creates a file that holds videos categories
    - Video categories snippet cost 3

    apikey: User's YouTube Data API v3 key
    code: User's country code
    """
    global quotas

    quotas += 3
    print(f"Video categories for region code:{code}...")
    c_data = video_categories_req(apikey, code)
    items = c_data['items']
    categories_dict = {}
    for i in range(len(items)):
        key = items[i]['id']
        value = items[i]['snippet']['title']
        categories_dict[key] = value
    with open(f'{code}_YouTube_Cat.csv', 'w') as file:
        for video_id, cat in categories_dict.items():
            file.write(f'{video_id}: {cat}\n')


def get_languages(apikey):
    """
    Creates a file that holds languages we can use in YouTube services

    apikey: User's YouTube Data API v3 key
    """
    lang_data = application_language_request(apikey)
    languages = lang_data['items']
    print(f'Retrieved {len(languages)} languages...')
    with open('YouTube Languages.txt', 'w') as file:
        for i in range(len(languages)):
            file.write(f'{languages[i]["id"]}: {languages[i]["snippet"]["name"]}\n')


def search_request(apikey, country_code='GR', category="", pagetoken='&'):
    """
    Request for searching the YouTube. If you don't pass any argument in category parameter it will search
    YouTube for the specific region code. Otherwise searches based on the category and the region code.
    - Search snippet cost 100


    apikey: User's YouTube Data API v3 key
    country_code: User's country code
    category: User's preferred category to search and scrape
    pagetoken: Token to be used to go through the resulting pages
    return: a dictionary with keys: "nextPageToken", "items". The value of "items" is a list of dictionaries,
    one per video
    """
    global quotas

    quotas += 100

    if category == "":
        url = search_url + f'fields=nextPageToken,items(id(videoId),snippet(channelId,title,channelTitle))' \
                           f'&maxResults=50&part=snippet&pageToken={pagetoken}regionCode={country_code}' \
                           f'&type=video&key={apikey}'
    else:
        url = search_url + f'fields=nextPageToken,items(id(videoId),snippet(channelId,title,channelTitle))' \
                           f'&maxResults=50&part=snippet&pageToken={pagetoken}regionCode={country_code}' \
                           f'&type=video&videoCategoryId={category}&key={apikey}'
    r = requests.get(url)
    search_data = r.json()

    return search_data


def channel_subscribers(apikey, channelid):
    """
    A helper function to retrieve the number of subscribers for each channel.
    - Channel requests cost 3 quotas

    apikey: User's YouTube Data API v3 key
    channelid: Channel Id in YouTube. We get it from get_features()
    return: string, the number of subscribers
    """
    global quotas

    quotas += 3
    url = channel_url + f'part=statistics&id={channelid}&key={apikey}'
    r = requests.get(url)
    subscribers = r.json()['items'][0]['statistics']['subscriberCount']  # this is a single value of type string
    return subscribers


def video_request(apikey, videoid):
    """
    A helper function that retrieves additional features that we might need to use for analysis.
    Features that we can't take from the search part.
    - Video's snippet, content details and statistics cost 7

    apikey: User's YouTube Data API v3 key
    videoid: Video Id. We get it from get_features()
    return: a dictionary or an empty list
    """
    global quotas

    quotas += 7

    url = video_url + f'part=snippet,contentDetails,statistics&id={videoid}' \
                      f'&fields=items(snippet(tags),contentDetails(duration),statistics)&key={apikey}'
    r = requests.get(url)
    video = r.json()
    #  video = {
    #  "items": [
    #  {"snippet": {tags:[tags]},
    #  "contentDetails":{"duration": string},
    #  "statistics":{"views":string,"likes": string, "dislikes": string, "favorite": string, "comments":string}}
    #  ]
    #  }
    if 'items' in video.keys():
        return video['items'][0]
    else:
        return []


def get_features(video_list, apikey):
    """
    Helper function to extract features for each video.

    video_list: List with features of each video
    apikey: User's YouTube Data API v3 key
    return: a list of dicts. Each dict contains the desirable features for each video
    """
    videos = []
    for item in video_list:
        features = OrderedDict()
        features['video_id'] = item['id'].get('videoId', None)
        features['channel_Id'] = item['snippet'].get('channelId', None)
        features['title'] = item['snippet'].get('title', None)
        features['channel_Title'] = item['snippet'].get('channelTitle', None)

        video_info = video_request(apikey, features['video_id'])
        if "statistics" not in video_info.keys():
            print(f"Video with ID:{features['video_id']} is not valid!")
            continue
        try:
            features['tags'] = video_info['snippet'].get('tags', None)
        except KeyError:
            features['tags'] = None
        try:
            features['duration'] = video_info['contentDetails'].get('duration', None)
        except KeyError:
            features['duration'] = None
        try:
            features['views'] = video_info['statistics'].get('viewCount', None)
            features['likes'] = video_info['statistics'].get('likeCount', None)
            features['dislikes'] = video_info['statistics'].get('dislikeCount', None)
            features['comments'] = video_info['statistics'].get('commentCount', None)
        except KeyError:
            features['views'] = None
            features['likes'] = None
            features['dislikes'] = None
            features['comments'] = None
        subscribers = channel_subscribers(apikey, features['channel_Id'])
        features['subscribers'] = subscribers
        videos.append(features)

    return videos


def get_pages(apikey, category):
    """


    apikey: User's YouTube Data API v3 key
    category: User's category of choice
    return: Creates a csv file for our analysis
    """
    global quotas
    next_page_token = '&'
    videos_list = []
    with open(f'GR.csv', 'a+', encoding='utf-8', newline='') as file:
        writer = csv.writer(file, delimiter=',', quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        while (next_page_token is not None) and (quotas < 9000):
            videos_dict = search_request(apikey, 'GR', category, next_page_token)  # this is a dict
            if 'items' in videos_dict.keys():
                videos = get_features(videos_dict['items'], apikey)  # this is a list of dicts represent videos
                if len(videos) < 1:
                    break
                for features in videos:  # features is a dict
                    temp_seq = []
                    for key, value in features.items():
                        temp_seq.append(value)
                    writer.writerow(temp_seq)
                print(f"{len(videos)} new videos added...")
            else:
                print(videos_dict)
                break
            videos_list += videos
            if 'nextPageToken' in videos_dict.keys():
                next_page_token = videos_dict['nextPageToken'] + '&'
            else:
                print('No page token...')
                break
            print(f"You have request {quotas} queries")
    print(f'Videos collected {len(videos_list)}')


if __name__ == '__main__':
    api_key = setup('api_key.txt')
    get_languages(api_key)
    get_categories(api_key)
    with open("GR_YouTube_Cat.csv", 'r') as file:
        for line in file.readlines():
            print(line.strip())
    pref_category = input('Choose one of the above categories or press "Enter" to continue... ')
    # print('Go to "YouTube Languages.txt" and choose your desired language')
    # pref_lang = input('Enter language: ')
    get_pages(api_key, pref_category)
