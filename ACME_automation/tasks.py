import pandas as pd

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
    # creating a fresh index [0..n], while keeping the Series' old index as a column (in this case, the id).
    # When saving to a file, index will be dropped so nameless extra column is not kept in the final csv.
    orders_total_prices = orders_total_prices.reset_index()

    return orders_total_prices

def join_unique_ids(ids):
    """Return the unique ids as a sorted, space-separated string."""
    return " ".join(str(i) for i in sorted(set(ids)))

def product_customers(items):
    """Task 2: customers (unique, sorted) that bought each product."""
    items = items.groupby("product_id")["customer"].agg(join_unique_ids)

    # reset_index allows to rename the Series' data column
    items = items.reset_index(name="customer_ids").rename(columns={"product_id": "id"})

    return items

def customer_ranking(items, customers):
    """Task 3: total spent per customer, descending.

    Customers without orders are kept with total_euros = 0.
    """
    grouped_customers = items.groupby("customer")["cost"].sum()
    grouped_customers = grouped_customers.rename("total_euros")
    
    clients_info_and_total_spendings = (
        customers.merge(
            grouped_customers,
            left_on="id",
            right_on="customer",
            how="left" # Include customers who haven't ordered any product
        )
    )
    
    # Add 0 (€) value to each customer who hasn't ordered any product
    clients_info_and_total_spendings["total_euros"] = clients_info_and_total_spendings["total_euros"].fillna(0)

    # Order by descending order of total_euros
    clients_info_and_total_spendings = clients_info_and_total_spendings.sort_values(
        by=["total_euros", "id"], ascending=[False, True]
    )

    # Reset index with drop=True, as orderby ordered elements but kept the indexes.
    # Resetting allows to recreate from first to last as of [0..n]
    clients_info_and_total_spendings = clients_info_and_total_spendings.reset_index(drop=True)
    
    return clients_info_and_total_spendings