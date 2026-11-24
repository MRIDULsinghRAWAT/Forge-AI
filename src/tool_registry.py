import datetime
import math
import os
import csv
import json
from typing import Dict, Any, List

class ToolRegistry:
    """
    Curated tool registry for the Agent Factory.
    Enables tools like CSV lookup, calculator, date provider, and keyless public API (weather).
    Crucial evaluation check: The factory must attach ONLY the tools the brief actually needs.
    """
    def __init__(self, data_folder: str = ""):
        self.data_folder = data_folder
        self.registry = {
            "calculator": {
                "name": "calculator",
                "description": "Performs mathematical arithmetic calculations and expressions (e.g., price calculations, overtime multipliers, budgets).",
                "parameters": {"expression": "string, mathematical formula to evaluate e.g. '4200 * 3'"}
            },
            "csv_lookup": {
                "name": "csv_lookup",
                "description": "Performs fast structured row lookups and searches over tabular catalog CSVs (e.g. part IDs, prices, stock levels).",
                "parameters": {"query": "string, part ID or column keyword to search in CSV", "file": "optional filename"}
            },
            "current_date": {
                "name": "current_date",
                "description": "Returns current ISO date, month, year, and weekday for policy expiration or deadline comparisons.",
                "parameters": {}
            },
            "weather_api": {
                "name": "weather_api",
                "description": "Fetches current weather forecasts for a marine port or city via keyless open-meteo API.",
                "parameters": {"latitude": "float", "longitude": "float"}
            }
        }

    def list_available_tools(self) -> List[Dict[str, Any]]:
        return list(self.registry.values())

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        if tool_name == "calculator":
            expr = kwargs.get("expression", "")
            # Safe evaluation of math expressions
            allowed_names = {"abs": abs, "round": round, "min": min, "max": max, "math": math}
            clean_expr = expr.replace("^", "**")
            try:
                # Sanitize to prevent arbitrary code
                if any(bad in clean_expr for bad in ["import", "eval", "exec", "__", "open", "os", "sys"]):
                    return {"error": "Invalid characters in mathematical expression"}
                result = eval(clean_expr, {"__builtins__": None}, allowed_names)
                return {"success": True, "result": result}
            except Exception as e:
                return {"error": f"Calculation error: {str(e)}"}

        elif tool_name == "csv_lookup":
            query = kwargs.get("query", "").lower()
            filename = kwargs.get("file", "")
            matched_rows = []
            search_dir = self.data_folder if self.data_folder else "datasets"
            csv_files = []
            for root, _, files in os.walk(search_dir):
                for f in files:
                    if f.endswith(".csv"):
                        if not filename or filename in f:
                            csv_files.append(os.path.join(root, f))

            for csv_path in csv_files:
                try:
                    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if any(query in str(v).lower() for v in row.values()):
                                row_with_meta = dict(row)
                                row_with_meta["_source_file"] = os.path.basename(csv_path)
                                matched_rows.append(row_with_meta)
                except Exception as e:
                    pass

            return {"success": True, "matches_count": len(matched_rows), "results": matched_rows[:10]}

        elif tool_name == "current_date":
            now = datetime.datetime.now()
            return {
                "iso_date": now.strftime("%Y-%m-%d"),
                "formatted": now.strftime("%A, %B %d, %Y"),
                "year": now.year,
                "month": now.month,
                "day": now.day
            }

        elif tool_name == "weather_api":
            import requests
            lat = kwargs.get("latitude", 51.9244) # Default Rotterdam
            lon = kwargs.get("longitude", 4.4777)
            try:
                url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m"
                resp = requests.get(url, timeout=4)
                if resp.status_code == 200:
                    return {"success": True, "data": resp.json().get("current", {})}
                return {"error": f"API returned status {resp.status_code}"}
            except Exception as e:
                return {"error": f"Weather API unreachable: {str(e)}"}

        return {"error": f"Tool '{tool_name}' not found in registry"}

