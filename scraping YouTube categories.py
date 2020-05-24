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
    #  Setting up the API key is important cause we are going to use some services of the YouTube.
    #  So go create a YouTube Data API v3 key and write it in the file api_key.txt.
    with open(api_path, 'r') as hfile:
        apikey = hfile.readline().strip()
    # with open(ccode_path, 'r') as hfile:
    #     country_codes = [code.strip() for code in hfile]
    return apikey


def video_categories_req(apikey, ccode="GR", language='el'):
    #  This function requests all the possible categories for videos for specific region and language.
    #  Change the parameters "ccode" and "language" with them yours desired
    url = videoCategories_url + f'part=snippet&hl={language}&regionCode={ccode}&key={apikey}'
    r = requests.get(url)
    c_data = r.json()
    #  returns a dict
    return c_data


def application_language_request(apikey):
    #  Here we get all languages and their abbreviations that are applicable with the services we use
    url = appLanguages_url + f'part=snippet&key={apikey}'
    r = requests.get(url)
    l_data = r.json()
    #  returns a dict
    return l_data


def get_categories(apikey, code='GR'):
    global quotas
    # video categories snippet cost 3
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
    lang_data = application_language_request(apikey)
    languages = lang_data['items']
    print(f'Retrieved {len(languages)} languages...')
    with open('YouTube Languages.txt', 'w') as file:
        for i in range(len(languages)):
            file.write(f'{languages[i]["id"]}: {languages[i]["snippet"]["name"]}\n')


def search_request(apikey, country_code='GR', category="", pagetoken='&'):
    global quotas
    #  search snippet cost 100
    quotas += 100
    #  If you don't pass any argument in category parameter then will search YouTube for the specific region code,
    #  Otherwise searches based on the category and the region code.
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
    #  returns a dictionary with keys: "nextPageToken", "items". The value of "items"
    #  is a list of dictionaries, one per video
    return search_data


def channel_subscribers(apikey, channelid):
    global quotas
    # channel requests cost 3 quotas
    quotas += 3
    url = channel_url + f'part=statistics&id={channelid}&key={apikey}'
    r = requests.get(url)
    subscribers = r.json()['items'][0]['statistics']['subscriberCount']  # this is a single value of type string
    return subscribers


def video_request(apikey, videoid):
    global quotas
    # videos snippet, content details and statistics cost 7
    quotas += 7
    #  This part gives us the additional features that we might need to use for analysis. Features that we can't take
    #  from the search part.
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
        #  returns a dict
        return video['items'][0]
    else:
        return []


def get_features(video_list, apikey):
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
    #  returns a list of dicts. Each dict contains the desirable features for each video
    return videos


def get_pages(apikey, category):
    global quotas
    next_page_token = '&'
    videos_list = []
    with open(f'GR.csv', 'a+', encoding='utf-8', newline='') as file:
        writer = csv.writer(file, delimiter=',', quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        while (next_page_token is not None) and (quotas < 7000):
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
    get_pages(api_key, pref_category)
