import re
import requests as req
import gspread
from oauth2client.service_account import ServiceAccountCredentials

print "Welcome to Hjelleset Bot"
tag = raw_input("Please Enter your HashTag name: ")

""" google spreadsheet """

scope = ['https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(credentials)
google_sheet_name = "hjelleset_mining"
Tags_sheet = client.open(google_sheet_name).sheet1
tag_lists = Tags_sheet.col_values(1)

if tag not in tag_lists:
    Tags_sheet.append_row([tag])
    new_sheet = client.open(google_sheet_name).add_worksheet(tag, 1, 6)
    new_sheet.insert_row(
        ["ID", "Username", "Full Name", "Follower count",
         "Email Address", "LastMaxID"], 1)
    new_sheet.delete_row(2)

sheet = client.open(google_sheet_name).worksheet(tag)

headers = gspread.httpsession.HTTPSession(headers={'Connection': 'Keep-Alive'})  # increase session timeout
gc = gspread.Client(auth=credentials, http_session=headers)
gc.login()

unique_ids = []
unique_ids = sheet.col_values(1)
""" google spreadsheet """


def human_info(guest_user_id):
    full_url = "https://i.instagram.com/api/v1/users/" + guest_user_id + "/info/"
    return req.get(full_url).json()


def followers_count(human_info_json):
    return human_info_json["user"]["follower_count"]


def email_address(human_info_json):
    bio = human_info_json["user"]["biography"]
    match = re.findall(r'[\w\.-]+@[\w\.-]+', bio)
    if not match:
        match = "Null"
    return match


def full_name(human_info_json):
    return human_info_json["user"]["full_name"]


def user_name(human_info_json):
    return human_info_json["user"]["username"]


def hash_tag_mining():
    max_id = ''
    url = "https://www.instagram.com/explore/tags/" + tag + "/?__a=1"

    tag_json = req.get(url).json()

    has_next_page = tag_json["tag"]["media"]["page_info"]["has_next_page"]

    while has_next_page:

        for item in tag_json["tag"]["media"]["nodes"]:

            human_id = item["owner"]["id"]

            if human_id not in unique_ids:

                info_json = human_info(human_id)

                if info_json["status"] == "ok":

                    unique_ids.append(human_id)
                    if 1000 <= followers_count(info_json) <= 50000:
                        row = [human_id, user_name(info_json), full_name(info_json), followers_count(info_json),
                               email_address(info_json), max_id]
                        sheet.append_row(row)
                        max_id = ''
                else:
                    break

        if tag_json["tag"]["media"]["count"] > 15 and tag_json["tag"]["media"]["page_info"]["has_next_page"]:
            max_id = tag_json["tag"]["media"]["page_info"]["end_cursor"]
            url_next_page = "https://www.instagram.com/explore/tags/" + tag + "/?__a=1" + "&max_id=" + str(max_id)
            tag_json = req.get(url_next_page).json()

        else:
            has_next_page = False


hash_tag_mining()
