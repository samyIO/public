from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.chat_models import init_chat_model
from prompt import PromptCentral


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

    while True:
        user_query = input()
        if user_query == "bye":
            return

        # generate thoughts
        t_hist.append(HumanMessage(content=user_query))
        thoughts = llm.invoke(t_hist)
        print("##### generated thoughts ##### \n\n")
        print(f"{thoughts.content}")
        t_hist.remove(HumanMessage(content=user_query))

        # generate completion
        target_completion = PromptCentral.get_inject_system_prompt(
            user_query, thoughts.content
        )
        completion_prompt = PromptCentral.get_completion_prompt(target_completion)
        com_hist.append(HumanMessage(content=completion_prompt))
        response = distill.invoke(com_hist)
        print("##### generated completion ##### \n\n")
        print(f"{response.content}")

        com_hist.append(AIMessage(content=response.content))


if __name__ == "__main__":
    run_chat()
