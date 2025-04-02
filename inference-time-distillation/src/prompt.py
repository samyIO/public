

class PromptCentral:
    
    @staticmethod
    def get_chat_system_prompt():
        return """
        You are a thoughtful Assistant that creates mindful and helpful thoughts before responding. 
        Maintain professional presence and enhance it by describing your thought pattern in detail, 
        step by step. You can freely express your thought pattern step by step without 
        impacting the user experience, it helps you to explore topics and problems, so think extensively.
        """
    
    @staticmethod
    def get_thoughts_prompt():
        return """
        You are a thoughtful Assistant that creates mindful and helpful thoughts before responding. 
        Maintain professional presence and enhance it by describing your thought pattern in detail, 
        step by step. You can freely express your thought pattern step by step without 
        impacting the user experience, it helps you to explore topics and problems, so think extensively.
        do not generate a final response section, only the thought pattern.
        """
    
    @staticmethod
    def get_completion_prompt(excerpt):
        return f"""
        You are given an incomplete excerpt of an assistant response. The excerpt also contains the system prompt
        of the assistant that generated the thoughts and the input user query.

        Reflect on the assistant thoughts and review them critically step-by-step before completing the excerpt mindfully.

        Since he fails to generate the response based on his thought pattern, you have to generate the
        response as if you would be the assistant.

        generate your response between tags like this:

         <response> your response </response>


        Here is the excerpt:

        {excerpt}
        """

    @staticmethod
    def get_inject_system_prompt(query, thoughts):
        return f"""
        system:
        You are a thoughtful Assistant that creates mindful and helpful thoughts before responding. 
        Maintain professional presence and enhance it by describing your thought pattern in detail, 
        step by step. You can freely express your thought pattern step by step without 
        impacting the user experience, it helps you to explore topics and problems, so think extensively.

        user: 
        {query}
        
        assistant:
        <thinking>{thoughts}</thinking>

        <response>
       """
    
    def embed_in_tags(user_input, tag_type):
        """
        Embeds user input into appropriate tags based on the provided template.
        
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
        
        # Check if the tag type exists in our mappings
        if tag_type not in tag_mappings:
            raise ValueError(f"Unknown tag type: {tag_type}. Available tag types: {list(tag_mappings.keys())}")
        
        # Get start and end tags
        start_tag, end_tag = tag_mappings[tag_type]
        
        # Format the input with the appropriate tags
        formatted_text = f"{start_tag}\n{user_input}\n{end_tag}"
        
        return formatted_text
