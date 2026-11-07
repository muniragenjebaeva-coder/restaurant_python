# Restaurant Order Management System

A beginner-friendly Python console application for managing restaurant tables,
menu items, customer orders, bills, discounts and payments.

## Requirements

- Python 3.8 or newer
- No external Python packages are required.

## Run the application

Open a terminal in this project folder and run:

```bash
python app.py
```

The application displays the command guide at startup. Type `help` at any time
to display it again.

## Commands

| Command | Example | Description |
|---|---|---|
| `add-table NUMBER SEATS` | `add-table 1 4` | Add a table |
| `add-dish "NAME" PRICE food/drink` | `add-dish "Cola" 10000 drink` | Add a menu item |
| `open TABLE GUESTS [yes/no]` | `open 1 3 yes` | Open an order; yes means loyalty card |
| `add TABLE "DISH" [QUANTITY]` | `add 1 "Cola" 2` | Add items |
| `remove TABLE "DISH" [QUANTITY]` | `remove 1 "Cola" 1` | Remove items |
| `bill TABLE` | `bill 1` | Display the bill |
| `close TABLE` | `close 1` | Display bill and ask for payment confirmation |
| `move SOURCE DESTINATION` | `move 1 2` | Move an order to another table |
| `merge TARGET SOURCE` | `merge 1 2` | Combine two free tables |
| `help` | `help` | Display instructions |
| `exit` | `exit` | Save and quit |

Use quotation marks around menu names that contain spaces.

## Billing rules and assumptions

1. Service charge is 10% of the amount after discounts.
2. A loyalty card gives a 15% discount on the amount after promotions.
3. The 2+1 promotion applies to drinks: for every three units of the same drink,
   one unit is free. The free unit is charged at the normal menu price and is
   shown as a discount.
4. Happy Hours run from 15:00 inclusive to 17:00 exclusive. Drinks receive an
   additional 10% discount during this period.
5. Discounts are applied in this order: 2+1 promotion, Happy Hours, loyalty.
   Service charge is calculated after all discounts.
6. The bill is split equally by the guest count entered when the order is opened.
   Displayed amounts are rounded to two decimal places.
7. A table can have only one open order.
8. An order can be moved only to an existing, empty table with enough seats.
9. Tables can be merged only when both tables have no open orders. The first
   table in the command is the target; the second table is removed and its seats
   are added to the target.
10. Restaurant data is stored in `restaurant_data.json` in the project folder.

## Run the tests

```bash
python -m unittest -v
```

The tests cover open-order restrictions, adding/removing items, bill
calculation, Happy Hours, moving orders, merging tables, and the complete
open/add/bill/close flow with JSON persistence.
