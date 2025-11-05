import logging
import re

from neo4j import GraphDatabase, RoutingControl
from neo4j.exceptions import DriverError, Neo4jError, ResultNotSingleError, GqlError


class Neo4jDb:

    def __init__(self, uri, user, password, database=None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def find_movie(self, title):
        with self.driver.session():
            movie = self._find_and_return_movie(title)
        return movie

    def _find_and_return_movie(self, title):
        query = (
            """
            MATCH (m:movie {title: $title})
            OPTIONAL MATCH (m)<-[:directs]-(d:director)
            OPTIONAL MATCH (m)<-[:actsIn]-(a:actor)
            RETURN
            m.title AS title,
            m.releaseYear AS releaseYear,
            collect(DISTINCT d.name) AS directors,
            collect(DISTINCT a.name) AS actors
            """
        )
        try:
            records = self.driver.execute_query(
                query, title=title,
                database_=self.database, routing=RoutingControl.READ,
                result_transformer_=lambda r: r.single(strict=True).data("title", "releaseYear", "directors", "actors")
            )
            return records
        except (ResultNotSingleError) as exception:
            print(exception)
            return {"message": "No such movie title exist."}
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def add_movie(self, movie_id, title, year):
        with self.driver.session():
            movie = self._add_and_return_movie(movie_id, title, year)
        return movie

    def _add_and_return_movie(self, movie_id, title, year):
        query = (
            "MERGE (m:movie {movieId:$movieId, title:$title, releaseYear:$releaseYear}) "
            "RETURN m AS movie"
        )
        try:
            records = self.driver.execute_query(
                query, title=title, movieId=movie_id, releaseYear=year,
                database_=self.database, routing=RoutingControl.READ,
                result_transformer_=lambda r: r.single(strict=True).data("movie")
            )
            return records
        except (GqlError) as exception:
            return {"message": f"{exception.message}"}
        except (ResultNotSingleError) as exception:
            return {"message": "Movie was unable to be added. Try again."}
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def add_genres_to_movie(self, title, genres):
        with self.driver.session():
            result = self._add_and_return_genres_to_movie(title, genres)
        return result

    def _add_and_return_genres_to_movie(self, title, genres):
        query = (
            "MATCH (m:movie {title:$title}) "
            "UNWIND $genres AS genreName "
            "MATCH (g:genre {name:genreName}) "
            "MERGE (m) -[r:inGenre]-> (g) "
            "RETURN m AS movie, collect(g) AS genres"
        )
        try:
            records = self.driver.execute_query(
                query, title=title, genres=genres, 
                database_=self.database, routing=RoutingControl.READ,
                result_transformer_=lambda r: r.data("movie", "genres")
            )
            return records
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def find_movies(self):
        with self.driver.session():
            movies = self._find_and_return_movies()
        return movies

    def _find_and_return_movies(self):
        query = (
            "MATCH (m:movie) "
            "OPTIONAL MATCH (m)<-[:directs]-(d:director) "
            "OPTIONAL MATCH (m)<-[:actsIn]-(a:actor) "
            "WITH m, collect(DISTINCT a.name) AS actors, collect(DISTINCT d.name) AS directors "
            "RETURN collect({title:m.title, releaseYear:m.releaseYear, "
            " directors:directors, actors:actors}) AS movies"
        )
        try:
            records = self.driver.execute_query(
                query,
                database_=self.database, routing=RoutingControl.READ,
                result_transformer_=lambda r: r.data("movies")
            )
            return records
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def find_movie_reviews(self, title):
        with self.driver.session():
            reviews = self._find_and_return_movie_reviews(title)
        return reviews

    def _find_and_return_movie_reviews(self, title):
        query = (
            "MATCH (m:movie {title:$title})-[:hasReview]->(r:review)<-[:gaveReview]-(u:user) "
            "RETURN collect({ review:r.text, rating:r.rating, user:u.userName }) AS reviews"
        )
        try:
            records = self.driver.execute_query(
                query, title=title,
                database_=self.database, routing=RoutingControl.READ,
                result_transformer_=lambda r: r.data("reviews")
            )
            return records
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def find_movies_by_director(self, director_name):
        with self.driver.session():
            movies = self._find_and_return_movies_by_director(director_name)
        return movies

    def _find_and_return_movies_by_director(self, director_name):
        query = (
            "MATCH (m:movie)<-[:directs]-(d:director {name:$director_name}) "
            "RETURN collect({ title:m.title, releaseYear:m.releaseYear }) AS movies"
        )
        try:
            records = self.driver.execute_query(
                query, director_name=director_name,
                database_=self.database, routing=RoutingControl.READ,
                result_transformer_=lambda r: r.data("movies")
            )
            return records
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def find_movies_by_actor(self, actor_name):
        with self.driver.session():
            movies = self._find_and_return_movies_by_actor(actor_name)
        return movies

    def _find_and_return_movies_by_actor(self, actor_name):
        query = (
            "MATCH (m:movie)<-[:actsIn]-(a:actor {name:$actor_name}) "
            "RETURN collect({ title:m.title, year:m.releaseYear}) AS movies"
        )
        try:
            records = self.driver.execute_query(
                query, actor_name=actor_name,
                database_=self.database, routing=RoutingControl.READ,
                result_transformer_=lambda r: r.data("movies")
            )
            return records
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def find_movies_by_genre(self, genre):
        with self.driver.session():
            movies = self._find_and_return_movies_by_genre(genre)
        return movies

    def _find_and_return_movies_by_genre(self, genre_name):
        query = (
            "MATCH (m:movie)-[:inGenre]->(g:genre {name:$genre_name}) "
            "RETURN collect({ title:m.title, releaseYear:m.releaseYear }) AS movies"
        )
        try:
            records = self.driver.execute_query(
                query, genre_name=genre_name,
                database_=self.database, routing=RoutingControl.READ,
                result_transformer_=lambda r: r.data("movies")
            )
            return records
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def find_user(self, username):
        with self.driver.session():
            user = self._find_and_return_user(username)
        return user

    def _find_and_return_user(self, username):
        query = (
            "MATCH (u:user {userName:$username}) "
            "RETURN u.name AS name, u.userName AS userName, u.email AS email "
        )
        try:
            records = self.driver.execute_query(
                query, username=username,
                database_=self.database, routing=RoutingControl.READ,
                result_transformer_=lambda r: r.single(strict=True).data("name", "userName", "email")
            )
            return records
        except (ResultNotSingleError) as exception:
            return {"message": "No such user exist."}
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def find_watchlist(self, username):
        with self.driver.session() as session:
            watchlist = self._find_and_return_watchlist(username)
        return watchlist

    def _find_and_return_watchlist(self, username):
        query = (
            "MATCH (u:user {userName: $username }) -[r:wantsToWatch]-> (m:movie) "
            "RETURN m AS movie, r.addedOn as added_on"
        )
        try:
            records = self.driver.execute_query(
                query, username=username,
                database_=self.database, routing_=RoutingControl.READ,
                result_transformer_=lambda r: r.data("movie", "added_on")
            )
            return records
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def add_watchlist(self, username):
        pass

    def add_to_watchlist(self, username):
        pass

    def find_reviews_by_user(self, username):
        with self.driver.session():
            reviews = self._find_and_return_reviews_by_user(username)
        return reviews

    def _find_and_return_reviews_by_user(self, username):
        query = (
            "MATCH (u:user {userName: $username}) -[r:gaveReview]-> (review:review) <-[:hasReview]- (m:movie) "
            "ORDER BY review.reviewId "
            "RETURN m as movie, review, r.reviewDate as review_date"
        )
        try:
            records = self.driver.execute_query(
                query, username=username,
                database_=self.database, routing_=RoutingControl.READ,
                result_transformer_=lambda r: r.data("movie", "review", "review_date")
            )
            return records
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def add_reviews(self, username):
        pass

    def find_friends(self, username):
        friends = self._find_and_return_friends(username)
        for friend in friends:
            print(f"{username} is friends with {friend}")
        return friends

    def _find_and_return_friends(self, username):
        query = (
            "MATCH (:user {userName:$username})-[:isFriendsWith]->(u:user) "
            "RETURN u.name AS name, u.email AS email"
        )
        try:
            records = self.driver.execute_query(
                query, username=username,
                database_=self.database, routing_=RoutingControl.READ,
                result_transformer_=lambda r: r.data("name", "email")
            )
            return records
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def connect_friends(self, username1, username2):
        print(f"u1: {username1} u2: {username2}")
        with self.driver.session():
            # Write transactions allow the driver to handle retries and
            # transient errors
            result = self._create_and_return_friendship(
                username1, username2
            )
        return result

    def _create_and_return_friendship(self, username1, username2):
        print(f"Inside connection fn -> u1:{username1}, u2:{username2}")
        query = (
            "MATCH (u1:user { userName: $username1}) "
            "MATCH (u2:user { userName: $username2}) "
            "MERGE (u1)-[:isFriendsWith]->(u2) "
            "MERGE (u2)-[:isFriendsWith]->(u1) "
            "RETURN u1.name AS user1name, u2.name AS user2name"
        )
        try:
            record = self.driver.execute_query(
                query, username1=username1, username2=username2,
                database_=self.database,
                result_transformer_=lambda r: r.single(strict=True).data("user1name", "user2name")
            )
            return record
        except (ResultNotSingleError) as exception:
            return {"message": "Unable to create friendship between users. Please try again."}
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    # Advance Queries
    def find_friends_network(self, username, degree):
        with self.driver.session():
            result = self._create_and_return_friends_network(username, degree)
            print(f"network: {result}")
            return result

    def _create_and_return_friends_network(self, username, degree):
        query = f'''
            MATCH path=(u:user {{userName: $username}}) -[:isFriendsWith*1..{degree}]- (other:user)
            WHERE u <> other
            RETURN DISTINCT other AS person, length(path) AS degree
            ORDER BY degree, person.name
            '''
        try:
            record = self.driver.execute_query(
                query, username=username,
                database_=self.database,
                result_transformer_=lambda r: r.data("person", "degree")
            )
            return record
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def find_hottest_movies(self, username):
        with self.driver.session():
            recommendations = self._find_and_return_hottest_movies(username)
        return recommendations

    def _find_and_return_hottest_movies(self, username):
        query = (
            "MATCH (u:user {userName: $username })-[:isFriendsWith*1..10]-(friend:user) "
            "WHERE u <> friend "
            "MATCH (friend)-[:wantsToWatch]->(m:movie) "
            "WITH m, COUNT(DISTINCT friend) AS hotness "
            "ORDER BY hotness DESC "
            "LIMIT 10 "
            "RETURN m AS top_movie, hotness;"
        )
        try:
            records = self.driver.execute_query(
                query, username=username,
                database_=self.database, routing=RoutingControl.READ,
                result_transformer_=lambda r: r.data("top_movie", "hotness")
            )
            return records
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def find_movie_recommendations(self, username):
        with self.driver.session():
            recommendations = self._find_and_return_movie_recommendations(username)
        return recommendations

    def _find_and_return_movie_recommendations(self, username):
        query = (
            """
            MATCH friendshipPath = (u:user {userName: $username})-[:isFriendsWith*1..2]-(other:user)
            MATCH (other)-[:wantsToWatch]->(m:movie)
            WHERE u <> other
            RETURN DISTINCT other AS person, length(friendshipPath) AS degree, m AS recommendation
            ORDER BY recommendation.name, person, degree;
            """
        )
        try:
            records = self.driver.execute_query(
                query, username=username,
                database_=self.database, routing=RoutingControl.READ,
                result_transformer_=lambda r: r.data("recommendation", "person", "degree")
            )
            return records
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def find_reviews_with_keyword(self, keyword):
        with self.driver.session():
            reviews = self._find_and_return_reviews_with_keyword(keyword)
        return reviews

    def _find_and_return_reviews_with_keyword(self, keyword):
        pattern = r"^\w+$"
        if not re.match(pattern, keyword):
            err_msg = "Keyword must be one word."
            logging.error(err_msg)
            return {"message": err_msg}
        query = (
            "MATCH (m:movie)-[:hasReview]->(r:review) "
            "WHERE toLower(r.text) CONTAINS toLower($keyword) "
            "RETURN DISTINCT m.title AS movie, collect(r.text) AS review "
            "ORDER BY movie;"
        )
        try:
            records = self.driver.execute_query(
                query, keyword=keyword,
                database_=self.database, routing=RoutingControl.READ,
                result_transformer_=lambda r: r.data("movie", "review")
            )
            return records
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise
        pass
