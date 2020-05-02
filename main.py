from flask import Flask, request, render_template, redirect, url_for
from login import LoginForm
from register import RegistrationForm
from data import db_session
from data.users import User
from data.confirm_users import ConfirmUser
import cassiopeia as cass
from flask_login import LoginManager, login_user, login_required, logout_user
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from uuid import uuid4
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
cass.set_riot_api_key("RGAPI-fa29e3ff-89fe-40fa-bb6e-61d8d4462604")
cass.set_default_region("RU")


class NameError(Exception):
    pass


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/', methods=['POST', 'GET'])
def index():
    title = 'LolButt'
    if request.method == 'GET':
        return render_template(
            'index.html',
            title=title
        )
    elif request.method == 'POST':
        summoner_name = request.form.get('summoner_name')
        summoner = cass.get_summoner(name=summoner_name)
        try:
            if summoner.match_history[0].participants[summoner]:
                return redirect(f'/summoner/{summoner_name}')
        except:
            return render_template(
                "index.html",
                message="Неправильное имя призывателя!",
                title=title
            )


@app.route('/login', methods=['GET', 'POST'])
def login():
    title = 'Авторизация'
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form,
                               title=title)
    return render_template('login.html', title=title, form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    title='Регистрация'
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        try:
            cass.get_summoner(name=username)
        except:
            return render_template('register.html',
                                   form=form,
                                   message="Такого призывателя не существует!",
                                   title=title)
        email = form.email.data
        password = form.password.data
        session = db_session.create_session()
        if session.query(User).filter(User.email == email).first() or \
                session.query(ConfirmUser).filter(ConfirmUser.email == email).first():
            return render_template('register.html',
                                   form=form,
                                   message="Адрес почты занят!",
                                   title=title)
        if session.query(User).filter(User.name == username).first() or \
                session.query(User).filter(User.name == username).first():
            return render_template('register.html',
                                   form=form,
                                   message="Логин занят!",
                                   title=title
                                   )
        token = str(uuid4())
        user = ConfirmUser(name=username, email=email, token=token)
        user.set_password(password)
        session.add(user)
        session.commit()

        email_text = f'http://lolbutt.herokuapp.com/activation/{token}'
        try:
            send_email(email, email_text)
        except Exception:
            session.delete(user)
            session.commit()
            session.close()
            return redirect('/register')
        session.close()
        return render_template('final_register.html', title='Последний штрих')
    return render_template('register.html', form=form, title=title)


def send_email(email, text):
    msg = MIMEMultipart()
    message = text
    password = "MAXTHEPIK_loh123"
    msg['From'] = "lolbutt.noreply@gmail.com"
    msg['To'] = email
    msg['Subject'] = "Подтверждение почты"
    msg.attach(MIMEText(message, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com: 587')
    server.starttls()
    server.login(msg['From'], password)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()


@app.route('/summoner/<summoner_name>')
def search(summoner_name):
    summoner = cass.get_summoner(name=summoner_name)
    good_with = summoner.champion_masteries.filter(lambda cm: cm.level > 6)
    return render_template(
        'summoner.html',
        summoner=summoner,
        name=summoner.name,
        level=summoner.level,
        champions=[cm.champion.name for cm in good_with],
        profile_icon_url=summoner.profile_icon.url,
        match_history=summoner.match_history
    )


@app.route("/matches", methods=['GET', 'POST'])
def matches():
    if request.method == 'GET':
        return render_template(
            'matches.html'
        )
    elif request.method == 'POST':
        match_id = request.form.get('match_id')
        try:
            if cass.get_match(id=int(match_id)):
                return redirect(f'match/{match_id}')
        except:
            return render_template(
                'matches.html',
                message="Неверный id матча!"
            )


@app.route('/match/<match_id>')
def get_match(match_id):
    match = cass.get_match(id=int(match_id))
    red_team = match.red_team
    blue_team = match.blue_team
    red_team_stats = [
        sum(map(lambda participant: participant.stats.kills, red_team.participants)),
        sum(map(lambda participant: participant.stats.deaths, red_team.participants)),
        sum(map(lambda participant: participant.stats.assists, red_team.participants)),
        sum(map(lambda participant: participant.stats.gold_spent, red_team.participants)),
        sum(map(lambda participant: participant.stats.total_minions_killed, red_team.participants)),
        sum(map(lambda participant: participant.stats.gold_spent // match.duration.seconds * 60,
                red_team.participants)),
        sum(map(lambda participant: participant.stats.total_damage_dealt, red_team.participants)),
        sum(map(lambda participant: participant.stats.total_heal, red_team.participants)),
        sum(map(lambda participant: participant.stats.damage_dealt_to_turrets, red_team.participants))
    ]
    blue_team_stats = [
        sum(map(lambda participant: participant.stats.kills, blue_team.participants)),
        sum(map(lambda participant: participant.stats.deaths, blue_team.participants)),
        sum(map(lambda participant: participant.stats.assists, blue_team.participants)),
        sum(map(lambda participant: participant.stats.gold_spent, blue_team.participants)),
        sum(map(lambda participant: participant.stats.total_minions_killed, blue_team.participants)),
        sum(map(lambda participant: participant.stats.gold_spent // match.duration.seconds * 60,
                blue_team.participants)),
        sum(map(lambda participant: participant.stats.total_damage_dealt, blue_team.participants)),
        sum(map(lambda participant: participant.stats.total_heal, blue_team.participants)),
        sum(map(lambda participant: participant.stats.damage_dealt_to_turrets, blue_team.participants))
    ]

    duration = match.duration
    return render_template(
        'match.html',
        red_team={
            'name': 'Красная команда',
            'participants': red_team.participants,
            'stats': red_team_stats
        },
        blue_team={
            'name': 'Синяя команда',
            'participants': blue_team.participants,
            'stats': blue_team_stats
        },
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
        return render_template(
            'heroes.html',
            right_name=True
        )
    elif request.method == 'POST':
        hero = request.form.get('hero')
        hero = hero[0].upper() + hero[1:].lower()
        try:
            if hero in cass.Champions():
                return redirect(f'/heroes/{hero}')
            else:
                raise NameError("Неверное имя чемпиона")
        except NameError:
            return render_template(
                'heroes.html',
                message='Неправильное имя чемпиона!'
            )


@app.route("/heroes/<hero>")
def hero_search(hero):
    hero = cass.get_champion(hero)
    name = hero.name
    img = hero.image.url
    win_rates = dict()
    ban_rates = dict()
    play_rates = dict()
    for lane, rate in hero.win_rates.items():
        win_rates[lane] = round(rate * 100, 2)
    for lane, rate in hero.ban_rates.items():
        ban_rates[lane] = round(rate * 100, 2)
    for lane, rate in hero.play_rates.items():
        play_rates[lane] = round(rate * 100, 2)
    lanes = map(lambda z: z[0], sorted(play_rates.items(), key=lambda x: x[1], reverse=True))
    return render_template(
        'hero.html',
        name=name,
        img=img,
        win_rates=win_rates,
        ban_rates=ban_rates,
        play_rates=play_rates,
        lanes=lanes
    )


@app.route('/activation/<token>')
def activate(token):
    session = db_session.create_session()
    confirm_user = session.query(ConfirmUser).filter(ConfirmUser.token == token).first()
    if not confirm_user:
        return 'ошибка 404'
    username = confirm_user.name
    email = confirm_user.email
    password = confirm_user.hashed_password
    user = User(
        name=username,
        email=email,
        hashed_password=password
    )
    session.add(user)
    session.delete(confirm_user)
    session.commit()
    session.close()
    return redirect('/login')


if __name__ == '__main__':
    db_session.global_init("db/data.sqlite")
    #app.run(host='localhost', port=8080) # ДЛЯ ДУРАЧКОВ РАЗРАБОВ
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)  # СЕРВЕР
