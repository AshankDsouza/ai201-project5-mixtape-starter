

## Code Structure (codebase map)


 App (Python Flask app) ./app.py
        |
        |
        |
        V
      Routes  ./routes
        |
        |
        |
        V
     Services ./services
        |
        |
        |
        V
    Models ./models (gets data from seed_data.py and SQLAlchemy)


The REST APIs are grouped in routes with other related REST APIs which pertain to the same REST API. 

# Knownn Issues 

Service: streak_service.py
Comment: "My listening streak keeps resetting"




