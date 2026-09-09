import SwiftUI

struct PageBackground<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        ZStack {
            Color.ybScreen.ignoresSafeArea()
            content
        }
        .foregroundStyle(Color.ybText)
    }
}

struct ScrollPage<Content: View>: View {
    var title: String
    var subtitle: String? = nil
    var showBack: Bool = false
    var trailingSystemImage: String? = nil
    let content: Content

    @Environment(\.dismiss) private var dismiss

    init(title: String, subtitle: String? = nil, showBack: Bool = false, trailingSystemImage: String? = nil, @ViewBuilder content: () -> Content) {
        self.title = title
        self.subtitle = subtitle
        self.showBack = showBack
        self.trailingSystemImage = trailingSystemImage
        self.content = content()
    }

    var body: some View {
        PageBackground {
            VStack(spacing: 0) {
                topBar
                ScrollView(showsIndicators: false) {
                    VStack(spacing: 14) {
                        content
                    }
                    .padding(.horizontal, 18)
                    .padding(.bottom, 22)
                }
            }
        }
        .toolbar(.hidden, for: .navigationBar)
    }

    private var topBar: some View {
        HStack(spacing: 12) {
            if showBack {
                Button {
                    dismiss()
                } label: {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 18, weight: .heavy))
                        .foregroundStyle(Color.ybText)
                        .frame(width: 36, height: 36)
                        .background(Color.white)
                        .clipShape(Circle())
                        .ybCardShadow()
                }
            }

            VStack(alignment: .leading, spacing: 2) {
                if let subtitle {
                    Text(subtitle)
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                }
                Text(title)
                    .font(.system(size: 24, weight: .heavy, design: .rounded))
                    .foregroundStyle(Color.ybText)
            }

            Spacer()

            if let trailingSystemImage {
                Image(systemName: trailingSystemImage)
                    .font(.system(size: 16, weight: .bold))
                    .foregroundStyle(Color.ybText)
                    .frame(width: 36, height: 36)
                    .background(Color.white)
                    .clipShape(Circle())
                    .ybCardShadow()
            }
        }
        .padding(.horizontal, 18)
        .padding(.top, 10)
        .padding(.bottom, 12)
    }
}

struct YBCard<Content: View>: View {
    var padding: CGFloat = 16
    let content: Content

    init(padding: CGFloat = 16, @ViewBuilder content: () -> Content) {
        self.padding = padding
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            content
        }
        .padding(padding)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
        .ybCardShadow()
    }
}

struct HeroCard<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            content
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            LinearGradient(colors: [.ybPrimary, .ybPrimaryDark], startPoint: .topLeading, endPoint: .bottomTrailing)
        )
        .foregroundStyle(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
        .ybCardShadow()
    }
}

struct MetricTile: View {
    var number: String
    var title: String
    var tint: Color = .ybPrimary

    var body: some View {
        VStack(spacing: 4) {
            Text(number)
                .font(.system(size: 22, weight: .heavy, design: .rounded))
                .monospacedDigit()
                .lineLimit(1)
                .minimumScaleFactor(0.55)
                .allowsTightening(true)
                .padding(.horizontal, 4)
                .foregroundStyle(tint)
            Text(title)
                .font(.ybCaption)
                .foregroundStyle(Color.ybMuted)
        }
        .frame(maxWidth: .infinity)
        .padding(.horizontal, 4)
        .frame(height: 76)
        .background(Color.white.opacity(0.92))
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }
}

struct SectionTitle: View {
    var title: String
    var trailing: String? = nil

    var body: some View {
        HStack {
            Text(title)
                .font(.ybCardTitle)
            Spacer()
            if let trailing {
                Text(trailing)
                    .font(.ybCaption)
                    .foregroundStyle(Color.ybPrimary)
                    .fontWeight(.bold)
            }
        }
    }
}

struct StatusPill: View {
    var text: String
    var color: Color = .ybPrimary

    var body: some View {
        Text(text)
            .font(.system(size: 11, weight: .bold, design: .rounded))
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .foregroundStyle(color)
            .background(color.opacity(0.12))
            .clipShape(Capsule())
    }
}

struct EmojiCircle: View {
    var emoji: String
    var size: CGFloat = 44
    var background: Color = .ybSoft

    var body: some View {
        Text(emoji)
            .font(.system(size: size * 0.46))
            .frame(width: size, height: size)
            .background(background)
            .clipShape(Circle())
    }
}

