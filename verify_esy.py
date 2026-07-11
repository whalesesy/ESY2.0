import sys
import os
import shutil

# Ensure relative imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    print("[*] Testing module imports...")
    try:
        import config
        import voice
        import commands
        import core.memory as memory
        import core.brain as brain
        from core.plugin_manager import PluginManager
        print("[+] All modules imported successfully.")
        return True
    except Exception as e:
        print(f"[-] Import test failed: {e}")
        return False

def test_database():
    print("[*] Testing database persistence and operations...")
    import core.memory as memory
    
    # Init DB
    memory.init_db()
    
    # Test preferences
    memory.set_preference("test_key", "test_value")
    val = memory.get_preference("test_key")
    assert val == "test_value", f"Preference retrieval failed: expected 'test_value', got '{val}'"
    
    # Test chat saving
    memory.clear_chat_history()
    memory.save_chat_message("user", "Hello assistant")
    memory.save_chat_message("assistant", "Hello user")
    history = memory.get_chat_history()
    assert len(history) == 2, f"Chat history size unexpected: {len(history)}"
    assert history[0]["content"] == "Hello assistant"
    assert history[1]["content"] == "Hello user"
    
    # Test notes
    memory.delete_all_notes()
    memory.add_note("Meeting at 3pm")
    notes = memory.get_all_notes()
    assert len(notes) == 1, f"Notes count unexpected: {len(notes)}"
    assert notes[0]["content"] == "Meeting at 3pm"
    
    # Test security lab completion logs
    success = memory.log_lab_completion(
        platform="Hack The Box",
        room_name="Archetype",
        flags=2,
        notes="MSSQL privilege escalation test."
    )
    assert success is True, "Failed to log lab completion"
    
    stats = memory.get_security_stats()
    assert stats["total_rooms"] >= 1, f"Expected total_rooms >= 1, got {stats['total_rooms']}"
    assert stats["total_flags"] >= 2, f"Expected total_flags >= 2, got {stats['total_flags']}"
    
    history = memory.get_lab_history(platform="Hack The Box")
    assert len(history) >= 1, "Expected HTB lab history to be populated"
    assert history[0]["room_name"] == "Archetype", f"Expected room 'Archetype', got '{history[0]['room_name']}'"
    
    # Test nutrition logging
    food_success = memory.log_food_entry(
        meal_type="Lunch",
        food_item="Oats and whey",
        calories=450,
        protein=35,
        notes="Focus optimization snack."
    )
    assert food_success is True, "Failed to log food entry"
    
    food_stats = memory.get_nutrition_stats()
    assert food_stats["total_calories"] >= 450, f"Expected total_calories >= 450, got {food_stats['total_calories']}"
    assert food_stats["total_protein"] >= 35, f"Expected total_protein >= 35, got {food_stats['total_protein']}"
    
    food_history = memory.get_nutrition_history()
    assert len(food_history) >= 1, "Expected nutrition history to be populated"
    assert food_history[0]["food_item"] == "Oats and whey", f"Expected food item 'Oats and whey', got '{food_history[0]['food_item']}'"
    
    print("[+] Database memory operations: OK")

def test_plugin_routing():
    print("[*] Testing plugin manager discovery and routing...")
    import config
    from core.plugin_manager import PluginManager
    
    plugin_mgr = PluginManager(config.BASE_DIR / "plugins")
    plugin_mgr.load_plugins()
    
    plugin_names = [p.name for p in plugin_mgr.plugins]
    print(f"[*] Found plugins: {plugin_names}")
    assert "Security Intelligence Router" in plugin_names, "Security Intelligence Router plugin missing"
    assert "Lifestyle & Nutrition Intelligence" in plugin_names, "Nutrition plugin missing"
    
    # Test system stats routing
    handled, response = plugin_mgr.route_command("show cpu load")
    assert handled is True, "System command should be handled by SystemPlugin"
    assert "cpu" in response.lower() or "percent" in response.lower() or "usage" in response.lower(), f"Unexpected response: {response}"
    print("[+] System plugin routing: OK")
    
    # Test network latency routing
    handled, response = plugin_mgr.route_command("check ping latency")
    assert handled is True, "Network command should be handled by NetworkPlugin"
    assert "ping" in response.lower() or "internet" in response.lower() or "latency" in response.lower(), f"Unexpected response: {response}"
    print("[+] Network plugin routing: OK")
    
    # Test productivity note-taking routing
    handled, response = plugin_mgr.route_command("take note buy milk")
    assert handled is True, "Productivity command should be handled by ProductivityPlugin"
    assert "note recorded" in response.lower() or "note" in response.lower(), f"Unexpected response: {response}"
    print("[+] Productivity note routing: OK")
    
    # Test security plugin routing - log room
    handled, response = plugin_mgr.route_command("log room HTB Archetype flags 2 notes Windows exploit")
    assert handled is True, "Security plugin should handle log room command"
    assert "logged" in response.lower() or "archetype" in response.lower(), f"Unexpected response: {response}"
    print("[+] Security plugin logging routing: OK")
    
    # Test security plugin routing - show progress
    handled, response = plugin_mgr.route_command("show progress")
    assert handled is True, "Security plugin should handle show progress command"
    assert "compromised" in response.lower() or "flags" in response.lower(), f"Unexpected response: {response}"
    print("[+] Security plugin progress report: OK")
    
    # Test nutrition plugin routing - log meal
    handled, response = plugin_mgr.route_command("log meal lunch oats 400 cals 20 protein")
    assert handled is True, "Nutrition plugin should handle log meal command"
    assert "sync" in response.lower() or "logged" in response.lower() or "lunch" in response.lower(), f"Unexpected response: {response}"
    print("[+] Nutrition plugin logging routing: OK")
    
    # Test nutrition plugin routing - show stats
    handled, response = plugin_mgr.route_command("show nutrition")
    assert handled is True, "Nutrition plugin should handle show nutrition command"
    assert "consumed" in response.lower() or "calories" in response.lower(), f"Unexpected response: {response}"
    print("[+] Nutrition plugin progress report: OK")

def main():
    print("=== ESY JARVIS VERIFICATION TESTS ===")
    if not test_imports():
        sys.exit(1)
        
    try:
        test_database()
        test_plugin_routing()
        print("[+] All verification tests passed successfully!")
    except AssertionError as e:
        print(f"[-] Verification assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[-] Verification encountered an unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
