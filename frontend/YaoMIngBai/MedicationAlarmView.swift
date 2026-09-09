import SwiftUI

struct MedicationAlarmView: View {
    @EnvironmentObject private var app: AppState

    var body: some View {
        PageBackground {
            VStack(spacing: 18) {
                Spacer(minLength: 20)
                EmojiCircle(emoji: "⏰", size: 82, background: Color.ybSoft)
                Text("服药时间到了")
                    .font(.system(size: 28, weight: .heavy, design: .rounded))
                Text("现在是晚上 8:00，请确认是否需要服用“\(app.currentMedicine.name)”。")
                    .font(.ybBody)
                    .foregroundStyle(Color.ybMuted)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 32)

                YBCard {
                    InfoRow(label: "药品名称", value: app.currentMedicine.name)
                    Divider()
                    InfoRow(label: "一次用量", value: app.currentMedicine.dose)
                    Divider()
                    InfoRow(label: "服用时间", value: app.currentMedicine.mealTime)
                    Divider()
                    Text("请以医生、药师建议及药品正式说明书为准。")
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                }
                .padding(.horizontal, 18)

                VStack(spacing: 10) {
                    PrimaryButton(title: "已服药", systemImage: "checkmark.circle.fill") {
                        app.markTaken(medicineName: app.currentMedicine.name, dose: app.currentMedicine.dose)
                    }
                    SecondaryButton(title: "稍后提醒", systemImage: "clock.fill") {
                        Task {
                            try? await app.notifications.scheduleDemoReminder(title: "稍后提醒", body: "请再次确认是否需要服用 \(app.currentMedicine.name)。", secondsFromNow: 8)
                        }
                    }
                    SecondaryButton(title: "查看说明", systemImage: "doc.text.fill") {
                        app.path.append(Route.medicineCard)
                    }
                }
                .padding(.horizontal, 18)

                Spacer()
            }
        }
    }
}
