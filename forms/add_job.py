from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField, StringField
from wtforms.validators import DataRequired


class JobForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired()])
    leader = StringField('Team Leader id', validators=[DataRequired()])
    size = StringField('Work Size', validators=[DataRequired()])
    collaborators = StringField('Collaborators', validators=[DataRequired()])
    remember_me = BooleanField('Is job finished?')
    submit = SubmitField('Submit')
