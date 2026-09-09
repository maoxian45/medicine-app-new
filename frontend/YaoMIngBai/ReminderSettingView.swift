import SwiftUI

struct ReminderSettingView: View {
    @EnvironmentObject private var app: AppState
    @State private var member = ""
    @State private var selectedMedicineKey = ""
    @State private var times = "2 次"
    @State private var reminderTimes: [Date] = ReminderSettingView.defaultReminderTimes(count: 2)
    @State private var relation = "饭后"
    @State private var course = "5 天"
    @State private var missedDose = true
    @State private var savedMessage = ""
    @State private var isSaving = false

    private var memberOptions: [String] {
        let names = app.members.map(\.name)
        return names.isEmpty ? ["我", "爷爷", "奶奶", "小宝"] : names
    }

    private var medicineOptions: [Medicine] {
        let savedMedicines = app.medicines.filter { !$0.name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        guard !member.isEmpty else { return savedMedicines }
        return savedMedicines.filter { medicine in
            app.medicineIsAvailable(medicine, for: member)
        }
    }

    private var selectedMedicine: Medicine? {
        medicineOptions.first { medicineKey($0) == selectedMedicineKey }
    }

    private let timeOptions = ["1 次", "2 次", "3 次"]
    private let relationOptions = ["饭前", "饭后", "睡前", "无要求"]
    private let courseOptions = ["3 天", "5 天", "7 天", "长期"]

    private var selectedTimes: [String] {
        reminderTimes.map(Self.formatTime)
    }

    var body: some View {
        ScrollPage(title: "设置服药提醒", subtitle: selectedMedicine?.name ?? "请选择药品后保存", showBack: true, trailingSystemImage: "checkmark") {
            YBCard {
                SelectionBlock(title: "服药对象", subtitle: "先选择给谁提醒", options: memberOptions, selected: $member)
            }

            YBCard {
                SectionTitle(title: "选择药品", trailing: selectedMedicine == nil ? "必选" : "已选")
                if app.medicines.isEmpty {
                    EmptyMedicineHint(text: "家庭药箱还没有药品。请先添加药品，再为它设置提醒。")
                } else if medicineOptions.isEmpty {
                    EmptyMedicineHint(text: "还没有给 \(member.isEmpty ? "该成员" : member) 添加药品。请先把药品加入家庭药箱，并选择对应成员。")
                } else {
                    VStack(spacing: 10) {
                        ForEach(medicineOptions) { medicine in
                            MedicinePickRow(
                                medicine: medicine,
                                selected: medicineKey(medicine) == selectedMedicineKey
                            ) {
                                selectMedicine(medicine)
                            }
                        }
                    }
                }
            }

            YBCard {
                SelectionBlock(title: "每日次数", subtitle: selectedMedicine == nil ? "选药后可改" : "按说明书核对", options: timeOptions, selected: $times)
            }

            YBCard {
                SectionTitle(title: "提醒时间", trailing: "自由选择小时和分钟")
                VStack(spacing: 10) {
                    ForEach(reminderTimes.indices, id: \.self) { index in
                        HStack {
                            Text("第 \(index + 1) 次")
                                .font(.ybBody)
                            Spacer()
                            DatePicker(
                                "第 \(index + 1) 次提醒时间",
                                selection: $reminderTimes[index],
                                displayedComponents: .hourAndMinute
                            )
                            .labelsHidden()
                            .datePickerStyle(.compact)
                        }
                        .padding(.vertical, 4)
                    }
                }
                Text("每天会按以上时间分别创建提醒，保存前请确认符合医生、药师建议或正式说明书。")
                    .font(.ybCaption)
                    .foregroundStyle(Color.ybMuted)
            }

            YBCard {
                SelectionBlock(title: "服用关系", subtitle: "可修改", options: relationOptions, selected: $relation)
            }

            YBCard {
                SelectionBlock(title: "疗程", subtitle: "可长期提醒", options: courseOptions, selected: $course)
                Toggle("开启漏服提醒", isOn: $missedDose)
                    .font(.ybBody)
                    .tint(.ybPrimary)
            }

            YBCard {
                HStack(alignment: .top, spacing: 12) {
                    EmojiCircle(emoji: "ℹ️", size: 38, background: Color.ybBlue.opacity(0.12))
                    Text("保存前请确认提醒计划符合医生、药师建议或正式说明书。")
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                }
            }

            if !savedMessage.isEmpty {
                Text(savedMessage)
                    .font(.ybCaption)
                    .foregroundStyle(Color.ybPrimary)
                    .frame(maxWidth: .infinity, alignment: .center)

                SecondaryButton(title: "查看提醒列表", systemImage: "list.bullet.clipboard.fill") {
                    app.path.append(Route.reminderList)
                }
            }

            PrimaryButton(title: isSaving ? "保存中..." : "保存提醒计划", systemImage: "checkmark.circle.fill") {
                Task { await saveReminders() }
            }
            .disabled(isSaving || member.isEmpty || selectedMedicine == nil)
            .opacity(isSaving || member.isEmpty || selectedMedicine == nil ? 0.45 : 1)
        }
        .onAppear(perform: applyPendingContext)
        .onChange(of: times) { _ in
            syncReminderTimes()
            savedMessage = ""
        }
        .onChange(of: member) { _ in
            if let selectedMedicine, !medicineOptions.contains(where: { medicineKey($0) == medicineKey(selectedMedicine) }) {
                selectedMedicineKey = ""
            }
            savedMessage = ""
        }
    }

    private static func defaultReminderTimes(count: Int) -> [Date] {
        let defaults = [(8, 0), (14, 0), (20, 0)]
        return defaults.prefix(max(1, min(count, defaults.count))).map { hour, minute in
            Calendar.current.date(bySettingHour: hour, minute: minute, second: 0, of: Date()) ?? Date()
        }
    }

    private static func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: date)
    }

    private func syncReminderTimes() {
        let desiredCount = Int(times.split(separator: " ").first ?? "2") ?? 2
        let defaults = Self.defaultReminderTimes(count: desiredCount)
        if reminderTimes.count < desiredCount {
            reminderTimes.append(contentsOf: defaults.dropFirst(reminderTimes.count))
        } else if reminderTimes.count > desiredCount {
            reminderTimes = Array(reminderTimes.prefix(desiredCount))
        }
    }

    private func applyPendingContext() {
        if member.isEmpty {
            if let pendingMember = app.pendingReminderMember, memberOptions.contains(pendingMember) {
                member = pendingMember
                app.pendingReminderMember = nil
            } else {
                member = memberOptions.first ?? "我"
            }
        }

        if selectedMedicineKey.isEmpty,
           let pendingMedicine = app.pendingReminderMedicine {
            if member != pendingMedicine.owner
                && !pendingMedicine.owner.isEmpty
                && !app.isSharedMedicineOwner(pendingMedicine.owner) {
                member = pendingMedicine.owner
            }
            if let matched = medicineOptions.first(where: { sameMedicine($0, pendingMedicine) }) {
                selectMedicine(matched)
            }
            app.pendingReminderMedicine = nil
        }
    }

    private func selectMedicine(_ medicine: Medicine) {
        selectedMedicineKey = medicineKey(medicine)
        savedMessage = ""

        let frequency = medicine.frequency.trimmingCharacters(in: .whitespacesAndNewlines)
        if frequency.contains("3") || frequency.contains("三") {
            times = "3 次"
        } else if frequency.contains("1") || frequency.contains("一") || frequency.contains("需要时") {
            times = "1 次"
        } else if frequency.contains("2") || frequency.contains("二") || frequency.contains("两") {
            times = "2 次"
        }

        let meal = medicine.mealTime.trimmingCharacters(in: .whitespacesAndNewlines)
        if meal.contains("饭前") {
            relation = "饭前"
        } else if meal.contains("睡前") {
            relation = "睡前"
        } else if meal.contains("无") {
            relation = "无要求"
        } else if meal.contains("饭后") || meal.isEmpty == false {
            relation = "饭后"
        }
    }

    private func saveReminders() async {
        guard !member.isEmpty else { return }
        guard let medicine = selectedMedicine else {
            savedMessage = "请先选择要提醒的药品。"
            return
        }
        guard Set(selectedTimes).count == selectedTimes.count else {
            savedMessage = "每次提醒请选择不同的时间。"
            return
        }

        isSaving = true
        defer { isSaving = false }

        do {
            var savedCount = 0
            for time in selectedTimes {
                let reminder = ReminderPlan(
                    medicineBackendID: medicine.backendID,
                    medicineName: medicine.name,
                    memberName: member,
                    time: time,
                    mealLabel: relation,
                    dose: medicine.dose,
                    status: "待服药"
                )
                _ = try await app.saveReminder(reminder)
                savedCount += 1
            }

            for reminderDate in reminderTimes {
                let components = Calendar.current.dateComponents([.hour, .minute], from: reminderDate)
                if let hour = components.hour, let minute = components.minute {
                    try? await app.notifications.scheduleDailyReminder(
                        title: NotificationService.dailyReminderTitle(medicineName: medicine.name, memberName: member),
                        body: "请确认是否需要服用 \(medicine.name)。",
                        hour: hour,
                        minute: minute
                    )
                }
            }
            savedMessage = "已为 \(member) 的 \(medicine.name) 保存 \(savedCount) 条提醒。"
        } catch {
            savedMessage = "保存失败，请确认后端正在运行后重试。"
        }
    }

    private func medicineKey(_ medicine: Medicine) -> String {
        if let backendID = medicine.backendID {
            return "backend-\(backendID)"
        }
        return medicine.id.uuidString
    }

    private func sameMedicine(_ lhs: Medicine, _ rhs: Medicine) -> Bool {
        if let leftID = lhs.backendID, let rightID = rhs.backendID {
            return leftID == rightID
        }
        return lhs.name == rhs.name
            && lhs.spec == rhs.spec
            && lhs.owner == rhs.owner
            && lhs.location == rhs.location
    }
}

