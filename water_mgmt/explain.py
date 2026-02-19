"""Explanation and rationale formatting"""

from .schemas import AdviceResponse


class ExplanationGenerator:
    """Format advice for farmers"""
    
    @staticmethod
    def format_for_display(advice: AdviceResponse, language: str = "EN") -> str:
        """Human-readable advice in English or Vietnamese"""
        
        if language == "VI":
            return ExplanationGenerator.format_vietnamese(advice)
        else:
            return ExplanationGenerator.format_english(advice)
    
    @staticmethod
    def format_english(advice: AdviceResponse) -> str:
        """English format"""
        
        lines = []
        lines.append("=" * 60)
        lines.append(f"📋 WATER MANAGEMENT ADVICE")
        lines.append("=" * 60)
        lines.append(f"Farm: {advice.farm_id}")
        lines.append(f"Date: {advice.advice_date}")
        lines.append(f"Regime: {advice.regime_used}")
        lines.append("")
        
        # Recommendation
        action_emoji = {
            "IRRIGATE": "💧",
            "HOLD": "⏸️",
            "DRAIN": "🌊",
            "ALERT_ONLY": "⚠️"
        }
        emoji = action_emoji.get(advice.recommended_action, "📍")
        
        lines.append(f"{emoji} RECOMMENDATION: {advice.recommended_action}")
        if advice.target_description:
            lines.append(f"   → {advice.target_description}")
        lines.append("")
        
        # Confidence
        conf_emoji = {"high": "⭐⭐⭐", "medium": "⭐⭐", "low": "⭐"}
        lines.append(f"🎯 CONFIDENCE: {advice.confidence.upper()} {conf_emoji[advice.confidence]}")
        lines.append("")
        
        # Rationale
        lines.append("🔍 WHY THIS RECOMMENDATION:")
        for i, bullet in enumerate(advice.rationale, 1):
            source_tag = f"[{bullet.source_type}]"
            lines.append(f"   {i}. {bullet.text} {source_tag}")
        lines.append("")
        
        # Warnings
        if advice.risk_warnings:
            lines.append("⚠️  IMPORTANT WARNINGS:")
            for warning in advice.risk_warnings:
                lines.append(f"   • {warning}")
            lines.append("")
        
        # Counterfactuals
        if advice.counterfactuals:
            lines.append("🔀 WHAT IF:")
            for cf in advice.counterfactuals:
                risk_emoji = {"low": "✅", "medium": "⚠️", "high": "🚨"}
                lines.append(f"   • {cf.action}: {cf.outcome_summary} {risk_emoji[cf.risk_level]}")
            lines.append("")
        
        # Next steps
        if advice.next_observation_question:
            lines.append(f"👁️  NEXT CHECK: {advice.next_observation_question}")
            lines.append("")
        
        # Footer
        lines.append("-" * 60)
        lines.append("📌 [HANDBOOK] = From AWD manual | [GENERAL] = Standard practice")
        lines.append(f"Mode: {advice.mode_used} | Time: {advice.timestamp.strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_vietnamese(advice: AdviceResponse) -> str:
        """Vietnamese format"""
        
        lines = []
        lines.append("=" * 60)
        lines.append(f"📋 TƯ VẤN QUẢN LÝ NƯỚC")
        lines.append("=" * 60)
        lines.append(f"Trang trại: {advice.farm_id}")
        lines.append(f"Ngày: {advice.advice_date}")
        lines.append(f"Chế độ: {advice.regime_used}")
        lines.append("")
        
        # Recommendation
        action_map = {
            "IRRIGATE": "TƯỚI NƯỚC",
            "HOLD": "CHỜ",
            "DRAIN": "THOÁT NƯỚC",
            "ALERT_ONLY": "CẢNH BÁO"
        }
        action_emoji = {
            "IRRIGATE": "💧",
            "HOLD": "⏸️",
            "DRAIN": "🌊",
            "ALERT_ONLY": "⚠️"
        }
        emoji = action_emoji.get(advice.recommended_action, "📍")
        vietnamese_action = action_map.get(advice.recommended_action, advice.recommended_action)
        
        lines.append(f"{emoji} KHUYẾN NGHỊ: {vietnamese_action}")
        if advice.target_description:
            # Translate target description
            target_vi = advice.target_description
            target_vi = target_vi.replace("Refill to", "Tưới lại đến")
            target_vi = target_vi.replace("cm", "cm")
            target_vi = target_vi.replace("shallow ponding", "ngập nông")
            target_vi = target_vi.replace("Irrigate to maintain", "Tưới để duy trì")
            target_vi = target_vi.replace("Do not irrigate yet", "Chưa cần tưới")
            target_vi = target_vi.replace("monitor conditions", "theo dõi điều kiện")
            target_vi = target_vi.replace("Drain field", "Thoát nước ruộng")
            target_vi = target_vi.replace("No irrigation available", "Không có tưới")
            target_vi = target_vi.replace("monitor for stress", "theo dõi căng thẳng nước")
            lines.append(f"   → {target_vi}")
        lines.append("")
        
        # Confidence
        conf_map = {"high": "CAO", "medium": "TRUNG BÌNH", "low": "THẤP"}
        conf_emoji = {"high": "⭐⭐⭐", "medium": "⭐⭐", "low": "⭐"}
        lines.append(f"🎯 ĐỘ TIN CẬY: {conf_map[advice.confidence]} {conf_emoji[advice.confidence]}")
        lines.append("")
        
        # Rationale
        lines.append("🔍 TẠI SAO:")
        for i, bullet in enumerate(advice.rationale, 1):
            source_tag = f"[{bullet.source_type}]"
            # Basic translation of common terms
            text_vi = bullet.text
            text_vi = text_vi.replace("Water table depth at", "Độ sâu mực nước tại")
            text_vi = text_vi.replace("cracks observed in field", "xuất hiện nứt trong ruộng")
            text_vi = text_vi.replace("Heavy rain forecasted", "Dự báo mưa lớn")
            text_vi = text_vi.replace("in next", "trong")
            text_vi = text_vi.replace("hours", "giờ")
            lines.append(f"   {i}. {text_vi} {source_tag}")
        lines.append("")
        
        # Warnings
        if advice.risk_warnings:
            lines.append("⚠️  CẢNH BÁO QUAN TRỌNG:")
            for warning in advice.risk_warnings:
                # Translate warnings
                warning_vi = warning
                warning_vi = warning_vi.replace("stage is sensitive", "giai đoạn nhạy cảm")
                warning_vi = warning_vi.replace("to water stress", "với căng thẳng nước")
                warning_vi = warning_vi.replace("Monitor closely", "Theo dõi chặt chẽ")
                warning_vi = warning_vi.replace("Heavy rain forecasted", "Dự báo mưa lớn")
                warning_vi = warning_vi.replace("Consider delaying irrigation", "Cân nhắc trì hoãn tưới")
                warning_vi = warning_vi.replace("Excess ponding", "Ngập quá mức")
                warning_vi = warning_vi.replace("may increase disease risk", "có thể tăng nguy cơ bệnh")
                warning_vi = warning_vi.replace("Consider drainage", "Cân nhắc thoát nước")
                lines.append(f"   • {warning_vi}")
            lines.append("")
        
        # Counterfactuals
        if advice.counterfactuals:
            lines.append("🔀 NẾU:")
            for cf in advice.counterfactuals:
                risk_emoji = {"low": "✅", "medium": "⚠️", "high": "🚨"}
                action_vi = action_map.get(cf.action, cf.action)
                outcome_vi = cf.outcome_summary
                outcome_vi = outcome_vi.replace("Field refilled to", "Ruộng tưới lại đến")
                outcome_vi = outcome_vi.replace("Water table at", "Mực nước tại")
                outcome_vi = outcome_vi.replace("after", "sau")
                outcome_vi = outcome_vi.replace("days", "ngày")
                outcome_vi = outcome_vi.replace("Ponded water", "Nước ngập")
                lines.append(f"   • {action_vi}: {outcome_vi} {risk_emoji[cf.risk_level]}")
            lines.append("")
        
        # Next steps
        if advice.next_observation_question:
            next_vi = advice.next_observation_question
            next_vi = next_vi.replace("Check", "Kiểm tra")
            next_vi = next_vi.replace("AWD tube depth", "độ sâu ống AWD")
            next_vi = next_vi.replace("for soil cracks", "vết nứt đất")
            next_vi = next_vi.replace("ponded water depth", "độ sâu nước ngập")
            next_vi = next_vi.replace("for rainfall and soil moisture", "lượng mưa và độ ẩm đất")
            next_vi = next_vi.replace("field conditions", "điều kiện ruộng")
            next_vi = next_vi.replace("tomorrow", "ngày mai")
            lines.append(f"👁️  KIỂM TRA TIẾP: {next_vi}")
            lines.append("")
        
        # Footer
        lines.append("-" * 60)
        lines.append("📌 [HANDBOOK] = Từ sổ tay AWD | [GENERAL] = Thực hành chung")
        lines.append(f"Chế độ: {advice.mode_used} | Thời gian: {advice.timestamp.strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_compact(advice: AdviceResponse) -> str:
        """Compact format for mobile"""
        
        lines = []
        lines.append(f"💧 {advice.recommended_action}")
        if advice.target_description:
            lines.append(f"→ {advice.target_description}")
        lines.append(f"Confidence: {advice.confidence}")
        
        if advice.risk_warnings:
            lines.append(f"⚠️ {advice.risk_warnings[0]}")
        
        return "\n".join(lines)
