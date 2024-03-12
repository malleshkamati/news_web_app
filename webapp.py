from flask import Flask, render_template, request,url_for,redirect,session,flash
from authlib.integrations.flask_client import OAuth

from nltk.tokenize import word_tokenize
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import Counter
from urllib import request as urllib_request
import psycopg2
import nltk
import bs4
from nltk import sent_tokenize
from nltk import word_tokenize
from urllib import request as urllib_request2
from bs4 import BeautifulSoup
import requests
import re


nltk.download('all')

#from collections import Counter

conn = psycopg2.connect(host='dpg-cnmoa8acn0vc738f6ur0-a', database='kamati', user='mallesh', password='d9dgVZDaFuQVRHea8wxgK2eZuKzvvs3E')
cur = conn.cursor()
app = Flask(__name__, static_folder="static1")

oauth = OAuth(app)

# github
app.config['SECRET_KEY'] = "THIS is mine"
app.config['GITHUB_CLIENT_ID'] = "67ac24f4cce98e657f28"
app.config['GITHUB_CLIENT_SECRET'] = "91fc031922079eb0b928d6e13dfef81a484e299e"

github = oauth.register(
    name='github',
    client_id=app.config["GITHUB_CLIENT_ID"],
    client_secret=app.config["GITHUB_CLIENT_SECRET"],
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

# GitHub admin usernames for verification
github_admin_usernames = ["malleshkamati","atmabodha"]

def sentimental(text):
    tokens = word_tokenize(text)

    # Sentiment analysis using VADER sentiment analyzer
    sia = SentimentIntensityAnalyzer()
    sentiment_scores = [sia.polarity_scores(token)["compound"] for token in tokens]

    # Aggregate sentiment scores
    aggregate_score = sum(sentiment_scores)

    # Interpret the result
    if aggregate_score > 0:
        sentiment = "A GOOD NEWS"
    elif aggregate_score < 0:
        sentiment = "A BAD NEWS"
    else:
        sentiment = "NEUTRAL"

    return sentiment
def publish_details(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Finding the div tag with id="storycenterbyline"
    publish_results = soup.find(id="storycenterbyline")

    # Extracting the date information
    date_modified_tag = publish_results.find('span', itemprop='dateModified')
    # date_modified_tag = soup.find('span', itemprop='dateModified')
    if date_modified_tag:
        date_modified = "date modified"+date_modified_tag.text.strip()
    else:
        date_modified = "Date information not found"

 

    return date_modified
def calculate_reading_time(text, words_per_minute=200):
    # Remove any HTML tags and extra whitespaces
    clean_text = re.sub('<[^<]+?>', '', text)
    clean_text = ' '.join(clean_text.split())

    # Count the number of words in the text
    word_count = len(clean_text.split())

    # Calculate the reading time in minutes
    reading_time_minutes = word_count // words_per_minute

    return reading_time_minutes
# conn=psycopg2.connect(host='localhost',database='dhp2024',user='postgres',password='Mallesh@123')
# cur=conn.cursor()

cur.execute('''
    CREATE TABLE IF NOT EXISTS news_table (
       
        url VARCHAR(80000),
        title VARCHAR(500),
        sentiment VARCHAR(500),
        news_text VARCHAR(100000),
        number_of_sentences INTEGER,
        number_of_stopwords INTEGER,
        number_of_upos_tags VARCHAR(10000),
        image_link VARCHAR(255)
    );
''')
conn.commit()





@app.route("/", methods=["POST", "GET"])
def portal():
    enter_url = ''
    data = []
    # link=''
    # publish_dt=[]
    try:
        if request.method == 'POST':
            enter_url = request.form["enter_url"]

                # Fetching HTML content from the URL
            html = urllib_request.urlopen(enter_url).read().decode('utf8')

                # Parsing HTML content with BeautifulSoup
            page = requests.get(enter_url)
            soup = BeautifulSoup(page.content, 'html.parser')
            title1 = soup.title.string
            results = soup.find(id="pcl-full-content")
            # results = soup.find(class_="story-details")
            # results = results.find_all('p')
            # raw_html = str(results)
            # clean_text = re.sub(r'<.*?>', '', raw_html)
            # clean_text = clean_text.replace("\n", "")
            raw_html = str(results)
            results2 = soup.find(class_="custom-caption")
            if results2:
                img_tag = results2.find('img')
                if img_tag:
                    link = img_tag['src']
                    print("Image Link:", link)
            
            clean_text1 = re.sub(r'<a\b[^>]*>.*?</a>' ,'', raw_html)
            soup = BeautifulSoup(clean_text1,'html.parser')
            p = soup.findAll('p')
            stra = ''
            for i in p:
                text = i.get_text()
                stra +=text

            clean_text = stra.replace(r'[\\n]', "",)
            text = re.sub(r'[^\w\s\.\,\!\?\@\;\:]', '', clean_text)

            sentiment=sentimental(text)

            

                # Tokenizing text
            sent_list = sent_tokenize(clean_text)
            sent = len(sent_list)
            word_list = word_tokenize(clean_text)
            word = len(word_list)
            upos1 = nltk.pos_tag(word_list,tagset='universal')
            #upos = len(upos1)
            #upos = Counter( tag for word , tag in upos1)
            #upos
            upos_list=  [tag for word , tag in upos1]
            upos1={}
            for i in upos_list:
                if i in upos1.keys():
                    upos1[i]+=1
                else:
                    upos1[i]=1
            upos1=str(upos1)
            link_str=str(link)
            time1=calculate_reading_time(clean_text)

                # Filtering stop words
            stop_words_list_all = nltk.corpus.stopwords.words('english')
            stop_words_list = [i for i in word_list if i in stop_words_list_all]
            stop_words = len(stop_words_list)

            other = sent, stop_words, upos1, clean_text, title1,link

            # publish_dt=publish_details(results)

                # Inserting data into the database
            cur.execute('INSERT INTO news_table (url,title,sentiment,news_text,number_of_sentences,number_of_stopwords,number_of_upos_tags,image_link) VALUES (%s, %s,%s,%s,%s,%s,%s,%s)', (enter_url,title1,sentiment,clean_text,sent,stop_words,upos1,link_str))
            conn.commit()

            
            data=enter_url,title1,sentiment,clean_text,sent,stop_words,upos1,link,sentiment,time1,word

    except Exception as e:
         #Handle exceptions and log or display an error message
         # print(f"An error occurred: {str(e)}")
           flash(f"An error occurred: {str(e)}", 'error')


    return render_template("newsapp3.html", data=data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # if request.method == 'GET':
        # Render the login page
    return render_template('signup.html')






@app.route("/signin",methods=["POST", "GET"])
def signin():
    if request.method == 'POST':
        # Add your server-side login logic here if needed
        return redirect(url_for('portal'))

    #return render_template("login.html")
    return render_template("signin.html")

@app.route("/admin", methods=["GET","POST"])
def admin():
    enter_url = ''
    data = []
    # link=''
    # publish_dt=[]
    try:
        if request.method == 'POST':
            enter_url = request.form["enter_url"]

                # Fetching HTML content from the URL
            html = urllib_request.urlopen(enter_url).read().decode('utf8')

                # Parsing HTML content with BeautifulSoup
            page = requests.get(enter_url)
            soup = BeautifulSoup(page.content, 'html.parser')
            title1 = soup.title.string
            results = soup.find(id="pcl-full-content")
            # results = soup.find(class_="story-details")
            # results = results.find_all('p')
            raw_html = str(results)
            clean_text = re.sub(r'<.*?>', '', raw_html)
            clean_text = clean_text.replace("\n", "")
            text = re.sub(r'[^\w\s\.\,\!\?\@\;\:]', '', clean_text)

            sentiment=sentimental(text)
            results2 = soup.find(class_="custom-caption")
            
            
            


            if results2:
                img_tag = results2.find('img')
                if img_tag:
                    link = img_tag['src']
                    print("Image Link:", link)

                # Tokenizing text
            sent_list = sent_tokenize(clean_text)
            sent = len(sent_list)
            word_list = word_tokenize(clean_text)
            word = len(word_list)
            upos1 = nltk.pos_tag(word_list,tagset='universal')
            #upos = len(upos1)
            #upos = Counter( tag for word , tag in upos1)
            #upos
            upos_list=  [tag for word , tag in upos1]
            upos1={}
            for i in upos_list:
                if i in upos1.keys():
                    upos1[i]+=1
                else:
                    upos1[i]=1
            upos1=str(upos1)
            link_str=str(link)
            time1=calculate_reading_time(clean_text)

                # Filtering stop words
            stop_words_list_all = nltk.corpus.stopwords.words('english')
            stop_words_list = [i for i in word_list if i in stop_words_list_all]
            stop_words = len(stop_words_list)

            other = sent, stop_words, upos1, clean_text, title1,link

            #publish_dt=publish_details(results)

                # Inserting data into the database
            cur.execute('INSERT INTO news_table (url,title,sentiment,news_text,number_of_sentences,number_of_stopwords,number_of_upos_tags,image_link) VALUES (%s, %s,%s,%s,%s,%s,%s,%s)', (enter_url,title1,sentiment,clean_text,sent,stop_words,upos1,link_str))
            conn.commit()

            #data = enter_url, sent, stop_words, upos1, clean_text, title1,link 
            data=enter_url,title1,sentiment,clean_text,sent,stop_words,upos1,link,sentiment,time1

    except Exception as e:
         #Handle exceptions and log or display an error message
         print(f"An error occurred: {str(e)}")

    return render_template("admin.html", data=data)



    # return render_template("admin.html")
@app.route('/newsapp3')
def newsapp3():
    return render_template('newsapp3.html')

@app.route('/templates/newsapp3')
def render_newsapp3():
    return render_template('newsapp3.html')

@app.route('/contactus')
def contactus():
    return render_template('contactus.html')




@app.route("/view_data", methods=["GET","POST"])
def view_data():
    try:
        cur.execute('select * from news_table')
        data = cur.fetchall()
        return render_template("view_data.html", data=data)
    except Exception as e:
         #Handle exceptions and log or display an error message
        # print(f"An error occurred: {str(e)}")
        return render_template("view_data.html")
    
# Github login
# Default route
@app.route('/m')
def index():
    is_admin = False
    github_token = session.get('github_token')
    if github_token:
        github = oauth.create_client('github')
        resp = github.get('user').json()
        username = resp.get('login')
        print(f"\n{resp}\n")
        
        logged_in_username = resp.get('login')
        if logged_in_username in github_admin_usernames:
            cur.execute('select  * from news_table')
            data = cur.fetchall()
            
            return render_template("newsapp3.html", data=data)
        else:
            return redirect(url_for('admin'))


@app.route('/login/github')
def github_login():
    github = oauth.create_client('github')
    redirect_uri = url_for('github_authorize', _external=True)
    return github.authorize_redirect(redirect_uri)

# Github authorize route
@app.route('/login/github/authorize')
def github_authorize():
    try:
        github = oauth.create_client('github')
        token = github.authorize_access_token()
        session['github_token'] = token
        resp = github.get('user').json()
        print(f"\n{resp}\n")
        # print(type(repr))
        # data=get_history_from_database()
        # return render_template("history.html",data=data)
        logged_in_username = resp.get('login')
        if logged_in_username in github_admin_usernames:
            data = cur.fetchall()
            return render_template("view_data.html", data=data)
        else:
            return redirect(url_for('portal'))
    except:
        return redirect(url_for('admin'))

    
# Logout route for GitHub
@app.route('/logout/github')
def github_logout():
    session.clear()
    # session.pop('github_token', None)()
    print("logout")
    # return redirect(url_for('index'))
    return redirect(url_for('portal'))


if __name__ == '__main__':
    app.run(debug=True)
