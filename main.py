from flask import Flask, request, render_template, redirect
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
        if session.query(User).filter(User.email == email).first() or \
           session.query(ConfirmUser).filter(ConfirmUser.email == email).first():
            return render_template('register.html',
                                   form=form,
                                   message="Адрес почты занят!")
        if session.query(User).filter(User.name == username).first() or \
           session.query(User).filter(User.name == username).first():
            return render_template('register.html',
                                    form=form,
                                    message="Логин занят!")
        token = str(uuid4())
        user = ConfirmUser(name=username, email=email, token=token)
        user.set_password(password)
        session.add(user)
        session.commit()
        session.close()

        email_text = f'http://127.0.0.1:8080/activation/{token}'
        send_email(email, email_text)

        return redirect('/login')
    return render_template('register.html', form=form)


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
    return render_template(
        'match.html',
        red_team_participants=red_team.participants,
        blue_team_participants=blue_team.participants
    )


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


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
    app.run(host='127.0.0.1', port='8080', debug=True)
