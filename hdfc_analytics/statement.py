import json
import traceback
from typing import List

import pandas as pd
import toml
from litellm import completion


class StatementCategorizer:
    def __init__(self, config_path: str, llm_host: str, llm: bool = False):
        self.config_path = config_path
        self.llm = llm
        self.llm_host = llm_host
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

    def get_category_from_llm(self, text: str) -> str:
        try:
            category_keys = ", ".join(self.categories.keys())

            instructions = (
                f"tag the following transaction description to an expense category: '{text.lower()}'. "
                f"Below are the categories that you should prefer and if non of them feel appropriate, tag it based on your own logic. \n {category_keys}. "
                f"\n Below are some examples of the categories that exist right now. \n {json.dumps(self.categories)}"
                f"\n Give a response in json with `category` as key. It should only be a json response without markdown code block format "
            )
            messages = [
                {
                    "role": "user",
                    "content": instructions,
                },
            ]
            if self.llm_host:
                response = completion(
                    model=self.llm,
                    messages=messages,
                    api_base=self.llm_host,
                )
            else:
                response = completion(
                    model=self.llm,
                    messages=messages,
                )
            category_json = json.loads(response.choices[0].message.content)

            return category_json["category"]
        except Exception:
            traceback.print_exc()
            return "Other"  # Default category if no keywords match

    def categorize_transaction(self, description: str) -> str:
        for category, content in self.categories.items():
            if any(keyword in description.lower() for keyword in content["keywords"]):
                return category

        if self.llm:
            return self.get_category_from_llm(description)
        return "Other"  # Default category if no keywords match

    def categorize_dataframe(
        self, df: pd.DataFrame, description_column="description"
    ) -> pd.DataFrame:
        df = df[~df[description_column].str.contains('DUAL PYT', case=False, na=False)].copy()

        df["category"] = df[description_column].apply(self.categorize_transaction)

        return df
