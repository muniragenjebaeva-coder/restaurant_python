import unittest
import tempfile
import io
from pathlib import Path
from unittest.mock import patch
from datetime import time

from app import (
    empty_data, add_table, add_dish, open_order, add_item, remove_item,
    calculate_bill, move_order, merge_tables, save_data, load_data, run_command
)


class RestaurantAppTests(unittest.TestCase):

    def setUp(self):
        self.data = empty_data()
        add_table(self.data, 1, 4)
        add_table(self.data, 2, 2)
        add_dish(self.data, "Burger", 100.00, "food")
        add_dish(self.data, "Cola", 20.00, "drink")

    def test_1_table_cannot_have_two_open_orders(self):
        self.assertTrue(open_order(self.data, 1, 2)[0])
        self.assertFalse(open_order(self.data, 1, 2)[0])

    def test_2_add_and_remove_order_item(self):
        open_order(self.data, 1, 2)
        self.assertTrue(add_item(self.data, 1, "Burger", 2)[0])
        self.assertEqual(self.data["orders"]["1"]["items"]["Burger"], 2)
        self.assertTrue(remove_item(self.data, 1, "Burger", 1)[0])
        self.assertEqual(self.data["orders"]["1"]["items"]["Burger"], 1)

    def test_3_bill_discounts_service_charge_and_split(self):
        open_order(self.data, 1, 2, loyalty=True)
        add_item(self.data, 1, "Burger", 1)
        add_item(self.data, 1, "Cola", 3)
        bill = calculate_bill(
            self.data["orders"]["1"], self.data["menu"], time(12, 0)
        )
        # 100 food + 60 drinks - 20 free drink = 140.
        # Loyalty discount 21, service charge 11.90, total 130.90.
        self.assertEqual(bill["promotion_discount"], 20.00)
        self.assertEqual(bill["loyalty_discount"], 21.00)
        self.assertEqual(bill["service_charge"], 11.90)
        self.assertEqual(bill["total"], 130.90)
        self.assertEqual(bill["per_guest"], 65.45)

    def test_4_happy_hour_discount(self):
        open_order(self.data, 1, 1)
        add_item(self.data, 1, "Cola", 1)
        bill = calculate_bill(
            self.data["orders"]["1"], self.data["menu"], time(16, 0)
        )
        self.assertEqual(bill["happy_hour_discount"], 2.00)
        self.assertEqual(bill["total"], 19.80)

    def test_5_move_order_and_merge_tables(self):
        open_order(self.data, 1, 2)
        self.assertTrue(move_order(self.data, 1, 2)[0])
        self.assertIsNone(self.data["orders"].get("1"))
        self.assertIsNotNone(self.data["orders"].get("2"))
        # A table with an open order cannot be merged.
        self.assertFalse(merge_tables(self.data, 1, 2)[0])
        del self.data["orders"]["2"]
        self.assertTrue(merge_tables(self.data, 1, 2)[0])
        self.assertEqual(self.data["tables"]["1"]["seats"], 6)
        self.assertNotIn("2", self.data["tables"])

        # Check that restaurant information is available after a new program load.
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "restaurant_data.json"
            with patch("app.DATA_FILE", data_file):
                save_data(self.data)
                loaded_data = load_data()
        self.assertEqual(loaded_data["tables"]["1"]["seats"], 6)

    def test_6_empty_order_cannot_be_closed(self):
        open_order(self.data, 1, 2)

        with patch("builtins.input") as input_mock:
            self.assertTrue(run_command(self.data, ["close", "1"]))

        input_mock.assert_not_called()
        self.assertIn("1", self.data["orders"])

    def test_7_full_order_flow_bills_and_persists_items(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "restaurant_data.json"
            with patch("app.DATA_FILE", data_file):
                self.assertTrue(
                    run_command(self.data, ["open", "1", "3", "yes"])
                )
                self.assertTrue(
                    run_command(self.data, ["add", "1", "Burger", "2"])
                )
                self.assertTrue(
                    run_command(self.data, ["add", "1", "Cola", "3"])
                )

                order = self.data["orders"]["1"]
                self.assertEqual(order["items"], {"Burger": 2, "Cola": 3})

                with patch("sys.stdout", new_callable=io.StringIO) as output:
                    self.assertTrue(run_command(self.data, ["bill", "1"]))
                bill_output = output.getvalue()
                self.assertIn("Burger x 2 = 200.00", bill_output)
                self.assertIn("Cola x 3 = 60.00", bill_output)
                self.assertIn("TOTAL TO PAY:", bill_output)

                bill = calculate_bill(order, self.data["menu"], time(16, 0))
                self.assertEqual(bill["food_total"], 200.00)
                self.assertEqual(bill["drink_total"], 60.00)
                self.assertEqual(bill["promotion_discount"], 20.00)
                self.assertEqual(bill["happy_hour_discount"], 4.00)
                self.assertEqual(bill["loyalty_discount"], 35.40)
                self.assertEqual(bill["subtotal"], 200.60)
                self.assertEqual(bill["service_charge"], 20.06)
                self.assertEqual(bill["total"], 220.66)
                self.assertEqual(bill["per_guest"], 73.55)

                with patch("builtins.input", return_value="yes"):
                    with patch("sys.stdout", new_callable=io.StringIO):
                        self.assertTrue(
                            run_command(self.data, ["close", "1"])
                        )

                self.assertNotIn("1", self.data["orders"])
                loaded_data = load_data()

            self.assertNotIn("1", loaded_data["orders"])
            self.assertEqual(loaded_data["menu"]["Burger"]["price"], 100.00)


if __name__ == "__main__":
    unittest.main()
