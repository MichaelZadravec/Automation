#Steps to Complete and goal
#Goal is to filter out some of the junk in your email.Mostly the spam and marketing offers, because you're too lazy to unsubscribe...
#steps:
#pull Email files from outlook somehow and load them into a dataframe
#Use locally stored LLM to categorise emails - You can download this file from Open AI and store locally.
#Use new categories to move emails into folders and remove from the central inbox.

#Inital libraries neeeded
import imaplib
import email
import csv
from datetime import datetime, timedelta

# Your email details
username = 'INSERT YOUR EMAIL' #my email is @hotmail.com so i have actually only tested with this
password = 'INSERT YOUR PASSWORD' #Hardcoding passwords is not best practice, but for educational and personal purposes has helped me
imap_url = 'imap-mail.outlook.com' #this will change depending on the email browser use, can be found via google search
#
# Create the time variable - I will be running a clean everynight just before midnight to make sure i don't miss anything
today_date = datetime.now().strftime('%d-%b-%Y')

# Connect to the IMAP server and log in
mail = imaplib.IMAP4_SSL(imap_url)
mail.login(username, password)

# Select the mailbox you want to use. Use 'INBOX' for the main mailbox
mail.select('INBOX')

# Search for emails that came today
status, email_ids = mail.search(None, f'(ON "{today_date}")')
if status != 'OK':
    print("No emails found!")
    mail.logout()
    exit()

email_ids = email_ids[0].split()

