from flask_restful import Resource, Api, request, reqparse, marshal_with, fields, abort
from models import *

api = Api()

user_output_fields = {
    'id': fields.Integer,
    'username': fields.String,
    'email': fields.String,
    'dp': fields.String,
    # 'password_hash': fields.String,
    'bio': fields.String,
    'join_date': fields.DateTime,
    # 'posts': fields.Nested(post_output_fields)
}

user_args = reqparse.RequestParser()
user_args.add_argument("username", type = str, required=True, help='No username provided')
user_args.add_argument('email', type=str, required=True, help='No email provided')
user_args.add_argument('dp', type=str)
# user_args.add_argument('password', type=str, required=True, help='No password provided')
user_args.add_argument('bio', type=str)


class UserAPI(Resource):
    @marshal_with(user_output_fields)
    def get(self, id):
        user = User.query.get(id)
        if user:
            return user
        else:
            abort(404, message='User does not exist')

    @marshal_with(user_output_fields)
    def post(self):
        args = user_args.parse_args()
        usr = User.query.filter_by(username = args["username"]).first()
        if usr:
            abort(409, message = "Username already exists")
        else:
            # user = User(username=args["username"], email=args["email"], password=args["password"], dp=args["dp"], bio=args["bio"])
            user = User(username=args["username"], email=args["email"], dp=args["dp"], bio=args["bio"])
            db.session.add(user)
            db.session.commit()
            return user, 201

    @marshal_with(user_output_fields)
    def put(self, id):
        args = user_args.parse_args()
        user = User.query.get(id)
        if not user:
            abort(404, message='User not found')
        if 'username' in args:
            if User.query.filter_by(username=args['username']).first() is not None:
                return {'message': 'username already exist'}, 400
            user.username = args['username']
        if 'email' in args:
            user.email = args['email']
        if 'dp' in args:
            user.dp = args['dp']
        if 'bio' in args:
            user.bio = args['bio']

        db.session.commit()
        return user

    @marshal_with(user_output_fields)
    def delete(self, id):
        user = User.query.get(id)
        if not user:
            abort(404, message='User not found')
        db.session.delete(user)
        db.session.commit()
        return {
            "message" :"User deleted successfully"
        }, 204

api.add_resource(UserAPI, '/api/users', '/api/users/<int:id>')


post_output_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'body': fields.String,
    'image': fields.String,
    'timestamp': fields.DateTime,
    'author': fields.String
}

post_args = reqparse.RequestParser()
post_args.add_argument('title', type=str, required=True, help='No title provided')
post_args.add_argument('body', type=str, required=True, help='No body provided')
post_args.add_argument('image', type=str)
post_args.add_argument('user_id', type=int, required=True, help='No user_id provided')

class PostAPI(Resource):
    @marshal_with(post_output_fields)
    def get(self, id):
        post = Post.query.get(id)
        if not post:
            abort(404, message='Post not found')
        return post

    @marshal_with(post_output_fields)
    def post(self):
        args = post_args.parse_args()
        post = Post(title=args['title'], body=args['body'], image=args['image'], author=args['user_id'])
        db.session.add(post)
        db.session.commit()
        return post, 201


    @marshal_with(post_output_fields)
    def put(self, id):
        args = post_args.parse_args()
        post = Post.query.get(id)
        if not post:
            abort(404, message='Post not found')
        
        if 'title' in args:
            post.title = args['title']
        if 'body' in args:
            post.body = args['body']
        if 'image' in args:
            post.image = args['image']

        db.session.commit()
        return post

    def delete(self, id):
        post = Post.query.get(id)
        if not post:
            abort(404, message='Post not found')
        db.session.delete(post)
        db.session.commit()
        return {
            "message" :"Post deleted successfully"
        }, 204

api.add_resource(PostAPI, '/api/post', '/api/post/<int:id>')

class LikeAPI(Resource):
    def post(self):
        args = request.json
        user_id = args.get('user_id')
        post_id = args.get('post_id')
        if user_id is None or post_id is None:
            abort(400, message='Missing user_id or post_id')
        
        like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
        if like:
            abort(409, message='Like already exists')
        
        new_like = Like(user_id=user_id, post_id=post_id)
        db.session.add(new_like)
        db.session.commit()
        
        return {
            'message': 'Like added successfully',
            'like': {
                'user_id': user_id,
                'post_id': post_id
            }
        }, 201

    def delete(self):
        args = request.json
        user_id = args.get('user_id')
        post_id = args.get('post_id')
        if user_id is None or post_id is None:
            abort(400, message='Missing user_id or post_id')
        
        like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
        if not like:
            abort(404, message='Like not found')
        
        db.session.delete(like)
        db.session.commit()
        
        return {
            'message': 'Like removed successfully'
        }, 204

api.add_resource(LikeAPI, '/api/like')


class CommentAPI(Resource):
    def post(self):
        args = request.json
        user_id = args.get('user_id')
        post_id = args.get('post_id')
        content = args.get('content')
        if user_id is None or post_id is None or content is None:
            abort(400, message='Missing user_id, post_id, or content')
        
        new_comment = Comment(user_id=user_id, post_id=post_id, content=content)
        db.session.add(new_comment)
        db.session.commit()
        
        return {
            'message': 'Comment added successfully',
            'comment': {
                'user_id': user_id,
                'post_id': post_id,
                'content': content
            }
        }, 201

    def delete(self):
        args = request.json
        user_id = args.get('user_id')
        post_id = args.get('post_id')
        if user_id is None or post_id is None:
            abort(400, message='Missing user_id or post_id')
        
        comment = Comment.query.filter_by(user_id=user_id, post_id=post_id).first()
        if not comment:
            abort(404, message='Comment not found')
        
        db.session.delete(comment)
        db.session.commit()
        
        return {
            'message': 'Comment removed successfully'
        }, 204

api.add_resource(CommentAPI, '/api/comment')