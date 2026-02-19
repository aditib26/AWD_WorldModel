"""Command-line demo interface for water management module"""

import sys
from datetime import date, datetime
from .storage import JSONFileStorage
from .state import StateManager
from .llm_extractor import MockSlotExtractor
from .weather import StubWeatherAdapter
from .hydrology import HydrologyCoreSimulator
from .rules_handbook import HandbookRuleSet
from .rules_general import GeneralRuleSet
from .resolver import PolicyResolver
from .planner import WaterManagementPlanner
from .logger import EventLogger
from .explain import ExplanationGenerator
from .schemas import FarmerProfile, DailyCheckIn


class WaterManagementCLI:
    """Interactive CLI for water management"""
    
    def __init__(self):
        self.storage = JSONFileStorage()
        self.state_manager = StateManager()
        self.extractor = MockSlotExtractor()
        self.weather_adapter = StubWeatherAdapter()
        self.hydrology = HydrologyCoreSimulator()
        self.handbook = HandbookRuleSet()
        self.general = GeneralRuleSet()
        self.resolver = PolicyResolver(self.handbook, self.general, mode="handbook_plus")
        self.planner = WaterManagementPlanner(self.hydrology, self.resolver)
        self.logger = EventLogger()
        
        self.current_farm_id = None
    
    def run(self):
        """Main CLI loop"""
        print("=" * 60)
        print("🌾 RICE WATER MANAGEMENT ASSISTANT (CLI Demo)")
        print("=" * 60)
        print("Type 'help' for available commands")
        print()
        
        while True:
            try:
                command = input("> ").strip().lower()
                
                if not command:
                    continue
                
                if command == "exit" or command == "quit":
                    print("👋 Goodbye!")
                    break
                
                elif command == "help":
                    self.show_help()
                
                elif command == "create":
                    self.create_profile()
                
                elif command == "select":
                    self.select_farm()
                
                elif command == "show":
                    self.show_state()
                
                elif command == "checkin":
                    self.do_checkin()
                
                elif command == "chat":
                    self.do_chat()
                
                elif command.startswith("mode"):
                    self.set_mode(command)
                
                elif command.startswith("regime"):
                    self.set_regime(command)
                
                elif command.startswith("weather"):
                    self.set_weather(command)
                
                elif command == "advice":
                    self.get_advice()
                
                elif command == "logs":
                    self.show_logs()
                
                elif command == "clear":
                    print("\n" * 50)
                
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_help(self):
        """Show available commands"""
        print("\n📖 AVAILABLE COMMANDS:")
        print("  create       - Create a new farm profile")
        print("  select       - Select a farm to work with")
        print("  show         - Show current state")
        print("  checkin      - Submit daily check-in")
        print("  chat         - Chat with assistant (type message)")
        print("  advice       - Get irrigation advice")
        print("  mode <mode>  - Set mode (handbook_only|handbook_plus|general_only)")
        print("  regime <reg> - Set regime (AWD|CONTINUOUS|RAINFED|AUTO)")
        print("  weather      - Set manual weather values")
        print("  logs         - Show recent logs")
        print("  clear        - Clear screen")
        print("  help         - Show this help")
        print("  exit/quit    - Exit program")
        print()
    
    def create_profile(self):
        """Create a new farm profile"""
        print("\n📝 CREATE FARM PROFILE")
        print("-" * 40)
        
        try:
            farmer_id = input("Farmer ID: ").strip()
            farm_id = input("Farm ID: ").strip()
            province = input("Province (e.g., An Giang): ").strip() or "An Giang"
            
            print("\nSoil type options: alluvial, acid_sulfate, clay, sandy, unknown")
            soil_type = input("Soil type: ").strip() or "alluvial"
            
            print("\nIrrigation access? (yes/no)")
            irrigation = input("> ").strip().lower() in ["yes", "y", "true"]
            
            print("\nAWD tube available? (yes/no)")
            awd_tube = input("> ").strip().lower() in ["yes", "y", "true"]
            
            sowing_date_str = input("Sowing date (YYYY-MM-DD) or press Enter to skip: ").strip()
            sowing_date = None
            if sowing_date_str:
                sowing_date = date.fromisoformat(sowing_date_str)
            
            profile = FarmerProfile(
                farmer_id=farmer_id,
                farm_id=farm_id,
                province=province,
                soil_type=soil_type,
                irrigation_access=irrigation,
                awd_tube_available=awd_tube,
                sowing_date=sowing_date
            )
            
            self.storage.save_profile(profile)
            self.current_farm_id = farm_id
            
            print(f"✅ Profile created for farm: {farm_id}")
            
            # Create initial state
            state = self.state_manager.build_initial_state(profile, date.today())
            self.storage.save_state(state)
            print(f"✅ Initial state created")
        
        except Exception as e:
            print(f"❌ Failed to create profile: {e}")
    
    def select_farm(self):
        """Select a farm to work with"""
        farm_id = input("Enter farm ID: ").strip()
        
        profile = self.storage.load_profile(farm_id)
        if not profile:
            print(f"❌ Farm not found: {farm_id}")
            return
        
        self.current_farm_id = farm_id
        print(f"✅ Selected farm: {farm_id}")
    
    def show_state(self):
        """Show current state"""
        if not self.current_farm_id:
            print("❌ No farm selected. Use 'select' command first.")
            return
        
        state = self.storage.load_latest_state(self.current_farm_id)
        if not state:
            print("❌ No state found")
            return
        
        print("\n📊 CURRENT STATE")
        print("=" * 60)
        print(f"Farm ID: {state.farm_id}")
        print(f"Date: {state.state_date}")
        print(f"Regime: {state.regime}")
        print(f"Mode: {state.mode}")
        print()
        print(f"📅 Crop:")
        print(f"  DAS: {state.das or 'unknown'}")
        print(f"  Growth Stage: {state.growth_stage or 'unknown'}")
        print()
        print(f"💧 Water:")
        print(f"  Ponded Water: {state.ponded_water_cm:.1f} cm")
        print(f"  Water Table Depth: {state.water_table_depth_cm or 'not measured'}")
        print(f"  Soil Cracks: {state.soil_cracks}")
        print()
        print(f"🌤️  Weather:")
        print(f"  Rain (last 24h): {state.rain_last_24h_mm:.1f} mm")
        print(f"  Rain (next 72h): {state.rain_next_72h_mm:.1f} mm")
        print(f"  ET0: {state.et0_next_24h_mm or 'N/A'} mm/day")
        print("=" * 60)
    
    def do_checkin(self):
        """Submit daily check-in"""
        if not self.current_farm_id:
            print("❌ No farm selected")
            return
        
        print("\n📋 DAILY CHECK-IN")
        print("-" * 40)
        
        try:
            print("Measurement mode:")
            print("  1. AWD tube (cm below soil surface)")
            print("  2. Standing water bucket")
            print("  3. Qualitative only")
            mode_choice = input("Select (1/2/3): ").strip()
            
            measurement_mode = "none"
            water_table_depth_cm = None
            ponded_bucket = None
            
            if mode_choice == "1":
                measurement_mode = "awd_tube"
                depth = input("Water table depth (cm below surface): ").strip()
                water_table_depth_cm = float(depth)
            
            elif mode_choice == "2":
                measurement_mode = "standing_water_bucket"
                print("Ponded water: zero, one_two, three_five, over_five")
                bucket = input("Select: ").strip()
                ponded_bucket = bucket
            
            else:
                measurement_mode = "qualitative"
            
            print("Soil cracks: none, small, visible, deep")
            cracks = input("Soil cracks: ").strip() or "none"
            
            checkin = DailyCheckIn(
                farm_id=self.current_farm_id,
                checkin_date=date.today(),
                measurement_mode=measurement_mode,
                water_table_depth_cm=water_table_depth_cm,
                ponded_bucket=ponded_bucket,
                soil_cracks=cracks
            )
            
            # Process check-in
            state = self.storage.load_latest_state(self.current_farm_id)
            if not state:
                profile = self.storage.load_profile(self.current_farm_id)
                state = self.state_manager.build_initial_state(profile, date.today())
            
            state = self.state_manager.apply_checkin(state, checkin)
            
            # Get weather
            weather = self.weather_adapter.get_forecast({})
            forecast = self.weather_adapter.get_multi_day_forecast({}, days=7)
            
            state.rain_last_24h_mm = weather.rain_last_24h_mm
            state.rain_next_72h_mm = weather.rain_next_72h_mm
            
            # Get advice
            advice = self.planner.plan(state, forecast)
            
            # Save and log
            self.storage.save_state(state)
            self.logger.log_advice_event(state, advice, checkin=checkin)
            
            # Display advice
            print("\n" + ExplanationGenerator.format_for_display(advice))
        
        except Exception as e:
            print(f"❌ Failed to process check-in: {e}")
    
    def do_chat(self):
        """Chat with assistant"""
        if not self.current_farm_id:
            print("❌ No farm selected")
            return
        
        message = input("Your message: ").strip()
        if not message:
            return
        
        try:
            state = self.storage.load_latest_state(self.current_farm_id)
            if not state:
                print("❌ No state found")
                return
            
            # Extract slots
            extraction = self.extractor.extract(message)
            
            # Check for clarifications
            if extraction.need_clarification:
                print("\n❓ CLARIFICATION NEEDED:")
                for clarif in extraction.need_clarification:
                    print(f"  • {clarif.question}")
                print()
                return
            
            # Merge slots
            state = self.state_manager.apply_chat_slots(state, extraction.slots)
            
            # Get weather and advice
            weather = self.weather_adapter.get_forecast({})
            forecast = self.weather_adapter.get_multi_day_forecast({}, days=7)
            
            state.rain_last_24h_mm = weather.rain_last_24h_mm
            state.rain_next_72h_mm = weather.rain_next_72h_mm
            
            advice = self.planner.plan(state, forecast)
            
            # Save and log
            self.storage.save_state(state)
            self.logger.log_advice_event(state, advice, user_message=message)
            
            # Display
            print("\n" + ExplanationGenerator.format_for_display(advice))
        
        except Exception as e:
            print(f"❌ Failed to process message: {e}")
    
    def set_mode(self, command):
        """Set operational mode"""
        parts = command.split()
        if len(parts) < 2:
            print("Usage: mode <handbook_only|handbook_plus|general_only>")
            return
        
        mode = parts[1]
        if mode not in ["handbook_only", "handbook_plus", "general_only"]:
            print(f"Invalid mode: {mode}")
            return
        
        self.resolver.set_mode(mode)
        
        if self.current_farm_id:
            state = self.storage.load_latest_state(self.current_farm_id)
            if state:
                state.mode = mode
                self.storage.save_state(state)
        
        print(f"✅ Mode set to: {mode}")
    
    def set_regime(self, command):
        """Set irrigation regime"""
        parts = command.split()
        if len(parts) < 2:
            print("Usage: regime <AWD|CONTINUOUS|RAINFED|AUTO>")
            return
        
        regime = parts[1].upper()
        if regime not in ["AWD", "CONTINUOUS", "RAINFED", "AUTO"]:
            print(f"Invalid regime: {regime}")
            return
        
        if self.current_farm_id:
            state = self.storage.load_latest_state(self.current_farm_id)
            if state:
                state.regime = regime
                self.storage.save_state(state)
                print(f"✅ Regime set to: {regime}")
            else:
                print("❌ No state found")
        else:
            print("❌ No farm selected")
    
    def set_weather(self, command):
        """Set manual weather values"""
        print("\n🌤️  SET WEATHER (press Enter to skip)")
        print("-" * 40)
        
        try:
            rain_24h = input("Rain last 24h (mm): ").strip()
            rain_72h = input("Rain next 72h (mm): ").strip()
            et0 = input("ET0 (mm/day): ").strip()
            temp = input("Temperature (°C): ").strip()
            
            self.weather_adapter.set_weather(
                rain_24h=float(rain_24h) if rain_24h else None,
                rain_72h=float(rain_72h) if rain_72h else None,
                et0=float(et0) if et0 else None,
                temp=float(temp) if temp else None
            )
            
            print("✅ Weather values updated")
        
        except Exception as e:
            print(f"❌ Failed to set weather: {e}")
    
    def get_advice(self):
        """Get irrigation advice"""
        if not self.current_farm_id:
            print("❌ No farm selected")
            return
        
        try:
            state = self.storage.load_latest_state(self.current_farm_id)
            if not state:
                print("❌ No state found")
                return
            
            # Get weather and forecast
            weather = self.weather_adapter.get_forecast({})
            forecast = self.weather_adapter.get_multi_day_forecast({}, days=7)
            
            state.rain_last_24h_mm = weather.rain_last_24h_mm
            state.rain_next_72h_mm = weather.rain_next_72h_mm
            
            # Get advice
            advice = self.planner.plan(state, forecast)
            
            # Display
            print("\n" + ExplanationGenerator.format_for_display(advice))
        
        except Exception as e:
            print(f"❌ Failed to get advice: {e}")
    
    def show_logs(self):
        """Show recent logs"""
        if not self.current_farm_id:
            print("❌ No farm selected")
            return
        
        events = self.logger.read_events(farm_id=self.current_farm_id, limit=5)
        
        if not events:
            print("No logs found")
            return
        
        print(f"\n📜 RECENT LOGS (showing {len(events)})")
        print("=" * 60)
        
        for event in events:
            print(f"\n[{event['timestamp']}]")
            print(f"Type: {event['event_type']}")
            
            if event['event_type'] == 'advice':
                rec = event['recommendation']
                print(f"Action: {rec['action']}")
                print(f"Confidence: {rec['confidence']}")
                print(f"Regime: {rec['regime']}")
        
        print("=" * 60)


def main():
    """Entry point"""
    cli = WaterManagementCLI()
    cli.run()


if __name__ == "__main__":
    main()
