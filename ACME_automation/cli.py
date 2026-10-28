
"""Command-line entry point: reads the input CSV files, runs the three tasks
and writes the result files.
 
Usage (from the project root):
    python -m ACME_automation.cli [--input-dir DIR] [--output-dir DIR]
"""

import argparse
from pathlib import Path
 
import pandas as pd
 
from ACME_automation.tasks import (
    customer_ranking,
    explode_orders,
    order_prices,
    product_customers,
)

# Defaults are anchored to the project root, so they work from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_DIR = PROJECT_ROOT / "data"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"


def get_missing_files(files):
    missing = []
    for file in files:
        if not file.is_file():
            missing.append(file)

    return missing

def configure_parser():
    parser = argparse.ArgumentParser(
        description="Generate order prices, product customers and customer ranking."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Directory containing customers.csv, products.csv and orders.csv "
             f"(default: {DEFAULT_INPUT_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for output files, created if missing (default: {DEFAULT_OUTPUT_DIR})",
    )
    return parser


def save_to_file(items, file_name, output_dir, index=True):
    output_file = output_dir / file_name
    items.to_csv(output_file, index=index)

if __name__ == "__main__":

    # Configure arguments as Path instances
    parser = configure_parser()

    args = parser.parse_args()
    
    if not args.input_dir.is_dir():
        parser.error(f"Input directory does not exist: {args.input_dir}")

    try:
        args.output_dir.mkdir(parents=True, exist_ok=True) # Create directory and parents, skip if they already do
    except (FileExistsError, NotADirectoryError):
        parser.error(f"Output path exists but is not a directory: {args.output_dir}")
    except PermissionError:
        parser.error(f"Permission denied creating output directory: {args.output_dir}")

    # Each variable is a Path instance
    orders_file = args.input_dir / "orders.csv"
    customers_file = args.input_dir / "customers.csv"
    products_file = args.input_dir / "products.csv"
    output_dir = args.output_dir

    missing_files = get_missing_files([orders_file, customers_file, products_file])

    if missing_files:
        parser.error("Missing input files: " + ", ".join(map(str, missing_files)))

    try:
        df_orders = pd.read_csv(orders_file, dtype={"products": str}) # Specify string type to ensure it interprates the list as such
        df_customers = pd.read_csv(customers_file)
        df_products = pd.read_csv(products_file)

    except PermissionError as e:
        parser.error(f"Permission denied: {e.filename}")
    except (pd.errors.ParserError, pd.errors.EmptyDataError) as e:
        parser.error(f"Invalid CSV format: {e}")

    # Task 1
    items = explode_orders(df_orders, df_products)
    save_to_file(order_prices(items), "order_prices.csv", output_dir, index=False)

    # Task 2
    save_to_file(product_customers(items), "product_customers.csv", output_dir, index=False)

    # Task 3
    save_to_file(customer_ranking(items, df_customers), "customer_ranking.csv", output_dir, index=False)

