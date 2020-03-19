import os
import glob

from urllib.request import urlopen, urlretrieve
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, url_for


app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PICTURES_FOLDER_NAME = "static"
PICTURES_FOLDER_PATH = os.path.join(BASE_DIR, PICTURES_FOLDER_NAME)
EXCLUDE_FILES = [".gitkeep"]


def save_profile_pic(handle):
    try:
        html = urlopen(f"https://twitter.com/{handle}")
    except (HTTPError, URLError):
        return False

    soup = BeautifulSoup(html, "html.parser")

    profile_pic_url = soup.find("img", {"class": "ProfileAvatar-image"}).get("src")
    if profile_pic_url:
        _, extension = os.path.splitext(profile_pic_url)
        filename = f"{handle}{extension}"
        filepath = os.path.join(PICTURES_FOLDER_PATH, filename)

        try:
            urlretrieve(profile_pic_url, filepath)
        except (HTTPError, URLError):
            return False
        return True
    return False


@app.route("/scrape/", methods=["POST"])
def process_handle():
    if request.is_json:
        data = request.get_json()
        handle = data.get("handle")

        if not handle:
            return {"error": True, "handle": ["Please provide twitter handle"]}, 400

        saved = save_profile_pic(handle)
        if not saved:
            return {
                "error": True,
                "message": "Handle not found or twitter is not available",
            }, 400
        return {
            "error": False,
            "url": url_for("get_profile_picture_detail", handle=handle),
        }

    return {"error": True, "message": "Bad request"}, 400


@app.route("/users/<handle>/profile_pic/", methods=["GET"])
def get_profile_picture_detail(handle):
    files_list = glob.glob(f"{PICTURES_FOLDER_PATH}/{handle}.*")

    if not files_list:
        return render_template("error.html", message="Ooops! Profile picture was not found")

    _, extension = os.path.splitext(files_list[0])
    picture = f"/{PICTURES_FOLDER_NAME}/{handle}{extension}"

    return render_template("profile_pic_detail.html", picture=picture, handle=handle)


@app.route("/users/", methods=["GET"])
def get_profile_picture_list():
    template = "profile_pic_list.html"
    context = {}
    try:
        os.chdir(BASE_DIR)
        pictures_dir = os.listdir(PICTURES_FOLDER_NAME)
    except FileNotFoundError as err:
        template = "error.html"
    else:
        context["pictures"] = []
        for picture in pictures_dir:

            if picture in EXCLUDE_FILES:
                continue

            context["pictures"].append({
                "pic_url": picture,
                "handle": os.path.basename(picture).split(".")[0],
            })
    return render_template(template, **context)


if __name__ == "__main__":
    if not os.path.exists(PICTURES_FOLDER_PATH):
        os.mkdir(PICTURES_FOLDER_PATH)

    app.run(host="0.0.0.0", port="8000")
