import json

from flask import request, Response, url_for
from jsonschema import validate, ValidationError

import models
import decorators
from posts import app
from database import session

# JSON schema describing the structure of a post
post_schema = {
    "properties": {
        "title" : {"type" : "string"},
        "body": {"type": "string"}
    },
    "required": ["title", "body"]
}

@app.route("/api/posts", methods=["GET"])
@decorators.accept("application/json")
def posts_get():
	""" Get a list of posts from the database """
	#Get the querystring arguments
	title_like = request.args.get("title_like")
	body_like = request.args.get("body_like")

	#Get and filter posts from the database
	posts = session.query(models.Post)
	if title_like:
		posts = posts.filter(models.Post.title.contains(title_like))

	if body_like:
		posts = posts.filter(models.Post.body.contains(body_like))
	posts = posts.all()

	#Convert the posts to JSON and return a response
	data = json.dumps([post.as_dictionary() for post in posts])
	return Response(data, 200, mimetype="application/json")

@app.route("/api/posts", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def posts_post():
	"""Add a new post"""
	data = request.json

	#Check that the JSON supplied is valid
	#If not return a 422 Unprocessable Entity
	try:
		validate(data, post_schema)
	except ValidationError as error:
		data = {"message": error.message}
		return Response(json.dumps(data), 422, mimetype="application/json")

	#Add post to the database
	post=models.Post(title=data["title"], body=data["body"])
	session.add(post)
	session.commit()

	#Return a 201 created, containing the post as JSON and with
	#the Location header set to the location of the post

	data = json.dumps(post.as_dictionary())
	headers = {"Location": url_for("post_get", id=post.id)}
	return Response(data, 201, headers=headers,
		mimetype="application/json")


@app.route("/api/posts/<int:id>", methods=["GET"])
@decorators.accept("application/json") 
def post_get(id):
	""" Single post endpoint """
	#Get the post from the database
	post = session.query(models.Post).get(id)

	#Check if post exists; if not return 404 with error message

	if not post:
		message = "Could not find post with id {}".format(id)
		data = json.dumps({"message": message})
		return Response(data, 404, mimetype="application/json")

	#Return the post as a JSON
	data = json.dumps(post.as_dictionary())
	return Response(data, 200, mimetype="application/json")

@app.route("/api/posts/<int:id>", methods=["PUT"])
@decorators.accept("application/json")
@decorators.require("application/json")
def put_posts(id):
	""" Edit an existing post """

	data = request.json

	# Check JSON validity
	try:
		validate(data, post_schema)		
	except ValidationError as error:
		data = {"message": error.message}
		return Response(json.dumps(data), 422, mimetype="application/json")

	post = session.query(models.Post).filter_by(id=id).one()
	post.title = data["title"]
	post.body = data["body"]

	session.add(post)
	session.commit()

	#Return a 201 created, containing the post as JSON and with
	#the Location header set to the location of the post

	data = json.dumps(post.as_dictionary())
	headers = {"Location": url_for("post_get", id=post.id)}
	return Response(data, 201, headers=headers,
		mimetype="application/json")
