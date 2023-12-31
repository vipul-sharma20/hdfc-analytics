"""
hdfc-analytics: Analyze HDFC statements.

Usage:
  hdfc-analytics account --statement-csv=<statement-csv> --categories-config=<categories-config-toml> --column-config=<column-mapping-toml>

Options:
  --statement-csv=<sattement-csv>               Path to bank account / credit card statement csv.
  --categories-config=<categories-config-toml>  Path to file with categories configs.
  --column-config=<column-mapping-toml>         Path to file with column mapping configs.
"""
import io
from typing import List

import toml
import pandas as pd
from docopt import docopt

from hdfc_analytics.plot import plot_df
from hdfc_analytics.statement import StatementCategorizer
from hdfc_analytics import __version__


def main():
    args = docopt(__doc__, version=__version__)

    if args["account"]:
        statement_csv = args["--statement-csv"]
        categories_config = args["--categories-config"]
        column_config = args["--column-config"]

        # Load the mappings
        column_mappings = load_column_mappings(column_config)

        df = pd.read_csv(statement_csv)

        # Assuming "df" is the DataFrame loaded from the CSV file
        # Apply the column mappings
        df = map_columns(df, column_mappings)

        categorizer = StatementCategorizer(categories_config)

        # Categorize the DataFrame
        categorized_df = categorizer.categorize_dataframe(df)

        plot_df(categorized_df)


# Load column mappings from a TOML file
def load_column_mappings(config_path: str) -> List[str]:
    with open(config_path, "r") as config_file:
        config = toml.load(config_file)
    return config["default"]  # Assuming there"s only one mapping set, "default"


# Apply the column mappings to a DataFrame
def map_columns(df: pd.DataFrame, mappings: List[str]) -> pd.DataFrame:
    # Rename columns based on mappings
    column_renames = {value: key for key, value in mappings.items()}
    df = df.rename(columns=column_renames)
    return df

