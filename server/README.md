# REST API for MOM Implementation

## Content Table
- [Developers](#developers)
- [Introduction](#introduction)
- [Project Structure](#project-structure)
- [Pre-requisites](#pre-requisites)
- [Setup Instructions](#setup-instructions)
- [Contribution](#contribution)
- [License](#license)
- [Contact](#contact)

## Developers

- Juan Felipe Restrepo Buitrago
- Kevin Quiroz González 
- Julian Estiven Valencia Bolaños
- Julian Agudelo Cifuentes

## Introduction

This is a REST API for the implementation of a MOM middleware for the Topics of Telematics course at EAFIT University. The API is designed to send, receive, suscribe and disconnect to messages from the MOM. The API is built using FastAPI and is designed to be easy to use and extend. 

## Project Structure

. \
├── app \
│   ├── auth \
│   │   ├── __init__.py # Authentication initialization. \
│   │   └── auth.py # Authentication handling file. \
│   ├── config \
│   │   ├── __init__.py # Configuration initialization. \
│   │   ├── database.py # Database handling file. \
│   │   ├── env.py # Environment variables handling file. \
│   │   └── limiter.py # Rate limiter handling file. \
│   ├── MOM \    
│   ├── dtos \
│   │   ├── __init__.py # Models initialization. \
│   │   ├── home_routing_dto.py # Database models file. \
│   ├── routes \     
│   │   └── routes.py # Routes file. \      
│   ├── utils \
│   │   ├── __init__.py # Utils initialization. \
│   │   ├── crud.py # CRUD handling file. \
│   │   └── utils.py # Utils handling file. \
│   ├── tests \
│   │   ├── routes \
│   │   │   ├── __init__.py # Tests initialization. \
│   │   │   └── test.py # Tests for home routes. \
│   │   └── __init__.py # Tests initialization. \
│   ├── __init__.py # API initialization. \
│   └── app.py # API routes and methods. \
├── .env.example # Environment variables example. \
├── README.md # Folder or Service README. \
├── Dockerfile # File to build the docker image. \
├── .dockerignore # Files to ignore when building the docker image. \
└── requirements.txt # Python dependencies. \

## Pre-requisites

- Python 3.8 or higher.
- Pip.
- Virtual Environment (Optional).
- Docker (Optional).

## Setup Instructions

1. **Environment Setup**: Make sure you have python 3.8 or higher installed. The python version used was the 3.12.4. 
2. **Directory Navigation**: navigate to the BACKEND directory `cd PATH/TO/PROJECT`.
3. **Virtual Environment Setup (Optional)**: setup a python venv if desired `python -m  venv .venv` and activate it `.venv\Scripts\activate` in Windows or `source .venv\bin\activate` in Linux or Mac.
4. **Dependencies Installation**: Execute `pip install -r requirements.txt` to install the needed dependencies. 
5. **Environment Variables**: Configure the environment variables as in the `.env.example` file.
6. **Execution**: Execute `uvicorn app.app:app --reload --port 8000` to initialize the API in the 8000 port. 

## Docker Image

### Image Build

The access is private, so you need to ask for the access to the docker image in the ghcr.io registry. `ghcr.io/juanfeliperestrepobuitrago/momtet/mom_server_api:latest`.

1. **Navigate to the Backend Directory**: navigate to the BACKEND directory `cd BACKEND`.
2. **Build an image**: Create or build the image of the backend API with your docker hub user `docker build -t "$USER/$PROJECT_NAME:$API_NAME.v$API_VERSION" . --no-cache --network host` or without it `docker build -t "$PROJECT_NAME:$API_NAME.v$API_VERSION" . --no-cache --network host`.
3. **Push the image (Optional)**: Push the docker image you just created to docker hub, is optional. `sudo docker push "$USER/$PROJECT_NAME:$API_NAME.v$API_VERSION"`.

### Image Usage

#### Docker Image

For using the docker image, you can run the following command:

```bash
docker run -d -p 8000:8000 --env-file .env ${USER}/mom_server_api:${TAG}
```

## Endpoints

The API provides several endpoint to apply or use different numerical methods for different purposes. The available endpoints are: 

- `GET /`: Verifies if the API is Up.

## Contribution

For contributing to this project, follow the instructions below:

1. **Fork the repository**: Make a fork of the repository and clone your fork on your local machine.
2. **Create a new branch**: Create a new branch with a name which gives an idea of the addition or correction to the project. 
3. **Make your changes**: Make your code changes and test them. 
4. **Make a pull request**: Finally, make a pull request to the original repository. 

## Contact

For any questions or issues, feel free to reach out to:
- Juan Felipe Restrepo Buitrago: [jfrestrepb@eafit.edu.co](jfrestrepb@eafit.edu.co)
- Kevin Quiroz González: [kquirozg@eafit.edu.co](mailto:kquirozg@eafit.edu.co)
- Julian Estiven Valencia Bolaños: [jevalencib@eafit.edu.co](mailto:jevalencib@eafit.edu.co)
- Julian Agudelo Cifuentes: [jagudeloc@eafit.edu.co](mailto:jagudeloc@eafit.edu.co)