## hdfc-analytics

Get analysis of HDFC bank account and credit card statement

> [!NOTE]  
> Currently only supports bank account statement parsing and analysis

### Usage

1. `pip install https://github.com/vipul-sharma20/hdfc-analytics/releases/download/v0.1.0/hdfc_analytics-0.1.0-py3-none-any.whl` (check releases for latest whl releases)
2. Prepare bank statement data. Check the configuration section below
3. Run: `hdfc-analytics account --statement-csv=./configs/generated_statement.csv --categories-config=./configs/categories.toml --column-config=./configs/column_mapping.toml`. Look at [`configs/`][configs] directory for sample configs

### Configuration

Sample set of configurations can be found in [`configs/`][configs] directory.

1. **Statement**: HDFC provides bank statement in XLS format. Download and convert your
   statement to the format as defined in the sample statement csv in [`configs/`][configs]
   directory. You'll only need to remove a few rows at the top and at the
   bottom of the generated statement. Clean and save it to a csv file.
2. **Columns**: This configuration stores custom column names to be mapped for
   the generated sheet columns.
3. **Categories**: This configuration defines some list of strings under a
   category that the script tries to match and categorize each transactions
   into.

[configs]: https://github.com/vipul-sharma20/hdfc-analytics/tree/main/configs
