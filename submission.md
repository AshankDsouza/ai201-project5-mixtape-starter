

## AI usage

## Instance 1

### Original Usage / Prompt: 
Add a test to test if a notification is created when a song is rated and when it is added to a playlist. the notification should be created for the person who shared the song.

### Result:
Produced two unit tests for the notification service. 

### Change / Learnt:
Learnt to how to write unit tests and got the boilerplate for testing the notification service. Everything seems inorder and no need for any change. 


## Instance 2

### Original Usage / Prompt: 
Help me figure out how to reproduce the # 3 issue in the app which pertains to duplicate songs returned from search query. 

### Result:
Gave me a plausible bug fix but with no steps to help me reproduce the bug and confirm if the bug was actually fixed. 

### Change / Learnt:
Some less common bugs are so esoteric that they cannot be reproduced by AI which trained on routine problems/tasks. 


## Code Structure (codebase map)


       App ./app.py  (Python Flask app, serves as the entry point of the API service ) 
        |
        |
        |
        V
      Routes  ./routes (REST APIs endpoints grouped together by entities)
        |
        |
        |
        V
     Services ./services (used by across routes in service of various functions)
        |
        |
        |
        V
     Models ./models (data layer; represents entities of the relational database)

        Ʌ
        |
        |
        |
     seed_data.py (inserts data into data layer - SQLAlchemy)


     ./tests (tests most services and functions)
    

The REST APIs are grouped in routes with other related REST APIs which pertain to the same REST API. 

# Known Issues 

Service: streak_service.py
Comment: "My listening streak keeps resetting"




