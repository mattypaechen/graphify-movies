# Movie Rating And Discovery

Contributors: Kahlil Wassell, Matt Chen  
Stack: Neo4j (Graph Database), Python (Flask), JavaScript (Frontend)  

A graph powered web application for exploring movies, building watchlists, and discovering recommendations through social and rating data.  

---

## Project Overview

The app leverages Neo4j as the backend database and a Flask API to serve movie and user data to a lightweight web interface.  

### Core Features
1. User profiles – Create users with watchlists, ratings, and reviews.  
2. Social graph – Connect friends and explore "friends of friends" relationships.  
3. Movie discovery – Search by genres, actors, directors.  
4. Recommendations – Personalized suggestions using ratings and social connections.  
5. Interactive query GUI – A built-in web console for testing endpoints against the Neo4j graph.  

---

## Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/kahlilwassell/KW_MC_Initial_DB_Final_Project_Repo.git
```

### 2. Create A Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Neo4j
- Create a Neo4j database (local or AuraDB cloud).
- Update your connection details in config.ini:
```ini
[Flask]
version=1

[Neo4jdb]
scheme=neo4j
host_name=127.0.0.1
port=7687
user=neo4j
password=[your_password]
database=[your_db]
```

### 5. Run Flask Server
```bash
python api.py
```
By default, the API will be available at: `http://127.0.0.1:5000/api/v1`

### 6. Access the Query GUI
Navigate to: `http://127.0.0.1:5000/api/v1/ui`

## References
- [Neo4j Python Driver Documentation](https://neo4j.com/docs/python-manual/current/)  
- [Flask Documentation](https://flask.palletsprojects.com/)  
- [Cypher Query Language Reference](https://neo4j.com/developer/cypher/)  