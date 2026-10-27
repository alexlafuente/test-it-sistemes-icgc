import pandas as pd
import argparse
from pathlib import Path

def get_missing_files(files):
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

def save_to_file(items, file_name, output_dir, index=True):
    output_file = output_dir / file_name
    items.to_csv(output_file, index=index)

def explode_orders(orders, products):
    """Return one row per product unit in each order, with its cost.

    Columns: order_id, customer, product_id, product_name, cost.
    """
    items = orders.rename(columns={"id": "order_id",}).copy()
    items["product_id"] = items["products"].str.split()
    items = items.drop(columns="products")

    # Separate each row into n different rows, with n being the ammount of products in the original row. 
    items = items.explode("product_id", ignore_index=False).astype({"product_id": int})

    # Inner join, so each product id is intersected from both dataframes 
    items = items.merge(
        products.rename(columns={"id": "product_id", "name": "product_name"}), # Rename id column so it's the same in both tables, and can be connected via "on". Rename "name" to "product_name" for clarity.
        on="product_id",
        how="inner"
    )

    return items

def order_prices(items):
    """Task 1: Return dataframe with total cost in euros per order."""
    orders_total_prices = items.rename(columns={"cost": "euros"})
    orders_total_prices = orders_total_prices.groupby("order_id")["euros"].sum()
    orders_total_prices = orders_total_prices.rename_axis("id")

    # Currently, after groupby, we have a Series instance. Resetting the index transformes it into a Dataframe,
    # creating a fresh index (0..n), while keeping the Series' old index (in this case, the id).
    # When saving to a file, index will be dropped so nameless extra column is not kept in the final csv.
    orders_total_prices = orders_total_prices.reset_index()

    return orders_total_prices

def join_unique_ids(ids):
    return " ".join(str(i) for i in sorted(set(ids)))

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
    grouped_products = items.groupby("product_id")["customer"].apply(join_unique_ids)

    # Reset Series index, which currently has the customer values without its index.
    # Then rename product_id column
    grouped_products = grouped_products.reset_index(name="customer_ids").rename(columns={"product_id": "id"})
    save_to_file(grouped_products, "product_customers.csv", output_dir, False)


    # Task 3
    grouped_customers = items.groupby("customer")["cost"].sum()

    clients_info_and_total_spendings = (
        df_customers.merge(
            grouped_customers.reset_index(name="total_euros"), # Reset Series index, which currently has the customer values without its index (due to previous groupby)
            left_on="id",
            right_on="customer",
            how="left" # Include customers who haven't ordered any product
        )
    )

    # Order by descending order of total_euros
    clients_info_and_total_spendings = clients_info_and_total_spendings.sort_values(
        by=["total_euros", "id"], ascending=[False, True]
    )

    # Add 0 (€) value to each customer who hasn't ordered any product
    clients_info_and_total_spendings["total_euros"] = clients_info_and_total_spendings["total_euros"].fillna(0)

    clients_info_and_total_spendings = clients_info_and_total_spendings.drop(columns=["customer"])

    save_to_file(clients_info_and_total_spendings, "customer_ranking.csv", output_dir, False)