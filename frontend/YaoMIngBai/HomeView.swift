import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var app: AppState
    @State private var showTodayDetails = false

    private var pendingItems: [TodayMedicationItem] {
        app.todayItems.filter { !$0.isCompleted }
    }

    private var riskyMedicine: Medicine? {
        app.medicines.first { medicine in
            medicine.needsAttention
        }
    }

    var body: some View {
        ScrollPage(title: "药明白", subtitle: "家庭用药安全助手", trailingSystemImage: "person.crop.circle.fill") {
            HeroCard {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("今日用药 \(app.todayTotal) 项")
                            .font(.system(size: 22, weight: .heavy, design: .rounded))
                        Text(todayDescription)
                            .font(.system(size: 13, weight: .medium, design: .rounded))
                            .opacity(0.92)
                    }
                    Spacer()
                    Button {
                        withAnimation(.spring(response: 0.28, dampingFraction: 0.88)) {
                            showTodayDetails.toggle()
                        }
                    } label: {
                        Text(showTodayDetails ? "收起 ▴" : "展开 ▾")
                            .font(.system(size: 12, weight: .heavy, design: .rounded))
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(Color.white.opacity(0.18))
                            .clipShape(Capsule())
                    }
                    .buttonStyle(.plain)
                }

                HStack(spacing: 10) {
                    MetricTile(number: "\(app.todayCompleted)", title: "已完成", tint: .ybGreen)
                    MetricTile(number: "\(app.todayPending)", title: "待服药", tint: .ybOrange)
                    MetricTile(number: "\(app.riskCount)", title: "需处理", tint: .ybRed)
                }

                if showTodayDetails {
                    VStack(spacing: 8) {
                        if app.todayItems.isEmpty {
                            Text("今天还没有提醒计划。可以先去设置提醒，保存后这里会显示完成情况。")
                                .font(.system(size: 13, weight: .bold, design: .rounded))
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(12)
                                .background(Color.white.opacity(0.16))
                                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                        } else {
                            ForEach(app.todayItems) { item in
                                TodaySummaryRow(item: item) {
                                    app.markTaken(item: item)
                                } cancelTaken: {
                                    app.cancelTaken(item: item)
                                }
                            }
                        }
                    }
                    .transition(.opacity.combined(with: .move(edge: .top)))
                }
            }

            SectionTitle(title: "快捷入口")
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 12), count: 2), spacing: 12) {
                QuickActionCard(emoji: "📷", title: "识别 / 查询", subtitle: "拍照或输入药名查看信息") {
                    app.path.append(Route.addMedicine)
                }
                QuickActionCard(emoji: "📋", title: "提醒列表", subtitle: "查看服药计划和完成情况") {
                    app.path.append(Route.reminderList)
                }
                QuickActionCard(emoji: "⏰", title: "设置提醒", subtitle: "选择药品后保存") {
                    app.pendingReminderMedicine = nil
                    app.pendingReminderMember = nil
                    app.path.append(Route.reminderSetting)
                }
                QuickActionCard(emoji: "🧰", title: "家庭药箱", subtitle: "管理库存、有效期和位置") {
                    app.switchToTab(.box)
                }
            }

            SectionTitle(title: "家庭动态与风险", trailing: "按需查看")
            YBCard {
                if let firstPending = pendingItems.first {
                    RiskRow(icon: "⏰", title: "还有待服药事项", detail: "\(firstPending.time) · \(firstPending.memberName) · \(firstPending.medicineName) \(firstPending.dose)", color: .ybOrange) {
                        app.path.append(Route.reminderList)
                    }
                    if riskyMedicine != nil { Divider() }
                }

                if let riskyMedicine {
                    RiskRow(icon: "⚠️", title: riskyMedicine.displayStatus.contains("确认") ? "药品信息待核对" : "药品需要处理", detail: "\(riskyMedicine.name)：\(riskyMedicine.displayStatus)。点击进入详情页，可编辑库存、位置、使用者和状态。", color: .ybRed) {
                        app.currentMedicine = riskyMedicine
                        app.path.append(Route.medicineDetail)
                    }
                }

                if pendingItems.isEmpty && riskyMedicine == nil {
                    RiskRow(icon: "✅", title: "暂无待处理事项", detail: "今天没有待服药提醒，家庭药箱暂无明显风险。", color: .ybGreen) {
                        app.path.append(Route.reminderList)
                    }
                }
            }
        }
        .refreshable {
            await app.refreshFromBackend()
        }
    }

    private var todayDescription: String {
        if app.todayTotal == 0 {
            return "还没有设置今天的服药提醒。"
        }
        if app.todayPending == 0 {
            return "今天的提醒都已经完成。"
        }
        if let next = pendingItems.first {
            return "下一项：\(next.time) \(next.memberName) 服用 \(next.medicineName)。"
        }
        return "还有 \(app.todayPending) 项待服药。"
    }
}

struct TodaySummaryRow: View {
    var item: TodayMedicationItem
    var markTaken: () -> Void
    var cancelTaken: () -> Void

    var body: some View {
        HStack(spacing: 10) {
            Text(item.isCompleted ? "✓" : "!")
                .font(.system(size: 14, weight: .heavy, design: .rounded))
                .frame(width: 28, height: 28)
                .background(Color.white.opacity(0.18))
                .clipShape(Circle())

            VStack(alignment: .leading, spacing: 2) {
                Text("\(item.time)  \(item.medicineName)")
                    .font(.system(size: 13, weight: .heavy, design: .rounded))
                Text("\(item.memberName) · \(item.mealLabel.isEmpty ? "按时服用" : item.mealLabel) · \(item.dose.isEmpty ? "剂量未填写" : item.dose)")
                    .font(.system(size: 11, weight: .bold, design: .rounded))
                    .opacity(0.86)
            }
            Spacer()
            if item.isCompleted {
                Button("取消") {
                    cancelTaken()
                }
                .font(.system(size: 11, weight: .heavy, design: .rounded))
                .padding(.horizontal, 9)
                .padding(.vertical, 5)
                .background(Color.white.opacity(0.18))
                .clipShape(Capsule())
            } else {
                Button("确认") {
                    markTaken()
                }
                .font(.system(size: 11, weight: .heavy, design: .rounded))
                .padding(.horizontal, 9)
                .padding(.vertical, 5)
                .background(Color.white.opacity(0.92))
                .foregroundStyle(Color.ybPrimaryDark)
                .clipShape(Capsule())
            }
        }
        .padding(10)
        .background(Color.white.opacity(0.13))
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
    }
}

struct RiskRow: View {
    var icon: String
    var title: String
    var detail: String
    var color: Color
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(alignment: .top, spacing: 12) {
                EmojiCircle(emoji: icon, size: 42, background: color.opacity(0.12))
                VStack(alignment: .leading, spacing: 5) {
                    Text(title)
                        .font(.system(size: 15, weight: .heavy, design: .rounded))
                        .foregroundStyle(Color.ybText)
                    Text(detail)
                        .font(.system(size: 12, weight: .medium, design: .rounded))
                        .foregroundStyle(Color.ybMuted)
                        .lineLimit(3)
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .heavy))
                    .foregroundStyle(Color.ybMuted)
            }
        }
        .buttonStyle(.plain)
    }
}
