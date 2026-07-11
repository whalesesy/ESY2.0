import re
import urllib.request
import json
import sys
import core.memory as memory
from core.plugin import BasePlugin

class NutritionPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "Lifestyle & Nutrition Intelligence"
        self.description = "Manages caloric logging, meal recommendations, and Open Food Facts lookup."
        self.keywords = ["eat", "food", "calorie", "recipe", "protein", "diet", "meal", "nutrition", "ate"]

    def execute(self, command_text: str) -> str:
        command_lower = command_text.lower().strip()

        # 1. Open Food Facts API lookup (by barcode or product search)
        if "check product" in command_lower:
            product_search = command_lower.replace("check product", "").strip()
            return self._fetch_food_facts(product_search)

        # 2. Manual Food Logging Logic
        # e.g., "log meal lunch chicken rice 600 cals 45 protein"
        if "log meal" in command_lower or "ate" in command_lower:
            pattern = r'(?:log meal|ate)\s+(breakfast|lunch|dinner|snack)?\s*(.+?)\s+(\d+)\s*cals?\s+(\d+)\s*protein'
            match = re.search(pattern, command_lower, re.IGNORECASE)
            
            if match:
                meal_type_raw = match.group(1)
                food_item = match.group(2).strip()
                calories = int(match.group(3))
                protein = int(match.group(4))
                
                meal_type = meal_type_raw.capitalize() if meal_type_raw else "Snack"
                
                success = memory.log_food_entry(
                    meal_type=meal_type,
                    food_item=food_item,
                    calories=calories,
                    protein=protein,
                    notes="Logged via ESY terminal."
                )
                
                if success:
                    return f"🍏 **Jarvis Life Sync:** Logged {meal_type} of '{food_item}' ({calories} kcal, {protein}g protein) into database context."
                else:
                    return "❌ Error: Failed to log food entry to database."
            else:
                return (
                    "⚠️ **Nutrition Logger Helper:** To log a meal, use the format:\n"
                    "`log meal [Breakfast|Lunch|Dinner|Snack] [FoodItem] [Calories] cals [Protein] protein`\n"
                    "Example: `log meal lunch chicken rice 650 cals 40 protein`"
                )

        # 3. View Nutrition Stats / Progress
        if "show nutrition" in command_lower or "nutrition stats" in command_lower:
            stats = memory.get_nutrition_stats()
            history = memory.get_nutrition_history()
            
            output = (
                f"🥗 **Jarvis Lifestyle Operations Overview (Today):**\n"
                f"• Total Calories Consumed: {stats['total_calories']} kcal\n"
                f"• Total Protein Consumed : {stats['total_protein']}g\n\n"
                f"**Recent Food Logs:**\n"
            )
            
            if not history:
                output += "No meals logged recently."
            else:
                for row in history[:5]: # Show last 5
                    output += f"• [{row['logged_at'][11:16]}] {row['meal_type']}: **{row['food_item']}** ({row['calories']} kcal | {row['protein']}g protein)\n"
            return output

        # 4. Fallback/Default
        return (
            "🍱 **Jarvis Lifestyle Operations:** Target query route identified.\n"
            "- To analyze store products, specify: `check product [item_name/barcode]`.\n"
            "- To log dietary entries, specify: `log meal [meal_type] [item] [calories] cals [protein] protein`.\n"
            "- To view your logs, say `show nutrition`."
        )

    def _fetch_food_facts(self, product_query: str) -> str:
        """Queries the Open Food Facts API for unauthenticated open-source macro tracking."""
        try:
            # Handle standard UPC barcode parsing or basic search string
            if product_query.isdigit():
                url = f"https://world.openfoodfacts.org/api/v2/product/{product_query}.json"
            else:
                # Encode search terms
                encoded_terms = urllib.parse.quote(product_query)
                url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={encoded_terms}&search_simple=1&action=process&json=1"
                
            req = urllib.request.Request(url, headers={'User-Agent': 'ESYAssistant/2.0'})
            with urllib.request.urlopen(req, timeout=5.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    # 1. Product barcode direct lookup
                    if "product" in data:
                        prod = data["product"]
                        name = prod.get("product_name", "Unknown Product")
                        nutriments = prod.get("nutriments", {})
                        cals = nutriments.get("energy-kcal_100g", "Unknown")
                        proteins = nutriments.get("proteins_100g", "Unknown")
                        return (
                            f"🥗 **Open Food Facts Scanner Analysis:**\n"
                            f"• **Product:** {name}\n"
                            f"• **Calories (per 100g):** {cals} kcal\n"
                            f"• **Protein (per 100g):** {proteins}g\n"
                        )
                    # 2. Text search search results
                    elif "products" in data and len(data["products"]) > 0:
                        prod = data["products"][0]
                        name = prod.get("product_name", "Unknown Product")
                        nutriments = prod.get("nutriments", {})
                        cals = nutriments.get("energy-kcal_100g", "Unknown")
                        proteins = nutriments.get("proteins_100g", "Unknown")
                        return (
                            f"🥗 **Open Food Facts Search Result (Best Match):**\n"
                            f"• **Product:** {name}\n"
                            f"• **Calories (per 100g):** {cals} kcal\n"
                            f"• **Protein (per 100g):** {proteins}g\n"
                        )
            return f"❌ Could not resolve product info for: '{product_query}'"
        except Exception as e:
            return f"⚠️ Network timeout connecting to lifestyle telemetry engines: {e}"
