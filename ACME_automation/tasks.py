import pandas as pd
import argparse
from pathlib import Path

def get_missing_files(orders_file, customers_file, products_file):
    files = [orders_file, customers_file, products_file]
    missing = []

    for file in files:
        print(str(file))
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
        default=Path("../data"),
        help="Directory containing customers.csv, products.csv and orders.csv (default: '../data')",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("../output"),
        help="Directory for output files (default: '../output')",
    )
    return parser

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

    missing_files = get_missing_files(orders_file, customers_file, products_file)

    if missing_files:
        parser.error(
        "Missing input files: " + ", ".join(str(file) for file in missing_files)
    )

    try:
        df_orders = pd.read_csv(orders_file)
        df_customers = pd.read_csv(customers_file)
        df_products = pd.read_csv(products_file)

    except FileNotFoundError as e:
        parser.error(f"Input file not found: {e.filename}")

    except PermissionError as e:
        parser.error(f"Permission denied: {e.filename}")

    except pd.errors.ParserError as e:
        parser.error(f"Invalid CSV format: {e}")