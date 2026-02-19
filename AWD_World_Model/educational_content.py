from typing import Dict, Any


class EducationalContent:
    """Educational content about AWD for farmers"""
    
    @staticmethod
    def explain_awd_basics() -> str:
        """Explain what AWD is and how it works"""
        return """## 🌾 What is Alternate Wetting and Drying (AWD)?

**AWD is a water-saving technique for rice cultivation.**

### How it works:
Instead of keeping your field continuously flooded, you:
1. **Let the water drain** naturally until the water table reaches **15cm below soil surface**
2. **Re-irrigate** with 5cm of standing water
3. **Repeat** this cycle throughout the season

### What you need:
- **Water tube (pani nali)**: A perforated PVC pipe (10-15cm diameter, 30cm long) buried 20cm deep
- **Daily monitoring**: Check the water level using the tube
- **Bunded paddy field**: Field must be able to hold water

### AWD Cycle Timeline:
- **Drying phase**: 3-7 days (depends on soil type)
- **When to irrigate**: Water table at 15cm depth
- **After irrigation**: Maintain 5cm standing water
- **Cycles per season**: 2-4 cycles

### Critical stages (NO AWD):
- **10 days before flowering** to **10 days after flowering**: Maintain shallow water continuously during this period

### Benefits:
✅ Save 15-30% water
✅ Reduce methane emissions by ~48%
✅ Same or slightly higher yield
✅ Eligible for carbon credits

**Want to know if AWD is suitable for your field? Just ask me!**"""
    
    @staticmethod
    def explain_water_tube_installation() -> str:
        """Explain how to install and use water tube"""
        return """## 🔧 How to Install and Use a Water Tube

### Materials needed:
- PVC pipe: 10-15cm diameter, 30cm long
- Drill holes (5-10mm) on sides
- Plastic bag or cap for bottom

### Installation steps:
1. **Choose location**: Near center of field, away from bunds
2. **Dig hole**: 20-25cm deep
3. **Prepare pipe**: Drill holes on sides (not bottom)
4. **Insert pipe**: Place in hole, 10cm should be above soil
5. **Pack soil**: Firmly pack soil around the pipe

### How to read:
1. Wait 1-2 hours after checking (let water settle)
2. Use a measuring stick or rope with marker
3. Measure from soil surface to water level
4. **15cm = time to irrigate**

### Maintenance:
- Keep top covered to prevent debris
- Clean holes if clogged
- Check daily during AWD cycles

**Typical readings**:
- 0-5cm: Standing water present
- 5-10cm: Good, continue monitoring
- 10-15cm: Prepare to irrigate soon
- 15cm+: Irrigate now!"""
    
    @staticmethod
    def explain_benefits(
        water_savings: Dict[str, Any], 
        emission_savings: Dict[str, Any]
    ) -> str:
        """Explain benefits with specific estimates"""
        
        return f"""## 🌟 Benefits of AWD Practice

### 💧 Water Savings
- **Conventional method**: ~{water_savings['baseline_water_mm']:.0f}mm water per season
- **With AWD**: ~{water_savings['awd_water_mm']:.0f}mm water per season
- **You save**: ~{water_savings['water_saved_mm']:.0f}mm ({water_savings['water_saved_percent']:.0f}%)
- **Volume saved**: ~{water_savings['water_saved_m3']:.0f} cubic meters

💰 **Economic benefit**: Lower pumping costs or water fees

### 🌍 Environmental Benefits
- **Methane reduction**: ~{emission_savings['reduction_percent']:.0f}% less CH₄ emissions
- **CO₂ equivalent**: Saves ~{emission_savings['co2_equivalent_kg']:.0f} kg CO₂e
- **Carbon credits**: Potential income from emission reduction programs

### 🌾 Yield Impact
- **Yield**: Same or 5-10% higher in some cases
- **Root health**: Better root oxygenation during drying
- **Disease**: Reduced risk of some water-related diseases

### ⚠️ Important Notes
**AWD is safe when done correctly**:
- Monitor water level daily
- Never exceed 15cm depth (except very permeable soils)
- Maintain continuous flooding during flowering
- Stop if plants show stress

**Not suitable for**:
❌ Non-bunded fields
❌ Very sandy soils (water drains too fast)
❌ Heavy monsoon areas without irrigation control

**Best for**:
✅ Bunded lowland paddy
✅ Clay or loam soils
✅ Fields with irrigation control

**Ready to start? Ask me about irrigation timing or field assessment!**"""
    
    @staticmethod
    def explain_critical_stages() -> str:
        """Explain water management at critical stages"""
        return """## 📅 Water Management by Growth Stage

### 1. Establishment (0-15 days after transplanting)
- **Continuous shallow flooding** (3-5cm)
- **No AWD** - plants need to establish roots
- Keep water clear of weeds

### 2. Tillering (15-45 days)
- ✅ **AWD SAFE** - best phase to practice AWD
- Let water table drop to 15cm
- Multiple cycles possible
- **Water savings**: Maximum in this phase

### 3. Panicle Initiation (45-55 days)
- ⚠️ **Moderate sensitivity**
- AWD possible but monitor closely
- Don't exceed 15cm depth

### 4. Flowering (55-75 days)
- 🚨 **MOST CRITICAL STAGE**
- **NO AWD** - maintain 3-5cm standing water
- Start 10 days before first flower
- Continue until 10 days after flowering
- **Stress here = major yield loss**

### 5. Grain Filling (75-95 days)
- ⚠️ **Moderate sensitivity**
- AWD possible with caution
- Maximum depth: 12cm (more conservative)
- Monitor for stress

### 6. Maturity (95-120 days)
- Drain field 10-15 days before harvest
- Allows easier harvesting
- No AWD needed

**Key Rule**: When in doubt, keep water on the field during reproductive stages (panicle initiation to grain filling)."""
    
    @staticmethod
    def troubleshooting_guide() -> str:
        """Common problems and solutions"""
        return """## 🔧 AWD Troubleshooting Guide

### Problem 1: Soil cracking
**Symptoms**: Cracks in the soil surface

**Mild cracks** (thin lines):
✅ Normal - continue AWD
✅ Monitor for widening

**Severe cracks** (wide, deep):
⚠️ Irrigate immediately
⚠️ Risk of root damage
💡 Next cycle: irrigate at 12cm instead of 15cm

### Problem 2: Leaf rolling/curling
**Symptoms**: Leaves rolling inward or curling

🚨 **Action**: 
- Stop AWD immediately
- Irrigate to 5cm standing water
- Maintain water for 3-5 days
- Resume AWD only after recovery

**Prevention**: 
- Don't exceed 15cm depth
- Monitor daily
- Check critical stages

### Problem 3: Water tube issues
**Tube always dry**: 
- Holes may be clogged - clean with wire
- Tube may be above water table - normal if <15cm depth

**Can't measure**: 
- Use measuring stick or marked rope
- Measure from soil surface to water

**Tube damaged**: 
- Replace with new tube
- Ensure holes are on sides, not bottom

### Problem 4: Inconsistent water levels
**Symptoms**: Water level varies across field

**Causes**:
- Uneven field leveling
- Poor bund maintenance
- Varying soil percolation

**Solutions**:
- Level field before next season
- Repair bund leaks
- Use average of 2-3 tube readings

### Problem 5: Water drains too fast
**Symptoms**: Reaches 15cm in 1-2 days

⚠️ **Your soil may be too permeable for safe AWD**

**Options**:
1. Irrigate more frequently (at 10cm depth)
2. Consider continuous flooding if still too fast
3. Check and repair bund leaks

### Problem 6: Water level drops too slowly
**Symptoms**: Takes 7+ days to reach 15cm

**Heavy clay soil** - this is normal
✅ Continue AWD - you're still saving water
✅ May have fewer cycles per season

### When to stop AWD and flood continuously:
1. Flowering stage (10 days before to 10 days after)
2. Severe stress symptoms appear
3. Water management becomes uncontrollable
4. Heavy rainfall period

**Still confused? Ask me your specific problem!**"""