# Define your CSV file
with open('emails.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, escapechar='\\')
    # Define your header
    writer.writerow(['Subject', 'From', 'Date', 'Body', 'Messageid'])

    # Fetch each email
    for email_id in email_ids:
        status, data = mail.fetch(email_id, '(RFC822)')
        if status != 'OK' or not data or not data[0]:
            print(f"Failed to fetch email with ID {email_id.decode()}. Status: {status}")
            continue  # Skip this email and move to the next

        # Parse the email content - For this task i only need Subject and ID but returned more for testing other ideas
        message = email.message_from_bytes(data[0][1])
        subject = message.get('subject', '')
        from_ = message.get('from', '')
        date_ = message.get('date', '')
        message_id = message.get('Message-ID', '')  # Corrected line

        # Initialize an empty body
        body = ''
        
        # If the email message is multipart
        if message.is_multipart():
            for part in message.walk():
                # Capture only text/plain parts
                if part.get_content_type() == 'text/plain':
                    charset = part.get_content_charset()
                    if charset is None:
                        charset = 'utf-8'
                    part_payload = part.get_payload(decode=True)
                    body += part_payload.decode(charset, 'ignore').replace('\r\n', ' ').replace('\n', ' ')
        else:
            charset = message.get_content_charset()
            if charset is None:
                charset = 'utf-8'
            body = message.get_payload(decode=True).decode(charset, 'ignore').replace('\r\n', ' ').replace('\n', ' ')

        # Write to CSV
        writer.writerow([subject, from_, date_, body, message_id])

# Close the IMAP connection
mail.close()
mail.logout()

#loading the data into a dataframe to then runn the locally stored LLM
import pandas as pd

# Load the CSV file into a pandas DataFrame
df = pd.read_csv('emails.csv', encoding='utf-8')

# Display the first few rows of the DataFrame
print(df.head())
#initialise and pull in the local GPT model, this is what we will be using to categorise the emails
#libraries needed to call the local AI - You will need to PIP install GPT4all and download a local model which can be downloaded form the OpenAI website
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import LLMChain
from langchain.llms import GPT4All
from langchain.prompts import PromptTemplate
#path to the local LLM
local_path = (
    "INSERT THE PATH TO YOUR LOCAL FILE HERE/mistral-7b-openorca.Q4_0.gguf"  # replace with your desired local file path
)
template = """Question: {question}

Answer: """

prompt = PromptTemplate(template=template, input_variables=["question"])

# Callbacks support token-wise streaming - gonna be honest at time of writing this i didn't know what this did - GPT and langchain website helped me get through this
callbacks = [StreamingStdOutCallbackHandler()]

# Verbose is required to pass to the callback manager
llm = GPT4All(model=local_path, callbacks=callbacks, verbose=True)

llm_chain = LLMChain(prompt=prompt, llm=llm)

#Here i have duplicated the dataset, however through testing this is where I took only a couple of emails to test by copying the dataset to only a few emails rather than all of them.
df_reduced = df
#Visialising the set to find errors in the Messageids
print(df_reduced)
#Column Names for reference in code below
print(df_reduced.columns)
#Classifying emails - pandas already as PD from above
# Changing this so that the local GPT is only classifying based off the subject line. The body characters went over the character limit and after testing subject gets the job done (so far)

df_reduced['category'] = None

#this function is sending the question to the LLM via the lanchain template we setup before - The prompt isn't perfect. But i took a lazy route and opted to clean the data later.
def categorize_email(Subject):
    question = f"Based on this subject line '{Subject}', categorize it into exactly one of the following categories: [Job adverts], [Bills/receipts], [Spam],[Other]. Only return one categoy and if you are unsure, call it [other] and nothing else. If the subject line could fit into more than one category throw it into Other, choose the most likely one. Reply with only the category name."
    response = llm_chain.run(question)
    return response

# Iterate over the DataFrame and categorize each email
for index, row in df_reduced.iterrows():
    # Extract the message
    Subject = row['Subject']  # or use row['message'] if you have a message column

    # Categorize the email
    category = categorize_email(Subject)

    # Store the result back in the DataFrame
    df_reduced.at[index, 'category'] = category

# Now df has an additional column 'category' with the categorization results
# the LLM can return some funny results, cleaning the output to get to the base category - if you come up with a better prompt....let me know. 
df_reduced['category'] = df_reduced['category'].str.strip()
df_reduced['Messageid'] = df_reduced['Messageid'].str.strip('<>')
df_reduced['category'] = df_reduced['category'].str.strip(',')
df_reduced['category'] = df_reduced['category'].str.strip('[]')
df_reduced['Messageid'] = df_reduced['Messageid'].str.strip('\r\n <')
df_reduced['Messageid'] = df_reduced['Messageid'].str.strip('>')
df_reduced['Messageid'] = df_reduced['Messageid'].str.strip('<')
print(df_reduced.columns)
print(df_reduced)

import imaplib
import pandas as pd

#WARNING: If for some reason the code is unable to copy the original but 'deletes' it, it is expunged and you won't be able to retrieve it, it's wiped form the server. Shouldn't happen, but could happen if the folder you're copying to name changes. 
#in my opinion this is the biggest flaw in this code. 

# We have to log in again because each time we are loggin out.
imap_host = 'imap-mail.outlook.com'
imap_user = 'INSERT YOUR EMAIL HERE'
imap_pass = 'INSERT YOUR PASSWORD HERE'

# Connect to the IMAP server
mail = imaplib.IMAP4_SSL(imap_host)
mail.login(imap_user, imap_pass)

# Iterate through each row in the DataFrame
for index, row in df_reduced.iterrows():
    message_id = row['Messageid']
    category = row['category']

    # Select the mailbox
    mail.select('inbox')

    # Search for the email by its Message-ID
    result, data = mail.search(None, f'(HEADER Message-ID "{message_id}")')

    if result == 'OK':
        # Fetch the email
        email_ids = data[0].split()
        print(f"Email IDs for Message ID {message_id}: {email_ids}")

        for e_id in email_ids:
            # Copy the email to the appropriate category folder
            if category == 'Job adverts':
                mail.copy(e_id, '"Job Adverts"')
                mail.store(e_id, '+FLAGS', '\\Deleted')
            elif category == 'Spam':
                mail.copy(e_id, '"Marketing"')
                mail.store(e_id, '+FLAGS', '\\Deleted')
            elif category == 'Bills/receipts':
                mail.copy(e_id, '"Bills"')
            # Add more conditions for other categories
            # Copy the email to the appropriate category folder
            # Add conditions for each category you have
    else:
        print(f"Search failed for Message ID {message_id}")

# Close the mailbox and logout
mail.close()
mail.logout()

#in the above code you can see that two categories are being deleted, and one is just being coppied. The one being coppied is my bills, as an extra safety precaution for deleting. 

#Will need code to export the dataframe to a CSV on my local computer, JUST IN CASE, the script deletes something without copying it first.
#Also look to trim the fat in this code once comfortable