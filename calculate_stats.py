import sys
import json
from engine.common import STATS, OUTPUT_JSON, OUTPUT_JS_DATA, OUTPUT_REPORT
from engine import (
    load_game_data,
    calculate_avg_stats,
    get_valid_classes,
    generate_report,
    get_fe8_class_keys
)

def run_batch_calculation(game_key, db):
    """Generates average stats results for all characters in all valid classes."""
    results = {}
    stats_list = ["HP", "Str", "Mag", "Skl", "Spd", "Lck", "Def", "Bld", "Mov"] if game_key == "fe5" else STATS
    for char_name, char_data in sorted(db["characters"].items()):
        results[char_name] = {
            "name": char_name,
            "join_lv": char_data["join_lv"],
            "default_class": char_data["default_class"],
            "is_female": char_data["is_female"],
            "classes": {}
        }
        
        if game_key == "fe8":
            path_to_key = get_fe8_class_keys(char_name, char_data)
            for path, key in path_to_key.items():
                try:
                    calc = calculate_avg_stats(game_key, char_data, list(path), db)
                    results[char_name]["classes"][key] = {
                        "class_path": calc["class_path"],
                        "final_level": calc["final_level"],
                        "stats": {s: round(calc["stats"][s], 2) for s in stats_list}
                    }
                except Exception as ex:
                    print(f"Error calculating {game_key.upper()} {char_name} as {key}: {ex}")
        else:
            valid_classes = get_valid_classes(game_key, char_name, char_data)
            for cls in valid_classes:
                try:
                    calc = calculate_avg_stats(game_key, char_data, cls, db)
                    results[char_name]["classes"][cls] = {
                        "class_path": calc["class_path"],
                        "final_level": calc["final_level"],
                        "stats": {s: round(calc["stats"][s], 2) for s in stats_list}
                    }
                except Exception as ex:
                    print(f"Error calculating {game_key.upper()} {char_name} as {cls}: {ex}")
    return results

