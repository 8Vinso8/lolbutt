from flask import Flask, request, render_template, redirect, url_for
from login import LoginForm
from register import RegistrationForm
from data import db_session
from data.users import User
import cassiopeia as cass
from flask_login import LoginManager, login_user, login_required, logout_user
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
cass.set_riot_api_key("RGAPI-4ebb526b-2f70-46c7-8212-a490b83645fe")
cass.set_default_region("RU")


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/')
def base():
    return render_template('base.html')


@app.route('/index', methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    elif request.method == 'POST':
        summoner_name = request.form.get('summoner_name')
        return redirect(f'/search/{summoner_name}')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        session = db_session.create_session()
        if session.query(User).filter(User.email == email).first():
            return render_template('register.html',
                                   form=form,
                                   message="Адрес почты занят!")
        if session.query(User).filter(User.name == username).first():
            return render_template('register.html',
                                   form=form,
                                   message="Логин занят!")
        user = User(
            name=username,
            email=email,
        )
        user.set_password(password)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', form=form)


@app.route('/search/<summoner_name>')
def search(summoner_name):
    try:
        summoner = cass.get_summoner(name=summoner_name)
        name = summoner.name
        level = summoner.level
        good_with = summoner.champion_masteries.filter(lambda cm: cm.level >= 6)
        last_match = summoner.match_history[0]
        last_champion = last_match.participants[summoner].champion
        profile_icon = summoner.profile_icon.url
        return render_template(
            'search.html',
            name=name,
            level=level,
            champions=[cm.champion.name for cm in good_with],
            last_champion=last_champion.name,
            profile_icon_url=profile_icon,
            last_match_id=str(last_match.id)
        )
    except:
         return redirect('/index')


@app.route('/match/<match_id>')
def get_match(match_id):
    match = cass.get_match(id=int(match_id))
    red_team = match.red_team
    blue_team = match.blue_team
    duration = match.duration
    return render_template(
        'match.html',
        red_team={'name': 'Красная команда', 'participants': red_team.participants},
        blue_team={'name': 'Синяя команда', 'participants': blue_team.participants},
        match_duration=duration,
        str=str,
        round=round,
        sorted=sorted,
        filter=filter,
        sort_key=lambda item: item.name,
        filter_key=lambda item: item is not None
    )


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/heroes", methods=['GET', 'POST'])
def heroes():
    if request.method == 'GET':
        return render_template('heroes.html')
    elif request.method == 'POST':
        hero = request.form.get('hero')
        return redirect(f'/heroes/{hero}')


@app.route("/heroes/<hero>")
def hero_search(hero):
    if hero in cass.Champions():
        hero = cass.Champion(name=f"{hero}")
        name = hero.name
        print(1)
        return render_template(
            'hero.html',
            name=name
            )


if __name__ == '__main__':
    db_session.global_init("db/data.sqlite")
    app.run(host='127.0.0.1', port='8080')
