from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
import json

from data_eval import AdaptiveRouter
from prompt import PromptCentral


class Score(BaseModel):
    "Complexity score to assign to query"

    score: float = Field(description="The final complexity score")


def prepare_threshhold():
    router = AdaptiveRouter()
    # router.run_data_creation(Score)
    result_data = router.load_result_data("data/result.json")
    threshold = router.calculate_threshold(result_data)
    print(f"final threshold: {threshold}")
    return threshold


def run_router():
    threshold = prepare_threshhold()

    while True:

        parsed_object = ""
        i = 0

        while i < 2 and parsed_object == "":

            llm = init_chat_model(
                "llama3.2:3b-instruct-q8_0", model_provider="ollama", temperature=0
            )

            # Try 3 times to increase error tolerance
            if i == 2:
                break

            try:
                user_query = input("Enter a query: ")

                if user_query == "bye":
                    print("See you next time")
                    return
                # Prepare llama tag-embedded prompt
                bare_prompt = PromptCentral.get_router_prompt()
                tagged_prompt = PromptCentral.embed_in_tags(bare_prompt, "system")
                router_prompt = tagged_prompt + PromptCentral.embed_in_tags(
                    user_query, "user"
                )
                print(f"router prompt is: {router_prompt}")

                score = llm.with_structured_output(Score).invoke(router_prompt)
                parsed_object = json.dumps({"score": score.score})
                print(f"successfully generated router score: {score.score}")

            except Exception:
                print("failed to generate router score retrying..")
                i += 1

        """
        A major challenge is the conversation history management due the mechanics
        of model distillation. If routing should be used in extensive relational tasks,
        using the same conversation history for both model routes would lead to a 
        potential reverse distillation, for the run time period.
        The responses of the smaller model impact the performance cap of the bigger 
        model due to context attention. For categorization applications this doesn't 
        matter since the models would amost never share the same context
        """

        if parsed_object:
            compare_t = json.loads(parsed_object)
            if float(compare_t["score"]) < threshold:
                print("Query assinged to smaller model")
            else:
                print("Query assigned to bigger model")


if __name__ == "__main__":
    run_router()
