from flask import Flask, jsonify, request, views
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, func, ForeignKey
)
from sqlalchemy.orm import sessionmaker, relationship
import pydantic
from flask_bcrypt import Bcrypt

app = Flask('BBoard')

bcrypt = Bcrypt(app)

PG_DSN = 'postgresql://postgres:postgres@localhost:5432/backend'
engine = create_engine(PG_DSN)
Session = sessionmaker(bind=engine)

BaseModel = declarative_base()


class HttpError(Exception):
    def __init__(self, status_code, error_message):
        self.status_code = status_code
        self.error_message = error_message


@app.errorhandler(HttpError)
def http_error_handler(error):
    response = jsonify({'error': error.error_message})
    response.status_code = error.status_code
    return response


class UserModel(pydantic.BaseModel):
    name: str
    password: str

    @pydantic.validator('password')
    def strong_password(cls, value):
        if len(value) < 6:
            raise ValueError('password too short')
        return value


class BbMessageModel(pydantic.BaseModel):
    title: str
    description: str
    author_id: int

    @pydantic.validator('title')
    def meaningful_title(cls, value):
        if len(value) < 5:
            raise ValueError('title is too short')
        return value

    @pydantic.validator('description')
    def meaningful_description(cls, value):
        if len(value) < 10:
            raise ValueError('description is too short')
        return value


class User(BaseModel):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True, nullable=True, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class BbMessage(BaseModel):
    __tablename__ = 'bb_messages'
    id = Column(Integer, primary_key=True)
    title = Column(String, index=True, nullable=True, unique=True)
    description = Column(String, index=True, nullable=False)
    author_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )
    user = relationship('User', backref='authors')
    created_at = Column(DateTime, server_default=func.now())


BaseModel.metadata.create_all(engine)


class UserView(views.MethodView):
    def get(self, user_id):
        with Session() as session:
            user = session.query(User).get(user_id)
            if not user:
                raise HttpError(404, 'User not found')

            return jsonify({
                'id': user.id,
                'name': user.name,
                'created_at': user.created_at.isoformat()
            })

    def post(self):
        try:
            validated_data = UserModel(**request.json).dict()
        except pydantic.ValidationError as er:
            raise HttpError(400, er.errors())

        password = validated_data.pop('password').encode()
        password = bcrypt.generate_password_hash(password).decode()
        validated_data['password'] = password

        with Session() as session:
            user = User(**validated_data)
            session.add(user)
            try:
                session.commit()
            except IntegrityError:
                raise HttpError(400, 'name not unique')
            response = jsonify({'id': user.id, 'name': user.name})
            response.status_code = 201
            return response

    def delete(self, user_id):
        with Session() as session:
            user = session.query(User).get(user_id)
            if not user:
                raise HttpError(400, 'User not found')
            session.delete(user)
            session.commit()
            return jsonify({
                'id': user_id,
                'message': 'user deleted'
            })


def message_serializer(bb_message):
    return {
        'id': bb_message.id,
        'author': bb_message.user.name,
        'title': bb_message.title,
        'description': bb_message.description,
        'created_at': bb_message.created_at.isoformat()
    }


class BbMessageView(views.MethodView):
    def get(self, bbm_id=None):
        with Session() as session:
            if bbm_id:
                bb_message = session.query(BbMessage).get(bbm_id)
                if not bb_message:
                    raise HttpError(404, 'Message not found')
                return jsonify(message_serializer(bb_message))
            else:
                bb_messages = session.query(BbMessage).all()
                res = [message_serializer(bb_msg) for bb_msg in bb_messages]
                return jsonify(res)

    def post(self):
        try:
            validated_data = BbMessageModel(**request.json).dict()
        except pydantic.ValidationError as er:
            raise HttpError(400, er.errors())
        with Session() as session:
            bb_message = BbMessage(**validated_data)
            session.add(bb_message)
            try:
                session.commit()
            except IntegrityError as er:
                session.rollback()
                error = er.orig.pgerror.strip().replace('\"', '`').split('\n')
                raise HttpError(400, error)
            return jsonify(message_serializer(bb_message))

    def delete(self, bbm_id):
        with Session() as session:
            bb_message = session.query(BbMessage).get(bbm_id)
            if not bb_message:
                raise HttpError(404, 'Message not found')
            session.delete(bb_message)
            session.commit()
            return jsonify({
                'id': bb_message.id,
                'message': 'message deleted'
            })


app.add_url_rule(
    '/user/', view_func=UserView.as_view('create_user'),
    methods=['POST'])
app.add_url_rule(
    '/user/<int:user_id>', view_func=UserView.as_view('get_user'),
    methods=['GET'])
app.add_url_rule(
    '/user/<int:user_id>', view_func=UserView.as_view('delete_user'),
    methods=['DELETE'])

app.add_url_rule(
    '/bboard/', view_func=BbMessageView.as_view('create_message'),
    methods=['POST'])
app.add_url_rule(
    '/bboard/', view_func=BbMessageView.as_view('list_messages'),
    methods=['GET'])
app.add_url_rule(
    '/bboard/<int:bbm_id>', view_func=BbMessageView.as_view('get_message'),
    methods=['GET'])
app.add_url_rule(
    '/bboard/<int:bbm_id>', view_func=BbMessageView.as_view('delete_message'),
    methods=['DELETE'])

if __name__ == '__main__':
    app.run()
