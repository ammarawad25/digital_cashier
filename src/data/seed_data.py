from faker import Faker
from sqlalchemy.orm import Session
import random
from datetime import datetime, timedelta
from src.models.database import Customer, MenuItem, Order, OrderItem, Issue, FAQ
from src.models.enums import OrderStatus, IssueType, IssueStatus, Sentiment

fake = Faker()

def generate_menu_items(db: Session):
    brands = {
        "Burger Hub": [
            ("Classic Burger", "برجر كلاسيكي", "100% beef patty with lettuce, tomato, onion", 8.99, "Burgers", ["dairy"], ["gluten"]),
            ("Cheeseburger", "برجر بالجبنة", "Classic burger with cheddar cheese", 9.99, "Burgers", ["dairy"], ["gluten", "dairy"]),
            ("Double Cheeseburger", "برجر دبل تشيز", "Double beef patty with double cheese", 12.99, "Burgers", ["dairy"], ["gluten", "dairy"]),
            ("Triple Cheeseburger", "برجر تربل تشيز", "Triple beef patty with triple cheese", 15.99, "Burgers", ["dairy"], ["gluten", "dairy"]),
            ("Veggie Burger", "برجر نباتي", "Plant-based patty with fresh vegetables", 9.49, "Burgers", ["vegan"], ["gluten"]),
            ("Bacon Burger", "برجر بيكون", "Double patty with crispy bacon", 12.99, "Burgers", [], ["gluten", "dairy"]),
            ("Chicken Burger", "برجر دجاج", "Crispy chicken with special sauce", 10.99, "Burgers", [], ["gluten", "dairy"]),
            ("BBQ Burger", "برجر باربيكيو", "Burger with BBQ sauce and onion rings", 11.99, "Burgers", [], ["gluten", "dairy"]),
            ("Fries", "بطاطس مقلية", "Golden crispy french fries", 3.99, "Sides", ["vegan"], []),
            ("Onion Rings", "حلقات البصل", "Beer-battered onion rings", 4.49, "Sides", [], ["gluten"]),
            ("Coca Cola", "كوكاكولا", "Classic Coca Cola soft drink", 1.99, "Beverages", ["vegan"], []),
            ("Pepsi", "بيبسي", "Pepsi soft drink", 1.99, "Beverages", ["vegan"], []),
            ("7UP", "سفن اب", "Lemon-lime flavored soft drink", 1.99, "Beverages", ["vegan"], []),
            ("Sprite", "سبرايت", "Lemon-lime soda", 1.99, "Beverages", ["vegan"], []),
            ("Fanta Orange", "فانتا برتقال", "Orange flavored soft drink", 1.99, "Beverages", ["vegan"], []),
            ("Water", "ماء", "Bottled water", 0.99, "Beverages", ["vegan"], []),
            ("Milkshake Vanilla", "ميلك شيك فانيليا", "Creamy vanilla milkshake", 4.99, "Beverages", [], ["dairy"]),
            ("Milkshake Chocolate", "ميلك شيك شوكولاتة", "Rich chocolate milkshake", 4.99, "Beverages", [], ["dairy"]),
            ("Milkshake Strawberry", "ميلك شيك فراولة", "Fresh strawberry milkshake", 4.99, "Beverages", [], ["dairy"]),
            ("Brownie", "براوني", "Chocolate fudge brownie", 3.99, "Desserts", [], ["gluten", "dairy", "eggs"]),
        ],
        "Pizza Palace": [
            ("Margherita Pizza", "بيتزا مارجريتا", "Fresh mozzarella, basil, tomato sauce", 12.99, "Pizza", [], ["gluten", "dairy"]),
            ("Pepperoni Pizza", "بيتزا ببروني", "Classic pepperoni with mozzarella", 14.99, "Pizza", [], ["gluten", "dairy"]),
            ("Veggie Pizza", "بيتزا نباتية", "Mushrooms, peppers, onions, olives", 13.99, "Pizza", [], ["gluten", "dairy"]),
            ("BBQ Chicken Pizza", "بيتزا دجاج باربيكيو", "BBQ sauce, chicken, red onions", 15.99, "Pizza", [], ["gluten", "dairy"]),
            ("Garlic Bread", "خبز بالثوم", "Toasted bread with garlic butter", 4.99, "Sides", [], ["gluten", "dairy"]),
            ("Wings", "أجنحة دجاج", "Buffalo chicken wings", 8.99, "Sides", [], []),
            ("Salad", "سلطة", "Fresh garden salad", 6.99, "Sides", ["vegan"], []),
            ("Coca Cola", "كوكاكولا", "Classic Coca Cola soft drink", 1.99, "Beverages", ["vegan"], []),
            ("Pepsi", "بيبسي", "Pepsi soft drink", 1.99, "Beverages", ["vegan"], []),
            ("Water", "ماء", "Bottled water", 0.99, "Beverages", ["vegan"], []),
            ("Tiramisu", "تيراميسو", "Italian coffee-flavored dessert", 5.99, "Desserts", [], ["gluten", "dairy", "eggs"]),
        ]
    }
    
    import json
    for brand, items in brands.items():
        for name, arabic_name, desc, price, category, dietary, allergens in items:
            item = MenuItem(
                name=name,
                arabic_name=arabic_name,
                description=desc,
                price=price,
                category=category,
                dietary_tags=json.dumps(dietary),
                allergens=json.dumps(allergens),
                is_available=True,
                brand=brand
            )
            db.add(item)
    
    db.commit()
    print("✓ Menu items created for 2 brands")

