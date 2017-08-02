import pickle
import re
import requests as req
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import json


def refresh_token():
    if credentials.access_token_expired:  # refreshes the token
        client.login()


def human_info(guest_user_id):
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


def update_local_files(max_id):
    with open("last_page_max_id/#" + tag + "_" + spreadsheet_name + "_max_id_list.txt", "wb") as fp:  # Pickling
        pickle.dump(max_id, fp)
    with open("guests_uniqueIDs/#" + tag + "_" + spreadsheet_name + ".txt", "wb") as fp:  # Pickling
        pickle.dump(unique_id_list, fp)


def spreadsheet_empty_or_notfound():
    global spreadsheet_name
    global spreadsheets_name_list
    print "Please Create a new google spreadsheet from any browser you prefer."
    print "Please Share this email with your spreadsheet with edit permisson."
    with open('client_secret.json') as data_file:
        data = json.load(data_file)
    print "The Email: ", data["client_email"]
    spreadsheet_name = raw_input("Enter the spreadsheet name: ")
    if spreadsheet_name == "":
        print "Invalid spreadsheet name."
        exit(4)
    else:
        try:
            client.open(spreadsheet_name)
        except Exception as e:
            print "Please share the email with your spreadsheet"
            exit(11)
        if spreadsheet_name not in spreadsheets_name_list:
            spreadsheets_name_list.append(spreadsheet_name)
        else:
            exit(10)
        with open("Spreadsheets_names/spreadsheets_name_list.txt", "wb") as fp:  # Pickling
            pickle.dump(spreadsheets_name_list, fp)
        print "The data will be updated to \"" + spreadsheet_name + "\" spreadsheet"
    return spreadsheet_name


def spreadsheet_mangmaent():
    global spreadsheet_name
    global spreadsheets_name_list
    try:

        with open("Spreadsheets_names/spreadsheets_name_list.txt", "rb") as fp:  # Unpickling
            spreadsheets_name_list = pickle.load(fp)
            sp_len = len(spreadsheets_name_list)

            if sp_len > 0:
                spreadsheet_name = spreadsheets_name_list[-1]
                print "The data will be updated to \"" + spreadsheet_name + "\" spreadsheet"
                ans1 = raw_input("If you want to continue press y or to use a previous one press n: ")
                if ans1 in ["n", "no", "N", "No"]:
                    print "The previous spreadsheets: ", spreadsheets_name_list
                    temp_name = raw_input(
                        "Enter the spreadsheet name or Enter another name from outside the list for a new one: ")
                    spreadsheet_name = temp_name
                    if temp_name in spreadsheets_name_list:
                        print "The data will be updated to \"" + spreadsheet_name + "\" spreadsheet"
                    else:
                        print "The spreadsheet name not found. follow these steps for a new one"
                        ans2 = raw_input("Do you want to create a new one (y/n)? ")
                        if ans2 in ["n", "no", "N", "No"]:
                            exit(7)
                        else:
                            spreadsheet_empty_or_notfound()

            else:
                return spreadsheet_empty_or_notfound()
    except IOError as e:
        print e, "and  a new one has been created for you."
        return spreadsheet_empty_or_notfound()


