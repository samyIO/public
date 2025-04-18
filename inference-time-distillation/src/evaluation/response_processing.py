import pandas as pd
import re


class ResponseProcessor:
    def __init__(self, csv_file_path):
        """
        Initialize the processor with the path to the test data CSV.

        Args:
            csv_file_path (str): Path to the CSV file containing the questions
        """

        self.data = pd.read_csv(csv_file_path)
        self.processed_data = {
            "Question": [],
            "Complex_CoT": [],
            "Response": [],
            "Tags_Missing": [],
        }
        self.missing_tags_count = 0
        self.current_question = None
        self.current_thought = None

    def process_thought(self, question, thought):
        """
        This function stores the current question and thought for later use.
        Args:
            question (str): The question that was asked
            thought (str): The generated chain-of-thought reasoning
        """

        # Store the current question and thought
        self.current_question = question
        self.current_thought = thought.strip()
        print(f"Processed thought for question: {question[:50]}...")

    def process_response(self, response):
        """
        This function combines the stored question and thought
        with the new response.

        Args:
            response (str): The final response generated by the LLM
        Returns:
            bool: True if the response was processed successfully,
            False otherwise
        """

        if self.current_question is None or self.current_thought is None:
            print(
                "Error: No current question or thought found. "
                "Call process_thought first."
            )
            return False

        # Extract only the content between <response> tags if it exists
        response_pattern = re.compile(r"<response>([\s\S]*?)</response>", re.DOTALL)
        response_match = response_pattern.search(response)

        # Check if tags are missing
        tags_missing = False

        if response_match:
            # If <response> tags are found, extract the content between them
            final_response = response_match.group(1).strip()
            tags_missing = False
        else:
            # If no <response> tags, use the whole response as is
            final_response = response.strip()
            tags_missing = True
            self.missing_tags_count += 1
            print(
                f"Warning: Missing <response> tags in response for question: "
                f"{self.current_question[:50]}..."
            )

        # Store all the data
        self.processed_data["Question"].append(self.current_question)
        self.processed_data["Complex_CoT"].append(self.current_thought)
        self.processed_data["Response"].append(final_response)
        self.processed_data["Tags_Missing"].append(tags_missing)

        # Reset current values to prevent accidental reuse
        question = self.current_question
        self.current_question = None
        self.current_thought = None

        print(f"Processed complete response for question: {question[:50]}...")
        return True

    def save_results(self, output_file_path):
        """
        Save the processed data to a CSV file.

        Args:
            output_file_path (str): Path where the output CSV should be saved
        Returns:
            pd.DataFrame: The processed data as a DataFrame
        """

        result_df = pd.DataFrame(self.processed_data)
        result_df.to_csv(output_file_path, index=False)

        # Statistics about the processed data
        total_count = len(result_df)
        print(f"Saved {total_count} processed responses to {output_file_path}")
        print(
            f"Number of responses missing <response> tags: {self.missing_tags_count}"
            f"({(self.missing_tags_count/total_count)*100:.2f}%)"
        )

        # Append tag statistics to filename

        base_name = output_file_path.rsplit(".", 1)
        stats_file_path = f"{base_name}_stats.txt"

        with open(stats_file_path, "w") as f:
            f.write(f"Total responses: {total_count}\n")
            f.write(
                f"Responses missing tags: {self.missing_tags_count}"
                f"({(self.missing_tags_count/total_count)*100:.2f}%)\n"
            )
            f.write(
                f"Responses with correct tags: {total_count - self.missing_tags_count}"
                f"({((total_count - self.missing_tags_count)/total_count)*100:.2f}%)\n"
            )

        print(f"Tag statistics saved to {stats_file_path}")

        return result_df
