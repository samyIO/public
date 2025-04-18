from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.chat_models import init_chat_model
from evaluation.response_processing import ResponseProcessor
from prompt import PromptCentral
import pandas as pd


def run_chat():

    llm = init_chat_model("llama3.1:8b", model_provider="ollama", temperature=0.7)

    distill = init_chat_model(
        "llama3.2:3b-instruct-q8_0", model_provider="ollama", temperature=0.7
    )
    # thoughts
    t_hist = []
    t_hist.append(SystemMessage(content=PromptCentral.get_thoughts_prompt()))
    # completion
    com_hist = []
    test_data = pd.read_csv("resources/benchmark/test_data.csv")
    r_processor = ResponseProcessor("resources/benchmark/test_data.csv")

    for i in range(len(test_data)):

        user_query = test_data["Question"][i]
        if user_query == "bye":
            return

        # generate thoughts
        t_hist.append(HumanMessage(content=user_query))
        thoughts = llm.invoke(t_hist)
        print("##### generated thoughts ##### \n\n")
        print(f"{thoughts.content}")
        t_hist.remove(HumanMessage(content=user_query))
        r_processor.process_thought(user_query, thoughts.content)
        # generate completion
        target_completion = PromptCentral.get_inject_system_prompt(
            user_query, thoughts.content
        )
        completion_prompt = PromptCentral.get_completion_prompt(target_completion)
        com_hist.append(HumanMessage(content=completion_prompt))
        response = distill.invoke(com_hist)
        print("##### generated completion ##### \n\n")
        print(f"{response.content}")
        r_processor.process_response(response.content)
        com_hist.append(AIMessage(content=response.content))

    r_processor.save_results(f"resources/benchmark/responses_{datetime.now()}.csv")


if __name__ == "__main__":
    run_chat()
