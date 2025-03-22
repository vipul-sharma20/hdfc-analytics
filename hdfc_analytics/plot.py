import pandas as pd
import plotly.express as px


def plot_df(categorized_df: pd.DataFrame, statement_type: str = "account") -> None:
    categorized_df = categorized_df[~categorized_df["description"].str.contains("dual pyt", case=False, na=False)]

    if statement_type == "cc":
        categorized_df["amount"] = categorized_df["amount"].apply(
            lambda x: abs(float(x)) if float(x) < 0 else 0
        )
    elif statement_type == "total":
        categorized_df["amount"] = categorized_df["amount"].apply(
            lambda x: abs(float(x)) if float(x) < 0 else 0
        )
        categorized_df["amount"] = categorized_df["withdrawal_amount"].fillna(0) + categorized_df["amount"].fillna(0)
        # categorized_df["amount"] = categorized_df["withdrawal_amount"].fillna(0)

    # Filter out positive amounts
    if statement_type == "cc":
        categorized_df = categorized_df[categorized_df["amount"] > 0]

        total_amount = categorized_df['amount'].sum()
        print(total_amount)

        categorized_df.to_csv('expenses.csv', index=False)

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
