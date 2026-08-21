import json
import random
import string
import math

def generate_neon_city():
    """
    Generates a procedural cyberpunk city map.
    Creates grid-based blocks with buildings, road networks, and visual properties.
    """
    print("<architect_log> Initializing Neon Metropolis Blueprint... </architect_log>")
    
    config = {
        "width": 1000,
        "height": 800,
        "grid_rows": 4,
        "grid_cols": 5,
        "road_width": 30,
        "neon_palette": ["#00FFFF", "#FF00FF", "#FFFF00", "#00FF00", "#FF0055"],
        "blocks": [],
        "traffic_nodes": [] 
    }
    
    # Calculate block dimensions
    total_road_x = (config["grid_cols"] + 1) * config["road_width"]
    total_road_y = (config["grid_rows"] + 1) * config["road_width"]
    
    block_w = (config["width"] - total_road_x) / config["grid_cols"]
    block_h = (config["height"] - total_road_y) / config["grid_rows"]
    
    for r in range(config["grid_rows"]):
        for c in range(config["grid_cols"]):
            # Calculate grid position
            x = c * (block_w + config["road_width"]) + config["road_width"]
            y = r * (block_h + config["road_width"]) + config["road_width"]
            
            buildings = []
            # Determine density based on distance from center (city center is denser)
            dist_from_center = math.sqrt((r - config["grid_rows"]/2)**2 + (c - config["grid_cols"]/2)**2)
            density = max(1, int(5 - dist_from_center)) 
            
            for _ in range(density):
                b_w = random.randint(20, int(block_w * 0.8))
                b_h = random.randint(20, int(block_h * 0.8))
                b_height_3d = random.randint(50, 300) # Height for pseudo-3D rendering
                
                # Random position within block
                bx = x + random.randint(0, int(block_w - b_w))
                by = y + random.randint(0, int(block_h - b_h))
                
                color = random.choice(config["neon_palette"])
                
                buildings.append({
                    "x": bx,
                    "y": by,
                    "w": b_w,
                    "h": b_h,
                    "height": b_height_3d,
                    "color": color,
                    "id": f"BLD-{r}{c}-{_}" 
                })
                
                # Add traffic node if building is large
                if b_height_3d > 100:
                    config["traffic_nodes"].append({
                        "x": bx + b_w/2,
                        "y": by + b_h/2,
                        "type": "hub"
                    })
            
            config["blocks"].append({
                "x": x, "y": y, "w": block_w, "h": block_h,
                "buildings": buildings
            })
    
    # Save to file
    with open('city_data.json', 'w') as f:
        json.dump(config, f)
    
    print(f"<architect_log> Blueprint Complete. Generated {len(config['blocks'])} blocks and {len(config['traffic_nodes'])} traffic hubs. Saved to city_data.json </architect_log>")

if __name__ == "__main__":
    generate_neon_city()