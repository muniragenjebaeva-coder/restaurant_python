import json
import shlex
from datetime import datetime, time
from pathlib import Path

DATA_FILE = Path(__file__).with_name("restaurant_data.json")
SERVICE_CHARGE_RATE = 0.10
LOYALTY_DISCOUNT_RATE = 0.15
HAPPY_HOUR_DISCOUNT_RATE = 0.10
HAPPY_HOUR_START = time(15, 0)
HAPPY_HOUR_END = time(17, 0)


def empty_data():
    return {"tables": {}, "menu": {}, "orders": {}}


def load_data():
    """Load saved restaurant data. Start with empty data if no file exists."""
    if not DATA_FILE.exists():
        return empty_data()

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        data.setdefault("tables", {})
        data.setdefault("menu", {})
        data.setdefault("orders", {})
        return data
    except (json.JSONDecodeError, OSError):
        print("Warning: saved data could not be read. Starting with empty data.")
        return empty_data()


def save_data(data):
    """Save all restaurant data so it is available next time."""
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def find_menu_item(data, dish_name):
    """Find a menu item without caring about upper/lowercase."""
    for name in data["menu"]:
        if name.lower() == dish_name.lower():
            return name
    return None


def get_order_for_table(data, table_number):
    return data["orders"].get(str(table_number))


def is_happy_hour(current_time):
    """Happy Hours are from 15:00 (inclusive) to 17:00 (exclusive)."""
    if isinstance(current_time, datetime):
        current_time = current_time.time()
    return HAPPY_HOUR_START <= current_time < HAPPY_HOUR_END


def calculate_bill(order, menu, current_time=None):
    """
    Calculate a bill.
    Promotion and happy-hour discounts are applied before loyalty discount.
    Service charge is added after all discounts.
    """
    if current_time is None:
        current_time = datetime.now().time()

    food_total = 0.0
    drink_total_before_promotions = 0.0
    promotion_discount = 0.0

    for dish_name, quantity in order["items"].items():
        item = menu[dish_name]
        line_total = item["price"] * quantity

        if item["category"] == "drink":
            drink_total_before_promotions += line_total

            # For every group of three of the same drink, one is free.
            free_quantity = quantity // 3
            promotion_discount += free_quantity * item["price"]
        else:
            food_total += line_total

    drink_total_after_promotion = drink_total_before_promotions - promotion_discount

    happy_hour_discount = 0.0
    if is_happy_hour(current_time):
        happy_hour_discount = drink_total_after_promotion * HAPPY_HOUR_DISCOUNT_RATE

    subtotal_after_promotions = (
        food_total + drink_total_after_promotion - happy_hour_discount
    )

    loyalty_discount = 0.0
    if order["loyalty"]:
        loyalty_discount = subtotal_after_promotions * LOYALTY_DISCOUNT_RATE

    subtotal_after_all_discounts = subtotal_after_promotions - loyalty_discount
    service_charge = subtotal_after_all_discounts * SERVICE_CHARGE_RATE
    total = subtotal_after_all_discounts + service_charge

    guests = order["guests"]
    split_amount = total / guests if guests > 0 else total

    return {
        "food_total": round(food_total, 2),
        "drink_total": round(drink_total_before_promotions, 2),
        "promotion_discount": round(promotion_discount, 2),
        "happy_hour_discount": round(happy_hour_discount, 2),
        "loyalty_discount": round(loyalty_discount, 2),
        "subtotal": round(subtotal_after_all_discounts, 2),
        "service_charge": round(service_charge, 2),
        "total": round(total, 2),
        "guests": guests,
        "per_guest": round(split_amount, 2),
    }


def add_table(data, number, seats):
    number = str(number)
    if number in data["tables"]:
        return False, "That table already exists."
    if seats <= 0:
        return False, "The number of seats must be greater than zero."

    data["tables"][number] = {"seats": seats}
    return True, f"Table {number} added. It has {seats} seats."


def add_dish(data, name, price, category):
    name = name.strip()
    category = category.lower()

    if not name:
        return False, "Dish name cannot be empty."
    if name in data["menu"]:
        return False, "That dish is already on the menu."
    if price <= 0:
        return False, "Price must be greater than zero."
    if category not in ("food", "drink"):
        return False, "Category must be food or drink."

    data["menu"][name] = {"price": round(price, 2), "category": category}
    return True, f"{name} added to the {category} menu for {price:.2f}."


def open_order(data, table_number, guests, loyalty=False):
    table_number = str(table_number)

    if table_number not in data["tables"]:
        return False, "This table does not exist."
    if get_order_for_table(data, table_number):
        return False, "This table already has an open order."
    if guests <= 0:
        return False, "Guest count must be greater than zero."
    if guests > data["tables"][table_number]["seats"]:
        return False, "There are not enough seats for this number of guests."

    data["orders"][table_number] = {
        "table": table_number,
        "guests": guests,
        "loyalty": bool(loyalty),
        "items": {},
    }
    return True, f"Order opened for table {table_number}, guests: {guests}."


