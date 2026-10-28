import pandas as pd

from ACME_automation.tasks import (
    customer_ranking,
    explode_orders,
    join_unique_ids,
    order_prices,
    product_customers
)

PRODUCTS = pd.DataFrame({"id": [0, 1], "name": ["a", "b"], "cost": [1.5, 2.0]})
CUSTOMERS = pd.DataFrame({"id": [0, 1, 2], "firstname": ["A", "B", "C"], "lastname": ["X", "Y", "Z"]})
ORDERS = pd.DataFrame({"id": [0, 1], "customer": [1, 1], "products": ["0 0 1", "1"]})


def test_join_unique_ids_deduplicates_and_sorts_numerically():
    assert join_unique_ids(pd.Series([10, 2, 10, 3])) == "2 3 10"


def test_order_prices_counts_repeated_products():
    result = order_prices(explode_orders(ORDERS, PRODUCTS))
    assert result.to_dict("list") == {"id": [0, 1], "euros": [5.0, 2.0]}


def test_product_customers_unique():
    result = product_customers(explode_orders(ORDERS, PRODUCTS))
    assert result.to_dict("list") == {"id": [0, 1], "customer_ids": ["1", "1"]}


def test_ranking_includes_customers_without_orders_and_sorts():
    result = customer_ranking(explode_orders(ORDERS, PRODUCTS), CUSTOMERS)
    assert result["id"].tolist() == [1, 0, 2]
    assert result["total_euros"].tolist() == [7.0, 0.0, 0.0]
