import SwiftUI

extension Color {
    static let ybScreen = Color(hex: 0xF7FBF9)
    static let ybPrimary = Color(hex: 0x16A085)
    static let ybPrimaryDark = Color(hex: 0x0F766E)
    static let ybSoft = Color(hex: 0xE5F7F2)
    static let ybText = Color(hex: 0x17212B)
    static let ybMuted = Color(hex: 0x667085)
    static let ybLine = Color(hex: 0xE5E7EB)
    static let ybOrange = Color(hex: 0xF59E0B)
    static let ybRed = Color(hex: 0xEF4444)
    static let ybBlue = Color(hex: 0x3B82F6)
    static let ybGreen = Color(hex: 0x22C55E)

    init(hex: UInt, opacity: Double = 1) {
        let red = Double((hex >> 16) & 0xFF) / 255
        let green = Double((hex >> 8) & 0xFF) / 255
        let blue = Double(hex & 0xFF) / 255
        self.init(.sRGB, red: red, green: green, blue: blue, opacity: opacity)
    }
}

extension Font {
    static let ybTitle = Font.system(size: 26, weight: .heavy, design: .rounded)
    static let ybSubtitle = Font.system(size: 14, weight: .semibold, design: .rounded)
    static let ybCardTitle = Font.system(size: 18, weight: .bold, design: .rounded)
    static let ybBody = Font.system(size: 14, weight: .medium, design: .rounded)
    static let ybCaption = Font.system(size: 12, weight: .medium, design: .rounded)
}

struct YBShadow: ViewModifier {
    func body(content: Content) -> some View {
        content.shadow(color: Color.black.opacity(0.06), radius: 16, x: 0, y: 8)
    }
}

extension View {
    func ybCardShadow() -> some View {
        modifier(YBShadow())
    }
}
