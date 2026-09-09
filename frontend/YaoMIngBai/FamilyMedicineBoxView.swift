import SwiftUI

struct FamilyMedicineBoxView: View {
    @EnvironmentObject private var app: AppState
    @State private var selectedCategory = "全部"

    var showBack: Bool = false

    private var categories: [String] {
        var items = ["全部"]
        let dynamic = Set(app.medicines.map(\.category).filter { !$0.isEmpty }).sorted()
        items.append(contentsOf: dynamic)
        items.append("即将过期")
        return items
    }

    private var filteredMedicines: [Medicine] {
        if selectedCategory == "全部" { return app.medicines }
        if selectedCategory == "即将过期" { return app.medicines.filter { $0.displayStatus.contains("过期") } }
        return app.medicines.filter { $0.category == selectedCategory }
    }

    private var groupedMedicines: [MedicineGroup] {
        Dictionary(grouping: filteredMedicines, by: { $0.groupingKey })
            .map { MedicineGroup(key: $0.key, items: $0.value) }
            .sorted { left, right in
                left.representative.name.localizedCompare(right.representative.name) == .orderedAscending
            }
    }

    private var expiringCount: Int {
        app.medicines.filter { $0.displayStatus.contains("过期") }.count
    }

    private var lowStockCount: Int {
        app.medicines.filter { $0.displayStatus.contains("少") || $0.displayStatus.contains("不足") }.count
    }

    var body: some View {
        ScrollPage(title: "家庭药箱", subtitle: "家庭统一管理", showBack: showBack, trailingSystemImage: "shippingbox.fill") {
            HeroCard {
                Text("药箱状态")
                    .font(.system(size: 20, weight: .heavy, design: .rounded))
                Text(boxSummary)
                    .font(.ybBody)
                    .opacity(0.92)

                HStack(spacing: 10) {
                    MetricTile(number: "\(groupedTotalCount)", title: "药品组", tint: .ybPrimary)
                    MetricTile(number: "\(expiringCount)", title: "快过期", tint: .ybOrange)
                    MetricTile(number: "\(lowStockCount)", title: "库存少", tint: .ybRed)
                }
            }

            Button {
                app.path.append(Route.addMedicine)
            } label: {
                YBCard {
                    HStack(alignment: .center, spacing: 12) {
                        EmojiCircle(emoji: "➕", size: 50, background: Color.ybSoft)
                        VStack(alignment: .leading, spacing: 5) {
                            Text("添加药品")
                                .font(.system(size: 18, weight: .heavy, design: .rounded))
                                .foregroundStyle(Color.ybText)
                            Text("识别或输入药名，保存时再选择成员、位置和库存")
                                .font(.ybCaption)
                                .foregroundStyle(Color.ybMuted)
                        }
                        Spacer()
                        Image(systemName: "chevron.right")
                            .font(.system(size: 14, weight: .heavy))
                            .foregroundStyle(Color.ybMuted)
                    }
                }
            }
            .buttonStyle(.plain)

            if !app.medicines.isEmpty {
                YBCard {
                    SectionTitle(title: "药品分类")
                    FlowLayout(spacing: 8) {
                        ForEach(categories, id: \.self) { item in
                            Button {
                                selectedCategory = item
                            } label: {
                                Text(item)
                                    .font(.system(size: 12, weight: .heavy, design: .rounded))
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 8)
                                    .foregroundStyle(selectedCategory == item ? Color.white : Color.ybPrimary)
                                    .background(selectedCategory == item ? Color.ybPrimary : Color.ybSoft)
                                    .clipShape(Capsule())
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
            }

            if groupedMedicines.isEmpty {
                YBCard {
                    HStack(alignment: .top, spacing: 12) {
                        EmojiCircle(emoji: "🧰", size: 48, background: Color.ybSoft)
                        VStack(alignment: .leading, spacing: 6) {
                            Text(app.medicines.isEmpty ? "药箱还是空的" : "当前分类没有药品")
                                .font(.system(size: 17, weight: .heavy, design: .rounded))
                            Text("点击上方“添加药品”，保存前会让你选择具体放在哪里。")
                                .font(.ybCaption)
                                .foregroundStyle(Color.ybMuted)
                        }
                    }
                }
            } else {
                SectionTitle(title: "药品列表", trailing: "相同药品已合并")
                ForEach(groupedMedicines) { group in
                    MedicineGroupRow(group: group) {
                        app.currentMedicine = group.representative
                        app.path.append(Route.medicineDetail)
                    }
                }
            }
        }
        .refreshable {
            await app.refreshFromBackend()
        }
    }

    private var groupedTotalCount: Int {
        Dictionary(grouping: app.medicines, by: { $0.groupingKey }).count
    }

    private var boxSummary: String {
        if app.medicines.isEmpty {
            return "还没有保存药品。添加时会选择成员、位置、库存和有效期。"
        }
        return "共 \(app.medicines.count) 条药品记录，合并为 \(groupedTotalCount) 组；\(expiringCount) 件需要关注有效期，\(lowStockCount) 件库存偏少。"
    }
}

struct MedicineGroup: Identifiable {
    var key: String
    var items: [Medicine]

    var id: String { key }

    var representative: Medicine {
        items.sorted { ($0.backendID ?? 0) > ($1.backendID ?? 0) }.first ?? items[0]
    }

    var displayStock: String {
        Medicine.mergedStocks(items.map(\.stock))
    }

    var mergedLabel: String {
        items.count > 1 ? "已合并 \(items.count) 份" : representative.displayStatus
    }

    var statusColor: Color {
        representative.needsAttention ? .ybOrange : .ybPrimary
    }
}

struct MedicineGroupRow: View {
    var group: MedicineGroup
    var action: () -> Void

    var medicine: Medicine { group.representative }

    var body: some View {
        Button(action: action) {
            VStack(spacing: 10) {
                HStack(spacing: 12) {
                    EmojiCircle(emoji: medicine.emoji, size: 46)
                    VStack(alignment: .leading, spacing: 4) {
                        Text(medicine.name)
                            .font(.system(size: 16, weight: .heavy, design: .rounded))
                            .foregroundStyle(Color.ybText)
                        Text("\(medicine.category.isEmpty ? "未分类" : medicine.category) · \(medicine.owner.isEmpty ? "未选择成员" : medicine.owner)")
                            .font(.ybCaption)
                            .foregroundStyle(Color.ybMuted)
                    }
                    Spacer()
                    StatusPill(text: group.mergedLabel, color: group.statusColor)
                }

                HStack {
                    InfoMini(title: "位置", value: medicine.location.isEmpty ? "未填写" : medicine.location)
                    InfoMini(title: "有效期", value: medicine.expiryDisplayText.isEmpty ? "未填写" : medicine.expiryDisplayText)
                    InfoMini(title: "库存", value: group.displayStock)
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
