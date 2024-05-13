import re
from fastapi import FastAPI, HTTPException
import redis

from models import ItemPayLoad

#grocery_list: dict[int, ItemPayLoad] = {}
redis_client = redis.StrictRedis(host='0.0.0.0', port=6379, db=0, decode_responses=True)
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

# Rout to add an item
@app.post("/items/{item_name}/{quantity}")
def add_item(item_name:str, quantity:int):
    if quantity <=0:
        raise HTTPException(status_code=400, detail='Quantity must be greater than 0.')
    # if item already exists, we'll just add the quantity.
    # get all item names
    #items_ids= {item.item_name: item.item_id if item.item_id is not None else 0 for item in grocery_list.values()}
    item_id_str = redis_client.hget("item_name_to_id", item_name)
    #if item_name in items_ids.keys():
    if item_id_str is not None:
        # get index of item_name in items_ids, which is the item_id
        # item_id = items_ids[item_name]
        # grocery_list[item_id].quantity += quantity
        item_id = int(item_id_str)
        redis_client.hincrby(f"item_id:{item_id}", "quantity", quantity)
    # otherwise, create a new item
    else:
        # generate an ID for the item based on the highest ID in the grocery_list
        #item_id = max(grocery_list.keys()) + 1 if grocery_list else 0
        item_id = redis_client.incr("item_ids")
        # grocery_list[item_id] = ItemPayLoad(
        #     item_id= item_id, item_name=item_name, quantity=quantity
        # )
        redis_client.hset(
            f"item_id:{item_id}",
            mapping={
                "item_id": item_id,
                "item_name": item_name,
                "quantity": quantity,
            })
        redis_client.hset("item_name_to_id", item_name, item_id)
    #return {"item": grocery_list[item_id]}
    return {"item": ItemPayLoad(item_id=item_id, item_name=item_name, quantity=quantity)}

# Route to list a specific item by ID
@app.get("/items/{item_id}")
def list_item(item_id: int):
    if not redis_client.hexists(f"item_id:{item_id}", "item_id"):
        raise HTTPException(status_code=404, detail="Item not found.")
    else:
        return {"item": redis_client.hgetall(f"item_id:{item_id}")}

# def list_item(item_id: int) -> dict[str, ItemPayLoad]:
#     if item_id not in grocery_list:
#         raise HTTPException(status_code=400, detail='Item not found.')
#     return {"Item": grocery_list[item_id]}

# Rout to list all items
@app.get("/items")
def list_items():
    items = []
    stored_items = redis_client.hgetall("item_name_to_id")

    for name, id_str in stored_items.items():
        item_id = int(id_str)
        item_name_str = redis_client.hget(f"item_id:{item_id}", "item_name")
        if item_name_str is not None:
            item_name = item_name_str
        else:
            continue

        item_quantity_str = redis_client.hget(f"item_id:{item_id}", "quantity")
        if item_quantity_str is not None:
            item_quantity = int(item_quantity_str)
        else:
            item_quantity = 0

        items.append(
            ItemPayLoad(item_id=item_id, item_name=item_name, quantity=item_quantity)
        )
    return {"items": items}
# def list_items() -> dict[str, dict[int, ItemPayLoad]]:
#     return {"Items": grocery_list}

# Route to delete a specific item by ID
@app.delete("/items/{item_id}")
def delete_item(item_id):
    if not redis_client.hexists(f"item_id:{item_id}", "item_id"):
        raise HTTPException(status_code=404, detail="Item not found.")
    else:
        item_name = redis_client.hget(f"item_id:{item_id}", "item_name")
        redis_client.hdel("item_name_to_id", f"{item_name}")
        redis_client.delete(f"item_id:{item_id}")
        return {"result": "Item deleted."}

# def delete_item(item_id:int):
#     if item_id not in grocery_list:
#         raise HTTPException(status_code=404, detail='Item not found.')
#     deleted_item = grocery_list[item_id]
#     del grocery_list[item_id]
#     return {"result": f'Item "{deleted_item}" is deleted.'}

# Route to remove some quantity of a specific item by ID
@app.delete("/items/{item_id}/{quantity}")
def remove_quantity(item_id, quantity):
    if not redis_client.hexists(f"item_id:{item_id}", "item_id"):
        raise HTTPException(status_code=404, detail="Item not found.")
    
    item_quantity = redis_client.hget(f"item_id:{item_id}", "quantity")
    if item_quantity is None:
        existing_quantity = 0
    else:
        existing_quantity = int(item_quantity)
    if existing_quantity <= quantity:
        item_name = redis_client.hget(f"item_id:{item_id}", "item_name")
        redis_client.hdel("item_name_to_id", f"{item_name}")
        redis_client.delete(f"item_id:{item_id}")
        return {"result" : "Item deleted."}
    else:
        redis_client.hincrby(f"item_id:{item_id}", "quantity", -quantity)
        return {"result": f"{quantity} items removed."}
# def remove_quantity(item_id:int, quantity:int):
#     if item_id not in grocery_list:
#         raise HTTPException(status_code=404, detail='Item not found.')
#     # if quantity to be removed is higher or equal to item's quantity, deltet the item
#     if quantity >= grocery_list[item_id].quantity:
#         deleted_item = grocery_list[item_id]
#         del grocery_list[item_id]
#         return {"result": f'Item "{deleted_item}" is deleted'}
#     else:
#         grocery_list[item_id].quantity -= quantity
#         return {"result": f'{quantity} of {grocery_list[item_id].item_name} is removed.'}
