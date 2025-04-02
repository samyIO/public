import json

from prompt import PromptCentral
from langchain.chat_models import init_chat_model

class AdaptiveRouter:

    def __init__(self):
        self.current_topic = None
        self.complexity_thresholds = {}
        self.evaluation_set = {}
    
    def load_result_data(self, file_path="data/result.json"):
        """
        Load and parse the result data from a JSON file.
        
        Args:
            file_path (str): Path to the JSON file
            
        Returns:
            dict: Parsed JSON data
        """

        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                print(f"Successfully loaded data from {file_path}")
                return data
        except FileNotFoundError:
            print(f"Error: File {file_path} not found")
            return None
        except json.JSONDecodeError:
            print(f"Error: File {file_path} contains invalid JSON")
            return None

    def load_questions(self, file_path, param="question"):
        """
        Load questions from a JSON file and return them as a list of strings.
        
        Args:
            file_path (str): Path to the JSON file
            
        Returns:
            list: List of questions as strings
        """
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                # Extract only the question text from each question object
                questions = [item[param] for item in data["questions"]]
                return questions
        except FileNotFoundError:
            print(f"Error: File {file_path} not found")
            return []
        except json.JSONDecodeError:
            print(f"Error: File {file_path} is not valid JSON")
            return []
        except KeyError:
            print("Error: Unexpected JSON structure")
            return []
        
    def save_test_results(self, test_set, filename="data/result.json"):
        try:
            formatted_data = {
                "test_results": [
                    {
                        "question": question,
                        "complexity": result["complexity"],
                        "individual_scores": result["scores"],
                        "mean_score": result["mean"],
                        "variance": result["variance"]
                    } for question, result in test_set.items()
                ],               
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(formatted_data, f, indent=2, ensure_ascii=False)
                
            print(f"Successfully saved results to {filename}")
            
        except Exception as e:
            print(f"Error saving results: {str(e)}")
            
    def run_data_creation(self, metric):
        questions = self.load_questions("data/data.json")
        complexity = self.load_questions("data/data.json", "complexity")
        test_set = {}
        n=0
        for q in questions:
            router_prompt = PromptCentral.get_router_prompt(q)
            # Higher temperature than the actual router to create response variance
            llm = init_chat_model("llama3.2:3b-instruct-q8_0", model_provider="ollama", temperature=0.6)
            scores = []
            # Run 5 times for each question
            for run in range(5):  
                score_generated = False
                attempts = 0
                
                while not score_generated and attempts < 2:
                    try:
                        score = llm.with_structured_output(metric).invoke(router_prompt)
                        scores.append(score.score)
                        print(f"Successfully generated score {run + 1}/5 for question: {q[:50]}...")
                        score_generated = True
                    except Exception:
                        print(f"Failed attempt {attempts + 1} for run {run + 1}")
                        attempts += 1
                        
                if not score_generated:
                    scores.append(None)
                    print(f"Failed to generate score for run {run + 1}")
            
            # Store all scores and calculate statistics
            test_set[q] = {
                "complexity": complexity[n],
                "scores": scores,
                "mean": sum([s for s in scores if s is not None]) / len([s for s in scores if s is not None]) if scores else None,
                "variance": sum((x - sum([s for s in scores if s is not None]) / len([s for s in scores if s is not None]))
                                ** 2 for x in [s for s in scores if s is not None]) / len([s for s in scores if s is not None]) 
                                if scores else None
            }
            n+=1
        
        print("Generated test set successfully")
        self.save_test_results(test_set)

    def calculate_threshold(self, result_data):
        """
        Calculate threshold from result data considering complexity categories.
        
        Args:
            result_data (dict): JSON data containing test results with complexity categories
            
        Returns:
            float: Calculated threshold
        """
        try:
            # Split questions by complexity
            simple_questions = [q for q in result_data["test_results"] if q["complexity"] == "easy"]
            complex_questions = [q for q in result_data["test_results"] if q["complexity"] == "hard"]
            
            # Get max score for simple questions
            max_simple_score = max(q["mean_score"] for q in simple_questions)
            print(f"Maximum simple score: {max_simple_score}")
            
            # Get min score for complex questions
            min_complex_score = min(q["mean_score"] for q in complex_questions)
            print(f"Minimum complex score: {min_complex_score}")
            
            # Calculate midpoint threshold
            gap = min_complex_score - max_simple_score
            midpoint_threshold = max_simple_score + (gap / 2)
            print(f"Midpoint threshold: {midpoint_threshold}")
            
            # so far midpoint threshold seems to be more appropriate then the following
            # final_threshold = midpoint_threshold + (max_simple_score - min_complex_score)
            # print(f"Final threshold: {final_threshold}")
            
            # Print questions close to threshold for verification
            print("\nQuestions closest to final threshold:")
            sorted_questions = sorted(result_data["test_results"], 
                                key=lambda x: abs(x["mean_score"] - midpoint_threshold))
            for q in sorted_questions[:3]:
                print(f"{q['question'][:50]}... ({q['complexity']}): {q['mean_score']}")
                
            return midpoint_threshold
            
        except KeyError as e:
            print(f"Error: Missing required key in data structure: {e}")
            return None
        except Exception as e:
            print(f"Error calculating threshold: {e}")
            return None
