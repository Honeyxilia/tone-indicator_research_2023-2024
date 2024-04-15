import re
import sys
import ipdb
import requests
import pyexcel
import auth_file_project
import ti_values


def get_ti_info_about_user(username, headers, params):
    ti_count = {
        "Total number of comments": 0,
        "Total number of comments w/ tone indicators": 0,
        "Total number of tone indicators": 0,
    }

    ti_count.update(ti_values.ti_count)

    match_ti = "/(" + "|".join(ti_values.ti_count.keys()) + ")($| )"

    output_sheet = [
        [
            "tone indicator",
            "date du message",
            "subreddit",
            "contenu du message",
            "lien vers le message"
        ],
    ]

    while True:
        request_resp = requests.get(
            f"https://oauth.reddit.com/user/{username}/comments",
            headers=headers,
            params=params,
            timeout=10
        )
        request_resp.raise_for_status()
        json_commentaires = request_resp.json()

        ti_count["Total number of comments"] += json_commentaires['data']['dist']
        next_page = json_commentaires['data']['after']

        for commentaire in json_commentaires['data']['children']:
            ti_found = re.findall(
                match_ti,
                commentaire['data']["body"]
            )
            if ti_found:
                ti_count["Total number of comments w/ tone indicators"] += 1
                for ti in ti_found:
                    ti_count["Total number of tone indicators"] += 1
                    ti_count[ti[0]] += 1

                    output_sheet.append(
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

    params.pop('after')
    output_ti = [username]
    output_ti += list(ti_count.values())

    print(output_ti)

    return output_sheet, output_ti


def main():
    # Authentication
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

    output_sheets = {
        "General statistics":
            [
                [
                    "Username",
                    "Total number of scouted comments",
                    "Number of comments w/ tone indicators",
                    "Number of tone indicators",
                ]
            ],
    }

    output_sheets["General statistics"][0] += list(ti_values.ti_count.keys())

    # Input the username
    searched_usernames = input("Please enter the users (seperated by commas) you wish to research : ")
    searched_usernames = searched_usernames.split(",")

    for username in searched_usernames:
        res = requests.get(
            f"https://oauth.reddit.com/user/{username}/about",
            headers=headers,
            params=params,
            timeout=10
        )

        if res.status_code != 200:
            print(f"User u/{username} not found...")
            continue

        print(f"user u/{username} found : collecting comments...")

        output_sheet, output_ti = get_ti_info_about_user(username, headers, params)

        output_sheets["General statistics"].append(output_ti)
        output_sheets[username] = output_sheet

        print(f"Searched tone indicators : {' '.join(ti_values.ti_count.keys())}")
        print(f"Total number of comments : {output_ti[1]}")
        print(f"Total number of comments w/ tone indicators: {output_ti[2]}")
        print(f"Total number of tone indicators: {output_ti[3]}")

        for i in range(4, len(output_ti)):
            print(f"Comments with {output_sheets['General statistics'][0][i]} : {output_sheets['General statistics'][1][i]}")

    pyexcel.Book(output_sheets).save_as("ti_stats.xlsx")


if __name__ == "__main__":
    main()
