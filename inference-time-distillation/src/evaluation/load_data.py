from datasets import load_dataset
import pandas as pd

# Load the dataset from Hugging Face
dataset = load_dataset("FreedomIntelligence/medical-o1-reasoning-SFT", "en")

# Access the first split
first_split = list(dataset.keys())[0]
data = dataset[first_split]

# Convert the first 30 rows to a pandas DataFrame
df = pd.DataFrame(data[:30])

# Save the first 30 rows as CSV
df.to_csv("test_data.csv", index=False)

print(f"Successfully saved the first 30 rows of the dataset to test_data.csv")