private struct MedicinePickRow: View {
    var medicine: Medicine
    var selected: Bool
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                EmojiCircle(emoji: medicine.emoji, size: 42, background: selected ? Color.ybPrimary.opacity(0.14) : Color.ybSoft)
                VStack(alignment: .leading, spacing: 4) {
                    Text(medicine.name)
                        .font(.system(size: 16, weight: .heavy, design: .rounded))
                        .foregroundStyle(Color.ybText)
                    Text("\(medicine.owner.isEmpty ? "未指定成员" : medicine.owner) · \(medicine.dose.isEmpty ? "剂量未填写" : medicine.dose) · \(medicine.location.isEmpty ? "位置未填写" : medicine.location)")
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                }
                Spacer()
                Image(systemName: selected ? "checkmark.circle.fill" : "circle")
                    .font(.system(size: 22, weight: .heavy))
                    .foregroundStyle(selected ? Color.ybPrimary : Color.ybMuted.opacity(0.45))
            }
            .padding(12)
            .background(selected ? Color.ybSoft : Color.ybScreen)
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        }
        .buttonStyle(.plain)
    }
}

private struct EmptyMedicineHint: View {
    var text: String
    @EnvironmentObject private var app: AppState

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(text)
                .font(.ybBody)
                .foregroundStyle(Color.ybText)
            SecondaryButton(title: "先添加药品", systemImage: "plus.circle.fill") {
                app.path.append(Route.addMedicine)
            }
        }
    }
}

