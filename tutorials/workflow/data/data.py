import pandas as pd

def get_data():
    # Hardcoded order data
    order_data = {
        'order_id': ['ORD001', 'ORD002', 'ORD003', 'ORD004', 'ORD005'],
        'delivery_time': ['2023-08-10', '2023-08-12', '2023-08-15', '2023-08-11', '2023-08-14']
    }
    order_df = pd.DataFrame(order_data)
    return order_df
