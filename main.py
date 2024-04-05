import requests
import sys
import init_headers
import re
import auth_file_project


def main():
    global json_commentaires
    fin_atteinte = False
    nb_commentaires = 0
    nb_commentaires_w_ti = 0

    base_url = "https://www.reddit.com/"
    auth = auth_file_project.auth
    data = auth_file_project.data

    headers = {'User-Agent': 'M2_tone-indicators_research/1.0'}

    params = {
        'limit': "100"
    }

    res = requests.post(
        base_url + "api/v1/access_token",
        auth=auth,
        data=data,
        headers=headers
    )

    res.raise_for_status()

    TOKEN = res.json()['access_token']
    headers = {**headers, **{'Authorization': f"bearer {TOKEN}"}}

    # Input the username
    username = input("Please enter the user you wish to research : ")
    res = requests.get(f"https://oauth.reddit.com/user/{username}/about",
                       headers=headers,
                       params=params
                       )

    while res.status_code != 200:
        print("ERROR : Invalid username")
        username = input("Please enter the user you wish to research : ")
        res = requests.get(f"https://oauth.reddit.com/user/{username}/about",
                           headers=headers,
                           params=params
                           )

    print(f"user u/{username} found : collecting comments...")

    ti_count = {
        'genq': 0,
        'gen': 0,
        'nm': 0,
        'srs': 0,
        's': 0,
        'j': 0,
        'hj': 0,
        'lh': 0,
        'pos': 0,
        'neg': 0,
    }
    match_ti = "/(" + "|".join(ti_count.keys()) + ")($| )"

    while True:
        request_resp = requests.get(
            f"https://oauth.reddit.com/user/{username}/comments",
            headers=headers,
            params=params
        )
        request_resp.raise_for_status()
        json_commentaires = request_resp.json()

        nb_commentaires += json_commentaires['data']['dist']
        next_page = json_commentaires['data']['after']

        for commentaire in json_commentaires['data']['children']:
            ti_found = re.findall(
                match_ti,
                commentaire['data']["body"]
            )
            if ti_found:
                nb_commentaires_w_ti += 1
                for ti in ti_found:
                    ti_count[ti[0]] += 1

        if next_page is None:
            break
        else:
            params['after'] = next_page

    print(f"Searched tone indicators : {' '.join(ti_count.keys())}")
    print(f"Total number of comments : {nb_commentaires}")
#    print(f"Total number of comments w/ tone indicators: {nb_commentaires_w_ti}")
    for ti in ti_count.keys():
        print(f"Comments with /{ti} : {ti_count[ti]}")


if __name__ == "__main__":
    main()