def main():
    # 1. Load Databases
    databases = {}
    for gk in ["fe5", "fe6", "fe7", "fe8", "fe9", "fe10", "fe11", "fe12"]:
        try:
            databases[gk] = load_game_data(gk)
            print(f"Successfully loaded {gk.upper()} campaign data.")
        except Exception as e:
            print(f"Failed to load {gk.upper()} data: {e}")
            return

    db_fe5 = databases["fe5"]
    db_fe6 = databases["fe6"]
    db_fe7 = databases["fe7"]
    db_fe8 = databases["fe8"]
    db_fe9 = databases["fe9"]
    db_fe10 = databases["fe10"]
    db_fe11 = databases["fe11"]
    db_fe12 = databases["fe12"]

    # Check for CLI Query Arguments
    if len(sys.argv) > 1:
        query_char = sys.argv[1].strip()
        
        # Search all databases
        char_name = None
        db_active = None
        game_label = None
        
        for glabel, db in [("FE5", db_fe5), ("FE12", db_fe12), ("FE6", db_fe6), ("FE7", db_fe7), ("FE8", db_fe8), ("FE9", db_fe9), ("FE10", db_fe10), ("FE11", db_fe11)]:
            for name in db["characters"]:
                if name.lower() == query_char.lower():
                    char_name = name
                    db_active = db
                    game_label = glabel
                    break
            if char_name:
                break
                
        if not char_name:
            # Try substring matches
            matches = {}
            for glabel, db in [("FE5", db_fe5), ("FE12", db_fe12), ("FE6", db_fe6), ("FE7", db_fe7), ("FE8", db_fe8), ("FE9", db_fe9), ("FE10", db_fe10), ("FE11", db_fe11)]:
                matches[glabel] = [name for name in db["characters"] if query_char.lower() in name.lower()]
            
            total_matches = sum(len(m) for m in matches.values())
            if total_matches == 1:
                for glabel, match_list in matches.items():
                    if match_list:
                        char_name = match_list[0]
                        db_active = databases[glabel.lower()]
                        game_label = glabel
                        break
            elif total_matches > 1:
                print(f"Ambiguous query '{query_char}'. Matches found: " + ", ".join(f"{k}: {v}" for k, v in matches.items() if v))
                return
            else:
                print(f"Character '{query_char}' not found in any database.")
                return

        char_data = db_active["characters"][char_name]
        game_key = game_label.lower()
        valid_classes = get_valid_classes(game_key, char_name, char_data)
        stats_list = ["HP", "Str", "Mag", "Skl", "Spd", "Lck", "Def", "Bld", "Mov"] if game_key == "fe5" else STATS

        if len(sys.argv) > 2:
            query_class = sys.argv[2].strip()
            class_name = None
            for cls in valid_classes:
                if cls.lower() == query_class.lower() or query_class.lower() in cls.lower():
                    class_name = cls
                    break
            
            if not class_name:
                print(f"Class '{query_class}' is not a valid option for {char_name}.")
                print(f"Valid options are: {', '.join(valid_classes)}")
                return
            
            if game_key == "fe8":
                path_to_key = get_fe8_class_keys(char_name, char_data)
                target_path = None
                for path, key in path_to_key.items():
                    if key == class_name:
                        target_path = list(path)
                        break
                calc = calculate_avg_stats(game_key, char_data, target_path, db_active)
            else:
                calc = calculate_avg_stats(game_key, char_data, class_name, db_active)
                
            print(f"\n=========================================================================")
            print(f"DETAILED LEVEL-BY-LEVEL STATS FOR {char_name.upper()} ({game_label}) AS {class_name.upper()}")
            print(f"Path: {calc['class_path']} (Final Level: {calc['final_level']})")
            print(f"=========================================================================\n")
            
            header = f"{'Level':<8} | {'Class':<18} | " + " | ".join(f"{s:<5}" for s in stats_list)
            print(header)
            print("-" * len(header))
            
            for item in calc["history"]:
                lv_str, cls, stats = item
                stats_str = " | ".join(f"{stats[s]:.2f}" for s in stats_list)
                print(f"{str(lv_str):<8} | {cls:<18} | {stats_str}")
            print()
            return
        else:
            print(f"\n=========================================================================")
            print(f"AVERAGE STAT SUMMARY FOR {char_name.upper()} ({game_label})")
            print(f"Base Level: {char_data['join_lv']} | Default Class: {char_data['default_class']}")
            print(f"=========================================================================\n")
            
            header = f"{'Class':<22} | " + " | ".join(f"{s:<5}" for s in stats_list)
            print(header)
            print("-" * len(header))
            
            for cls in sorted(valid_classes):
                if game_key == "fe8":
                    path_to_key = get_fe8_class_keys(char_name, char_data)
                    target_path = None
                    for path, key in path_to_key.items():
                        if key == cls:
                            target_path = list(path)
                            break
                    calc = calculate_avg_stats(game_key, char_data, target_path, db_active)
                else:
                    calc = calculate_avg_stats(game_key, char_data, cls, db_active)
                stats = calc["stats"]
                stats_str = " | ".join(f"{stats[s]:.1f}" for s in stats_list)
                print(f"{cls:<22} | {stats_str}")
            print()
            return

    # Batch calculation mode
    print("Calculating average stats for FE5, FE6, FE7, FE8, FE9, FE10, FE11 and FE12...")

    results = {}
    for gk in ["fe5", "fe6", "fe7", "fe8", "fe9", "fe10", "fe11", "fe12"]:
        results[gk] = run_batch_calculation(gk, databases[gk])

    # Save complete JSON database
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    print(f"Saved complete unified JSON database to {OUTPUT_JSON}")

    # Save JS package structure for HTML Report
    with open(OUTPUT_JS_DATA, "w", encoding="utf-8") as f:
        f.write("const AVERAGE_STATS_DATA = ")
        json.dump(results, f, indent=4)
        f.write(";\n\n")
        
        # Raw FE5
        db_fe5_js = {
            "characters": db_fe5["characters"],
            "classes": {
                "promo_gains": {
                    f"{k[0]} -> {k[1]}" if isinstance(k, tuple) else k: v 
                    for k, v in db_fe5["classes"]["promo_gains"].items()
                }
            }
        }
        f.write("const FE5_RAW_DATABASE = ")
        json.dump(db_fe5_js, f, indent=4)
        f.write(";\n\n")
        
        # Raw FE12
        db_fe12_js = {
            "characters": db_fe12["characters"],
            "classes": {
                "bases": db_fe12["classes"]["bases"],
                "growths": db_fe12["classes"]["growths"],
                "caps": db_fe12["classes"]["caps"],
                "promo_gains": {f"{k[0]} -> {k[1]}": v for k, v in db_fe12["classes"]["promo_gains"].items()}
            }
        }
        f.write("const FE12_RAW_DATABASE = ")
        json.dump(db_fe12_js, f, indent=4)
        f.write(";\n\n")

        # Raw FE11
        db_fe11_js = {
            "characters": db_fe11["characters"],
            "classes": {
                "bases": db_fe11["classes"]["bases"],
                "growths": db_fe11["classes"]["growths"],
                "caps": db_fe11["classes"]["caps"],
                "promo_gains": {f"{k[0]} -> {k[1]}": v for k, v in db_fe11["classes"]["promo_gains"].items()}
            }
        }
        f.write("const FE11_RAW_DATABASE = ")
        json.dump(db_fe11_js, f, indent=4)
        f.write(";\n\n")

        # Raw FE6
        db_fe6_js = {
            "characters": db_fe6["characters"],
            "classes": {
                "caps": db_fe6["classes"]["caps"],
                "promo_gains": {f"{k[0]} -> {k[1]}": v for k, v in db_fe6["classes"]["promo_gains"].items()}
            }
        }
        f.write("const FE6_RAW_DATABASE = ")
        json.dump(db_fe6_js, f, indent=4)
        f.write(";\n\n")

        # Raw FE7
        db_fe7_js = {
            "characters": db_fe7["characters"],
            "classes": {
                "caps": db_fe7["classes"]["caps"],
                "promo_gains": db_fe7["classes"]["promo_gains"]
            }
        }
        f.write("const FE7_RAW_DATABASE = ")
        json.dump(db_fe7_js, f, indent=4)
        f.write(";\n\n")

        # Raw FE8
        db_fe8_js = {
            "characters": db_fe8["characters"],
            "classes": {
                "caps": db_fe8["classes"]["caps"],
                "promo_gains": {f"{k[0]} -> {k[1]}": v for k, v in db_fe8["classes"]["promo_gains"].items()}
            }
        }
        f.write("const FE8_RAW_DATABASE = ")
        json.dump(db_fe8_js, f, indent=4)
        f.write(";\n\n")

        # Raw FE9
        db_fe9_js = {
            "characters": db_fe9["characters"],
            "classes": {
                "caps": db_fe9["classes"]["caps"],
                "promo_gains": {f"{k[0]} -> {k[1]}": v for k, v in db_fe9["classes"]["promo_gains"].items()}
            }
        }
        f.write("const FE9_RAW_DATABASE = ")
        json.dump(db_fe9_js, f, indent=4)
        f.write(";\n\n")

        # Raw FE10
        db_fe10_js = {
            "characters": db_fe10["characters"],
            "classes": {
                "caps": db_fe10["classes"]["caps"],
                "promo_gains": {
                    f"{k[0]} -> {k[1]}" if isinstance(k, tuple) else k: v 
                    for k, v in db_fe10["classes"]["promo_gains"].items()
                }
            }
        }
        f.write("const FE10_RAW_DATABASE = ")
        json.dump(db_fe10_js, f, indent=4)
        f.write(";\n")
        
    print(f"Saved unified JS database to {OUTPUT_JS_DATA}")

    # Human-readable report
    generate_report(results, db_fe5, db_fe12, db_fe6, db_fe7, db_fe8, db_fe9, db_fe10, db_fe11, OUTPUT_REPORT)
    print(f"Saved human-readable text report to {OUTPUT_REPORT}")
    print("\nCalculations finished successfully!")
    print(f"Generated average stats for FE5 ({len(results['fe5'])} units), FE6 ({len(results['fe6'])} units), FE7 ({len(results['fe7'])} units), FE8 ({len(results['fe8'])} units), FE9 ({len(results['fe9'])} units), FE10 ({len(results['fe10'])} units), FE11 ({len(results['fe11'])} units), and FE12 ({len(results['fe12'])} units).")



if __name__ == "__main__":
    main()
