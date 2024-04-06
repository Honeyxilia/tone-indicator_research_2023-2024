import re
import requests
import pyexcel
import auth_file_project


def main():
    nb_commentaires = 0
    nb_commentaires_w_ti = 0

    base_url = "https://www.reddit.com/"

    headers = {'User-Agent': 'M2_tone-indicators_research/1.0'}

    params = {
        'limit': "100"
    }

    res = requests.post(
        base_url + "api/v1/access_token",
        auth=auth_file_project.auth,
        data=auth_file_project.data,
        headers=headers,
        timeout=10
    )

    res.raise_for_status()

    token = res.json()['access_token']
    headers = {**headers, **{'Authorization': f"bearer {token}"}}

    # Input the username
    username = input("Please enter the user you wish to research : ")
    res = requests.get(
        f"https://oauth.reddit.com/user/{username}/about",
        headers=headers,
        params=params,
        timeout=10
    )

    while res.status_code != 200:
        print("ERROR : Invalid username")
        username = input("Please enter the user you wish to research : ")
        res = requests.get(
            f"https://oauth.reddit.com/user/{username}/about",
            headers=headers,
            params=params,
            timeout=10
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

    output_sheets = {
        'General stats': [],
        'Individual comments': [
            [
                "tone indicator",
                "date du message",
                "subreddit",
                "contenu du message",
                "lien vers le message"
            ],
        ],
    }

    while True:
        request_resp = requests.get(
            f"https://oauth.reddit.com/user/{username}/comments",
            headers=headers,
            params=params,
            timeout=10
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

                    output_sheets['Individual comments'].append(
                        [
                            ti[0],
                            commentaire['data']['created_utc'],
                            commentaire['data']['subreddit_name_prefixed'],
                            commentaire['data']['body'],
                            commentaire['data']['link_permalink'],
                        ]
                    )

        if next_page is None:
            break
        params['after'] = next_page

    print(f"Searched tone indicators : {' '.join(ti_count.keys())}")
    print(f"Total number of comments : {nb_commentaires}")
    print(f"Total number of comments w/ tone indicators: {nb_commentaires_w_ti}")

    output_sheets['General stats'] = [
        ["Total number of comments", nb_commentaires],
        ["Total number of comments w/ tone indicators", nb_commentaires_w_ti],
        ["Total number of tone indicators", len(output_sheets['Individual comments']) - 1],
    ]

    for ti in ti_count.items():
        print(f"Comments with /{ti} : {ti_count[ti]}")
        output_sheets['General stats'].append(
            [ti, ti_count[ti]]
        )

    output = pyexcel.Book(output_sheets)
    output.save_as(f"{username}_ti_stats.xls")


if __name__ == "__main__":
    main()
