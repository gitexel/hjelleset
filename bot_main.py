import pickle
import re
import requests as req
import gspread
from oauth2client.service_account import ServiceAccountCredentials

print "Welcome to Hjelleset Bot"
tag = raw_input("Please Enter your HashTag name: ")
print "Please Wait..."
unique_id_list = []

""" google spreadsheet """

scope = ['https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
headers = gspread.httpsession.HTTPSession(headers={'Connection': 'Keep-Alive'})  # increase session timeout
client = gspread.Client(auth=credentials, http_session=headers)
client.login()

google_sheet_name = "hjelleset_mining"
Tags_sheet = client.open(google_sheet_name).sheet1
tag_lists = Tags_sheet.col_values(1)

if tag not in tag_lists:
    Tags_sheet.append_row([tag])
    new_sheet = client.open(google_sheet_name).add_worksheet(tag, 1, 6)
    new_sheet.insert_row(
        ["ID", "Username", "Full Name", "Followers count",
         "Email Address", "LastMaxID"], 1)
    new_sheet.delete_row(2)
else:
    """Local files - unique ids """
    try:
        with open("guests_uniqueIDs/" + tag + ".txt", "rb") as fp:  # Unpickling
            unique_id_list = pickle.load(fp)
    except e:
        print e

sheet = client.open(google_sheet_name).worksheet(tag)


def human_info(guest_user_id):
    if credentials.access_token_expired:  # refreshes the token
        client.login()
    full_url = "https://i.instagram.com/api/v1/users/" + guest_user_id + "/info/"
    return req.get(full_url).json()


def followers_count(human_info_json):
    return human_info_json["user"]["follower_count"]


def email_address(human_info_json):
    bio = human_info_json["user"]["biography"]
    match = re.findall(r'[\w\.-]+@[\w\.-]+', bio)
    if not match:
        return "Null"
    return match[0]


def full_name(human_info_json):
    return human_info_json["user"]["full_name"]


def user_name(human_info_json):
    return human_info_json["user"]["username"]


def hash_tag_mining():

    try:

        max_id = ''
        url = "https://www.instagram.com/explore/tags/" + tag + "/?__a=1"

        tag_json = req.get(url).json()

        has_next_page = tag_json["tag"]["media"]["page_info"]["has_next_page"]

        while has_next_page:

            for item in tag_json["tag"]["media"]["nodes"]:

                human_id = item["owner"]["id"]

                if human_id not in unique_id_list:

                    info_json = human_info(human_id)

                    if info_json["status"] == "ok":

                        unique_id_list.append(human_id)
                        if 1000 <= followers_count(info_json) <= 50000:
                            row = [human_id, user_name(info_json), full_name(info_json), followers_count(info_json),
                                   email_address(info_json), max_id]
                            if credentials.access_token_expired:  # refreshes the token
                                client.login()
                            sheet.append_row(row)
                            max_id = ''
                    else:
                        print info_json["status"], "requsts"
                        break

            if tag_json["tag"]["media"]["count"] > 15 and tag_json["tag"]["media"]["page_info"]["has_next_page"]:
                if credentials.access_token_expired:  # refreshes the token
                    client.login()
                max_id = tag_json["tag"]["media"]["page_info"]["end_cursor"]
                url_next_page = "https://www.instagram.com/explore/tags/" + tag + "/?__a=1" + "&max_id=" + str(max_id)
                tag_json = req.get(url_next_page).json()

            else:
                has_next_page = False

    except Exception as e:
        print(e)


hash_tag_mining()

with open("guests_uniqueIDs/" + tag + ".txt", "wb") as fp:  # Pickling
    pickle.dump(unique_id_list, fp)
