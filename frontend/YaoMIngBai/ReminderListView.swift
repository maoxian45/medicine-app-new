import SwiftUI

struct ReminderListView: View {
    @EnvironmentObject private var app: AppState
    @State private var memberFilter = "全部"
    @State private var reminderToDelete: ReminderPlan? = nil

    private var memberOptions: [String] {
        let names = Set(app.reminders.map(\.memberName))
        return ["全部"] + names.sorted()
    }

    private var filteredReminders: [ReminderPlan] {
        guard memberFilter != "全部" else { return app.reminders }
        return app.reminders.filter { $0.memberName == memberFilter }
    }

    private var pendingCount: Int {
        app.todayPending
    }

    private var completedCount: Int {
        app.todayCompleted
    }

    var body: some View {
        ScrollPage(title: "提醒列表", subtitle: "已设置的服药计划", showBack: true, trailingSystemImage: "bell.badge.fill") {
            HeroCard {
                Text("提醒计划概览")
                    .font(.system(size: 20, weight: .heavy, design: .rounded))
                Text(app.reminders.isEmpty ? "还没有提醒计划。" : "提醒计划会同步到今日状态，确认服药后首页也会更新。")
                    .font(.ybBody)
                    .opacity(0.92)

                HStack(spacing: 10) {
                    MetricTile(number: "\(app.reminders.count)", title: "全部计划", tint: .ybPrimary)
                    MetricTile(number: "\(pendingCount)", title: "待服药", tint: .ybOrange)
                    MetricTile(number: "\(completedCount)", title: "已服药", tint: .ybGreen)
                }
            }

            if memberOptions.count > 1 {
                YBCard {
                    SelectionBlock(title: "成员筛选", subtitle: "按服药对象查看", options: memberOptions, selected: $memberFilter)
                }
            }

            if filteredReminders.isEmpty {
                YBCard {
                    HStack(alignment: .top, spacing: 12) {
                        EmojiCircle(emoji: "🔔", size: 46, background: Color.ybSoft)
                        VStack(alignment: .leading, spacing: 5) {
                            Text("还没有提醒计划")
                                .font(.system(size: 16, weight: .heavy, design: .rounded))
                            Text("先设置一个提醒，保存后就能在这里查看。")
                                .font(.ybCaption)
                                .foregroundStyle(Color.ybMuted)
                        }
                    }
                }
            } else {
                SectionTitle(title: "计划列表", trailing: "共 \(filteredReminders.count) 条")
                ForEach(filteredReminders) { reminder in
                    ReminderPlanCard(
                        reminder: reminder,
                        todayItem: todayItem(for: reminder),
                        markTaken: { app.markTaken(reminder: reminder) },
                        cancelTaken: { app.cancelTaken(reminder: reminder) },
                        requestDelete: { reminderToDelete = reminder }
                    )
                }
            }

            PrimaryButton(title: "新增提醒", systemImage: "plus.circle.fill") {
                app.pendingReminderMedicine = nil
                if memberFilter != "全部" {
                    app.pendingReminderMember = memberFilter
                }
                app.path.append(Route.reminderSetting)
            }
        }
        .alert("删除提醒？", isPresented: Binding(
            get: { reminderToDelete != nil },
            set: { if !$0 { reminderToDelete = nil } }
        )) {
            Button("取消", role: .cancel) { reminderToDelete = nil }
            Button("删除", role: .destructive) {
                if let reminder = reminderToDelete {
                    Task { await app.deleteReminder(reminder) }
                }
                reminderToDelete = nil
            }
        } message: {
            Text("删除后，这条提醒不会再出现在今日用药计划中。")
        }
        .refreshable {
            await app.refreshFromBackend()
        }
    }

    private func todayItem(for reminder: ReminderPlan) -> TodayMedicationItem? {
        app.todayItems.first { item in
            if let reminderID = reminder.backendID, item.reminderBackendID == reminderID { return true }
            return item.medicineName == reminder.medicineName
                && item.memberName == reminder.memberName
                && item.time == reminder.time
        }
    }
}

struct ReminderPlanCard: View {
    var reminder: ReminderPlan
    var todayItem: TodayMedicationItem?
    var markTaken: () -> Void
    var cancelTaken: () -> Void
    var requestDelete: () -> Void

    private var isCompleted: Bool {
        todayItem?.isCompleted == true || reminder.status.contains("已") || reminder.status.contains("完成")
    }

    private var statusColor: Color {
        if isCompleted { return .ybGreen }
        if reminder.status.contains("稍后") { return .ybBlue }
        return .ybOrange
    }

    var body: some View {
        YBCard {
            HStack(alignment: .top, spacing: 12) {
                EmojiCircle(emoji: "⏰", size: 46, background: Color.ybSoft)
                VStack(alignment: .leading, spacing: 5) {
                    Text(reminder.medicineName)
                        .font(.system(size: 17, weight: .heavy, design: .rounded))
                    Text("\(reminder.memberName) · \(reminder.mealLabel) · \(reminder.dose.isEmpty ? "剂量未填写" : reminder.dose)")
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                }
                Spacer()
                StatusPill(text: isCompleted ? "已服药" : "待服药", color: statusColor)
            }

            Divider()

            HStack {
                Label(reminder.time, systemImage: "clock.fill")
                    .font(.system(size: 15, weight: .heavy, design: .rounded))
                    .foregroundStyle(Color.ybPrimary)
                Spacer()
                Text("每日提醒")
                    .font(.ybCaption)
                    .foregroundStyle(Color.ybMuted)
            }

            if isCompleted {
                SecondaryButton(title: "点错了，取消已服药", systemImage: "arrow.uturn.backward.circle.fill") {
                    cancelTaken()
                }
            } else {
                PrimaryButton(title: "标记已服药", systemImage: "checkmark.circle.fill") {
                    markTaken()
                }
            }

            PrimaryButton(title: "删除这条提醒", systemImage: "trash.fill", color: .ybRed) {
                requestDelete()
            }
        }
    }
}
