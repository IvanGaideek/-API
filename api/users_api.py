import flask
from flask import jsonify, make_response
import requests

from data import db_session
from data.users import User

blueprint = flask.Blueprint(
    'picture_city',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/user/city/<int:user_id>')
def get_coord_city(user_id):
    db_sess = db_session.create_session()
    city_text, name, surname = db_sess.query(User.city_from, User.name, User.surname).filter(User.id == user_id).first()
    if not city_text:
        return make_response(jsonify({'error': 'Not found'}), 404)
    geocoder_params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": city_text,
        "format": "json"}
    response = requests.get("http://geocode-maps.yandex.ru/1.x/", params=geocoder_params)
    json_response = response.json()
    toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
    # Координаты центра топонима:
    toponym_coodrinates = toponym["Point"]["pos"]
    db_sess.close()
    return jsonify({"data": {'coordinate': toponym_coodrinates, "name_user": name, "surname_user": surname,
                             "town": city_text}})
