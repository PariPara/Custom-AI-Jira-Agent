# Custom-AI-Jira-Agent 
A chat interface to interact with Jira via an AI agent, with a custom AI tool to triage newly created Jira tickets.

The project makes use of LLMs served via Django (with PostgreSQL for vector storage) and Google Mesop for the UI. Services are provided in Docker to be run locally. 
The prompting strategy includes a CO-STAR system prompt and Chain-of-Thought (CoT) reasoning with few-shot prompting.

The inspiration for this project came from hosting a Jira ticket creation tool on a web application I had developed for internal users. I also added automated Jira ticket creation upon system errors. 
Users and system errors often create similar tickets, so I wanted to see if the reasoning capabilities of LLMs could be used to automatically triage tickets by linking related issues, creating user stories, acceptance criteria, and priority.

Additionally, giving users and product/managerial stakeholders easier access to interact directly with Jira in natural language without any technical competencies was an interesting prospect.

For more information, please read the medium article [here](https://medium.com/@ljamesdatascience/custom-ai-jira-agent-google-mesop-django-langchain-agent-co-star-chain-of-thought-cot-and-fb903468bff6). 

![Custom AI Jira agent demo](https://github.com/user-attachments/assets/5d8b0a22-6673-408b-80c8-c1d28a83380a)

## Examples 
![Example workflow](https://github.com/user-attachments/assets/88d1a2eb-e43d-46aa-8b7f-d9f4b5b85eb5)
![Jira result](https://github.com/user-attachments/assets/862c97e8-514b-4936-ae3b-0876f3d6a9db)
![Docker logs](https://github.com/user-attachments/assets/9d3e8777-d4ce-4414-98f6-6a8827246255)
![Tasks in progress](https://github.com/user-attachments/assets/7ecef653-3a08-4534-bbcf-05fb7f93d6cb)

## Architecture

The project consists of three main services:
- **Django REST API**: Handles AI model inference and Jira integration
- **Google Mesop**: Provides the chat interface UI
- **PostgreSQL with pgvector**: Stores conversation history and enables vector similarity search

## What is Google Mesop?
Mesop is a Python web framework (introduced in 2023) used at Google for rapid AI app development.
"Mesop provides a versatile range of 30 components, from low-level building blocks to high-level, AI-focused components. 
This flexibility lets you rapidly prototype ML apps or build custom UIs, all within a single framework that adapts to your project's use case." - [Mesop Homepage](https://google.github.io/mesop/)

## What is an AI Agent? 
"An artificial intelligence (AI) agent is a software program that can interact with its environment, collect data, and use the data to perform self-determined tasks to meet predetermined goals.
Humans set goals, but an AI agent independently chooses the best actions it needs to perform to achieve those goals." - [AWS Website](https://aws.amazon.com/what-is/ai-agents/)

## What is CO-STAR prompting?
"The CO-STAR framework, a brainchild of GovTech Singapore's Data Science & AI team, is a handy template for structuring prompts.
It considers all the key aspects that influence the effectiveness and relevance of an LLM's response, leading to more optimal responses." - [Sheila Teo's Medium Post](https://towardsdatascience.com/how-i-won-singapores-gpt-4-prompt-engineering-competition-34c195a93d41)

## What is Chain of Thought (CoT) prompting? 
Originally proposed in a Google paper; [Wei et al. (2022)](https://arxiv.org/pdf/2201.11903). Chain-of-Thought (CoT) prompting means to provide few-shot prompting examples of intermediate reasoning steps, which improves common-sense reasoning of the model output.

## What is Django? 
Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. 
It takes care of much of the hassle of web development, allowing you to focus on writing your app without needing to reinvent the wheel. - [Django Homepage](https://www.djangoproject.com/) 

## Requirements  
* Docker Desktop 
* Hugging Face API Token (get it from https://huggingface.co/settings/tokens)
* JIRA API Token 
* Jira Username 
* Jira Instance URL 

## Configuration

1. Edit `config/config.ini` with your credentials:
   ```ini
   [JIRA]
   JIRA_URL = your-jira-instance-url
   JIRA_EMAIL = your-jira-email
   JIRA_API_TOKEN = your-jira-api-token

   [HUGGINGFACE]
   HF_TOKEN = your-huggingface-token
   ```

2. The default model is `meta-llama/Llama-3.2-3B-Instruct`. You can change it in `django/api/utils/model_utils.py`

## Run Locally  

1. Add your credentials to the config file:
   ```
   ./config/config.ini
   ```

2. Build and run the Docker containers:
   ```bash
   docker compose up --build 
   ```

3. Access the Mesop UI in your browser:
   ```
   http://localhost:8080/
   ```

4. When finished, stop the containers:
   ```bash
   docker compose down
   ```

## Project Structure

```
├── config/              # Configuration files
├── django/              # Django REST API
│   ├── api/            # API endpoints and views
│   │   └── utils/      # Utility functions (Jira, model inference)
│   └── app/            # Django project settings
├── mesop/              # Mesop UI application
│   └── src/            # Source code and UI components
├── pgvector/           # PostgreSQL with vector extension
└── postman/            # API testing collection
```

## Features

- Natural language interaction with Jira
- Automatic ticket triaging and linking
- User story and acceptance criteria generation
- Priority assessment based on context
- Vector similarity search for related tickets
- REST API for integration with other services

## References 
* https://google.github.io/mesop/getting-started/quickstart/#starter-kit
* https://www.django-rest-framework.org/#example
* https://blog.logrocket.com/dockerizing-django-app/
* https://huggingface.co/docs/api-inference/index

## TODO 
* Add coding agent tool
* Implement caching for model responses
* Add support for multiple Jira projects
