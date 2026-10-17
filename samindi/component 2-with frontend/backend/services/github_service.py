import requests


def analyze_github(username):

    url=f"https://api.github.com/users/{username}"

    response=requests.get(url)


    if response.status_code != 200:
        return None


    data=response.json()


    return {

        "username":data.get("login"),

        "public_repositories":
        data.get("public_repos"),

        "followers":
        data.get("followers"),

        "profile_created":
        data.get("created_at"),

        "profile_url":
        data.get("html_url")
    }

    def extract_github_username(url):

    parts=url.split("/")

    return parts[-1]