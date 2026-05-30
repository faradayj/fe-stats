from engine.common import STATS
from engine.fe5 import get_fe5_direct_promotion_class, STATS_FE5
from engine.fe12 import get_direct_promotion_class
from engine.fe6 import get_fe6_direct_promotion_class
from engine.fe7 import get_fe7_direct_promotion_class
from engine.fe8 import get_fe8_direct_promotion_class
from engine.fe9 import get_fe9_direct_promotion_class
from engine.fe10 import get_fe10_direct_promotion_class
from engine.fe11 import get_fe11_direct_promotion_class


def write_game_leaderboard(f, label, results, db_chars, get_direct_promo_fn, name_col_width=20, stats_list=None):
    if stats_list is None:
        stats_list = STATS
    f.write("------------------------------------------------------------------------\n")
    f.write(f"{label} DIRECT PROMOTION PATHS - BST LEADERBOARD PER CLASS\n")
    f.write("------------------------------------------------------------------------\n")
    
    class_rankings = {}
    for char_name, char_data in results.items():
        if "My Unit" in char_name:
            promoted_or_special = {
                "Falcon Knight", "Dracoknight", "Paladin", "Sniper", "Swordmaster", 
                "Sage", "Bishop", "General", "Hero", "Warrior", "Horseman", "Berserker", "Sorcerer",
                "Lord", "Thief", "Dancer", "Chameleon", "Manakete", "Ballistician"
            }
            for cls_name, cls_data in char_data["classes"].items():
                if cls_name in promoted_or_special:
                    bst = sum(cls_data["stats"].values())
                    if cls_name not in class_rankings:
                        class_rankings[cls_name] = []
                    class_rankings[cls_name].append({
                        "name": char_name,
                        "stats": cls_data["stats"],
                        "bst": bst,
                        "final_level": cls_data["final_level"]
                    })
        else:
            direct_cls = get_direct_promo_fn(char_name, db_chars[char_name])
            if direct_cls in char_data["classes"]:
                cls_data = char_data["classes"][direct_cls]
                bst = sum(cls_data["stats"].values())
                
                if direct_cls not in class_rankings:
                    class_rankings[direct_cls] = []
                    
                class_rankings[direct_cls].append({
                    "name": char_name,
                    "stats": cls_data["stats"],
                    "bst": bst,
                    "final_level": cls_data["final_level"]
                })
            
    for cls_name in sorted(class_rankings.keys()):
        char_list = sorted(class_rankings[cls_name], key=lambda x: x["bst"], reverse=True)
        f.write(f"\n=== {cls_name.upper()} (Max Level: {char_list[0]['final_level']}) ===\n")
        f.write(f"  {'Rank':<4} | {'Name':<{name_col_width}} | {'BST':<6} | " + " ".join(f"{s:<4}" for s in stats_list) + "\n")
        f.write("  " + "-" * (17 + name_col_width + len(stats_list) * 5) + "\n")
        
        for rank, item in enumerate(char_list, 1):
            leader_flag = " ★" if rank == 1 else ""
            stats_str = " ".join(f"{item['stats'][s]:4.1f}" for s in stats_list)
            f.write(f"  #{rank:<3} | {item['name'] + leader_flag:<{name_col_width}} | {item['bst']:6.1f} | {stats_str}\n")
        f.write("\n")

