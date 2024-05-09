import traceback
import json
from typing import List

import pandas as pd
import toml
import ollama


class StatementCategorizer:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.load_categories()

    def load_categories(self) -> None:
        with open(self.config_path, "r") as config_file:
            self.categories = toml.load(config_file)

    def add_category(self, category: str, keywords: List[str]) -> None:
        self.categories[category] = {"keywords": keywords}
        self.save_categories()

    def save_categories(self) -> None:
        with open(self.config_path, "w") as config_file:
            toml.dump(self.categories, config_file)

    def categorize_transaction(self, description: str) -> str:
        for category, content in self.categories.items():
            if any(keyword in description.lower() for keyword in content["keywords"]):
                return category
        try:
            response = ollama.chat(model="mistral", messages=[
              {
                "role": "user",
                "content": f"tag the following transaction description to an expense category: '{description.lower()}'. Give a response in json with category",
              },
            ])
            category_json = response["message"]["content"]
            print(category_json)
            category = json.loads(category_json)

            return category["category"]
        except Exception as e:
            traceback.print_exc()
            return "Other"  # Default category if no keywords match
        return "Other"

    def categorize_dataframe(self, df: pd.DataFrame, description_column="description") -> pd.DataFrame:
        df["category"] = df[description_column].apply(self.categorize_transaction)

        # Store other transactions to analyze and add more keywords to categories.toml
        with open("other_transactions.csv", "w") as fp:
            other_transactions = df[df["category"] == "Other"]
            fp.write(other_transactions.to_csv())

        return df
