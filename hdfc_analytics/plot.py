import pandas as pd
import plotly.express as px


def plot_df(categorized_df: pd.DataFrame) -> None:

    categorized_df["amount"] = categorized_df["withdrawal_amount"].fillna(0)

    # Summarize the data by category
    category_summary = categorized_df.groupby("category")["amount"].sum().reset_index()

    # Plot the pie chart using Plotly
    fig = px.pie(category_summary, values="amount", names="category", title="Expenses by Category")
    fig.update_traces(textinfo='percent+label')

    # Show the figure
    fig.show()
