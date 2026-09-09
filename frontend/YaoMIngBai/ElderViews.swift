import SwiftUI

enum ElderSection: String, CaseIterable {
    case today = "今天吃药"
    case medicines = "我的药"
    case family = "找家人"

    var emoji: String {
        switch self {
        case .today: return "⏰"
        case .medicines: return "💊"
        case .family: return "☎️"
        }
    }
}

struct ElderModeShell: View {
    @EnvironmentObject private var app: AppState
    @AppStorage("elderModeMemberName") private var elderModeMemberName = "爷爷"
    @State private var section: ElderSection = .today

    private var currentElderName: String {
        let trimmed = elderModeMemberName.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? "老人" : trimmed
    }

    private var elderCandidateNames: [String] {
        app.members.map { $0.name.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { app.isEligibleElderMember($0) }
    }

    private func ensureSelectedMemberIsValid() {
        if elderCandidateNames.contains(currentElderName) {
            return
        }

        if let elderCandidate = app.members.first(where: { member in
            app.isEligibleElderMember(member.name)
                && (member.name.contains("爷爷")
                    || member.name.contains("奶奶")
                    || member.role.contains("老人")
                    || member.emoji.contains("👴")
                    || member.emoji.contains("👵"))
        }) {
            elderModeMemberName = elderCandidate.name
        } else if let firstName = elderCandidateNames.first {
            elderModeMemberName = firstName
        } else {
            elderModeMemberName = "爷爷"
        }
    }

    var body: some View {
        PageBackground {
            VStack(spacing: 0) {
                elderTopBar

                ScrollView(showsIndicators: false) {
                    VStack(spacing: 16) {
                        switch section {
                        case .today:
                            ElderTodayPanel()
                        case .medicines:
                            ElderMedicinesPanel()
                        case .family:
                            ElderFamilyPanel()
                        }
                    }
                    .padding(.horizontal, 18)
                    .padding(.bottom, 18)
                }

                elderBottomBar
            }
        }
        .task {
            await app.refreshFromBackend()
            ensureSelectedMemberIsValid()
        }
    }

    private var elderTopBar: some View {
        HStack(spacing: 12) {
            Text("👴")
                .font(.system(size: 42))
                .frame(width: 58, height: 58)
                .background(Color.ybSoft)
                .clipShape(Circle())

            VStack(alignment: .leading, spacing: 4) {
                Text("\(currentElderName)老人模式")
                    .font(.system(size: 24, weight: .heavy, design: .rounded))
                Text("只显示和确认自己的用药")
                    .font(.system(size: 15, weight: .bold, design: .rounded))
                    .foregroundStyle(Color.ybMuted)
            }
            Spacer()
        }
        .padding(.horizontal, 18)
        .padding(.top, 10)
        .padding(.bottom, 12)
        .background(Color.ybScreen)
    }

    private var elderBottomBar: some View {
        HStack(spacing: 10) {
            ForEach(ElderSection.allCases, id: \.self) { item in
                Button {
                    section = item
                } label: {
                    VStack(spacing: 4) {
                        Text(item.emoji)
                            .font(.system(size: 24))
                        Text(item.rawValue)
                            .font(.system(size: 15, weight: .heavy, design: .rounded))
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 11)
                    .foregroundStyle(section == item ? Color.white : Color.ybPrimary)
                    .background(section == item ? Color.ybPrimary : Color.ybSoft)
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.horizontal, 14)
        .padding(.top, 10)
        .padding(.bottom, 12)
        .background(Color.white)
    }
}

struct ElderTodayPanel: View {
    @EnvironmentObject private var app: AppState
    @AppStorage("elderModeMemberName") private var elderModeMemberName = "爷爷"

    private var currentElderName: String {
        elderModeMemberName.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var elderItems: [TodayMedicationItem] {
        app.todayItemsForElder(currentElderName)
    }

    private var pendingItems: [TodayMedicationItem] {
        elderItems.filter { !$0.isCompleted }
    }

    private var completedItems: [TodayMedicationItem] {
        elderItems.filter(\.isCompleted)
    }

    var body: some View {
        HeroCard {
            Text(pendingItems.isEmpty ? "今天都吃完了" : "还有 \(pendingItems.count) 次药没确认")
                .font(.system(size: 28, weight: .heavy, design: .rounded))
            Text(pendingItems.isEmpty ? "家人可以看到你的用药已经完成。" : "请只确认自己的药，看清药名和用量后再点击。")
                .font(.system(size: 17, weight: .bold, design: .rounded))
                .opacity(0.94)

            HStack(spacing: 10) {
                MetricTile(number: "\(completedItems.count)", title: "已吃", tint: .ybGreen)
                MetricTile(number: "\(pendingItems.count)", title: "未吃", tint: .ybOrange)
            }
        }

        if let next = pendingItems.first {
            ElderDoseActionCard(item: next)
        } else if elderItems.isEmpty {
            ElderEmptyCard(title: "今天没有你的提醒", detail: "请让家人确认是否已经给你设置服药提醒。")
        } else {
            ElderEmptyCard(title: "不用再操作了", detail: "今天的提醒都已经确认。")
        }

        if !pendingItems.dropFirst().isEmpty {
            SectionTitle(title: "后面还要吃")
            ForEach(Array(pendingItems.dropFirst())) { item in
                ElderSimpleDoseRow(item: item)
            }
        }

        if !completedItems.isEmpty {
            SectionTitle(title: "已经吃过")
            ForEach(completedItems) { item in
                ElderSimpleDoseRow(item: item)
            }
        }
    }
}

struct ElderDoseActionCard: View {
    @EnvironmentObject private var app: AppState
    @AppStorage("elderModeMemberName") private var elderModeMemberName = "爷爷"
    var item: TodayMedicationItem

    private var currentElderName: String {
        elderModeMemberName.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var canOperate: Bool {
        app.canElderOperate(memberName: item.memberName, as: currentElderName)
    }

    var body: some View {
        YBCard(padding: 20) {
            Text("现在要确认")
                .font(.system(size: 22, weight: .heavy, design: .rounded))
                .foregroundStyle(Color.ybPrimary)

            HStack(spacing: 14) {
                EmojiCircle(emoji: "💊", size: 64)
                VStack(alignment: .leading, spacing: 8) {
                    Text(item.medicineName)
                        .font(.system(size: 30, weight: .heavy, design: .rounded))
                    Text("\(item.time) · \(item.mealLabel.isEmpty ? "按时服用" : item.mealLabel)")
                        .font(.system(size: 17, weight: .bold, design: .rounded))
                        .foregroundStyle(Color.ybMuted)
                }
            }

            VStack(alignment: .leading, spacing: 8) {
                ElderInfoLine(label: "一次吃", value: item.dose.isEmpty ? "请看说明书" : item.dose)
                ElderInfoLine(label: "给谁吃", value: item.memberName)
            }

            PrimaryButton(title: canOperate ? "我已经吃药了" : "不是我的用药，不能确认", systemImage: "checkmark.circle.fill", color: canOperate ? .ybPrimary : .ybMuted) {
                app.markTakenForElder(item: item, currentElderName: currentElderName)
            }
            .disabled(!canOperate)
            .opacity(canOperate ? 1 : 0.55)

            SecondaryButton(title: "听一遍", systemImage: "speaker.wave.2.fill") {
                app.speech.speak("现在需要服用 \(item.medicineName)。一次 \(item.dose.isEmpty ? "请按说明书核对剂量" : item.dose)。\(item.mealLabel)。吃完后请点击我已经吃药了。")
            }
        }
    }
}

struct ElderSimpleDoseRow: View {
    @EnvironmentObject private var app: AppState
    @AppStorage("elderModeMemberName") private var elderModeMemberName = "爷爷"
    var item: TodayMedicationItem

    private var currentElderName: String {
        elderModeMemberName.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var canOperate: Bool {
        app.canElderOperate(memberName: item.memberName, as: currentElderName)
    }

    var body: some View {
        YBCard(padding: 18) {
            HStack(spacing: 12) {
                Text(item.isCompleted ? "✅" : "⏰")
                    .font(.system(size: 34))
                VStack(alignment: .leading, spacing: 5) {
                    Text("\(item.time)  \(item.medicineName)")
                        .font(.system(size: 22, weight: .heavy, design: .rounded))
                    Text("\(item.memberName) · \(item.dose.isEmpty ? "剂量未填写" : item.dose)")
                        .font(.system(size: 15, weight: .bold, design: .rounded))
                        .foregroundStyle(Color.ybMuted)
                }
                Spacer()
                StatusPill(text: item.isCompleted ? "已吃" : "待吃", color: item.isCompleted ? .ybGreen : .ybOrange)
            }

            if item.isCompleted && canOperate {
                SecondaryButton(title: "点错了，取消", systemImage: "arrow.uturn.backward.circle.fill") {
                    app.cancelTakenForElder(item: item, currentElderName: currentElderName)
                }
            }
        }
    }
}

struct ElderMedicinesPanel: View {
    @EnvironmentObject private var app: AppState
    @AppStorage("elderModeMemberName") private var elderModeMemberName = "爷爷"

    private var currentElderName: String {
        elderModeMemberName.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var elderMedicines: [Medicine] {
        app.medicinesForElder(currentElderName)
    }

    var body: some View {
        HeroCard {
            Text("我的药")
                .font(.system(size: 28, weight: .heavy, design: .rounded))
            Text("只显示属于你的药名、吃法和存放位置。")
                .font(.system(size: 17, weight: .bold, design: .rounded))
                .opacity(0.94)
        }

        if elderMedicines.isEmpty {
            ElderEmptyCard(title: "还没有你的药品", detail: "请让家人先把你的药加入家庭药箱。")
        } else {
            ForEach(elderMedicines) { medicine in
                ElderMedicineLargeRow(medicine: medicine)
            }
        }
    }
}

struct ElderMedicineLargeRow: View {
    @EnvironmentObject private var app: AppState
    var medicine: Medicine

    var body: some View {
        YBCard(padding: 20) {
            HStack(spacing: 14) {
                EmojiCircle(emoji: medicine.emoji, size: 62)
                VStack(alignment: .leading, spacing: 6) {
                    Text(medicine.name)
                        .font(.system(size: 26, weight: .heavy, design: .rounded))
                    Text(medicine.owner.isEmpty ? "家庭药箱" : medicine.owner)
                        .font(.system(size: 15, weight: .bold, design: .rounded))
                        .foregroundStyle(Color.ybMuted)
                }
            }

            ElderInfoLine(label: "一次吃", value: medicine.dose.isEmpty ? "看说明书" : medicine.dose)
            ElderInfoLine(label: "什么时候", value: medicine.mealTime.isEmpty ? "按提醒" : medicine.mealTime)
            ElderInfoLine(label: "放在哪里", value: medicine.location.isEmpty ? "问家人" : medicine.location)

            SecondaryButton(title: "听一遍", systemImage: "speaker.wave.2.fill") {
            let text: String

            if !medicine.elderSpeechText
             .trimmingCharacters(
                 in: .whitespacesAndNewlines
              ).isEmpty {
               text = medicine.elderSpeechText
            } else if !medicine.speechText
               .trimmingCharacters(
                   in: .whitespacesAndNewlines
               ).isEmpty {
               text = medicine.speechText
            } else {
              text =
                 "\(medicine.name)，一次 \(medicine.dose)，\(medicine.mealTime)。用药前请再次核对。"
            }
                
                app.speech.speak(text)
            }
        }
    }
}

struct ElderFamilyPanel: View {
    @AppStorage("elderMode") private var elderMode = true

    var body: some View {
        HeroCard {
            Text("需要帮助就找家人")
                .font(.system(size: 28, weight: .heavy, design: .rounded))
            Text("不舒服或拿不准时，先找家人。")
                .font(.system(size: 17, weight: .bold, design: .rounded))
                .opacity(0.94)
        }

        YBCard(padding: 20) {
            HStack(spacing: 14) {
                EmojiCircle(emoji: "🆘", size: 66, background: Color.ybRed.opacity(0.12))
                VStack(alignment: .leading, spacing: 6) {
                    Text("一键找家人")
                        .font(.system(size: 28, weight: .heavy, design: .rounded))
                    Text("不舒服、忘记怎么吃药，就按这里。")
                        .font(.system(size: 16, weight: .bold, design: .rounded))
                        .foregroundStyle(Color.ybMuted)
                }
            }
            PrimaryButton(title: "联系家人", systemImage: "phone.fill", color: .ybRed) {}
        }

        YBCard(padding: 20) {
            Text("家人管理")
                .font(.system(size: 22, weight: .heavy, design: .rounded))
            Text("家人可以退出后管理药品和提醒。")
                .font(.system(size: 15, weight: .bold, design: .rounded))
                .foregroundStyle(Color.ybMuted)
            SecondaryButton(title: "退出老人模式", systemImage: "rectangle.portrait.and.arrow.right") {
                elderMode = false
            }
        }
    }
}

struct ElderInfoLine: View {
    var label: String
    var value: String

    var body: some View {
        HStack(alignment: .firstTextBaseline) {
            Text(label)
                .font(.system(size: 16, weight: .heavy, design: .rounded))
                .foregroundStyle(Color.ybMuted)
            Spacer()
            Text(value)
                .font(.system(size: 20, weight: .heavy, design: .rounded))
                .multilineTextAlignment(.trailing)
        }
        .padding(.vertical, 6)
    }
}

struct ElderEmptyCard: View {
    var title: String
    var detail: String

    var body: some View {
        YBCard(padding: 20) {
            HStack(spacing: 14) {
                EmojiCircle(emoji: "✅", size: 58, background: Color.ybSoft)
                VStack(alignment: .leading, spacing: 6) {
                    Text(title)
                        .font(.system(size: 24, weight: .heavy, design: .rounded))
                    Text(detail)
                        .font(.system(size: 16, weight: .bold, design: .rounded))
                        .foregroundStyle(Color.ybMuted)
                }
            }
        }
    }
}

// 以下几个 View 保留给普通模式里的历史导航入口使用；真正的老人模式由 ElderModeShell 接管整个 App。
struct ElderHomeView: View {
    var body: some View { ElderModeShell() }
}

struct ElderAlarmView: View {
    var body: some View { ElderModeShell() }
}

struct ElderMedicineDetailView: View {
    var body: some View { ElderModeShell() }
}

struct ElderMyMedicinesView: View {
    var body: some View { ElderModeShell() }
}

struct ElderMissedDoseView: View {
    var body: some View { ElderModeShell() }
}

struct ElderContactFamilyView: View {
    var body: some View { ElderModeShell() }
}

struct ElderSettingsView: View {
    var body: some View { ElderModeShell() }
}

struct FamilyContactRow: View {
    var emoji: String
    var name: String
    var detail: String

    var body: some View {
        YBCard {
            HStack(spacing: 12) {
                EmojiCircle(emoji: emoji, size: 50)
                VStack(alignment: .leading, spacing: 5) {
                    Text(name)
                        .font(.system(size: 18, weight: .heavy, design: .rounded))
                    Text(detail)
                        .font(.system(size: 14, weight: .bold, design: .rounded))
                        .foregroundStyle(Color.ybMuted)
                }
                Spacer()
            }
        }
    }
}