def generate_report(unified_results, db_fe5, db_fe12, db_fe6, db_fe7, db_fe8, db_fe9, db_fe10, db_fe11, output_path):
    results_fe5 = unified_results["fe5"]
    results_fe12 = unified_results["fe12"]
    results_fe6 = unified_results["fe6"]
    results_fe7 = unified_results["fe7"]
    results_fe8 = unified_results["fe8"]
    results_fe9 = unified_results["fe9"]
    results_fe10 = unified_results["fe10"]
    results_fe11 = unified_results["fe11"]
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("========================================================================\n")
        f.write("FIRE EMBLEM MULTI-GAME AVERAGE STATS REPORT\n")
        f.write("========================================================================\n\n")
        
        # --- FE5 Section ---
        f.write("========================================================================\n")
        f.write("FIRE EMBLEM 5: THRACIA 776 (FE5) AVERAGE STATS REPORT\n")
        f.write("========================================================================\n\n")
        
        write_game_leaderboard(f, "FE5", results_fe5, db_fe5["characters"], get_fe5_direct_promotion_class, name_col_width=20, stats_list=STATS_FE5)
        f.write("\n\n")
        
        # --- FE12 Section ---
        f.write("========================================================================\n")
        f.write("FIRE EMBLEM 12: HEROES OF LIGHT AND SHADOW (FE12) AVERAGE STATS REPORT\n")
        f.write("========================================================================\n\n")
        
        # Pegasus Knight manual evaluations
        f.write("------------------------------------------------------------------------\n")
        f.write("FE12 PEGASUS KNIGHT DEFAULT EVALUATIONS (Elysian Whip Falcon Knight 20/20)\n")
        f.write("------------------------------------------------------------------------\n")
        peg_knights = ["Shiida", "Caeda", "Catria", "Palla", "Est"]
        for pk in peg_knights:
            if pk in results_fe12 and "Falcon Knight" in results_fe12[pk]["classes"]:
                pk_data = results_fe12[pk]
                fk_stats = pk_data["classes"]["Falcon Knight"]["stats"]
                f.write(f"\n{pk} (Pegasus Knight Level {pk_data['join_lv']} -> Falcon Knight 20/20):\n")
                f.write("  " + "  ".join(f"{s}: {fk_stats[s]:.2f}" for s in STATS) + "\n")
        f.write("\n\n")
        
        write_game_leaderboard(f, "FE12", results_fe12, db_fe12["characters"], get_direct_promotion_class, name_col_width=15)
        
        # --- FE6 Section ---
        f.write("\n\n========================================================================\n")
        f.write("FIRE EMBLEM 6: THE BINDING BLADE (FE6) AVERAGE STATS REPORT\n")
        f.write("========================================================================\n\n")
        
        write_game_leaderboard(f, "FE6", results_fe6, db_fe6["characters"], get_fe6_direct_promotion_class, name_col_width=20)
        
        # --- FE7 Section ---
        f.write("\n\n========================================================================\n")
        f.write("FIRE EMBLEM 7: THE BLAZING BLADE (FE7) AVERAGE STATS REPORT\n")
        f.write("========================================================================\n\n")
        
        write_game_leaderboard(f, "FE7", results_fe7, db_fe7["characters"], get_fe7_direct_promotion_class, name_col_width=20)
        
        # --- FE8 Section ---
        f.write("\n\n========================================================================\n")
        f.write("FIRE EMBLEM 8: THE SACRED STONES (FE8) AVERAGE STATS REPORT\n")
        f.write("========================================================================\n\n")
        
        write_game_leaderboard(f, "FE8", results_fe8, db_fe8["characters"], get_fe8_direct_promotion_class, name_col_width=20)

        # --- FE9 Section ---
        f.write("\n\n========================================================================\n")
        f.write("FIRE EMBLEM 9: PATH OF RADIANCE (FE9) AVERAGE STATS REPORT\n")
        f.write("========================================================================\n\n")
        
        write_game_leaderboard(f, "FE9", results_fe9, db_fe9["characters"], get_fe9_direct_promotion_class, name_col_width=20)

        # --- FE10 Section ---
        f.write("\n\n========================================================================\n")
        f.write("FIRE EMBLEM 10: RADIANT DAWN (FE10) AVERAGE STATS REPORT\n")
        f.write("========================================================================\n\n")
        
        write_game_leaderboard(f, "FE10", results_fe10, db_fe10["characters"], get_fe10_direct_promotion_class, name_col_width=20)

        # --- FE11 Section ---
        f.write("\n\n========================================================================\n")
        f.write("FIRE EMBLEM 11: SHADOW DRAGON (FE11) AVERAGE STATS REPORT\n")
        f.write("========================================================================\n\n")
        
        write_game_leaderboard(f, "FE11", results_fe11, db_fe11["characters"], get_fe11_direct_promotion_class, name_col_width=20)