def hash_tag_mining():
    global unique_id_list
    try:

        max_id = Max_id_cursor
        if max_id != '':
            url = "https://www.instagram.com/explore/tags/" + tag + "/?__a=1" + "&max_id=" + str(max_id)
        else:
            url = "https://www.instagram.com/explore/tags/" + tag + "/?__a=1"

        tag_json = req.get(url).json()

        has_next_page = tag_json["tag"]["media"]["page_info"]["has_next_page"]

        update_local_files(max_id)

        while has_next_page:
            items = tag_json["tag"]["media"]["nodes"]
            items_length = len(items)
            item_num = 0
            while item_num < items_length:
                human_id = items[item_num]["owner"]["id"]
                if human_id not in unique_id_list:
                    info_json = human_info(human_id)
                    if info_json["status"] == "ok":
                        unique_id_list.append(human_id)
                        if followers_min <= followers_count(info_json) <= followers_max:
                            row = [human_id, user_name(info_json), full_name(info_json), followers_count(info_json),
                                   email_address(info_json)]
                            refresh_token()
                            sheet.append_row(row)
                        item_num += 1
                    else:
                        count = 0.0
                        print info_json["message"]
                        print "Sleep mode on"
                        while (human_info(human_id)["status"] == "fail"):
                            time.sleep(10)
                            count += 1
                        print "Sleep mode off,", "Waiting time:", (count * 10.0) / 60.0, "minute(s)"
                else:
                    item_num += 1
            update_local_files(max_id)
            new_max_id = tag_json["tag"]["media"]["page_info"]["end_cursor"]

            if new_max_id and tag_json["tag"]["media"]["page_info"]["has_next_page"]:

                if max_id == new_max_id:  # if the loading have problem
                    print "Finsished with problem in loading tags page"
                    exit(3)
                else:
                    max_id = new_max_id
                url_next_page = "https://www.instagram.com/explore/tags/" + tag + "/?__a=1" + "&max_id=" + str(max_id)
                tag_json = req.get(url_next_page).json()
            else:
                has_next_page = False
    except Exception as e:
        print e


unique_id_list = []
Max_id_cursor = ""
spreadsheet_name = ""
spreadsheets_name_list = []

print "Welcome to Hjelleset Bot"
print "The bot helps you mining for Instagram users info depends on the hashtag mining."

""" google spreadsheet scope"""

scope = ['https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
headers = gspread.httpsession.HTTPSession(headers={'Connection': 'Keep-Alive'})  # increase session timeout
client = gspread.Client(auth=credentials, http_session=headers)
client.login()

spreadsheet_mangmaent()

tag = raw_input("Please Enter your HashTag name: ")
followers_min = int(raw_input("Enter the Minumum number of followers: "))
followers_max = int(raw_input("Enter the Maximum number of followers: "))

if followers_min > followers_max or followers_min == 0 or followers_max == 0:
    print "Invalid inputs"
    exit(1)
# todo wron loading spread sheet name and
print "Mining for #" + tag + "..."
tag_lists = []
Tags_sheet = client.open(spreadsheet_name)
try:

    try:
        Tags_sheet = client.open(spreadsheet_name).worksheet("Used Tags")
    except Exception as e:
        Tags_sheet = client.open(spreadsheet_name).sheet1

    tag_lists = Tags_sheet.col_values(1)
    emptey_count = 0
    for item in tag_lists:
        if item == "":
            emptey_count += 1

    if emptey_count == 1000:
        Tags_sheet = client.open(spreadsheet_name).add_worksheet("Used Tags", 1, 1)
        Tags_sheet.insert_row(["Working tags"], 1)
        Tags_sheet.delete_row(2)

except Exception as e:
    print e  # find if the tag exist or not

if tag not in tag_lists:
    Tags_sheet.append_row([tag])
    new_sheet = client.open(spreadsheet_name).add_worksheet(tag, 1, 5)
    new_sheet.insert_row(
        ["ID", "Username", "Full Name", "Followers count",
         "Email Address"], 1)
    new_sheet.delete_row(2)
else:
    try:
        with open("guests_uniqueIDs/#" + tag + "_" + spreadsheet_name + ".txt", "rb") as fp:  # Unpickling
            unique_id_list = pickle.load(fp)
    except Exception as e:
        print e
    try:
        with open("last_page_max_id/#" + tag + "_" + spreadsheet_name + "_max_id_list.txt", "rb") as fp:  # Unpickling
            Max_id_cursor = pickle.load(fp)
    except Exception as e:
        print e

sheet = client.open(spreadsheet_name).worksheet(tag)

hash_tag_mining()

print "Successfully mining."