def generate_faqs(db: Session):
    import json
    faqs = [
        # Hours & Location
        ("What are your hours?", "We're open Monday-Friday 11am-10pm, Saturday-Sunday 10am-11pm.", "hours", ["hours", "open", "time", "ساعات", "متى"]),
        ("Are you open on holidays?", "We're open on most holidays with reduced hours. Please call ahead.", "hours", ["holiday", "closed", "عطلة"]),
        ("Where are you located?", "We have locations across the city. Check our website for the nearest one.", "location", ["location", "address", "where", "موقع", "عنوان", "وين"]),
        
        # Menu & Food
        ("What's on your menu?", "We serve delicious burgers, pizzas, sides, salads, beverages and desserts. We have options for different dietary needs including vegan and gluten-free items.", "menu", ["menu", "منيو", "القائمة", "عندكم", "لديكم", "what do you have"]),
        ("Do you have burgers?", "Yes! We have Classic Burger, Cheeseburger, Veggie Burger, Bacon Burger, Chicken Burger, BBQ Burger, and more specialty options.", "menu", ["burger", "برجر", "برغر"]),
        ("Do you have pizza?", "Yes! We offer Margherita, Pepperoni, Veggie Pizza, and BBQ Chicken Pizza.", "menu", ["pizza", "بيتزا"]),
        ("What sides do you have?", "We have Fries, Onion Rings, Garlic Bread, Wings, Salad, Loaded Fries, Cheese Sticks, Chicken Strips, and Nuggets.", "menu", ["sides", "جوانب", "مقبلات", "بطاطس"]),
        
        # Dietary & Allergens
        ("Do you have gluten-free options?", "Yes, we have gluten-free pizzas and some allergen-free items. Ask about specific items.", "allergens", ["gluten", "gluten-free", "celiac", "جلوتين"]),
        ("What if I have allergies?", "Please inform us of any allergies when ordering. We take allergies seriously and will do our best to accommodate.", "allergens", ["allergy", "allergies", "allergic", "حساسية"]),
        ("Do you have vegan options?", "Yes! We have vegan burgers, veggie pizza, salads, and fries.", "allergens", ["vegan", "plant-based", "نباتي"]),
        ("Is your food halal?", "Yes, all our meat is halal certified.", "allergens", ["halal", "حلال"]),
        
        # Ordering & Payment
        ("What payment methods do you accept?", "We accept credit/debit cards, Apple Pay, Google Pay, and cash at our drive-thru.", "payment", ["payment", "pay", "card", "دفع"]),
        ("How long until my order is ready?", "Orders are typically ready in about 1 minute for drive-thru pickup.", "timing", ["how long", "ready", "wait", "كم", "متى"]),
        ("Can I track my order?", "Yes, you'll receive an order number and can check status anytime.", "tracking", ["track", "tracking", "تتبع"]),
        
        # Restaurant Info
        ("What type of restaurant is this?", "Burgerizzer is a drive-thru restaurant specializing in burgers, pizzas, and American fast food with quick service.", "info", ["restaurant", "type", "about", "نوع", "مطعم"]),
        ("Do you deliver?", "This is a drive-thru location. We focus on quick pickup service.", "service", ["deliver", "delivery", "توصيل"]),
    ]
    
    for question, answer, category, keywords in faqs:
        faq = FAQ(
            question=question,
            answer=answer,
            category=category,
            keywords=json.dumps(keywords),
            usage_count=0
        )
        db.add(faq)
    
    db.commit()
    print("✓ FAQs created")

def generate_customers(db: Session, count=100):
    for i in range(count):
        customer = Customer(
            name=fake.name(),
            phone=f"+1{fake.numerify('##########')}",
            email=fake.email(),
            loyalty_points=random.randint(0, 500)
        )
        db.add(customer)
    
    db.commit()
    print(f"✓ {count} customers created")

def generate_orders(db: Session, count=200):  # Increased from 50 to 200
    customers = db.query(Customer).all()
    menu_items = db.query(MenuItem).all()
    
    for _ in range(count):
        customer = random.choice(customers)
        num_items = random.randint(1, 4)
        items = random.sample(menu_items, num_items)
        
        subtotal = sum(item.price * random.randint(1, 3) for item in items)
        tax = subtotal * 0.08
        delivery_fee = 4.99
        total = subtotal + tax + delivery_fee
        
        order = Order(
            customer_id=customer.id,
            status=random.choice(list(OrderStatus)),
            subtotal=round(subtotal, 2),
            tax=round(tax, 2),
            delivery_fee=delivery_fee,
            total=round(total, 2),
            fulfillment_type="drive-thru",
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
        )
        db.add(order)
        db.flush()
        
        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item.id,
                quantity=random.randint(1, 3),
                unit_price=item.price
            )
            db.add(order_item)
    
    db.commit()
    print(f"✓ {count} orders created")

def seed_all(db: Session):
    print("Starting database seeding...")
    generate_menu_items(db)
    generate_faqs(db)
    generate_customers(db)
    generate_orders(db)
    print("\n✅ Database seeded successfully!")

if __name__ == "__main__":
    from src.models.db_session import SessionLocal, init_db
    
    init_db()
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()
