from google.protobuf.json_format import MessageToDict
from pymongo import MongoClient
from datetime import datetime, timedelta
import re
import numpy as np


def get_elemMatchStatement(property, value):

    if value != None:
        return {"$elemMatch": {"property": property, "value": value}}
    return {"$elemMatch": {"property": property}}


class MarketDataClient:
    def __init__(self):
        client = MongoClient("mongodb://localhost:27017/")
        db = client["marketplace"]
        self.collection = db["listings"]
        self.collection.create_index("listingId", unique=True)

    # Sample function to handle MarketResponse
    def put_listing(self, listing):
        listing_dict = MessageToDict(listing)

        if "listingId" not in listing_dict or listing_dict["listingId"] is None:
            print("Invalid listingId found, skipping this listing.")
            print(listing)
            return

        listing_dict["item"]["itemId"], listing_dict["item"]["rarity"] = (
            self.get_id_and_rarity(listing)
        )

        # Calculate timePosted
        time_to_expire = listing.timeToExpire / 1000  # Convert ms to seconds
        time_posted = datetime.now() - timedelta(
            seconds=604800 - time_to_expire
        )  # 604800 seconds in a week
        listing_dict["timePosted"] = int(time_posted.timestamp())

        # Insert into MongoDB
        self.collection.replace_one(
            {"listingId": listing_dict["listingId"]}, listing_dict, upsert=True
        )

    def show_listings(self):
        listings = self.collection.find()
        for listing in listings:
            print(listing)

    def wipe_listings(self):
        self.collection.delete_many({})

    def get_all_prices_for_item(self, item_id):
        query = {"item.itemId": item_id}
        projection = {"_id": 0, "price": 1}
        results = self.collection.find(query, projection)
        # Print the prices
        return results

    def query(self, itemId, rarity, primary_effects, secondary_effects):
        query = {}
        if itemId != None:
            query["item.itemId"] = itemId

        if rarity != None:
            query["item.rarity"] = rarity

        if len(primary_effects) > 0:
            query["item.primaryPropertyArray"] = {
                "$all": [
                    get_elemMatchStatement(p, primary_effects[p])
                    for p in primary_effects
                ]
            }
        if len(secondary_effects) > 0:
            query["item.secondaryPropertyArray"] = {
                "$all": [
                    get_elemMatchStatement(p, secondary_effects[p])
                    for p in secondary_effects
                ]
            }
        print("query: ", query)

        return self.collection.find(query)

    def get_id_and_rarity(self, listing):
        listing_dict = MessageToDict(listing)
        item_id = listing_dict["item"]["itemId"]
        match = re.search(r"_(\d+)$", item_id)
        if match:
            item_id = item_id[: match.start()]
            rarity = int(match.group(1)) // 1000
        elif "secondaryPropertyArray" in listing_dict["item"]:
            rarity = len(listing_dict["item"]["secondaryPropertyArray"]) + 2
        else:
            rarity = -1
        return item_id, rarity

    def get_previous_prices_for_listing(
        self, listing, use_secondary=False, use_rolls=False
    ):
        print(listing)
        item_id, rarity = self.get_id_and_rarity(listing)

        secondary = (
            {p.property: None for p in listing.item.secondaryPropertyArray}
            if use_secondary
            else {}
        )
        secondary = (
            {p.property: p.value for p in listing.item.secondaryPropertyArray}
            if use_rolls
            else secondary
        )
        results = self.query(
            item_id,
            rarity,
            {},
            secondary,
        )
        prices = np.array([r["price"] for r in results])
        return prices

    def get_suggested_price(self, listing):

        target_percentile = 5
        needed_for_confidence = 2

        suggested_price = 0

        base_prices = self.get_previous_prices_for_listing(listing, False, False)
        if len(base_prices) >= needed_for_confidence:
            print("Base price: ", base_prices)
            suggested_price = max(
                suggested_price, np.percentile(base_prices, target_percentile)
            )

        properties_prices = self.get_previous_prices_for_listing(listing, True, False)
        if len(properties_prices) >= needed_for_confidence:
            print("Properties price: ", properties_prices)
            suggested_price = max(
                suggested_price, np.percentile(properties_prices, target_percentile)
            )

        rolls_price = self.get_previous_prices_for_listing(listing, True, True)
        if len(rolls_price) >= needed_for_confidence:
            print("Rolls price: ", rolls_price)
            suggested_price = max(
                suggested_price, np.percentile(rolls_price, target_percentile)
            )

        return suggested_price


def main():

    client = MarketDataClient()
    # client.show_listings()
    # prices = client.get_all_prices_for_item(
    #     "DesignDataItem:Id_Item_GlovesOfUtility_5001"
    # )
    # for price in prices:
    #     print(price)
    result = client.query(
        "DesignDataItem:Id_Item_GlovesOfUtility",
        5,
        {},
        {
            "DesignDataItemPropertyType:Id_ItemPropertyType_Effect_MemoryCapacityBonus": None
        },
    )

    for r in result:
        print(r)


if __name__ == "__main__":
    main()
