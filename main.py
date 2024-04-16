import requests
from flask import Flask, render_template, redirect, request, send_file
from flask_login import login_required, logout_user, login_user
from flask_login import LoginManager, current_user
from forms.login import LoginForm
from forms.add_job import JobForm
from forms.register import RegisterForm
from data import db_session
from data.users import User, Jobs
from api import users_api
from requests import get
import io

db_session.global_init("db/blogs.db")
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'  # ключ от csfr атак
login_manager = LoginManager()
login_manager.init_app(app)
app.register_blueprint(users_api.blueprint)


@app.route('/')
def main():
    '''Главная страница'''
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        data_jobs = db_sess.query(Jobs).filter(Jobs.user == current_user).all()
        team_leaders = []
        if data_jobs:
            i = data_jobs[0]
            team_leaders = [' '.join(db_sess.query(User.surname, User.name).filter(User.id ==
                                                                                   i.team_leader).first())] * len(data_jobs)
    else:
        data_jobs = db_sess.query(Jobs).all()
        team_leaders = []
        for i in data_jobs:
            team_leaders.append(
                ' '.join(db_sess.query(User.surname, User.name).filter(User.id == i.team_leader).first()))
    db_sess.commit()
    return render_template('index.html', all=zip(data_jobs, team_leaders))


@login_manager.user_loader
def load_user(user_id):
    '''Системная'''
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''Авторизация пользователя'''
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', name='Авторизация пользователя', form=form)


@app.route('/logout')
@login_required
def logout():
    '''Обработчик кнопки - имени'''
    logout_user()
    return redirect("/")


@app.route('/addjob', methods=['GET', 'POST'])
def addjob():
    '''Добавление работы (в БД)'''
    message = ''
    form = JobForm()
    if form.submit.data and request.method == 'POST':
        db_sess = db_session.create_session()
        there_coll = all(db_sess.query(User).filter(User.id == i).first() for i in form.collaborators.data.split(', '))
        if db_sess.query(User).filter(User.id == form.leader.data).first():
            try:
                if int(form.size.data) > 0:
                    if there_coll:
                        job = Jobs(
                            team_leader=form.leader.data,
                            job=form.title.data,
                            work_size=form.size.data,
                            collaborators=form.collaborators.data,
                            is_finished=form.remember_me.data
                        )
                        db_sess.add(job)
                        db_sess.commit()
                        return redirect('/')
                    else:
                        message = 'Collaborators должны быть в виде существующих индефекаторов пользователей (1, 2) !'
                else:
                    message = 'Длина работы должна быть больше 0'
            except ValueError:
                message = 'Длина работа должна быть представлена в виде числа'
        else:
            message = 'Руководителя с таким id нет в наших базах данных'
    if message:
        return render_template('login.html', title='Добавление работы', name='Adding a Job', form=form, message=message)
    return render_template('login.html', title='Добавление работы', name='Adding a Job', form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.submit.data:
        if form.password.data != form.password_again.data:
            return render_template('login.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают", name='Register')
        elif int(form.age.data) < 0:
            return render_template('login.html', title='Регистрация',
                                   form=form,
                                   message="Возраст не может быть отрицательным", name='Register')
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('login.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть", name='Register')
        user = User(
            name=form.name.data,
            email=form.email.data,
            surname=form.surname.data,
            age=form.age.data,
            position=form.position.data,
            speciality=form.speciality.data,
            address=form.address.data,
            city_from=form.city.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        login_user(user)
        db_sess.commit()
        return redirect('/')
    return render_template('login.html', title='Регистрация', form=form, name='Register')


@app.route('/get_image/<string:coord>')
def get_image(coord):
    map_params = {
        'll': ",".join(coord.split()),
        'l': "sat",
        "spn": "0.05,0.05"
    }
    response = requests.get("http://static-maps.yandex.ru/1.x/", params=map_params)
    print(response.status_code)
    image_data = io.BytesIO(response.content)
    return send_file(
        image_data,
        mimetype='image/jpeg')


@app.route('/users_show/<int:user_id>', methods=["GET"])
def users_show(user_id):
    '''Просмотр родины пользователя'''
    data = get(f'http://127.0.0.1:8080/api/user/city/{user_id}').json()["data"]
    name_user = data["name_user"] + " " + data["surname_user"]
    return render_template("nostalgy_home.html", title="Hometown", name=name_user, town=data["town"],
                           coordinate=data["coordinate"])


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
