from flask import Flask, g, Blueprint, request, jsonify, render_template, current_app
import neo4jconn
import configparser

ver_bp = Blueprint("api", __name__)


def connect_db(config):
    if 'neo4j_conn' not in g:
        scheme = config["SCHEME"]
        host_name = config["HOST_NAME"]
        port = config["PORT"]
        g.neo4j_conn = neo4jconn.Neo4jDb(
            uri=f"{scheme}://{host_name}:{port}",
            user=config["USER"],
            password=config["PASSWORD"],
            database=config["DATABASE"]
        )
    return g.neo4j_conn


def create_app(config):
    app = Flask(__name__)
    app.config.from_mapping(config)

    app.register_blueprint(ver_bp, url_prefix="/api/v1")

    @app.teardown_appcontext
    def close_db(exception):
        """Close the Neo4j connection when the app context ends."""
        conn = g.pop('neo4j_conn', None)
        if conn is not None:
            conn.close()

    return app

@ver_bp.route("/movie/")
def invalid_path(): # Ideally would want to implement form validation, but simple hack to sidestep frontend work .
    return {"message": "Invalid path. You probably meant to hit the /movie/title. If you are accessing through the GUI please input a title."}

# checked and tested
@ver_bp.route("/movie/<title>")
def get_movie(title):
    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.find_movie(title)
    return result

# checked and tested
@ver_bp.route("/movie/new", methods=["POST"])
def set_movie():
    data = request.get_json()
    movie_id = data.get("movieId")
    title = data.get("title")
    year = data.get("releaseYear")

    if not all([movie_id, title, year]):
        return {"message": "The movie_id, title, and year must not be empty."}

    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)

    result = driver.add_movie(movie_id, title, year)
    return result

# checked and tested
@ver_bp.route("/movie/genres/new", methods=["POST"])
def set_movie_genres():
    data = request.get_json()
    title = data.get("title")
    genres = data.get("genres", [])

    if len(genres) == 0:
        return {"message": "Include more than one genre."}

    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)

    result = driver.add_genres_to_movie(title, genres)
    return result

# checked and tested
@ver_bp.route("/movies")
def get_movies():
    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.find_movies()
    return result

@ver_bp.route("/movie/<title>/reviews")
def get_movie_reviews(title):
    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.find_movie_reviews(title)
    return result

# checked and tested
@ver_bp.route("/movies/director/<fullname>")
def get_movies_by_director(fullname):
    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.find_movies_by_director(fullname)
    return result

# checked and tested
@ver_bp.route("/movies/actor/<fullname>")
def get_movies_by_actor(fullname):
    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.find_movies_by_actor(fullname)
    return result

# checked and tested
@ver_bp.route("/movies/genre/<genre>")
def get_movies_by_genre(genre):
    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.find_movies_by_genre(genre)
    return result

# checked and tested
@ver_bp.route("/user/<username>")
def get_user(username):
    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.find_user(username)
    return result

# checked and tested
@ver_bp.route("/user/<username>/watchlist")
def get_watchlist(username):
    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.find_watchlist(username)
    return result

# checked and tested
@ver_bp.route("/user/<username>/reviews")
def get_reviews(username):
    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.find_reviews_by_user(username)
    return result

# checked and tested
@ver_bp.route("/user/<username>/friends")
def get_friends(username):
    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.find_friends(username)
    return result

# checked
@ver_bp.route("/friends/new", methods=["POST"])
def set_friends():
    data = request.get_json()
    u1 = data.get("username1")
    u2 = data.get("username2")
    if not all([u1, u2]):
        return {"message": "Both username1 and username2 is required to create a friendship"}

    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.connect_friends(u1, u2)
    return result

# Advanced queries
# checked
@ver_bp.route("/user/<username>/friends/network/<degree>")
def get_friends_network(username, degree):
    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.find_friends_network(username, degree)
    return result

# checked
@ver_bp.route("/user/<username>/movies/hottest")
def get_hottest_movies(username):
    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.find_hottest_movies(username)
    return result

# checked
@ver_bp.route("/user/<username>/movies/recommendations")
def get_movie_recommendations(username):
    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.find_movie_recommendations(username)
    return result

# checked
@ver_bp.route("/reviews/<keyword>")
def get_reviews_with_keyword(keyword):
    driver = g.neo4j_conn if 'neo4j_conn' in g else connect_db(current_app.config)
    result = driver.find_reviews_with_keyword(keyword)
    return result

@ver_bp.route("/ui")
def ui_console():
    return render_template(
        "query_ui.html",
        base_url="/api/v1",
        endpoints=[
            "GET /movie/:title",
            "GET /movies",
            "GET /movie/:title/reviews",
            "GET /movies/director/:fullname",
            "GET /movies/actor/:fullname",
            "GET /movies/genre/:genre",
            "GET /user/:username",
            "GET /user/:username/watchlist",
            "GET /user/:username/reviews",
            "GET /user/:username/friends",
            "GET /user/:username/friends/network/:degree",
            "GET /user/:username/movies/hottest",
            "GET /user/:username/movies/recommendations",
            "GET /reviews/:keyword",
            "POST /movie/new",
            "POST /movie/genres/new",
            "POST /friends/new",
        ],
    )
