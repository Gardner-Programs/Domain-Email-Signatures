from unicodedata import name
from google.oauth2 import service_account
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import json

#creating the credentials to contact the admin sdk api for google
def create_directory_service():
    service_account_json_file_path = 'the json keyfile path goes here'
	credentials = ServiceAccountCredentials.from_json_keyfile_name(
        service_account_json_file_path,
        #scopes needed to access the api
        scopes=['https://www.googleapis.com/auth/admin.directory.user'])
    credz = credentials.create_delegated("the email address of the person authorized to make the changes goes here")
    return build('admin', 'directory_v1', credentials=credz)

#creating the credentials to contact the gmail api for google
def setup_credentials_gmail():
    key_path = 'path to client secret json file goes here'
    #scopes needed to access the api
    API_scopes =['https://www.googleapis.com/auth/gmail.settings.basic',
                 'https://www.googleapis.com/auth/gmail.settings.sharing',
                 'https://www.googleapis.com/auth/admin.directory.user']
    credentials = service_account.Credentials.from_service_account_file(key_path,scopes=API_scopes)
    return credentials

#creates json files for each user in the domain with all of the information from their user information on the admin page
def make_jsons():
    files = []
    first_page = {}
    aditional_pages = {}
    #creating the varible that calls the api with the creditials listed above
    service = create_directory_service()
    #the admin sdk only lets you get 500 users at a time, it makes the last item in the jason file a next page token that you then have to use to get the next 500 users
    result = service.users().list(domain='domain name goes here', maxResults = 500, orderBy='email').execute()
    first_page.update(result)
    convert1 = json.dumps(first_page)
    #saving a copy of first page of the json returned
    with open("user_info.json", "w") as file:
        file.write(convert1)
    files.append("user_info.json")
    nextPageToken = result.get('nextPageToken', {})
    #looping through to get any more pages in case there are more than 500
    loop = True
    file_number = 2
    while loop:
        if nextPageToken:
            loop_result = service.users().list(domain='domain name goes here', pageToken = nextPageToken, maxResults = 500, orderBy='email').execute()
            aditional_pages.update(loop_result)
            convert2 = json.dumps(aditional_pages)
            #creating the names for all future pages
            filename = str("user_info"+str(file_number)+".json")
            with open(filename, "w") as file:
                file.write(convert2)
            files.append(filename)
            nextPageToken = loop_result.get('nextPageToken', {})
            file_number += 1
            if not nextPageToken:
                loop = False
                break
    return files

def sort_user_information(files):
    #breaking down the saved json files to get the relevant data to apply to the users signatures 
    for file in files:
        with open(file) as data:
            x = json.load(data)
            #this seperates the json by users
            for person in x["users"]:
                #within those users you need to pull the information that changes depending on the users i.e. name, title email... ect
                fullname = person["name"]["fullName"]
                email = person["primaryEmail"]
                try:
                    title = person["organizations"][0]["title"]
                except:
                    title = ""
                #for my project i determine which signature each user gets by their department in the user information but you can use and number of methods to decide
                try:
                    department = person["organizations"][0]["department"]
                except:
                    department = ""
                #the text of the html file you want the signature you want to apply to users in your domain you can list multiple htmls here and decide which user gets which signature assigned to them in the next section
                signautre_html = """html text goes here"""+fullname+"""more html"""+email+title+"""add varibles in the html with three quotation marks sepereated by + signs"""
                signautre2_html = "other signature arranged like above"
                #here is where you decide who gets which signature in this project i use their department as the deciding factor
                if department == "criteria for selecting department goes here i.e. HR, accounting whatever you want it to look for":
                    html = signautre_html
                    #see next set_signature section
                    set_signature(email, html)
                elif department == "whatever other criteria you want":
                    html = signautre2_html
                    set_signature(email, html)

    
#the email and html are passed through from the sort user information section
def set_signature(email, html):
    #this is the varible that changes the signature the changed html goes here
    DATA  = {"signature": html}
    #calls the credentials created at the begining of the code
    credentials = setup_credentials_gmail()
    #this contactes the api on behalf of the user you are changing the signature of
    credentials_delegated = credentials.with_subject(email)
    gmail_service = build("gmail","v1",credentials=credentials_delegated)
    #this lists all the emails of the user and finds the primary address
    addresses = gmail_service.users().settings().sendAs().list(userId="me", fields="sendAs(isPrimary,sendAsEmail)").execute().get("sendAs", [])
    for address in addresses:
        if address["isPrimary"]:
            break
    #this is the call that sets the signature using the data varible from above
    rsp = gmail_service.users().settings().sendAs().patch(userId="me", sendAsEmail=address["sendAsEmail"], body=DATA).execute()

#creates the list of files
files = make_jsons()
#sorts through jsons and sets the signatures
sort_user_information(files)
