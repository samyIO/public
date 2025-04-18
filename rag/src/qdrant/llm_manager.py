from langchain.chat_models import init_chat_model


class LlmManager:

    def create_context_from_retrieval(self, retrieval):
        result = ""
        for doc in retrieval:
            part = ""
            if result == "":
                print("added result reference")
                part += f"\n## Reference:{doc.metadata["source"]}\n"
            part += f"## Content: {doc.metadata["document"]}"
            result += part
        return result

    def generate_response(self, user_input, retrieval):
        context = self.create_context_from_retrieval(retrieval)
        print(f"Generated Context: {context}")
        prompt = self.generate_prompt(user_input, context)
        print(f"Generated Prompt: {prompt}")
        model = init_chat_model("llama3.1:8b", model_provider="ollama", temperature=0.3)
        response = model.invoke(prompt)
        print("Successfully generated response")
        return response.content

    def generate_prompt(self, user_input, context):
        return f"""You are a helpful assistant that answers the following 
        user query based on the given context.Generate a response that is 
        precisely based on the given context. Do not add any information. 
        If the user query cannot be answered based on the given context, 
        answer with 'I am sorry, I don't know'.

        Here is the user query you should answer:
            {user_input}


        Here is the given context:
            {context}
        

        Double check if your response would contain all informations of the context.
        It is important to preserve all given informations in your response.

        """