struct QuickActionCard: View {
    var emoji: String
    var title: String
    var subtitle: String
    var action: () -> Void = {}

    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 8) {
                EmojiCircle(emoji: emoji, size: 42, background: Color.ybSoft)
                Text(title)
                    .font(.system(size: 15, weight: .bold, design: .rounded))
                    .foregroundStyle(Color.ybText)
                Text(subtitle)
                    .font(.system(size: 11, weight: .medium, design: .rounded))
                    .foregroundStyle(Color.ybMuted)
                    .lineLimit(2)
            }
            .padding(14)
            .frame(maxWidth: .infinity, minHeight: 122, alignment: .leading)
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
            .ybCardShadow()
        }
        .buttonStyle(.plain)
    }
}

struct PrimaryButton: View {
    var title: String
    var systemImage: String? = nil
    var color: Color = .ybPrimary
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                if let systemImage {
                    Image(systemName: systemImage)
                }
                Text(title)
                    .fontWeight(.heavy)
            }
            .font(.system(size: 15, weight: .bold, design: .rounded))
            .frame(maxWidth: .infinity)
            .padding(.vertical, 15)
            .foregroundStyle(Color.white)
            .background(color)
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        }
        .buttonStyle(.plain)
    }
}

struct SecondaryButton: View {
    var title: String
    var systemImage: String? = nil
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                if let systemImage {
                    Image(systemName: systemImage)
                }
                Text(title)
                    .fontWeight(.heavy)
            }
            .font(.system(size: 15, weight: .bold, design: .rounded))
            .frame(maxWidth: .infinity)
            .padding(.vertical, 15)
            .foregroundStyle(Color.ybPrimary)
            .background(Color.ybSoft)
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        }
        .buttonStyle(.plain)
    }
}

struct InfoRow: View {
    var label: String
    var value: String
    var icon: String? = nil

    var body: some View {
        HStack {
            if let icon {
                Text(icon)
                    .font(.title3)
            }
            Text(label)
                .font(.ybCaption)
                .foregroundStyle(Color.ybMuted)
            Spacer()
            Text(value)
                .font(.system(size: 14, weight: .heavy, design: .rounded))
                .foregroundStyle(Color.ybText)
        }
        .padding(.vertical, 8)
    }
}

struct MedicineListRow: View {
    var medicine: Medicine
    var action: (() -> Void)? = nil

    var body: some View {
        Button {
            action?()
        } label: {
            VStack(spacing: 10) {
                HStack(spacing: 12) {
                    EmojiCircle(emoji: medicine.emoji, size: 46)
                    VStack(alignment: .leading, spacing: 4) {
                        Text(medicine.name)
                            .font(.system(size: 16, weight: .heavy, design: .rounded))
                            .foregroundStyle(Color.ybText)
                        Text("\(medicine.category) · \(medicine.owner)")
                            .font(.ybCaption)
                            .foregroundStyle(Color.ybMuted)
                    }
                    Spacer()
                    StatusPill(text: medicine.displayStatus, color: medicine.needsAttention ? .ybOrange : .ybPrimary)
                }

                HStack {
                    InfoMini(title: "位置", value: medicine.location.isEmpty ? "未填写" : medicine.location)
                    InfoMini(title: "有效期", value: medicine.expiryDisplayText.isEmpty ? "未填写" : medicine.expiryDisplayText)
                    InfoMini(title: "库存", value: medicine.stock.isEmpty ? "未填写" : medicine.stock)
                }
            }
            .padding(14)
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
            .ybCardShadow()
        }
        .buttonStyle(.plain)
    }
}

struct InfoMini: View {
    var title: String
    var value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.system(size: 10, weight: .bold, design: .rounded))
                .foregroundStyle(Color.ybMuted)
            Text(value)
                .font(.system(size: 12, weight: .heavy, design: .rounded))
                .foregroundStyle(Color.ybText)
                .lineLimit(1)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(Color.ybScreen)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }
}

struct TagWrapView: View {
    var tags: [String]
    var tint: Color = .ybOrange

    var body: some View {
        FlowLayout(spacing: 8) {
            ForEach(tags, id: \.self) { tag in
                Text(tag)
                    .font(.system(size: 12, weight: .bold, design: .rounded))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(tint.opacity(0.12))
                    .foregroundStyle(tint)
                    .clipShape(Capsule())
            }
        }
    }
}

struct FlowLayout: Layout {
    var spacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let maxWidth = proposal.width ?? 320
        var x: CGFloat = 0
        var y: CGFloat = 0
        var rowHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x + size.width > maxWidth, x > 0 {
                x = 0
                y += rowHeight + spacing
                rowHeight = 0
            }
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
        return CGSize(width: maxWidth, height: y + rowHeight)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var x = bounds.minX
        var y = bounds.minY
        var rowHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x + size.width > bounds.maxX, x > bounds.minX {
                x = bounds.minX
                y += rowHeight + spacing
                rowHeight = 0
            }
            subview.place(at: CGPoint(x: x, y: y), proposal: ProposedViewSize(size))
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
    }
}