def add_item(data, table_number, dish_name, quantity=1):
    table_number = str(table_number)
    order = get_order_for_table(data, table_number)

    if not order:
        return False, "There is no open order at this table."
    if quantity <= 0:
        return False, "Quantity must be greater than zero."

    real_name = find_menu_item(data, dish_name)
    if real_name is None:
        return False, "This dish is not on the menu."

    order["items"][real_name] = order["items"].get(real_name, 0) + quantity
    return True, f"Added {quantity} x {real_name} to table {table_number}."


def remove_item(data, table_number, dish_name, quantity=1):
    table_number = str(table_number)
    order = get_order_for_table(data, table_number)

    if not order:
        return False, "There is no open order at this table."
    if quantity <= 0:
        return False, "Quantity must be greater than zero."

    real_name = find_menu_item(data, dish_name)
    if real_name is None or real_name not in order["items"]:
        return False, "This item is not in the order."

    if quantity >= order["items"][real_name]:
        del order["items"][real_name]
        return True, f"Removed {real_name} from the order."

    order["items"][real_name] -= quantity
    return True, f"Removed {quantity} x {real_name} from the order."


def move_order(data, source_number, destination_number):
    source_number = str(source_number)
    destination_number = str(destination_number)

    if source_number == destination_number:
        return False, "Choose two different tables."
    if source_number not in data["tables"] or destination_number not in data["tables"]:
        return False, "Both tables must exist."
    order = get_order_for_table(data, source_number)
    if not order:
        return False, "The source table has no open order."
    if get_order_for_table(data, destination_number):
        return False, "The destination table already has an open order."
    if order["guests"] > data["tables"][destination_number]["seats"]:
        return False, "The destination table does not have enough seats."

    del data["orders"][source_number]
    order["table"] = destination_number
    data["orders"][destination_number] = order
    return True, f"Order moved from table {source_number} to table {destination_number}."


def merge_tables(data, target_number, source_number):
    """Add source table's seats to target table, then remove the source table."""
    target_number = str(target_number)
    source_number = str(source_number)

    if target_number == source_number:
        return False, "Choose two different tables."
    if target_number not in data["tables"] or source_number not in data["tables"]:
        return False, "Both tables must exist."
    if get_order_for_table(data, target_number) or get_order_for_table(data, source_number):
        return False, "Both tables must be free before they can be merged."

    data["tables"][target_number]["seats"] += data["tables"][source_number]["seats"]
    del data["tables"][source_number]
    return True, (
        f"Tables merged. Table {target_number} now has "
        f"{data['tables'][target_number]['seats']} seats. "
        f"Table {source_number} was removed."
    )


def print_bill(order, menu):
    result = calculate_bill(order, menu)

    print("\n========== BILL ==========")
    print(f"Table: {order['table']}")
    print(f"Guests: {order['guests']}")
    print("Items:")
    if not order["items"]:
        print("  No items in this order.")
    for dish_name, quantity in order["items"].items():
        item_total = menu[dish_name]["price"] * quantity
        print(f"  {dish_name} x {quantity} = {item_total:.2f}")

    print("--------------------------")
    print(f"Food total:              {result['food_total']:.2f}")
    print(f"Drinks before promotion: {result['drink_total']:.2f}")
    print(f"2+1 promotion discount: -{result['promotion_discount']:.2f}")
    print(f"Happy Hours discount:   -{result['happy_hour_discount']:.2f}")
    print(f"Loyalty discount:       -{result['loyalty_discount']:.2f}")
    print(f"Subtotal:                {result['subtotal']:.2f}")
    print(f"Service charge (10%):    {result['service_charge']:.2f}")
    print(f"TOTAL TO PAY:             {result['total']:.2f}")
    print(f"Split equally:            {result['per_guest']:.2f} per guest")
    print("==========================\n")
    return result


