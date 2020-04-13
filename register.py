from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, validators, SubmitField
from flask_wtf import FlaskForm


class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', [validators.Length(min=4, max=50)])
    email = StringField('Email адрес', [validators.Length(min=6, max=35)])
    password = PasswordField('Пароль', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Пароли не совпадают')
    ])
    confirm = PasswordField('Повторите пароль')
    submit = SubmitField('Зарегистрироваться')
