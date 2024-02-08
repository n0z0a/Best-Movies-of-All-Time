from models import db
import json
import os
from dotenv import load_dotenv
import requests
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, current_user, login_user

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
login_manager = LoginManager(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://app_user:app_password@localhost/app_database'
db.init_app(app)
from models import Person, Rating


@login_manager.user_loader
def load_user(user_id):
    user = db.session.query(Person).get(int(user_id))
    return user

#Routes:
@app.route('/')
def index():
    return render_template('Login.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = Person.query.filter_by(username=username).first()
        if user:
            login_user(user)
            return redirect(url_for('moviepage'))
        else:
            return render_template('login.html', error='User does not exist')
    else:
        return render_template('login.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        existing_user = Person.query.filter_by(username=username).first()
        if existing_user:
            return render_template('signup.html', error='Username already exists.')
        #Create new user
        new_user = Person(username=username)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')
@app.route('/moviepage', methods=['GET','POST'])
def moviepage():
    load_dotenv()
    movie_ids = [406, 80, 9323]
    api_key = os.getenv('TMDB_API_KEY')
    img_URL = 'https://image.tmdb.org/t/p/w1280'
    movies_info = []

    for movie_id in movie_ids:
        url = f'https://api.themoviedb.org/3/movie/{movie_id}?language=en-US'
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        movie_obj = data

        # Fetching movie information
        movie_title = movie_obj['title']
        movie_tagline = movie_obj['tagline']
        movie_poster_path = movie_obj['poster_path']
        movie_poster = f'{img_URL}{movie_poster_path}'
        movie_genres = ', '.join([genre['name'] for genre in movie_obj.get('genres', [])])

        # Fetching Wikipedia URL based on the movie ID
        page_ids = {80: 805120, 406: 497081, 9323: 12914}
        page_id = page_ids.get(movie_id)
        if page_id is not None:
            BASE_WIKI_URL = 'https://en.wikipedia.org/w/api.php'
            wiki_search = movie_title
            response = requests.get(BASE_WIKI_URL, params={'action': 'query', 'format': 'json', 'prop': 'info', 'generator': 'allpages', 'inprop': 'url', 'gapfrom': wiki_search, 'gaplimit': '5'})
            json_data = response.json()
            wiki_object = json_data
            movie_url = wiki_object['query']['pages'][str(page_id)]['fullurl']
        else:
            movie_url = ""

        ratings = Rating.query.filter_by(movie_id=movie_id).all()
        rating_info = []
        for rating in ratings:
            user = Person.query.get(rating.user_id)
            if user:
                rating_info.append({'username': user.username, 'rating': rating.rating, 'comment': rating.comment})

        movie_info = {
            'id': movie_id,
            'title': movie_title,
            'tagline': movie_tagline,
            'poster': movie_poster,
            'genre': movie_genres,
            'url': movie_url,
            'ratings': rating_info
        }
        movies_info.append(movie_info)

    if request.method == 'POST':
        movie_id = request.form['movieID']
        rating_value = request.form['rating']
        comment = request.form['comment']
        user_id = current_user.id
        # Create a new rating object and add it to the database
        new_rating = Rating(movie_id=movie_id, user_id=user_id, rating=rating_value, comment=comment)
        db.session.add(new_rating)
        db.session.commit()
        # Redirect to the movie page to display updated ratings and comments
        return redirect(url_for('moviepage'))
    return render_template('moviepage.html', movies_info=movies_info)
if __name__ == '__main__':
    app.run(debug=True)