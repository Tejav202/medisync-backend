from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime, timedelta
import asyncio

# Initialize FastAPI app
app = FastAPI(title="MediSync Agent")

# Mock database for inventory
inventory: Dict[str, int] = {
    "insulin": 5,
    "gloves": 100,
    "syringes": 45,
    "bandages": 200,
    "masks": 15,
    "thermometers": 8,
    "antibiotics": 30
}

# Mock suppliers database
suppliers_db: Dict[str, List[str]] = {
    "insulin": ["MedSupply Co.", "HealthCare Distributors", "PharmaDirect"],
    "gloves": ["MedSupply Co.", "SafetyFirst Inc.", "HealthCare Distributors"],
    "syringes": ["MedSupply Co.", "PharmaDirect", "MedEquip Ltd."],
    "bandages": ["HealthCare Distributors", "FirstAid Supplies", "MedEquip Ltd."],
    "masks": ["SafetyFirst Inc.", "HealthCare Distributors", "ProtectAll Corp."],
    "thermometers": ["MedEquip Ltd.", "HealthCare Distributors", "TechMed Solutions"],
    "antibiotics": ["PharmaDirect", "MedSupply Co.", "HealthCare Distributors"]
}

# Pydantic model for Order
class Order(BaseModel):
    item_name: str = Field(..., description="Name of the medical item to order")
    quantity: int = Field(..., gt=0, description="Quantity to order (must be positive)")
    priority: str = Field(..., description="Order priority: low, medium, high, or critical")

    class Config:
        json_schema_extra = {
            "example": {
                "item_name": "insulin",
                "quantity": 50,
                "priority": "high"
            }
        }

# GET endpoint: Check inventory for a specific item
@app.get("/inventory/{item_name}")
async def get_inventory(item_name: str):
    """
    Get the current stock level for a specific medical item.
    Returns the stock level and status (Critical if < 10, Normal otherwise).
    """
    item_name_lower = item_name.lower()
    
    if item_name_lower not in inventory:
        raise HTTPException(status_code=404, detail=f"Item '{item_name}' not found in inventory")
    
    stock_level = inventory[item_name_lower]
    status = "Critical" if stock_level < 10 else "Normal"
    
    return {
        "item_name": item_name_lower,
        "stock_level": stock_level,
        "status": status
    }

# GET endpoint: Get suppliers for a specific item
@app.get("/suppliers/{item_name}")
async def get_suppliers(item_name: str):
    """
    Get a list of suppliers who stock a specific medical item.
    """
    item_name_lower = item_name.lower()
    
    if item_name_lower not in suppliers_db:
        raise HTTPException(status_code=404, detail=f"No suppliers found for item '{item_name}'")
    
    suppliers_list = suppliers_db[item_name_lower]
    
    return {
        "item_name": item_name_lower,
        "suppliers": suppliers_list,
        "supplier_count": len(suppliers_list)
    }

# POST endpoint: Place an order
@app.post("/place_order")
async def place_order(order: Order):
    """
    Place an order for a medical item.
    Simulates processing delay and returns order confirmation with ID and delivery date.
    """
    item_name_lower = order.item_name.lower()
    
    # Check if item exists in inventory
    if item_name_lower not in inventory:
        raise HTTPException(status_code=404, detail=f"Item '{order.item_name}' not available for ordering")
    
    # Validate priority
    valid_priorities = ["low", "medium", "high", "critical"]
    if order.priority.lower() not in valid_priorities:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
        )
    
    # Simulate processing delay (0.5 to 2 seconds based on priority)
    delay_map = {"critical": 0.5, "high": 1.0, "medium": 1.5, "low": 2.0}
    delay = delay_map.get(order.priority.lower(), 1.5)
    await asyncio.sleep(delay)
    
    # Generate order ID
    order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{item_name_lower[:3].upper()}"
    
    # Calculate delivery date based on priority
    delivery_days_map = {"critical": 1, "high": 2, "medium": 5, "low": 7}
    delivery_days = delivery_days_map.get(order.priority.lower(), 5)
    delivery_date = (datetime.now() + timedelta(days=delivery_days)).strftime("%Y-%m-%d")
    
    return {
        "order_id": order_id,
        "item_name": item_name_lower,
        "quantity": order.quantity,
        "priority": order.priority.lower(),
        "status": "confirmed",
        "delivery_date": delivery_date,
        "message": f"Order placed successfully. Expected delivery in {delivery_days} days."
    }

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint providing API information.
    """
    return {
        "message": "Welcome to MediSync Agent API",
        "version": "1.0.0",
        "endpoints": {
            "inventory": "/inventory/{item_name}",
            "suppliers": "/suppliers/{item_name}",
            "place_order": "/place_order"
        }
    }