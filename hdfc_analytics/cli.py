"""
hdfc-analytics: Analyze HDFC statements.

Usage:
  hdfc-analytics account --statement-csv=<statement-csv> --categories-config=<categories-config-toml> --column-config=<column-mapping-toml> [--llm=<llm-name>] [--llm-host=<llm-host-url>]
  hdfc-analytics cc --statement-dir=<statement-dir> --name=<name> --categories-config=<categories-config-toml> --column-config=<column-mapping-toml> [--password=<password>] [--passwords=<password1,password2,...>] [--llm=<llm-name>] [--llm-host=<llm-host-url>]
  hdfc-analytics total --statement-csv=<statement-csv> --statement-dir=<statement-dir> --name=<name> --categories-config=<categories-config-toml> --column-config=<column-mapping-toml> [--password=<password>] [--passwords=<password1,password2,...>] [--llm=<llm-name>] [--llm-host=<llm-host-url>]

Options:
  --statement-csv=<sattement-csv>               Path to bank account statement csv.
  --statement-dir=<sattement-dir>               Path to bank credit card statement directory.
  --name=<name>                                 Your name as written on the statement (applicable for CC analytics only)
  --password=<password>                         Password to open CC statement pdf (format is: first 5 letters of your first name followed by DDMM of your DOB)
  --passwords=<password1,password2,...>         Multiple comma-separated passwords to try for CC statement pdfs (useful when CC number changed)
  --categories-config=<categories-config-toml>  Path to file with categories configs.
  --column-config=<column-mapping-toml>         Path to file with column mapping configs.
  --llm=<llm-name>                              Flag to enable LLMs to tag transaction.
  --llm-host=<llm-host-url>                     LLM host. Applicable for Ollama or Huggingface served models.
"""

import csv
import glob
import io
import os
from typing import List

import hdfc_cc_parser
import pandas as pd
import toml
from docopt import docopt

from hdfc_analytics import __version__
from hdfc_analytics.plot import plot_df
from hdfc_analytics.statement import StatementCategorizer


def parse_pdf_with_passwords(pdf_file, name, passwords):
    """Try to parse a PDF with multiple passwords until one works."""
    for password in passwords:
        try:
            output = hdfc_cc_parser.parse_cc_statement(pdf_file, name, password)
            if output:  # If parsing was successful
                return output
        except Exception:
            continue  # Try next password
    
    # If we get here, none of the passwords worked
    raise Exception(f"Could not parse {pdf_file} with any of the provided passwords")


def get_passwords(args):
    """Extract passwords from CLI arguments."""
    if args["--passwords"]:
        passwords_arg = args["--passwords"]
        if isinstance(passwords_arg, list):
            # If docopt parsed it as a list, join and split again
            passwords_str = ",".join(passwords_arg)
        else:
            # If it's a string, use as is
            passwords_str = passwords_arg
        return [pwd.strip() for pwd in passwords_str.split(",")]
    elif args["--password"]:
        return [args["--password"]]
    else:
        raise ValueError("Either --password or --passwords must be provided")


def main():
    args = docopt(__doc__, version=__version__)

    if args["account"]:
        statement_csv = args["--statement-csv"]
        categories_config = args["--categories-config"]
        column_config = args["--column-config"]
        llm_host = args["--llm-host"]
        llm = args["--llm"]

        # Load the mappings
        column_mappings = load_column_mappings(column_config)

        df = pd.read_csv(statement_csv)

        # Assuming "df" is the DataFrame loaded from the CSV file
        # Apply the column mappings
        df = map_columns(df, column_mappings)

        categorizer = StatementCategorizer(categories_config, llm_host, llm)

        # Categorize the DataFrame
        categorized_df = categorizer.categorize_dataframe(df)

        plot_df(categorized_df)
    if args["total"]:
        # Load account transactions
        account_statement_csv = args["--statement-csv"]
        account_column_mappings = load_column_mappings(args["--column-config"])
        account_df = pd.read_csv(account_statement_csv)
        account_df = map_columns(account_df, account_column_mappings)

        # Load credit card transactions
        statement_dir = args["--statement-dir"]
        pdf_files = glob.glob(os.path.join(statement_dir, "*.PDF")) + glob.glob(os.path.join(statement_dir, "*.pdf"))
        passwords = get_passwords(args)
        cc_dfs = []
        for pdf_file in pdf_files:
            output = parse_pdf_with_passwords(pdf_file, args["--name"], passwords)
            rows = list(csv.reader(io.StringIO(output.replace('\x00', ''))))
            rows = [row for row in rows if row]
            if rows:
                df = pd.DataFrame(rows, columns=['date', 'description', 'rp', 'amount'])
                cc_dfs.append(df)
        combined_cc_df = pd.concat(cc_dfs, ignore_index=True)
        cc_column_mappings = load_column_mappings(args["--column-config"], statement_type="cc")
        combined_cc_df = map_columns(combined_cc_df, cc_column_mappings)

        # Combine account and credit card DataFrames
        combined_df = pd.concat([account_df, combined_cc_df], ignore_index=True)

        # Categorize the combined DataFrame
        categorizer = StatementCategorizer(args["--categories-config"], args["--llm-host"], args["--llm"])
        categorized_df = categorizer.categorize_dataframe(combined_df)

        # Plot the combined categorized DataFrame
        plot_df(categorized_df, statement_type="total")

    elif args["cc"]:
        statement_dir = args["--statement-dir"]
        categories_config = args["--categories-config"]
        column_config = args["--column-config"]
        llm_host = args["--llm-host"]
        llm = args["--llm"]

        pdf_files = glob.glob(os.path.join(statement_dir, "*.PDF")) + glob.glob(os.path.join(statement_dir, "*.pdf"))
        passwords = get_passwords(args)
        dfs = []
        for pdf_file in pdf_files:
            output = parse_pdf_with_passwords(pdf_file, args["--name"], passwords)
            rows = list(csv.reader(io.StringIO(output.replace('\x00', ''))))
            rows = [row for row in rows if row]
            if rows:
                df = pd.DataFrame(rows, columns=['date', 'description', 'rp', 'amount'])
                dfs.append(df)

        # Concatenate all the DataFrames
        combined_df = pd.concat(dfs, ignore_index=True)

        # Load the mappings
        column_mappings = load_column_mappings(column_config, statement_type="cc")

        # Apply the column mappings
        combined_df = map_columns(combined_df, column_mappings)

        categorizer = StatementCategorizer(categories_config, llm_host, llm)

        # Categorize the DataFrame
        categorized_df = categorizer.categorize_dataframe(combined_df)

        plot_df(categorized_df, statement_type="cc")


# Load column mappings from a TOML file
def load_column_mappings(
    config_path: str, statement_type: str = "account"
) -> List[str]:
    with open(config_path, "r") as config_file:
        config = toml.load(config_file)
    return config[statement_type]  # Assuming there"s only one mapping set, "default"


# Apply the column mappings to a DataFrame
def map_columns(df: pd.DataFrame, mappings: List[str]) -> pd.DataFrame:
    # Rename columns based on mappings
    column_renames = {value: key for key, value in mappings.items()}
    df = df.rename(columns=column_renames)
    return df