def show_help():
    print("""
============================================================
       RESTAURANT ORDER MANAGEMENT SYSTEM
============================================================
This program manages restaurant tables, menu items, orders,
promotions and customer bills.

COMMANDS
------------------------------------------------------------
help
  Show this command guide.

add-table NUMBER SEATS
  Add a restaurant table.
  Example: add-table 1 4

add-dish "NAME" PRICE CATEGORY
  Add a food or drink to the menu.
  CATEGORY must be food or drink.
  Example: add-dish "Burger" 45000 food
  Example: add-dish "Cola" 10000 drink

open TABLE GUESTS [loyalty yes/no]
  Open one order for a table.
  Example: open 1 3 yes
  Use yes if at least the order has a loyalty card.

add TABLE "DISH NAME" [QUANTITY]
  Add a menu item to an open order.
  Example: add 1 "Burger" 2

remove TABLE "DISH NAME" [QUANTITY]
  Remove an item from an open order.
  Example: remove 1 "Burger" 1

bill TABLE
  Show the bill, discounts, service charge and split amount.

close TABLE
  Show the final bill, accept payment and close the order.

move SOURCE_TABLE DESTINATION_TABLE
  Move an open order to another free table.
  Example: move 1 3

merge TARGET_TABLE SOURCE_TABLE
  Merge two free tables. Their seats are added together.
  The source table is removed.
  Example: merge 1 2

exit
  Save data and close the application.

BILLING RULES
------------------------------------------------------------
- Service charge: 10% after discounts.
- Loyalty card: 15% discount.
- Drinks promotion: buy 2, get the 3rd of the same drink free.
- Happy Hours: 15:00-17:00, 10% off drinks.
- The bill is split equally between the guests.
- Data is saved in restaurant_data.json.
============================================================
""")


def run_command(data, parts):
    if not parts:
        return True

    command = parts[0].lower()

    try:
        if command == "help":
            show_help()

        elif command == "add-table":
            if len(parts) != 3:
                print('Usage: add-table NUMBER SEATS')
            else:
                success, message = add_table(data, parts[1], int(parts[2]))
                print(message)

        elif command == "add-dish":
            if len(parts) != 4:
                print('Usage: add-dish "NAME" PRICE food/drink')
            else:
                success, message = add_dish(data, parts[1], float(parts[2]), parts[3])
                print(message)

        elif command == "open":
            if len(parts) not in (3, 4):
                print("Usage: open TABLE GUESTS [yes/no]")
            else:
                loyalty = len(parts) == 4 and parts[3].lower() in ("yes", "y")
                success, message = open_order(data, parts[1], int(parts[2]), loyalty)
                print(message)

        elif command == "add":
            if len(parts) not in (3, 4):
                print('Usage: add TABLE "DISH NAME" [QUANTITY]')
            else:
                quantity = int(parts[3]) if len(parts) == 4 else 1
                success, message = add_item(data, parts[1], parts[2], quantity)
                print(message)

        elif command == "remove":
            if len(parts) not in (3, 4):
                print('Usage: remove TABLE "DISH NAME" [QUANTITY]')
            else:
                quantity = int(parts[3]) if len(parts) == 4 else 1
                success, message = remove_item(data, parts[1], parts[2], quantity)
                print(message)

        elif command == "bill":
            if len(parts) != 2:
                print("Usage: bill TABLE")
            else:
                order = get_order_for_table(data, parts[1])
                if order:
                    if not order["items"]:
                        print("This order has no items. Add items before viewing the bill.")
                    else:
                        print_bill(order, data["menu"])
                else:
                    print("There is no open order at this table.")

        elif command == "close":
            if len(parts) != 2:
                print("Usage: close TABLE")
            else:
                order = get_order_for_table(data, parts[1])
                if not order:
                    print("There is no open order at this table.")
                elif not order["items"]:
                    print("This order has no items. Add items before closing it.")
                else:
                    print_bill(order, data["menu"])
                    answer = input("Has the customer paid? (yes/no): ").strip().lower()
                    if answer in ("yes", "y"):
                        del data["orders"][str(parts[1])]
                        print("Payment received. Order closed. Table is now free.")
                    else:
                        print("Order remains open. No payment was recorded.")

        elif command == "move":
            if len(parts) != 3:
                print("Usage: move SOURCE_TABLE DESTINATION_TABLE")
            else:
                success, message = move_order(data, parts[1], parts[2])
                print(message)

        elif command == "merge":
            if len(parts) != 3:
                print("Usage: merge TARGET_TABLE SOURCE_TABLE")
            else:
                success, message = merge_tables(data, parts[1], parts[2])
                print(message)

        elif command == "exit":
            save_data(data)
            print("All data saved. Goodbye!")
            return False

        else:
            print("Unknown command. Type help to see all available commands.")

    except ValueError:
        print("Invalid number. Check the command example and try again.")

    save_data(data)
    return True


def main():
    data = load_data()
    print("Restaurant Order Management System")
    print("Your restaurant data has been loaded.")
    show_help()

    while True:
        try:
            command_line = input("restaurant> ").strip()
            parts = shlex.split(command_line)
            if not run_command(data, parts):
                break
        except KeyboardInterrupt:
            save_data(data)
            print("\nData saved. Application stopped.")
            break
        except EOFError:
            save_data(data)
            print("\nData saved. Application stopped.")
            break


if __name__ == "__main__":
    main()
