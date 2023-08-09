from flask_wtf import FlaskForm
from models import User
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, Email, EqualTo, Length, InputRequired
from flask_uploads import IMAGES, UploadSet

photos = UploadSet('photos', IMAGES)

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(max=30, message='Should be less than 30 characters')])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    password2 = PasswordField('Repeat Password', validators=[InputRequired(), EqualTo('password')])
    dp = FileField(validators=[FileAllowed(IMAGES, 'Only images are allowed')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('User already exists!')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class PostForm(FlaskForm):
    title = StringField('Post Title', validators=[InputRequired()])
    description = TextAreaField('Post Description', validators=[InputRequired()])
    image = FileField(validators=[FileAllowed(IMAGES, 'Only images are allowed')])
    submit = SubmitField('Post')

class CommentForm(FlaskForm):
    content = StringField('Comment', validators=[InputRequired()])
    submit = SubmitField('Post Comment')

class EditProfile(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    dp = FileField(validators=[FileAllowed(IMAGES, 'Only images are allowed')])
    bio = StringField('Bio')
    submit = SubmitField('Update')