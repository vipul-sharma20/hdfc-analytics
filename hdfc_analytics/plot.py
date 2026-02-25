import re

import pandas as pd
import plotly.express as px


def clean_amount(amount_str):
    """Clean amount string by extracting numeric value and removing reference numbers."""
    if pd.isna(amount_str) or amount_str == "":
        return 0

    # Convert to string if not already
    amount_str = str(amount_str)

    # Extract numeric part (remove any text in parentheses and non-numeric characters)
    # First, remove anything in parentheses
    amount_str = re.sub(r"\([^)]*\)", "", amount_str)

    # Extract numeric value (including negative signs and decimals)
    numeric_match = re.search(r"-?\d+\.?\d*", amount_str)
    if numeric_match:
        return float(numeric_match.group())

    return 0


def plot_df(categorized_df: pd.DataFrame, statement_type: str = "account") -> None:
    categorized_df = categorized_df.copy()

    if statement_type == "cc":
        raw_amounts = categorized_df["amount"].apply(clean_amount)

        categorized_df["amount"] = raw_amounts.apply(lambda a: abs(a) if a < 0 else 0)
    elif statement_type == "total":
        # Drop CC bill payment rows from the account statement to avoid double counting
        categorized_df = categorized_df[
            categorized_df["category"] != "CreditCard"
        ].copy()
        cc_raw = categorized_df["amount"].apply(clean_amount)
        categorized_df["amount"] = cc_raw.apply(lambda a: abs(a) if a < 0 else 0)
        categorized_df["amount"] = categorized_df["withdrawal_amount"].fillna(
            0
        ) + categorized_df["amount"].fillna(0)
    elif statement_type == "account":
        categorized_df["amount"] = categorized_df["withdrawal_amount"].fillna(0)

    if statement_type in ("cc", "total"):
        spend_df = categorized_df[categorized_df["amount"] > 0]

        spend_df.to_csv("expenses.csv", index=False)

        # Write untagged purchases sorted by amount for easy category tagging
        other_transactions = spend_df[spend_df["category"] == "Other"][
            ["date", "description", "amount"]
        ].sort_values("amount", ascending=False)
        other_transactions.to_csv("other_transactions.csv", index=False)

        categorized_df = spend_df

    # Summarize the data by category
    category_summary = categorized_df.groupby("category")["amount"].sum().reset_index()

    # Plot the pie chart using Plotly
    # Calculate the total amount
    total_amount = category_summary["amount"].sum()

    # Filter out categories contributing less than 1% of the total amount
    category_summary = category_summary[
        category_summary["amount"] >= 0.005 * total_amount
    ]
    # Plot the pie chart using Plotly
    fig = px.pie(
        category_summary,
        values="amount",
        names="category",
        title="Expenses by Category",
    )
    fig.update_traces(textinfo="percent+label")

    # Show the figure
    fig.show()
