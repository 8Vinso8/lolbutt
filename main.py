from flask import Flask, request, render_template, redirect
from login import LoginForm
from register import RegistrationForm
from data import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route('/')
@app.route('/index')
def index():
    return render_template('base.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        the_username = form.username.data
        the_password = form.password.data
        print(the_username, the_password)
        return redirect('/')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        the_username = form.username.data
        the_email = form.email.data
        the_password = form.password.data
        print(the_email, the_username, the_password)
        return redirect('/')
    return render_template('register.html', form=form)


def main():
    db_session.global_init("db/data.sqlite")
    app.run(host='127.0.0.1', port='8080', debug=True)


if __name__ == '__main__':
    main()