struct SelectionBlock: View {
    var title: String
    var subtitle: String
    var options: [String]
    @Binding var selected: String

    var body: some View {
        SectionTitle(title: title, trailing: subtitle)
        FlowLayout(spacing: 8) {
            ForEach(options, id: \.self) { option in
                Button {
                    selected = option
                } label: {
                    Text(option)
                        .font(.system(size: 13, weight: .heavy, design: .rounded))
                        .padding(.horizontal, 14)
                        .padding(.vertical, 9)
                        .foregroundStyle(selected == option ? Color.white : Color.ybPrimary)
                        .background(selected == option ? Color.ybPrimary : Color.ybSoft)
                        .clipShape(Capsule())
                }
                .buttonStyle(.plain)
            }
        }
    }
}

struct TimeTile: View {
    var time: String
    var label: String
    var active: Bool

    var body: some View {
        VStack(spacing: 6) {
            Text(time)
                .font(.system(size: 17, weight: .heavy, design: .rounded))
            Text(label)
                .font(.system(size: 11, weight: .bold, design: .rounded))
                .foregroundStyle(active ? Color.ybPrimaryDark : Color.ybMuted)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 14)
        .foregroundStyle(active ? Color.ybPrimary : Color.ybMuted)
        .background(active ? Color.ybSoft : Color.ybScreen)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }
}
