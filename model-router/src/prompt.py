

class PromptCentral:


    @staticmethod
    def get_router_prompt(): 
        return f"""You are acting as a query complexity router. Please assign a float score
        to the user query, that indicates the level of complexity of it. Generate a score between
        0.1 (easy to answer) and 1.0 (require thinking). Generate your response in valid JSON
        format. Only return a realistic single float value, the score. Do not generate anything else. 
        """
    
    @staticmethod
    def embed_in_tags(user_input, tag_type):
        """
        Embeds user input into llama3 tags. 
        I wanted to demonstrate the intent behind prompt template classes like
        from langchain.
        
        Args:
            user_input (str): The text to be embedded in tags
            tag_type (str): The type of tag to use (e.g., 'begin_of_text', 'header_id', 'system')
        
        Returns:
            str: The user input properly embedded in the specified tags
        """

        # Define tag mappings
        tag_mappings = {
            # Role tags
            'system': ('<|start_header_id|>system<|end_header_id|>', '<|eot_id|>'),
            'user': ('<|start_header_id|>user<|end_header_id|>', '<|eot_id|>'),
            'assistant': ('<|start_header_id|>assistant<|end_header_id|>', '<|eot_id|>')
        }
        
        # Check if the tag type exists in the mappings
        if tag_type not in tag_mappings:
            raise ValueError(f"Unknown tag type: {tag_type}. Available tag types: {list(tag_mappings.keys())}")
        
        # Get start and end tags
        start_tag, end_tag = tag_mappings[tag_type]
        
        # Format the input with the appropriate tags
        formatted_text = f"{start_tag}\n{user_input}\n{end_tag}"
        
        return formatted_text
