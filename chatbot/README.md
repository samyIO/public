### Chat AI - Asynchronous Chatbot

Simple async Chat implementation that can run with common providers and models.
The app is implemented using Streamlit, Langchain and Asyncio.
It can be used to try out models fast, but is not suited for very long conversations.
Parameter and Prompt modification is also not supported in this version.

## Usage

### Prerequisites
- Running ollama endpoint
- Downloaded model 'llama3.2:3b-instruct-q8_0'

### Environment variables

Set by the flags: --model=${MODEL} --model_provider=${PROVIDER}
Another option is to use .env with "MODEL" and "MODEL_PROVIDER" set to the according values.
Default values are llama3.1:8 and ollama.

### Linux

### Create & activate a virtual environment
```bash
python3 -m venv venv
```
```bash
source venv/bin/activate
```

### Install the dependencies
```bash
pip install -r requirements.txt
```

### Run the program
```bash
streamlit run src/async_chatbot.py -- --model=${MODEL} --model_provider=${PROVIDER}
```

### Windows

### Create & activate a virtual environment
```cmd
python -m venv venv
```
```cmd
venv\Scripts\activate
```

### Install the dependencies
```cmd
pip install -r requirements.txt
```

### Run the program
```cmd
streamlit run src\async_chatbot.py -- --model=${MODEL} --model_provider=${PROVIDER}
```