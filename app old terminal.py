# Business Expense Tracker - Version 0.3 (Full Feature)
import json
import os
import csv
from datetime import datetime

SAVE_FILE = "business_data.json"

print("=" * 40)
print("BUSINESS MONITORING APP")
print("=" * 40)

# Load existing data
if os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"expenses": [], "income": []}

expenses = data["expenses"]
income = data["income"]

def save_data():
    with open(SAVE_FILE, "w") as f:
        json.dump({"expenses": expenses, "income": income}, f, indent=2)

def add_income():
    print("\n--- ADD INCOME ---")
    source = input("Income source (e.g., 'Client A', 'Product Sales'): ")
    amount = float(input("Amount received: $"))
    date = input("Date (YYYY-MM-DD) or press Enter for today: ")
    if not date:
        date = datetime.today().strftime('%Y-%m-%d')
    
    income.append({"source": source, "amount": amount, "date": date})
    save_data()
    print(f"✓ Added income: ${amount} from {source}")

def add_expense():
    print("\n--- ADD EXPENSE ---")
    name = input("Expense name: ")
    amount = float(input("Amount spent: $"))
    category = input("Category (Food, Rent, Supplies, Marketing, Other): ")
    date = input("Date (YYYY-MM-DD) or press Enter for today: ")
    if not date:
        date = datetime.today().strftime('%Y-%m-%d')
    
    expenses.append({"name": name, "amount": amount, "category": category, "date": date})
    save_data()
    
    # Budget warning
    total_expenses = sum(e["amount"] for e in expenses)
    if total_expenses > 1000:  # Default budget warning at $1000
        print(f"⚠️ WARNING: Total expenses have exceeded $1000 (currently ${total_expenses})")
    
    print(f"✓ Added expense: ${amount} - {name}")

def view_all():
    print("\n" + "=" * 40)
    print("INCOME")
    print("=" * 40)
    if not income:
        print("No income recorded.")
    else:
        for i, inc in enumerate(income, 1):
            print(f"{i}. {inc['source']} - ${inc['amount']} ({inc['date']})")
    
    print("\n" + "=" * 40)
    print("EXPENSES")
    print("=" * 40)
    if not expenses:
        print("No expenses recorded.")
    else:
        for i, exp in enumerate(expenses, 1):
            print(f"{i}. {exp['name']} - ${exp['amount']} ({exp['category']}) - {exp['date']}")

def profit_loss():
    total_income = sum(inc["amount"] for inc in income)
    total_expenses = sum(exp["amount"] for exp in expenses)
    profit = total_income - total_expenses
    
    print("\n" + "=" * 40)
    print("PROFIT & LOSS SUMMARY")
    print("=" * 40)
    print(f"💰 Total Income:   ${total_income}")
    print(f"💸 Total Expenses: ${total_expenses}")
    print(f"📈 Profit/Loss:    ${profit}")
    
    if profit > 0:
        print("✅ You are profitable!")
    elif profit < 0:
        print("⚠️ You are operating at a loss.")
    else:
        print("📊 Breaking even.")
    print("=" * 40)

def view_by_category():
    if not expenses:
        print("\nNo expenses yet.")
        return
    
    categories = {}
    for exp in expenses:
        cat = exp['category']
        categories[cat] = categories.get(cat, 0) + exp['amount']
    
    print("\n--- EXPENSES BY CATEGORY ---")
    for cat, total_cat in categories.items():
        print(f"{cat}: ${total_cat}")

def edit_item():
    print("\n--- EDIT ITEM ---")
    print("1. Edit Income")
    print("2. Edit Expense")
    choice = input("Choose: ")
    
    if choice == "1" and income:
        view_all()
        idx = int(input("Enter income number to edit: ")) - 1
        if 0 <= idx < len(income):
            print(f"Editing: {income[idx]['source']} - ${income[idx]['amount']}")
            income[idx]['source'] = input(f"New source [{income[idx]['source']}]: ") or income[idx]['source']
            amount = input(f"New amount [{income[idx]['amount']}]: ")
            if amount:
                income[idx]['amount'] = float(amount)
            save_data()
            print("✓ Income updated")
    
    elif choice == "2" and expenses:
        view_all()
        idx = int(input("Enter expense number to edit: ")) - 1
        if 0 <= idx < len(expenses):
            print(f"Editing: {expenses[idx]['name']} - ${expenses[idx]['amount']}")
            expenses[idx]['name'] = input(f"New name [{expenses[idx]['name']}]: ") or expenses[idx]['name']
            amount = input(f"New amount [{expenses[idx]['amount']}]: ")
            if amount:
                expenses[idx]['amount'] = float(amount)
            expenses[idx]['category'] = input(f"New category [{expenses[idx]['category']}]: ") or expenses[idx]['category']
            save_data()
            print("✓ Expense updated")

def delete_item():
    print("\n--- DELETE ITEM ---")
    print("1. Delete Income")
    print("2. Delete Expense")
    choice = input("Choose: ")
    
    if choice == "1" and income:
        view_all()
        idx = int(input("Enter income number to delete: ")) - 1
        if 0 <= idx < len(income):
            removed = income.pop(idx)
            save_data()
            print(f"✓ Deleted: {removed['source']} - ${removed['amount']}")
    
    elif choice == "2" and expenses:
        view_all()
        idx = int(input("Enter expense number to delete: ")) - 1
        if 0 <= idx < len(expenses):
            removed = expenses.pop(idx)
            save_data()
            print(f"✓ Deleted: {removed['name']} - ${removed['amount']}")

def export_csv():
    print("\n--- EXPORT TO CSV ---")
    filename = input("Filename (e.g., 'my_data' will save as my_data.csv): ")
    if not filename:
        filename = "business_export"
    
    # Export income
    with open(f"{filename}_income.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Source", "Amount", "Date"])
        for inc in income:
            writer.writerow([inc["source"], inc["amount"], inc["date"]])
    
    # Export expenses
    with open(f"{filename}_expenses.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Amount", "Category", "Date"])
        for exp in expenses:
            writer.writerow([exp["name"], exp["amount"], exp["category"], exp["date"]])
    
    print(f"✓ Exported to {filename}_income.csv and {filename}_expenses.csv")
    print("  Open these in Excel or any spreadsheet app.")

# Main menu
while True:
    print("\n" + "=" * 40)
    print("MAIN MENU")
    print("=" * 40)
    print("1. Add Income")
    print("2. Add Expense")
    print("3. View All")
    print("4. Profit & Loss")
    print("5. View by Category")
    print("6. Edit Item")
    print("7. Delete Item")
    print("8. Export to CSV")
    print("9. Exit")
    
    choice = input("\nEnter choice (1-9): ")
    
    if choice == "1":
        add_income()
    elif choice == "2":
        add_expense()
    elif choice == "3":
        view_all()
    elif choice == "4":
        profit_loss()
    elif choice == "5":
        view_by_category()
    elif choice == "6":
        edit_item()
    elif choice == "7":
        delete_item()
    elif choice == "8":
        export_csv()
    elif choice == "9":
        save_data()
        print("\n✓ All data saved. Goodbye!")
        break
    else:
        print("\n❌ Invalid choice. Enter 1-9.")