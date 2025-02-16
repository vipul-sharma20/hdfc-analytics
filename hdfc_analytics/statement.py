import json
import traceback
from typing import List

import pandas as pd
import toml
from litellm import completion


class StatementCategorizer:
    def __init__(self, config_path: str, use_llm: bool = False):
        self.config_path = config_path
        self.use_llm = use_llm
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

        if self.use_llm:
            try:
                category_keys = ", ".join(self.categories.keys())

                instructions = (
                    f"tag the following transaction description to an expense category: '{description.lower()}'. "
                    f"Below are the categories that you should prefer and if non of them feel appropriate, tag it based on your own logic. \n {category_keys}. "
                    f"\n Below are some examples of the categories that exist right now. \n {json.dumps(self.categories)}"
                    f"\n Give a response in json with `category` as key. It should only be a json response. "
                )
                response = completion(
                    model="ollama/llama3.2",
                    messages=[
                        {
                            "role": "user",
                            "content": instructions,
                        },
                    ],
                    api_base="http://localhost:11434",
                )
                category_json = json.loads(response.choices[0].message.content)

                return category_json["category"]
            except Exception:
                return "Other"  # Default category if no keywords match

        return "Other"  # Default category if no keywords match

    def categorize_dataframe(
        self, df: pd.DataFrame, description_column="description"
    ) -> pd.DataFrame:
        df["category"] = df[description_column].apply(self.categorize_transaction)

        # Store other transactions to analyze and add more keywords to categories.toml
        with open("other_transactions.csv", "w") as fp:
            other_transactions = df[df["category"] == "Other"]
            fp.write(other_transactions.to_csv())

        return df
