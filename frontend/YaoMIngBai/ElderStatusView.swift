import SwiftUI

struct ElderStatusView: View {
    @EnvironmentObject private var app: AppState

    private var grandpaItems: [TodayMedicationItem] {
        app.todayItems.filter { $0.memberName == "爷爷" }
    }

    private var completedCount: Int {
        grandpaItems.filter(\.isCompleted).count
    }

    private var pendingCount: Int {
        grandpaItems.filter { !$0.isCompleted }.count
    }

    private var grandpaReminders: [ReminderPlan] {
        app.reminders.filter { $0.memberName == "爷爷" }
    }

    var body: some View {
        ScrollPage(title: "爷爷用药状态", subtitle: "家属协同", showBack: true, trailingSystemImage: "ellipsis") {
            HeroCard {
                Text(grandpaItems.isEmpty ? "爷爷还没有今日提醒" : "爷爷今日完成 \(completedCount)/\(grandpaItems.count)")
                    .font(.system(size: 22, weight: .heavy, design: .rounded))
                Text(pendingCount == 0 ? "今天没有待服药提醒。" : "还有 \(pendingCount) 条用药提醒待服药。")
                    .font(.ybBody)
                    .opacity(0.92)

                HStack(spacing: 10) {
                    MetricTile(number: "\(completedCount)", title: "已服药", tint: .ybGreen)
                    MetricTile(number: "\(pendingCount)", title: "待服药", tint: .ybOrange)
                    MetricTile(number: "\(grandpaReminders.count)", title: "提醒", tint: .ybBlue)
                }
            }

            YBCard {
                SectionTitle(title: "今日用药", trailing: "爷爷")
                if grandpaItems.isEmpty {
                    Text("还没有给爷爷设置提醒。")
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                } else {
                    ForEach(grandpaItems) { item in
                        ReminderRow(reminder: ReminderPlan(backendID: item.reminderBackendID, medicineName: item.medicineName, memberName: item.memberName, time: item.time, mealLabel: item.mealLabel, dose: item.dose, status: item.status))
                        Divider()
                    }
                }
                HStack(spacing: 10) {
                    PrimaryButton(title: "打电话提醒", systemImage: "phone.fill") {}
                    SecondaryButton(title: "帮爷爷设提醒", systemImage: "alarm.fill") {
                        app.pendingReminderMember = "爷爷"
                        app.path.append(Route.reminderSetting)
                    }
                }
            }

            SectionTitle(title: "爷爷的药")
            let medicines = app.medicines(for: "爷爷")
            if medicines.isEmpty {
                YBCard {
                    Text("还没有给爷爷保存药品。")
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                }
            } else {
                ForEach(medicines, id: \.id) { medicine in
                    MedicineListRow(medicine: medicine) {
                        app.currentMedicine = medicine
                        app.path.append(Route.medicineDetail)
                    }
                }
            }
        }
        .refreshable {
            await app.refreshFromBackend()
        }
    }
}

struct ReminderRow: View {
    var reminder: ReminderPlan

    var body: some View {
        HStack(spacing: 10) {
            Text(reminder.status.contains("已") ? "✓" : "!")
                .font(.system(size: 16, weight: .heavy))
                .frame(width: 30, height: 30)
                .foregroundStyle(reminder.status.contains("已") ? Color.ybGreen : Color.ybOrange)
                .background((reminder.status.contains("已") ? Color.ybGreen : Color.ybOrange).opacity(0.12))
                .clipShape(Circle())

            VStack(alignment: .leading, spacing: 4) {
                Text("\(reminder.time) \(reminder.medicineName) \(reminder.dose)")
                    .font(.system(size: 14, weight: .heavy, design: .rounded))
                Text(reminder.status.contains("已") ? "已服药" : "待服药")
                    .font(.ybCaption)
                    .foregroundStyle(Color.ybMuted)
            }
            Spacer()
        }
    }
}
