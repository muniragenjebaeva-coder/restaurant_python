# ADR.md - Architecture Decision Records

This file records the decisions and assumptions made while implementing the
Restaurant Order Management System.

## ADR-001: Simple Python structure

**Decision:** Use regular Python functions and dictionaries instead of a
class-heavy object-oriented design.

**Reason:** The application is intended for a beginner-level console project.
The functions are separated by task and are easier to read and test.

## ADR-002: JSON persistence

**Decision:** Store tables, menu items and open orders in `restaurant_data.json`.

**Reason:** JSON is built into Python, readable by a person and does not require
a database server or external package. The file is saved after commands and
when the program exits.

## ADR-003: One open order per table

**Decision:** The order is stored using the table number as its key. Opening a
second order for the same table is rejected.

**Reason:** This directly enforces Rule 1.

## ADR-004: Bill calculation order

**Decision:** Apply discounts in this order: 2+1 promotion, Happy Hours, loyalty
discount, then add the service charge.

**Reason:** The assignment does not specify how discounts interact. This order
is consistent and easy to explain. Service charge is calculated on the
discounted subtotal.

## ADR-005: Loyalty card

**Decision:** A loyalty card gives 15% off the subtotal after promotional
discounts and before service charge.

**Reason:** The assignment specifies the discount rate but not its calculation
base. Applying it before service charge avoids charging a service fee on the
discounted amount twice.

## ADR-006: 2+1 drinks promotion

**Decision:** For every three units of the same drink in an order, one unit is
free. The free unit is valued at the menu price.

**Reason:** Grouping identical drinks makes the promotion predictable. For
example, three Colas give one free Cola; six Colas give two free Colas.

## ADR-007: Happy Hours

**Decision:** Happy Hours run from 15:00 inclusive to 17:00 exclusive and give
10% off drinks.

**Reason:** The assignment does not provide a time range or discount rate.
These values are explicit implementation assumptions and can be changed in
the constants at the top of `app.py`.

## ADR-008: Equal bill split

**Decision:** Divide the final bill by the guest count recorded when the order
is opened.

**Reason:** The assignment requests equal splitting but does not specify a
separate guest-entry command. The guest count is collected when opening an
order. The displayed per-person amount is rounded to two decimal places.

## ADR-009: Moving an order

**Decision:** An order can move only to an existing table with no open order
and enough seats for all guests. The order's table number is updated.

**Reason:** This prevents two open orders on one table and prevents moving a
group to a table that is too small.

## ADR-010: Merging tables

**Decision:** Merge only two tables with no open orders. The first table is the
target. Its seat count increases by the second table's seats, and the second
table is removed.

**Reason:** The assignment does not describe how orders should behave during a
merge. Restricting merges to free tables avoids losing or mixing active orders.

## ADR-011: Console command format

**Decision:** Use text commands with arguments, such as `add-table 1 4` and
`open 1 3 yes`. Print a command guide at startup and provide `help`.

**Reason:** This matches the required command-based console application and
makes the program easier to operate and test.

## ADR-012: Testing

**Decision:** Use Python's built-in `unittest` module and provide five tests.

**Reason:** It requires no extra installation and tests the core rules,
discount calculations, order movement and table merging.
